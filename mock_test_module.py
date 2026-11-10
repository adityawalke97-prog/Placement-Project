"""Mock test module for an existing Flask + PyMySQL application.

Integration:
    from mock_test_module import create_mock_test_blueprint
    app.register_blueprint(create_mock_test_blueprint(get_db_connection))

Expected existing app conventions:
    - get_db_connection() returns a PyMySQL connection
    - session['user_id'] is set for authenticated users
    - session['role'] is 'admin' for administrators
    - endpoint 'login' exists
"""
from __future__ import annotations

import secrets
from functools import wraps
from urllib.parse import urljoin

import pymysql
from flask import (Blueprint, abort, current_app, flash, redirect, render_template,
                   request, session, url_for)


def create_mock_test_blueprint(get_db_connection):
    bp = Blueprint(
        "mock_tests", __name__,
        template_folder="templates",
        static_folder="static",
        static_url_path="/mock-tests-static",
        url_prefix="/mock-tests",
    )

    def db_cursor():
        conn = get_db_connection()
        return conn, conn.cursor(pymysql.cursors.DictCursor)

    def login_required(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not session.get("user_id"):
                flash("Please login to use Mock Tests.", "warning")
                return redirect(url_for("login", next=request.url))
            return view(*args, **kwargs)
        return wrapped

    def admin_required(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not session.get("user_id"):
                return redirect(url_for("login", next=request.url))
            if str(session.get("role", "")).lower() != "admin":
                abort(403)
            return view(*args, **kwargs)
        return wrapped

    def fetch_one(sql, params=()):
        conn, cur = db_cursor()
        try:
            cur.execute(sql, params)
            return cur.fetchone()
        finally:
            cur.close(); conn.close()

    def fetch_all(sql, params=()):
        conn, cur = db_cursor()
        try:
            cur.execute(sql, params)
            return cur.fetchall()
        finally:
            cur.close(); conn.close()

    def execute(sql, params=()):
        conn, cur = db_cursor()
        try:
            cur.execute(sql, params)
            conn.commit()
            return cur.lastrowid, cur.rowcount
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close(); conn.close()

    def user_label(user_id):
        user = fetch_one("SELECT name, email FROM users WHERE id=%s", (user_id,))
        return (user or {}).get("name") or (user or {}).get("email") or f"User {user_id}"

    @bp.app_context_processor
    def inject_mock_helpers():
        return {"mock_user_id": session.get("user_id")}

    @bp.route("/")
    @login_required
    def home():
        groups = fetch_all("""SELECT level_group, COUNT(*) AS course_count
                              FROM mock_catalog_courses WHERE is_active=1
                              GROUP BY level_group
                              ORDER BY FIELD(level_group,'School','College','Professional IT')""")
        recent = fetch_all("""SELECT t.id,t.title,t.share_token,t.created_at,t.time_limit_minutes,
                                   c.course_name, COUNT(DISTINCT a.id) AS attempts
                            FROM mock_tests t
                            JOIN mock_catalog_courses c ON c.id=t.course_id
                            LEFT JOIN mock_attempts a ON a.test_id=t.id AND a.status='submitted'
                            WHERE t.created_by=%s AND t.is_active=1
                            GROUP BY t.id ORDER BY t.created_at DESC LIMIT 5""", (session["user_id"],))
        return render_template("mock_tests/home.html", groups=groups, recent=recent)

    @bp.route("/courses")
    @login_required
    def courses():
        group = request.args.get("group", "")
        level = request.args.get("level", "")
        sql = "SELECT * FROM mock_catalog_courses WHERE is_active=1"
        params = []
        if group:
            sql += " AND level_group=%s"; params.append(group)
        if level:
            sql += " AND education_level=%s"; params.append(level)
        sql += " ORDER BY sort_order, course_name"
        rows = fetch_all(sql, tuple(params))
        return render_template("mock_tests/courses.html", courses=rows, selected_group=group, selected_level=level)

    @bp.route("/course/<slug>")
    @login_required
    def course_detail(slug):
        course = fetch_one("SELECT * FROM mock_catalog_courses WHERE slug=%s AND is_active=1", (slug,))
        if not course:
            abort(404)
        subjects = fetch_all("""SELECT s.*, COUNT(q.id) AS question_count
                               FROM mock_catalog_subjects s
                               LEFT JOIN mock_question_bank q ON q.subject_id=s.id AND q.is_active=1
                               WHERE s.course_id=%s GROUP BY s.id ORDER BY s.sort_order,s.subject_name""", (course["id"],))
        categories = fetch_all("""SELECT DISTINCT difficulty FROM mock_question_bank q
                                 JOIN mock_catalog_subjects s ON s.id=q.subject_id
                                 WHERE s.course_id=%s AND q.is_active=1 ORDER BY FIELD(difficulty,'Easy','Medium','Hard')""", (course["id"],))
        return render_template("mock_tests/course_detail.html", course=course, subjects=subjects, difficulties=categories)

    @bp.route("/start", methods=["POST"])
    @login_required
    def start_standard():
        subject_id = request.form.get("subject_id", type=int)
        difficulty = request.form.get("difficulty", "All")
        count = max(5, min(request.form.get("question_count", 20, type=int), 100))
        if not subject_id:
            flash("Please select a subject.", "warning"); return redirect(url_for("mock_tests.courses"))
        subject = fetch_one("""SELECT s.id,s.subject_name,s.course_id,c.slug,c.course_name
                               FROM mock_catalog_subjects s JOIN mock_catalog_courses c ON c.id=s.course_id
                               WHERE s.id=%s AND c.is_active=1""", (subject_id,))
        if not subject:
            abort(404)
        where = "q.subject_id=%s AND q.is_active=1"; params = [subject_id]
        if difficulty in ("Easy", "Medium", "Hard"):
            where += " AND q.difficulty=%s"; params.append(difficulty)
        available = fetch_one(f"SELECT COUNT(*) AS total FROM mock_question_bank q WHERE {where}", tuple(params))["total"]
        if available < 1:
            flash("Is subject aur level ke liye abhi questions available nahi hain. Admin ko question bank add karna hoga.", "info")
            return redirect(url_for("mock_tests.course_detail", slug=subject["slug"]))
        count = min(count, available)
        title = f"{subject['course_name']} · {subject['subject_name']}"
        test_id, _ = execute("""INSERT INTO mock_tests
            (title,course_id,subject_id,created_by,is_custom,share_token,time_limit_minutes,is_active)
            VALUES (%s,%s,%s,%s,0,%s,%s,1)""",
            (title, subject["course_id"], subject_id, session["user_id"], secrets.token_urlsafe(18), max(10, count * 1),))
        questions = fetch_all(f"SELECT id FROM mock_question_bank q WHERE {where} ORDER BY RAND() LIMIT %s", tuple(params + [count]))
        conn, cur = db_cursor()
        try:
            for index, q in enumerate(questions, 1):
                cur.execute("INSERT INTO mock_test_questions (test_id,question_id,question_order) VALUES (%s,%s,%s)", (test_id,q["id"],index))
            conn.commit()
        except Exception:
            conn.rollback(); raise
        finally:
            cur.close(); conn.close()
        return redirect(url_for("mock_tests.take_test", token=fetch_one("SELECT share_token FROM mock_tests WHERE id=%s", (test_id,))["share_token"]))

    @bp.route("/custom/create", methods=["GET", "POST"])
    @login_required
    def custom_create():
        courses_list = fetch_all("SELECT * FROM mock_catalog_courses WHERE is_active=1 ORDER BY sort_order,course_name")
        if request.method == "POST":
            course_id = request.form.get("course_id", type=int)
            subject_id = request.form.get("subject_id", type=int)
            title = (request.form.get("title") or "").strip()[:150]
            difficulty = request.form.get("difficulty", "All")
            count = max(5, min(request.form.get("question_count", 20, type=int), 100))
            minutes = max(5, min(request.form.get("time_limit", 30, type=int), 240))
            if difficulty not in ("All", "Easy", "Medium", "Hard"):
                difficulty = "All"
            subject = fetch_one("SELECT * FROM mock_catalog_subjects WHERE id=%s AND course_id=%s", (subject_id,course_id))
            course = fetch_one("SELECT * FROM mock_catalog_courses WHERE id=%s AND is_active=1", (course_id,))
            if not course or not subject:
                flash("Please select a valid course and subject.", "danger")
                return render_template("mock_tests/custom_create.html", courses=courses_list)
            where = "subject_id=%s AND is_active=1"; params = [subject_id]
            if difficulty != "All":
                where += " AND difficulty=%s"; params.append(difficulty)
            available = fetch_one(f"SELECT COUNT(*) AS total FROM mock_question_bank WHERE {where}", tuple(params))["total"]
            if available < 5:
                flash(f"Selected subject mein sirf {available} questions hain. Kam se kam 5 required hain.", "warning")
                return render_template("mock_tests/custom_create.html", courses=courses_list)
            count = min(count, available)
            token = secrets.token_urlsafe(24)
            title = title or f"{course['course_name']} - {subject['subject_name']} Challenge"
            test_id, _ = execute("""INSERT INTO mock_tests
                (title,course_id,subject_id,created_by,is_custom,share_token,time_limit_minutes,is_active)
                VALUES (%s,%s,%s,%s,1,%s,%s,1)""",
                (title,course_id,subject_id,session["user_id"],token,minutes))
            questions = fetch_all(f"SELECT id FROM mock_question_bank WHERE {where} ORDER BY RAND() LIMIT %s", tuple(params+[count]))
            conn, cur = db_cursor()
            try:
                for index, q in enumerate(questions, 1):
                    cur.execute("INSERT INTO mock_test_questions (test_id,question_id,question_order) VALUES (%s,%s,%s)", (test_id,q["id"],index))
                conn.commit()
            except Exception:
                conn.rollback(); raise
            finally:
                cur.close(); conn.close()
            return redirect(url_for("mock_tests.custom_created", token=token))
        return render_template("mock_tests/custom_create.html", courses=courses_list)

    @bp.route("/custom/created/<token>")
    @login_required
    def custom_created(token):
        test = fetch_one("""SELECT t.*,c.course_name,s.subject_name FROM mock_tests t
                           JOIN mock_catalog_courses c ON c.id=t.course_id
                           JOIN mock_catalog_subjects s ON s.id=t.subject_id
                           WHERE t.share_token=%s AND t.created_by=%s AND t.is_active=1""", (token,session["user_id"]))
        if not test: abort(404)
        share_url = url_for("mock_tests.take_test", token=token, _external=True)
        board_url = url_for("mock_tests.leaderboard", token=token, _external=True)
        return render_template("mock_tests/custom_created.html", test=test, share_url=share_url, board_url=board_url)

    @bp.route("/share/<token>")
    @login_required
    def take_test(token):
        test = fetch_one("""SELECT t.*,c.course_name,s.subject_name FROM mock_tests t
                           JOIN mock_catalog_courses c ON c.id=t.course_id
                           JOIN mock_catalog_subjects s ON s.id=t.subject_id
                           WHERE t.share_token=%s AND t.is_active=1""", (token,))
        if not test: abort(404)
        previous = fetch_one("SELECT id,status FROM mock_attempts WHERE test_id=%s AND user_id=%s", (test["id"],session["user_id"]))
        if previous:
            if previous["status"] == "submitted":
                return redirect(url_for("mock_tests.result", attempt_id=previous["id"]))
            return redirect(url_for("mock_tests.attempt", attempt_id=previous["id"]))
        attempt_id, _ = execute("INSERT INTO mock_attempts (test_id,user_id,status,started_at) VALUES (%s,%s,'in_progress',NOW())", (test["id"],session["user_id"]))
        return redirect(url_for("mock_tests.attempt", attempt_id=attempt_id))

    @bp.route("/attempt/<int:attempt_id>")
    @login_required
    def attempt(attempt_id):
        attempt_row = fetch_one("""SELECT a.*,t.title,t.time_limit_minutes,t.id AS test_id,t.share_token,
                                         GREATEST(0,TIMESTAMPDIFF(SECOND,NOW(),DATE_ADD(a.started_at, INTERVAL t.time_limit_minutes MINUTE))) AS seconds_left,
                                         c.course_name,s.subject_name
                                  FROM mock_attempts a JOIN mock_tests t ON t.id=a.test_id
                                  JOIN mock_catalog_courses c ON c.id=t.course_id
                                  JOIN mock_catalog_subjects s ON s.id=t.subject_id
                                  WHERE a.id=%s AND a.user_id=%s AND a.status='in_progress'""", (attempt_id,session["user_id"]))
        if not attempt_row: abort(404)
        questions = fetch_all("""SELECT q.id,q.question_text,q.option_a,q.option_b,q.option_c,q.option_d,m.question_order
                               FROM mock_test_questions m JOIN mock_question_bank q ON q.id=m.question_id
                               WHERE m.test_id=%s ORDER BY m.question_order""", (attempt_row["test_id"],))
        if not questions: flash("No questions found in this test.", "warning"); abort(404)
        seconds_left = max(0, int(attempt_row.get("seconds_left") or 0))
        return render_template("mock_tests/attempt.html", test=attempt_row, questions=questions, seconds_left=seconds_left)

    @bp.route("/submit/<int:attempt_id>", methods=["POST"])
    @login_required
    def submit(attempt_id):
        attempt_row = fetch_one("""SELECT a.*,t.time_limit_minutes,t.id AS test_id FROM mock_attempts a
                                  JOIN mock_tests t ON t.id=a.test_id
                                  WHERE a.id=%s AND a.user_id=%s AND a.status='in_progress'""", (attempt_id,session["user_id"]))
        if not attempt_row:
            existing = fetch_one("SELECT id FROM mock_attempts WHERE id=%s AND user_id=%s", (attempt_id,session["user_id"]))
            if existing: return redirect(url_for("mock_tests.result", attempt_id=attempt_id))
            abort(404)
        conn, cur = db_cursor()
        try:
            cur.execute("""SELECT q.id,q.correct_option FROM mock_test_questions m
                           JOIN mock_question_bank q ON q.id=m.question_id WHERE m.test_id=%s""", (attempt_row["test_id"],))
            answer_key = cur.fetchall()
            score = 0
            for q in answer_key:
                selected = request.form.get(f"question_{q['id']}")
                is_correct = bool(selected and selected == q["correct_option"])
                if is_correct: score += 1
                cur.execute("""INSERT INTO mock_attempt_answers (attempt_id,question_id,selected_option,is_correct)
                               VALUES (%s,%s,%s,%s)
                               ON DUPLICATE KEY UPDATE selected_option=VALUES(selected_option),is_correct=VALUES(is_correct)""",
                            (attempt_id,q["id"],selected,is_correct))
            total = len(answer_key)
            percent = round((score / total) * 100, 2) if total else 0
            cur.execute("""UPDATE mock_attempts SET status='submitted',score=%s,total_questions=%s,
                           percentage=%s,submitted_at=NOW(),time_taken_seconds=TIMESTAMPDIFF(SECOND,started_at,NOW())
                           WHERE id=%s""", (score,total,percent,attempt_id))
            conn.commit()
        except Exception:
            conn.rollback(); raise
        finally:
            cur.close(); conn.close()
        return redirect(url_for("mock_tests.result", attempt_id=attempt_id))

    @bp.route("/result/<int:attempt_id>")
    @login_required
    def result(attempt_id):
        result_row = fetch_one("""SELECT a.*,t.title,t.share_token,t.is_custom,c.course_name,s.subject_name
                                 FROM mock_attempts a JOIN mock_tests t ON t.id=a.test_id
                                 JOIN mock_catalog_courses c ON c.id=t.course_id
                                 JOIN mock_catalog_subjects s ON s.id=t.subject_id
                                 WHERE a.id=%s AND a.user_id=%s AND a.status='submitted'""", (attempt_id,session["user_id"]))
        if not result_row: abort(404)
        rank = fetch_one("""SELECT COUNT(*)+1 AS rank_no FROM mock_attempts
                            WHERE test_id=(SELECT test_id FROM mock_attempts WHERE id=%s)
                            AND status='submitted' AND (percentage>%s OR (percentage=%s AND time_taken_seconds<%s))""",
                         (attempt_id,result_row["percentage"],result_row["percentage"],result_row["time_taken_seconds"] or 0))["rank_no"]
        return render_template("mock_tests/result.html", result=result_row, rank=rank,
                               leaderboard_url=url_for("mock_tests.leaderboard", token=result_row["share_token"]))

    @bp.route("/leaderboard/<token>")
    @login_required
    def leaderboard(token):
        test = fetch_one("SELECT id,title,created_by FROM mock_tests WHERE share_token=%s AND is_active=1", (token,))
        if not test: abort(404)
        rows = fetch_all("""SELECT a.id,a.score,a.total_questions,a.percentage,a.time_taken_seconds,a.submitted_at,u.name
                           FROM mock_attempts a JOIN users u ON u.id=a.user_id
                           WHERE a.test_id=%s AND a.status='submitted'
                           ORDER BY a.percentage DESC,a.time_taken_seconds ASC,a.submitted_at ASC""", (test["id"],))
        return render_template("mock_tests/leaderboard.html", test=test, rows=rows)

    @bp.route("/my-tests")
    @login_required
    def my_tests():
        rows = fetch_all("""SELECT t.*,c.course_name,s.subject_name,COUNT(DISTINCT a.id) AS attempts
                           FROM mock_tests t JOIN mock_catalog_courses c ON c.id=t.course_id
                           JOIN mock_catalog_subjects s ON s.id=t.subject_id
                           LEFT JOIN mock_attempts a ON a.test_id=t.id AND a.status='submitted'
                           WHERE t.created_by=%s AND t.is_custom=1 GROUP BY t.id ORDER BY t.created_at DESC""", (session["user_id"],))
        return render_template("mock_tests/my_tests.html", tests=rows)

    @bp.route("/admin/questions", methods=["GET", "POST"])
    @admin_required
    def admin_questions():
        courses_list = fetch_all("SELECT * FROM mock_catalog_courses WHERE is_active=1 ORDER BY course_name")
        if request.method == "POST":
            subject_id = request.form.get("subject_id", type=int)
            question = (request.form.get("question_text") or "").strip()
            opts = [(request.form.get(f"option_{x.lower()}") or "").strip() for x in "ABCD"]
            correct = request.form.get("correct_option", "A")
            difficulty = request.form.get("difficulty", "Medium")
            explanation = (request.form.get("explanation") or "").strip()
            if not subject_id or not question or not all(opts) or correct not in "ABCD" or difficulty not in ("Easy","Medium","Hard"):
                flash("All question fields are required.", "danger")
            else:
                execute("""INSERT INTO mock_question_bank
                    (subject_id,question_text,option_a,option_b,option_c,option_d,correct_option,difficulty,explanation,created_by)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (subject_id,question,*opts,correct,difficulty,explanation,session["user_id"]))
                flash("Question added successfully.", "success")
                return redirect(url_for("mock_tests.admin_questions"))
        subjects = fetch_all("""SELECT s.id,s.subject_name,c.course_name FROM mock_catalog_subjects s
                                JOIN mock_catalog_courses c ON c.id=s.course_id ORDER BY c.course_name,s.subject_name""")
        return render_template("mock_tests/admin_questions.html", courses=courses_list, subjects=subjects)

    @bp.route("/api/subjects/<int:course_id>")
    @login_required
    def api_subjects(course_id):
        return {"subjects": fetch_all("SELECT id,subject_name FROM mock_catalog_subjects WHERE course_id=%s ORDER BY sort_order,subject_name", (course_id,))}

    return bp
