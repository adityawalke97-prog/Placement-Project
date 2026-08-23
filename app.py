from flask import (
    Flask,
    render_template,
    request,
    redirect,
    session,
    flash,
    send_file,
    Response,
    url_for,
    jsonify
)

from authlib.integrations.flask_client import OAuth
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.utils import secure_filename
from datetime import timedelta

import pymysql
import secrets
import math
import os
import json
import csv
import io

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer
)
from reportlab.lib.styles import getSampleStyleSheet
load_dotenv()
app = Flask(__name__)
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY not found.")
app.secret_key = SECRET_KEY
app.wsgi_app = ProxyFix(
    app.wsgi_app,
    x_proto=1,
    x_host=1
)
app.config.update(
    SECRET_KEY=SECRET_KEY,
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    PERMANENT_SESSION_LIFETIME=timedelta(days=7),
    PREFERRED_URL_SCHEME="https"
)

bcrypt = Bcrypt(app)


# --------------------------------------------------
# DATABASE
# --------------------------------------------------

def get_db_connection():

    return pymysql.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        port=int(os.getenv("DB_PORT", "4000")),
        ssl={
            "ca": "/etc/ssl/certs/ca-certificates.crt"
        },
        connect_timeout=30,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False
    )


# --------------------------------------------------
# GOOGLE OAUTH
# --------------------------------------------------

oauth = OAuth(app)

google = oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={
        "scope": "openid email profile"
    }
)


# --------------------------------------------------
# HOME
# --------------------------------------------------

@app.route("/")
def home():
    return redirect(url_for("login"))


# --------------------------------------------------
# GOOGLE LOGIN
# --------------------------------------------------

@app.route("/login/google")
def google_login():

    session.permanent = True

    redirect_uri = url_for(
        "google_callback",
        _external=True,
        _scheme="https"
    )

    return google.authorize_redirect(redirect_uri)
    # --------------------------------------------------
# GOOGLE CALLBACK
# --------------------------------------------------

@app.route("/login/google/callback")
def google_callback():

    try:

        token = google.authorize_access_token()

        userinfo = token.get("userinfo")

        if not userinfo:
            userinfo = google.get(
                "https://openidconnect.googleapis.com/v1/userinfo"
            ).json()

        name = userinfo["name"]
        email = userinfo["email"]
        picture = userinfo.get("picture")
        google_id = userinfo["sub"]
        verified = userinfo.get("email_verified", False)

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            "SELECT * FROM users WHERE email=%s",
            (email,)
        )

        user = cur.fetchone()

        if user:

            cur.execute("""
                UPDATE users
                SET
                    google_id=%s,
                    profile_pic=%s,
                    email_verified=%s,
                    login_provider='google'
                WHERE email=%s
            """, (
                google_id,
                picture,
                verified,
                email
            ))

            conn.commit()

            session["user_id"] = user["id"]
            session["name"] = user["name"]
            session["email"] = user["email"]
            session["profile_pic"] = picture

        else:

            random_password = secrets.token_hex(16)

            hashed_password = bcrypt.generate_password_hash(
                random_password
            ).decode("utf-8")

            cur.execute("""
                INSERT INTO users
                (
                    name,
                    email,
                    password,
                    google_id,
                    profile_pic,
                    email_verified,
                    login_provider
                )
                VALUES
                (%s,%s,%s,%s,%s,%s,'google')
            """, (
                name,
                email,
                hashed_password,
                google_id,
                picture,
                verified
            ))
            conn.commit()
            session["user_id"] = cur.lastrowid
            session["name"] = name
            session["email"] = email
            session["profile_pic"] = picture

        cur.close()
        conn.close()

        return redirect(url_for("dashboard"))

    except Exception as e:

        print("GOOGLE LOGIN ERROR:", e)

        flash("Google Login Failed", "danger")

        return redirect(url_for("login"))


# --------------------------------------------------
# SIGNUP
# --------------------------------------------------

@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            "SELECT id FROM users WHERE email=%s",
            (email,)
        )

        if cur.fetchone():

            cur.close()
            conn.close()

            flash("Email already exists.", "danger")
            return redirect(url_for("signup"))

        hashed = bcrypt.generate_password_hash(
            password
        ).decode("utf-8")

        cur.execute("""
            INSERT INTO users
            (
                name,
                email,
                password
            )
            VALUES
            (%s,%s,%s)
        """, (
            name,
            email,
            hashed
        ))

        conn.commit()

        cur.close()
        conn.close()

        flash("Account created successfully.", "success")

        return redirect(url_for("login"))

    return render_template("signup.html")


# --------------------------------------------------
# LOGIN
# --------------------------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            "SELECT * FROM users WHERE email=%s",
            (email,)
        )

        user = cur.fetchone()

        cur.close()
        conn.close()

        if user and bcrypt.check_password_hash(
            user["password"],
            password
        ):

            session.permanent = True

            session["user_id"] = user["id"]
            session["name"] = user["name"]
            session["email"] = user["email"]
            session["profile_pic"] = user.get("profile_pic")

            return redirect(url_for("dashboard"))

        flash(
            "Invalid Email or Password",
            "danger"
        )

    return render_template("login.html")

# --------------------------------------------------
# LOGOUT
# --------------------------------------------------

@app.route("/logout")
def logout():

    session.clear()

    flash(
        "Logged out successfully.",
        "success"
    )

    return redirect(url_for("login"))
    # =========================================================
# PART 3 — DASHBOARD + MOCK TEST ROUTES
# =========================================================

@app.route("/dashboard")
def dashboard():
    # -----------------------------------------------------
    # LOGIN CHECK
    # -----------------------------------------------------
    if "user_id" not in session:
        flash("Please login first.", "warning")
        return redirect(url_for("login"))

    user_id = session["user_id"]

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        # -------------------------------------------------
        # USER DETAILS
        # -------------------------------------------------
        cursor.execute("""
            SELECT
                id,
                name,
                email,
                role
            FROM users
            WHERE id = %s
            LIMIT 1
        """, (user_id,))

        user = cursor.fetchone()

        if not user:
            session.clear()
            flash("User account not found.", "danger")
            return redirect(url_for("login"))

        # -------------------------------------------------
        # TOTAL MOCK QUESTIONS
        # -------------------------------------------------
        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM mock_questions
        """)

        question_result = cursor.fetchone()
        total_questions = question_result["total"] if question_result else 0

        # -------------------------------------------------
        # TOTAL MOCK TESTS ATTEMPTED
        # -------------------------------------------------
        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM results
            WHERE user_id = %s
        """, (user_id,))

        test_result = cursor.fetchone()
        total_tests = test_result["total"] if test_result else 0

        # -------------------------------------------------
        # AVERAGE SCORE
        # -------------------------------------------------
        cursor.execute("""
            SELECT AVG(percentage) AS avg_percentage
            FROM results
            WHERE user_id = %s
        """, (user_id,))

        avg_result = cursor.fetchone()

        average_score = 0

        if avg_result and avg_result["avg_percentage"] is not None:
            average_score = round(float(avg_result["avg_percentage"]), 2)

        # -------------------------------------------------
        # BEST SCORE
        # -------------------------------------------------
        cursor.execute("""
            SELECT MAX(percentage) AS best_percentage
            FROM results
            WHERE user_id = %s
        """, (user_id,))

        best_result = cursor.fetchone()

        best_score = 0

        if best_result and best_result["best_percentage"] is not None:
            best_score = round(float(best_result["best_percentage"]), 2)

        # -------------------------------------------------
        # RECENT TEST RESULTS
        # -------------------------------------------------
        cursor.execute("""
            SELECT
                id,
                score,
                total_questions,
                percentage,
                test_date
            FROM results
            WHERE user_id = %s
            ORDER BY test_date DESC
            LIMIT 5
        """, (user_id,))

        recent_results = cursor.fetchall()

        # -------------------------------------------------
        # CATEGORY-WISE PERFORMANCE
        # -------------------------------------------------
        category_stats = []

        try:
            cursor.execute("""
                SELECT
                    mq.category,
                    COUNT(*) AS total_attempts
                FROM mock_questions mq
                GROUP BY mq.category
                ORDER BY mq.category
            """)

            category_stats = cursor.fetchall()

        except Exception:
            category_stats = []

        # -------------------------------------------------
        # DASHBOARD
        # -------------------------------------------------
        return render_template(
            "dashboard.html",
            user=user,
            total_questions=total_questions,
            total_tests=total_tests,
            average_score=average_score,
            best_score=best_score,
            recent_results=recent_results,
            category_stats=category_stats
        )

    except Exception as e:

        app.logger.exception(
            "Dashboard error for user_id=%s",
            user_id
        )

        flash("Unable to load dashboard.", "danger")

        return redirect(url_for("login"))

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =========================================================
# MOCK TEST CATEGORIES
# =========================================================

@app.route("/mock_categories")
def mock_categories():

    if "user_id" not in session:
        flash("Please login first.", "warning")
        return redirect(url_for("login"))

    conn = None
    cursor = None

    try:

        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        cursor.execute("""
            SELECT
                category,
                COUNT(*) AS total_questions
            FROM mock_questions
            GROUP BY category
            ORDER BY category
        """)

        categories = cursor.fetchall()

        return render_template(
            "mock_categories.html",
            categories=categories
        )

    except Exception:

        app.logger.exception("Unable to load mock categories")

        flash(
            "Unable to load mock test categories.",
            "danger"
        )

        return redirect(url_for("dashboard"))

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =========================================================
# START MOCK TEST
# =========================================================

@app.route("/mock_test")
def mock_test():

    if "user_id" not in session:
        flash("Please login first.", "warning")
        return redirect(url_for("login"))

    category = request.args.get("category", "").strip()

    conn = None
    cursor = None

    try:

        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        # -------------------------------------------------
        # CATEGORY FILTER
        # -------------------------------------------------
        if category:

            cursor.execute("""
                SELECT
                    id,
                    question,
                    option1,
                    option2,
                    option3,
                    option4,
                    answer,
                    category,
                    level
                FROM mock_questions
                WHERE category = %s
                ORDER BY RAND()
                LIMIT 20
            """, (category,))

        else:

            cursor.execute("""
                SELECT
                    id,
                    question,
                    option1,
                    option2,
                    option3,
                    option4,
                    answer,
                    category,
                    level
                FROM mock_questions
                ORDER BY RAND()
                LIMIT 20
            """)

        questions = cursor.fetchall()

        # -------------------------------------------------
        # NO QUESTIONS
        # -------------------------------------------------
        if not questions:

            flash(
                "No questions available for this category.",
                "warning"
            )

            return redirect(
                url_for("mock_categories")
            )

        # -------------------------------------------------
        # REMOVE ANSWER FROM FRONTEND
        # -------------------------------------------------
        safe_questions = []

        for q in questions:

            safe_questions.append({
                "id": q["id"],
                "question": q["question"],
                "option1": q["option1"],
                "option2": q["option2"],
                "option3": q["option3"],
                "option4": q["option4"],
                "category": q["category"],
                "level": q.get("level")
            })

        # -------------------------------------------------
        # SAVE TEST QUESTIONS IN SESSION
        # -------------------------------------------------
        session["mock_question_ids"] = [
            q["id"] for q in questions
        ]

        session["mock_category"] = category

        return render_template(
            "mock_test.html",
            questions=safe_questions,
            category=category
        )

    except Exception:

        app.logger.exception("Mock test loading error")

        flash(
            "Unable to start mock test.",
            "danger"
        )

        return redirect(
            url_for("mock_categories")
        )

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =========================================================
# SUBMIT MOCK TEST
# =========================================================

@app.route("/submit_mock_test", methods=["POST"])
def submit_mock_test():

    if "user_id" not in session:
        return jsonify({
            "success": False,
            "message": "Please login first."
        }), 401

    user_id = session["user_id"]

    conn = None
    cursor = None

    try:

        data = request.get_json(silent=True)

        if not data:
            data = request.form.to_dict()

        # -------------------------------------------------
        # ANSWERS
        # -------------------------------------------------
        answers = data.get("answers", {})

        if isinstance(answers, str):

            try:
                answers = json.loads(answers)

            except Exception:
                answers = {}

        question_ids = session.get(
            "mock_question_ids",
            []
        )

        if not question_ids:

            return jsonify({
                "success": False,
                "message": "Test session expired."
            }), 400

        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        # -------------------------------------------------
        # FETCH CORRECT ANSWERS
        # -------------------------------------------------
        placeholders = ",".join(
            ["%s"] * len(question_ids)
        )

        cursor.execute(
            f"""
            SELECT
                id,
                answer
            FROM mock_questions
            WHERE id IN ({placeholders})
            """,
            tuple(question_ids)
        )

        db_questions = cursor.fetchall()

        correct_map = {
            str(q["id"]): str(q["answer"]).strip()
            for q in db_questions
        }

        # -------------------------------------------------
        # CALCULATE SCORE
        # -------------------------------------------------
        score = 0
        total_questions = len(question_ids)

        for question_id in question_ids:

            user_answer = answers.get(
                str(question_id),
                ""
            )

            correct_answer = correct_map.get(
                str(question_id),
                ""
            )

            if (
                str(user_answer).strip().lower()
                == str(correct_answer).strip().lower()
            ):
                score += 1

        # -------------------------------------------------
        # PERCENTAGE
        # -------------------------------------------------
        percentage = 0

        if total_questions > 0:

            percentage = round(
                (score / total_questions) * 100,
                2
            )

        # -------------------------------------------------
        # SAVE RESULT
        # -------------------------------------------------
        cursor.execute("""
            INSERT INTO results
            (
                user_id,
                score,
                total_questions,
                percentage
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s
            )
        """, (
            user_id,
            score,
            total_questions,
            percentage
        ))

        conn.commit()

        # -------------------------------------------------
        # CLEAR TEST SESSION
        # -------------------------------------------------
        session.pop(
            "mock_question_ids",
            None
        )

        session.pop(
            "mock_category",
            None
        )

        return jsonify({
            "success": True,
            "score": score,
            "total_questions": total_questions,
            "percentage": percentage,
            "message": "Mock test submitted successfully."
        })

    except Exception:

        if conn:
            conn.rollback()

        app.logger.exception(
            "Mock test submission error"
        )

        return jsonify({
            "success": False,
            "message": "Unable to submit mock test."
        }), 500

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =========================================================
# MOCK TEST RESULT
# =========================================================

@app.route("/mock_result/<int:result_id>")
def mock_result(result_id):

    if "user_id" not in session:
        flash("Please login first.", "warning")
        return redirect(url_for("login"))

    user_id = session["user_id"]

    conn = None
    cursor = None

    try:

        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        cursor.execute("""
            SELECT
                id,
                score,
                total_questions,
                percentage,
                test_date
            FROM results
            WHERE id = %s
              AND user_id = %s
            LIMIT 1
        """, (
            result_id,
            user_id
        ))

        result = cursor.fetchone()

        if not result:

            flash(
                "Result not found.",
                "warning"
            )

            return redirect(
                url_for("mock_test_history")
            )

        return render_template(
            "mock_result.html",
            result=result
        )

    except Exception:

        app.logger.exception(
            "Mock result loading error"
        )

        flash(
            "Unable to load result.",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =========================================================
# MOCK TEST HISTORY
# =========================================================

@app.route("/mock_test_history")
def mock_test_history():

    if "user_id" not in session:
        flash("Please login first.", "warning")
        return redirect(url_for("login"))

    user_id = session["user_id"]

    conn = None
    cursor = None

    try:

        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        cursor.execute("""
            SELECT
                id,
                score,
                total_questions,
                percentage,
                test_date
            FROM results
            WHERE user_id = %s
            ORDER BY test_date DESC
        """, (user_id,))

        results = cursor.fetchall()

        return render_template(
            "mock_test_history.html",
            results=results
        )

    except Exception:

        app.logger.exception(
            "Mock test history error"
        )

        flash(
            "Unable to load test history.",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()
            # =========================================================
# PART 4 — INTERVIEW QUESTIONS
# =========================================================

@app.route("/interview")
@app.route("/interview_questions")
def interview_questions():

    if "user_id" not in session:
        flash("Please login first.", "warning")
        return redirect(url_for("login"))

    # -----------------------------------------------------
    # QUERY PARAMETERS
    # -----------------------------------------------------
    category = request.args.get("category", "").strip()
    level = request.args.get("level", "").strip()
    search = request.args.get("search", "").strip()

    try:
        page = int(request.args.get("page", 1))
    except (ValueError, TypeError):
        page = 1

    if page < 1:
        page = 1

    per_page = 20
    offset = (page - 1) * per_page

    conn = None
    cursor = None

    try:

        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        # -------------------------------------------------
        # BUILD FILTER
        # -------------------------------------------------
        conditions = []
        params = []

        if category:
            conditions.append("category = %s")
            params.append(category)

        if level:
            conditions.append("level = %s")
            params.append(level)

        if search:
            conditions.append("""
                (
                    question LIKE %s
                    OR answer LIKE %s
                )
            """)

            search_value = f"%{search}%"

            params.append(search_value)
            params.append(search_value)

        where_clause = ""

        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        # -------------------------------------------------
        # TOTAL QUESTIONS
        # -------------------------------------------------
        cursor.execute(
            f"""
            SELECT COUNT(*) AS total
            FROM interview_questions
            {where_clause}
            """,
            tuple(params)
        )

        count_result = cursor.fetchone()

        total_questions = (
            count_result["total"]
            if count_result
            else 0
        )

        # -------------------------------------------------
        # TOTAL PAGES
        # -------------------------------------------------
        total_pages = (
            (total_questions + per_page - 1)
            // per_page
        )

        # -------------------------------------------------
        # QUESTIONS
        # -------------------------------------------------
        cursor.execute(
            f"""
            SELECT
                id,
                question,
                answer,
                category,
                level
            FROM interview_questions
            {where_clause}
            ORDER BY id DESC
            LIMIT %s OFFSET %s
            """,
            tuple(params) + (
                per_page,
                offset
            )
        )

        questions = cursor.fetchall()

        # -------------------------------------------------
        # CATEGORIES
        # -------------------------------------------------
        cursor.execute("""
            SELECT DISTINCT category
            FROM interview_questions
            WHERE category IS NOT NULL
              AND category != ''
            ORDER BY category
        """)

        categories = cursor.fetchall()

        # -------------------------------------------------
        # LEVELS
        # -------------------------------------------------
        cursor.execute("""
            SELECT DISTINCT level
            FROM interview_questions
            WHERE level IS NOT NULL
              AND level != ''
            ORDER BY level
        """)

        levels = cursor.fetchall()

        return render_template(
            "interview_questions.html",
            questions=questions,
            categories=categories,
            levels=levels,
            category=category,
            level=level,
            search=search,
            page=page,
            per_page=per_page,
            total_questions=total_questions,
            total_pages=total_pages
        )

    except Exception:

        app.logger.exception(
            "Interview questions loading error"
        )

        flash(
            "Unable to load interview questions.",
            "danger"
        )

        return redirect(url_for("dashboard"))

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =========================================================
# RANDOM INTERVIEW QUESTION
# =========================================================

@app.route("/random_interview_question")
def random_interview_question():

    if "user_id" not in session:
        return jsonify({
            "success": False,
            "message": "Please login first."
        }), 401

    category = request.args.get(
        "category",
        ""
    ).strip()

    level = request.args.get(
        "level",
        ""
    ).strip()

    conn = None
    cursor = None

    try:

        conn = get_db_connection()
        cursor = conn.cursor(
            pymysql.cursors.DictCursor
        )

        conditions = []
        params = []

        if category:

            conditions.append(
                "category = %s"
            )

            params.append(category)

        if level:

            conditions.append(
                "level = %s"
            )

            params.append(level)

        where_clause = ""

        if conditions:

            where_clause = (
                "WHERE "
                + " AND ".join(conditions)
            )

        cursor.execute(
            f"""
            SELECT
                id,
                question,
                answer,
                category,
                level
            FROM interview_questions
            {where_clause}
            ORDER BY RAND()
            LIMIT 1
            """,
            tuple(params)
        )

        question = cursor.fetchone()

        if not question:

            return jsonify({
                "success": False,
                "message": "No question found."
            }), 404

        return jsonify({
            "success": True,
            "question": question
        })

    except Exception:

        app.logger.exception(
            "Random interview question error"
        )

        return jsonify({
            "success": False,
            "message": "Unable to load question."
        }), 500

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =========================================================
# SINGLE INTERVIEW QUESTION
# =========================================================

@app.route("/interview_question/<int:question_id>")
def interview_question(question_id):

    if "user_id" not in session:
        flash("Please login first.", "warning")
        return redirect(url_for("login"))

    conn = None
    cursor = None

    try:

        conn = get_db_connection()
        cursor = conn.cursor(
            pymysql.cursors.DictCursor
        )

        cursor.execute("""
            SELECT
                id,
                question,
                answer,
                category,
                level
            FROM interview_questions
            WHERE id = %s
            LIMIT 1
        """, (question_id,))

        question = cursor.fetchone()

        if not question:

            flash(
                "Interview question not found.",
                "warning"
            )

            return redirect(
                url_for("interview_questions")
            )

        return render_template(
            "interview_question.html",
            question=question
        )

    except Exception:

        app.logger.exception(
            "Interview question details error"
        )

        flash(
            "Unable to load question.",
            "danger"
        )

        return redirect(
            url_for("interview_questions")
        )

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =========================================================
# INTERVIEW QUESTION CATEGORIES API
# =========================================================

@app.route("/api/interview/categories")
def interview_categories_api():

    if "user_id" not in session:
        return jsonify({
            "success": False,
            "message": "Unauthorized"
        }), 401

    conn = None
    cursor = None

    try:

        conn = get_db_connection()
        cursor = conn.cursor(
            pymysql.cursors.DictCursor
        )

        cursor.execute("""
            SELECT
                category,
                COUNT(*) AS total
            FROM interview_questions
            WHERE category IS NOT NULL
              AND category != ''
            GROUP BY category
            ORDER BY category
        """)

        categories = cursor.fetchall()

        return jsonify({
            "success": True,
            "categories": categories
        })

    except Exception:

        app.logger.exception(
            "Interview categories API error"
        )

        return jsonify({
            "success": False,
            "message": "Unable to load categories."
        }), 500

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =========================================================
# INTERVIEW QUESTION SEARCH API
# =========================================================

@app.route("/api/interview/search")
def interview_search_api():

    if "user_id" not in session:
        return jsonify({
            "success": False,
            "message": "Unauthorized"
        }), 401

    search = request.args.get(
        "q",
        ""
    ).strip()

    category = request.args.get(
        "category",
        ""
    ).strip()

    level = request.args.get(
        "level",
        ""
    ).strip()

    if not search and not category and not level:

        return jsonify({
            "success": True,
            "questions": []
        })

    conn = None
    cursor = None

    try:

        conn = get_db_connection()
        cursor = conn.cursor(
            pymysql.cursors.DictCursor
        )

        conditions = []
        params = []

        if search:

            conditions.append("""
                (
                    question LIKE %s
                    OR answer LIKE %s
                )
            """)

            search_value = f"%{search}%"

            params.extend([
                search_value,
                search_value
            ])

        if category:

            conditions.append(
                "category = %s"
            )

            params.append(category)

        if level:

            conditions.append(
                "level = %s"
            )

            params.append(level)

        where_clause = " AND ".join(
            conditions
        )

        cursor.execute(
            f"""
            SELECT
                id,
                question,
                answer,
                category,
                level
            FROM interview_questions
            WHERE {where_clause}
            ORDER BY id DESC
            LIMIT 50
            """,
            tuple(params)
        )

        questions = cursor.fetchall()

        return jsonify({
            "success": True,
            "questions": questions
        })

    except Exception:

        app.logger.exception(
            "Interview search API error"
        )

        return jsonify({
            "success": False,
            "message": "Search failed."
        }), 500

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =========================================================
# BOOKMARK INTERVIEW QUESTION
# =========================================================

@app.route(
    "/api/interview/bookmark/<int:question_id>",
    methods=["POST"]
)
def bookmark_interview_question(question_id):

    if "user_id" not in session:

        return jsonify({
            "success": False,
            "message": "Please login first."
        }), 401

    user_id = session["user_id"]

    # -----------------------------------------------------
    # SESSION BASED BOOKMARK
    # -----------------------------------------------------
    bookmarks = session.get(
        "interview_bookmarks",
        []
    )

    if question_id in bookmarks:

        bookmarks.remove(question_id)

        bookmarked = False

    else:

        bookmarks.append(question_id)

        bookmarked = True

    session["interview_bookmarks"] = bookmarks

    return jsonify({
        "success": True,
        "bookmarked": bookmarked,
        "total_bookmarks": len(bookmarks)
    })


# =========================================================
# BOOKMARKED INTERVIEW QUESTIONS
# =========================================================

@app.route("/interview_bookmarks")
def interview_bookmarks():

    if "user_id" not in session:
        flash("Please login first.", "warning")
        return redirect(url_for("login"))

    bookmarks = session.get(
        "interview_bookmarks",
        []
    )

    if not bookmarks:

        return render_template(
            "interview_bookmarks.html",
            questions=[]
        )

    conn = None
    cursor = None

    try:

        conn = get_db_connection()
        cursor = conn.cursor(
            pymysql.cursors.DictCursor
        )

        placeholders = ",".join(
            ["%s"] * len(bookmarks)
        )

        cursor.execute(
            f"""
            SELECT
                id,
                question,
                answer,
                category,
                level
            FROM interview_questions
            WHERE id IN ({placeholders})
            ORDER BY id DESC
            """,
            tuple(bookmarks)
        )

        questions = cursor.fetchall()

        return render_template(
            "interview_bookmarks.html",
            questions=questions
        )

    except Exception:

        app.logger.exception(
            "Interview bookmarks error"
        )

        flash(
            "Unable to load bookmarks.",
            "danger"
        )

        return redirect(
            url_for("interview_questions")
        )

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()
# =========================================================
# PART 5 — RESUME BUILDER + ATS
# =========================================================

@app.route("/resume-builder")
@app.route("/resume_builder")
def resume_builder():

    if "user_id" not in session:
        flash("Please login first.", "warning")
        return redirect(url_for("login"))

    user_id = session["user_id"]

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        # -------------------------------------------------
        # GET USER DETAILS
        # -------------------------------------------------
        cursor.execute("""
            SELECT
                id,
                name,
                email
            FROM users
            WHERE id = %s
            LIMIT 1
        """, (user_id,))

        user = cursor.fetchone()

        # -------------------------------------------------
        # GET SAVED RESUME
        # -------------------------------------------------
        resume = None

        try:
            cursor.execute("""
                SELECT *
                FROM resumes
                WHERE user_id = %s
                ORDER BY id DESC
                LIMIT 1
            """, (user_id,))

            resume = cursor.fetchone()

        except Exception:
            # Resume table may not exist yet
            resume = None

        return render_template(
            "resume_builder.html",
            user=user,
            resume=resume
        )

    except Exception:

        app.logger.exception(
            "Resume builder loading error"
        )

        flash(
            "Unable to open resume builder.",
            "danger"
        )

        return redirect(url_for("dashboard"))

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =========================================================
# SAVE RESUME
# =========================================================

@app.route(
    "/save_resume",
    methods=["POST"]
)
def save_resume():

    if "user_id" not in session:

        return jsonify({
            "success": False,
            "message": "Please login first."
        }), 401

    user_id = session["user_id"]

    data = request.get_json(
        silent=True
    )

    if not data:
        data = request.form.to_dict()

    # -----------------------------------------------------
    # BASIC DETAILS
    # -----------------------------------------------------

    full_name = data.get(
        "full_name",
        ""
    ).strip()

    email = data.get(
        "email",
        ""
    ).strip()

    phone = data.get(
        "phone",
        ""
    ).strip()

    location = data.get(
        "location",
        ""
    ).strip()

    linkedin = data.get(
        "linkedin",
        ""
    ).strip()

    github = data.get(
        "github",
        ""
    ).strip()

    portfolio = data.get(
        "portfolio",
        ""
    ).strip()

    # -----------------------------------------------------
    # CAREER DETAILS
    # -----------------------------------------------------

    summary = data.get(
        "summary",
        ""
    ).strip()

    objective = data.get(
        "objective",
        ""
    ).strip()

    skills = data.get(
        "skills",
        ""
    ).strip()

    # -----------------------------------------------------
    # EDUCATION
    # -----------------------------------------------------

    education = data.get(
        "education",
        ""
    ).strip()

    degree = data.get(
        "degree",
        ""
    ).strip()

    college = data.get(
        "college",
        ""
    ).strip()

    graduation_year = data.get(
        "graduation_year",
        ""
    ).strip()

    # -----------------------------------------------------
    # EXPERIENCE
    # -----------------------------------------------------

    experience = data.get(
        "experience",
        ""
    ).strip()

    # -----------------------------------------------------
    # PROJECTS
    # -----------------------------------------------------

    projects = data.get(
        "projects",
        ""
    ).strip()

    # -----------------------------------------------------
    # CERTIFICATIONS
    # -----------------------------------------------------

    certifications = data.get(
        "certifications",
        ""
    ).strip()

    # -----------------------------------------------------
    # ACHIEVEMENTS
    # -----------------------------------------------------

    achievements = data.get(
        "achievements",
        ""
    ).strip()

    conn = None
    cursor = None

    try:

        conn = get_db_connection()
        cursor = conn.cursor()

        # -------------------------------------------------
        # CHECK EXISTING RESUME
        # -------------------------------------------------

        cursor.execute("""
            SELECT id
            FROM resumes
            WHERE user_id = %s
            ORDER BY id DESC
            LIMIT 1
        """, (user_id,))

        existing = cursor.fetchone()

        # -------------------------------------------------
        # UPDATE
        # -------------------------------------------------

        if existing:

            cursor.execute("""
                UPDATE resumes
                SET
                    full_name = %s,
                    email = %s,
                    phone = %s,
                    location = %s,
                    linkedin = %s,
                    github = %s,
                    portfolio = %s,
                    summary = %s,
                    objective = %s,
                    skills = %s,
                    education = %s,
                    degree = %s,
                    college = %s,
                    graduation_year = %s,
                    experience = %s,
                    projects = %s,
                    certifications = %s,
                    achievements = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                  AND user_id = %s
            """, (
                full_name,
                email,
                phone,
                location,
                linkedin,
                github,
                portfolio,
                summary,
                objective,
                skills,
                education,
                degree,
                college,
                graduation_year,
                experience,
                projects,
                certifications,
                achievements,
                existing[0],
                user_id
            ))

        # -------------------------------------------------
        # INSERT
        # -------------------------------------------------

        else:

            cursor.execute("""
                INSERT INTO resumes
                (
                    user_id,
                    full_name,
                    email,
                    phone,
                    location,
                    linkedin,
                    github,
                    portfolio,
                    summary,
                    objective,
                    skills,
                    education,
                    degree,
                    college,
                    graduation_year,
                    experience,
                    projects,
                    certifications,
                    achievements
                )
                VALUES
                (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s
                )
            """, (
                user_id,
                full_name,
                email,
                phone,
                location,
                linkedin,
                github,
                portfolio,
                summary,
                objective,
                skills,
                education,
                degree,
                college,
                graduation_year,
                experience,
                projects,
                certifications,
                achievements
            ))

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Resume saved successfully."
        })

    except Exception:

        if conn:
            conn.rollback()

        app.logger.exception(
            "Resume save error"
        )

        return jsonify({
            "success": False,
            "message": "Unable to save resume."
        }), 500

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =========================================================
# GET RESUME DATA API
# =========================================================

@app.route("/api/resume")
def get_resume():

    if "user_id" not in session:

        return jsonify({
            "success": False,
            "message": "Unauthorized"
        }), 401

    user_id = session["user_id"]

    conn = None
    cursor = None

    try:

        conn = get_db_connection()
        cursor = conn.cursor(
            pymysql.cursors.DictCursor
        )

        cursor.execute("""
            SELECT *
            FROM resumes
            WHERE user_id = %s
            ORDER BY id DESC
            LIMIT 1
        """, (user_id,))

        resume = cursor.fetchone()

        if not resume:

            return jsonify({
                "success": True,
                "resume": None
            })

        return jsonify({
            "success": True,
            "resume": resume
        })

    except Exception:

        app.logger.exception(
            "Resume API error"
        )

        return jsonify({
            "success": False,
            "message": "Unable to load resume."
        }), 500

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =========================================================
# ATS ANALYSIS
# =========================================================

@app.route(
    "/ats-analysis",
    methods=["GET", "POST"]
)
@app.route(
    "/ats_analysis",
    methods=["GET", "POST"]
)
def ats_analysis():

    if "user_id" not in session:
        flash("Please login first.", "warning")
        return redirect(url_for("login"))

    if request.method == "GET":

        return render_template(
            "ats_analysis.html"
        )

    # -----------------------------------------------------
    # GET RESUME TEXT
    # -----------------------------------------------------

    data = request.get_json(
        silent=True
    )

    if not data:
        data = request.form.to_dict()

    resume_text = data.get(
        "resume_text",
        ""
    ).strip()

    job_description = data.get(
        "job_description",
        ""
    ).strip()

    # -----------------------------------------------------
    # VALIDATION
    # -----------------------------------------------------

    if not resume_text:

        return jsonify({
            "success": False,
            "message": "Resume content is required."
        }), 400

    # -----------------------------------------------------
    # DEFAULT ATS KEYWORDS
    # -----------------------------------------------------

    common_keywords = [
        "java",
        "python",
        "html",
        "css",
        "javascript",
        "sql",
        "mysql",
        "git",
        "github",
        "flask",
        "spring",
        "react",
        "api",
        "rest",
        "database",
        "oop",
        "data structures",
        "algorithms",
        "problem solving",
        "communication",
        "teamwork"
    ]

    # -----------------------------------------------------
    # JOB DESCRIPTION KEYWORDS
    # -----------------------------------------------------

    if job_description:

        text_for_keywords = (
            job_description.lower()
        )

        keywords = []

        for keyword in common_keywords:

            if keyword.lower() in text_for_keywords:

                keywords.append(keyword)

    else:

        keywords = common_keywords

    # -----------------------------------------------------
    # MATCH KEYWORDS
    # -----------------------------------------------------

    resume_lower = resume_text.lower()

    matched_keywords = []
    missing_keywords = []

    for keyword in keywords:

        if keyword.lower() in resume_lower:

            matched_keywords.append(
                keyword
            )

        else:

            missing_keywords.append(
                keyword
            )

    # -----------------------------------------------------
    # ATS SCORE
    # -----------------------------------------------------

    if keywords:

        keyword_score = (
            len(matched_keywords)
            / len(keywords)
        ) * 100

    else:

        keyword_score = 0

    # -----------------------------------------------------
    # RESUME QUALITY CHECKS
    # -----------------------------------------------------

    quality_score = 0

    resume_length = len(
        resume_text.split()
    )

    if resume_length >= 100:
        quality_score += 20

    if resume_length >= 200:
        quality_score += 10

    if "education" in resume_lower:
        quality_score += 10

    if "experience" in resume_lower:
        quality_score += 10

    if "skills" in resume_lower:
        quality_score += 10

    if "projects" in resume_lower:
        quality_score += 10

    if "email" in resume_lower or "@" in resume_lower:
        quality_score += 10

    if "github" in resume_lower:
        quality_score += 5

    if "linkedin" in resume_lower:
        quality_score += 5

    # -----------------------------------------------------
    # FINAL SCORE
    # -----------------------------------------------------

    final_score = round(
        (keyword_score * 0.70)
        + (quality_score * 0.30),
        2
    )

    if final_score >= 80:

        rating = "Excellent"

    elif final_score >= 65:

        rating = "Good"

    elif final_score >= 50:

        rating = "Average"

    else:

        rating = "Needs Improvement"

    # -----------------------------------------------------
    # SUGGESTIONS
    # -----------------------------------------------------

    suggestions = []

    if missing_keywords:

        suggestions.append(
            "Consider adding relevant job-specific "
            "skills and keywords."
        )

    if resume_length < 100:

        suggestions.append(
            "Add more relevant project, education, "
            "and skill details."
        )

    if "experience" not in resume_lower:

        suggestions.append(
            "Add an Experience section if applicable."
        )

    if "projects" not in resume_lower:

        suggestions.append(
            "Add your important academic or personal projects."
        )

    if "github" not in resume_lower:

        suggestions.append(
            "Add your GitHub profile if you have one."
        )

    if "linkedin" not in resume_lower:

        suggestions.append(
            "Add your LinkedIn profile."
        )

    return jsonify({
        "success": True,
        "score": final_score,
        "rating": rating,
        "keyword_score": round(
            keyword_score,
            2
        ),
        "quality_score": quality_score,
        "matched_keywords": matched_keywords,
        "missing_keywords": missing_keywords,
        "suggestions": suggestions
    })


# =========================================================
# RESUME PREVIEW
# =========================================================

@app.route("/resume-preview")
@app.route("/resume_preview")
def resume_preview():

    if "user_id" not in session:
        flash("Please login first.", "warning")
        return redirect(url_for("login"))

    user_id = session["user_id"]

    conn = None
    cursor = None

    try:

        conn = get_db_connection()
        cursor = conn.cursor(
            pymysql.cursors.DictCursor
        )

        cursor.execute("""
            SELECT *
            FROM resumes
            WHERE user_id = %s
            ORDER BY id DESC
            LIMIT 1
        """, (user_id,))

        resume = cursor.fetchone()

        if not resume:

            flash(
                "Please create your resume first.",
                "warning"
            )

            return redirect(
                url_for("resume_builder")
            )

        return render_template(
            "resume_preview.html",
            resume=resume
        )

    except Exception:

        app.logger.exception(
            "Resume preview error"
        )

        flash(
            "Unable to open resume preview.",
            "danger"
        )

        return redirect(
            url_for("resume_builder")
        )

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =========================================================
# DELETE RESUME
# =========================================================

@app.route(
    "/delete_resume",
    methods=["POST"]
)
def delete_resume():

    if "user_id" not in session:

        return jsonify({
            "success": False,
            "message": "Unauthorized"
        }), 401

    user_id = session["user_id"]

    conn = None
    cursor = None

    try:

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM resumes
            WHERE user_id = %s
        """, (user_id,))

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Resume deleted successfully."
        })

    except Exception:

        if conn:
            conn.rollback()

        app.logger.exception(
            "Resume delete error"
        )

        return jsonify({
            "success": False,
            "message": "Unable to delete resume."
        }), 500

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()

# =========================================================
# PART 6 — COMMUNICATION + CODING + PROGRESS
# =========================================================


# =========================================================
# COMMUNICATION PRACTICE
# =========================================================

@app.route("/communication")
@app.route("/communication_practice")
def communication_practice():

    if "user_id" not in session:
        flash("Please login first.", "warning")
        return redirect(url_for("login"))

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        questions = []

        # -------------------------------------------------
        # CHECK COMMUNICATION QUESTIONS TABLE
        # -------------------------------------------------
        try:
            cursor.execute("""
                SELECT
                    id,
                    question,
                    answer,
                    category,
                    level
                FROM communication_questions
                ORDER BY id DESC
                LIMIT 50
            """)

            questions = cursor.fetchall()

        except Exception:
            questions = []

        return render_template(
            "communication.html",
            questions=questions
        )

    except Exception:
        app.logger.exception(
            "Communication page error"
        )

        flash(
            "Unable to load communication practice.",
            "danger"
        )

        return redirect(url_for("dashboard"))

    finally:
        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =========================================================
# RANDOM COMMUNICATION QUESTION
# =========================================================

@app.route("/api/communication/random")
def random_communication_question():

    if "user_id" not in session:
        return jsonify({
            "success": False,
            "message": "Unauthorized"
        }), 401

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(
            pymysql.cursors.DictCursor
        )

        cursor.execute("""
            SELECT
                id,
                question,
                answer,
                category,
                level
            FROM communication_questions
            ORDER BY RAND()
            LIMIT 1
        """)

        question = cursor.fetchone()

        if not question:
            return jsonify({
                "success": False,
                "message": "No question available."
            }), 404

        return jsonify({
            "success": True,
            "question": question
        })

    except Exception:
        app.logger.exception(
            "Random communication question error"
        )

        return jsonify({
            "success": False,
            "message": "Unable to load question."
        }), 500

    finally:
        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =========================================================
# CODING PRACTICE
# =========================================================

@app.route("/coding")
@app.route("/coding_practice")
def coding_practice():

    if "user_id" not in session:
        flash("Please login first.", "warning")
        return redirect(url_for("login"))

    category = request.args.get(
        "category",
        ""
    ).strip()

    level = request.args.get(
        "level",
        ""
    ).strip()

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(
            pymysql.cursors.DictCursor
        )

        conditions = []
        params = []

        if category:
            conditions.append(
                "category = %s"
            )
            params.append(category)

        if level:
            conditions.append(
                "level = %s"
            )
            params.append(level)

        where_clause = ""

        if conditions:
            where_clause = (
                "WHERE "
                + " AND ".join(conditions)
            )

        cursor.execute(
            f"""
            SELECT
                id,
                title,
                description,
                difficulty,
                category,
                input_format,
                output_format
            FROM coding_questions
            {where_clause}
            ORDER BY id DESC
            LIMIT 50
            """,
            tuple(params)
        )

        questions = cursor.fetchall()

        # -------------------------------------------------
        # CATEGORIES
        # -------------------------------------------------
        cursor.execute("""
            SELECT DISTINCT category
            FROM coding_questions
            WHERE category IS NOT NULL
              AND category != ''
            ORDER BY category
        """)

        categories = cursor.fetchall()

        # -------------------------------------------------
        # LEVELS
        # -------------------------------------------------
        cursor.execute("""
            SELECT DISTINCT difficulty
            FROM coding_questions
            WHERE difficulty IS NOT NULL
              AND difficulty != ''
            ORDER BY difficulty
        """)

        levels = cursor.fetchall()

        return render_template(
            "coding_practice.html",
            questions=questions,
            categories=categories,
            levels=levels,
            selected_category=category,
            selected_level=level
        )

    except Exception:
        app.logger.exception(
            "Coding practice error"
        )

        flash(
            "Unable to load coding practice.",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )

    finally:
        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =========================================================
# CODING QUESTION DETAILS
# =========================================================

@app.route("/coding/<int:question_id>")
def coding_question(question_id):

    if "user_id" not in session:
        flash("Please login first.", "warning")
        return redirect(url_for("login"))

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(
            pymysql.cursors.DictCursor
        )

        cursor.execute("""
            SELECT *
            FROM coding_questions
            WHERE id = %s
            LIMIT 1
        """, (question_id,))

        question = cursor.fetchone()

        if not question:
            flash(
                "Coding question not found.",
                "warning"
            )

            return redirect(
                url_for("coding_practice")
            )

        return render_template(
            "coding_question.html",
            question=question
        )

    except Exception:
        app.logger.exception(
            "Coding question error"
        )

        flash(
            "Unable to load coding question.",
            "danger"
        )

        return redirect(
            url_for("coding_practice")
        )

    finally:
        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =========================================================
# CODING SUBMISSION
# =========================================================

@app.route(
    "/api/coding/submit",
    methods=["POST"]
)
def submit_coding():

    if "user_id" not in session:
        return jsonify({
            "success": False,
            "message": "Unauthorized"
        }), 401

    user_id = session["user_id"]

    data = request.get_json(
        silent=True
    ) or {}

    question_id = data.get(
        "question_id"
    )

    language = data.get(
        "language",
        ""
    ).strip()

    code = data.get(
        "code",
        ""
    )

    if not question_id:
        return jsonify({
            "success": False,
            "message": "Question ID is required."
        }), 400

    if not code.strip():
        return jsonify({
            "success": False,
            "message": "Code cannot be empty."
        }), 400

    # -----------------------------------------------------
    # NOTE
    # -----------------------------------------------------
    # This route stores the submission.
    # Actual code execution should be handled
    # separately through a secure sandbox.
    # -----------------------------------------------------

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO coding_submissions
                (
                    user_id,
                    question_id,
                    language,
                    code,
                    status
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
            """, (
                user_id,
                question_id,
                language,
                code,
                "submitted"
            ))

            conn.commit()

        except Exception:
            conn.rollback()

            # If submission table isn't present,
            # don't expose database error.
            app.logger.exception(
                "Coding submission table error"
            )

            return jsonify({
                "success": False,
                "message": "Submission storage is not configured."
            }), 500

        return jsonify({
            "success": True,
            "status": "submitted",
            "message": "Code submitted successfully."
        })

    except Exception:
        if conn:
            conn.rollback()

        app.logger.exception(
            "Coding submission error"
        )

        return jsonify({
            "success": False,
            "message": "Unable to submit code."
        }), 500

    finally:
        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =========================================================
# USER PROGRESS
# =========================================================

@app.route("/progress")
@app.route("/my_progress")
def user_progress():

    if "user_id" not in session:
        flash("Please login first.", "warning")
        return redirect(url_for("login"))

    user_id = session["user_id"]

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(
            pymysql.cursors.DictCursor
        )

        # -------------------------------------------------
        # MOCK TEST PROGRESS
        # -------------------------------------------------
        cursor.execute("""
            SELECT
                COUNT(*) AS total_tests,
                COALESCE(AVG(percentage), 0) AS average_score,
                COALESCE(MAX(percentage), 0) AS best_score
            FROM results
            WHERE user_id = %s
        """, (user_id,))

        mock_progress = cursor.fetchone()

        # -------------------------------------------------
        # RECENT RESULTS
        # -------------------------------------------------
        cursor.execute("""
            SELECT
                score,
                total_questions,
                percentage,
                test_date
            FROM results
            WHERE user_id = %s
            ORDER BY test_date DESC
            LIMIT 10
        """, (user_id,))

        recent_results = cursor.fetchall()

        # -------------------------------------------------
        # CODING SUBMISSIONS
        # -------------------------------------------------
        coding_progress = {
            "total": 0,
            "accepted": 0
        }

        try:
            cursor.execute("""
                SELECT
                    COUNT(*) AS total,
                    SUM(
                        CASE
                            WHEN status = 'accepted'
                            THEN 1
                            ELSE 0
                        END
                    ) AS accepted
                FROM coding_submissions
                WHERE user_id = %s
            """, (user_id,))

            coding_result = cursor.fetchone()

            if coding_result:
                coding_progress = {
                    "total": coding_result["total"] or 0,
                    "accepted": coding_result["accepted"] or 0
                }

        except Exception:
            coding_progress = {
                "total": 0,
                "accepted": 0
            }

        return render_template(
            "progress.html",
            mock_progress=mock_progress,
            recent_results=recent_results,
            coding_progress=coding_progress
        )

    except Exception:
        app.logger.exception(
            "Progress page error"
        )

        flash(
            "Unable to load progress.",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )

    finally:
        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =========================================================
# ACTIVITY API
# =========================================================

@app.route("/api/activity")
def activity_api():

    if "user_id" not in session:
        return jsonify({
            "success": False,
            "message": "Unauthorized"
        }), 401

    user_id = session["user_id"]

    conn = None
    cursor = None

    activities = []

    try:
        conn = get_db_connection()
        cursor = conn.cursor(
            pymysql.cursors.DictCursor
        )

        # -------------------------------------------------
        # MOCK TEST ACTIVITY
        # -------------------------------------------------
        cursor.execute("""
            SELECT
                'Mock Test' AS activity_type,
                score,
                total_questions,
                percentage,
                test_date AS activity_date
            FROM results
            WHERE user_id = %s
            ORDER BY test_date DESC
            LIMIT 10
        """, (user_id,))

        results = cursor.fetchall()

        for result in results:

            activities.append({
                "type": "Mock Test",
                "title": "Mock Test Completed",
                "score": result["score"],
                "total": result["total_questions"],
                "percentage": result["percentage"],
                "date": result["activity_date"]
            })

        # -------------------------------------------------
        # CODING ACTIVITY
        # -------------------------------------------------
        try:
            cursor.execute("""
                SELECT
                    language,
                    status,
                    created_at
                FROM coding_submissions
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT 10
            """, (user_id,))

            submissions = cursor.fetchall()

            for submission in submissions:

                activities.append({
                    "type": "Coding",
                    "title": "Coding Submission",
                    "language": submission["language"],
                    "status": submission["status"],
                    "date": submission["created_at"]
                })

        except Exception:
            pass

        # -------------------------------------------------
        # SORT ACTIVITY
        # -------------------------------------------------
        activities.sort(
            key=lambda x: str(
                x.get("date", "")
            ),
            reverse=True
        )

        return jsonify({
            "success": True,
            "activities": activities[:20]
        })

    except Exception:
        app.logger.exception(
            "Activity API error"
        )

        return jsonify({
            "success": False,
            "message": "Unable to load activity."
        }), 500

    finally:
        if cursor:
            cursor.close()

        if conn:
            conn.close()

# =========================================================
# PART 7 — ADMIN DASHBOARD + ADMIN MANAGEMENT
# =========================================================


# =========================================================
# ADMIN ACCESS HELPER
# =========================================================

def admin_required():

    if "user_id" not in session:
        return False

    role = session.get("role", "")

    return role.lower() == "admin"




# =========================================================
# ADMIN — USERS
# =========================================================

@app.route("/admin/users")
def admin_users():

    if not admin_required():
        flash("Admin access required.", "danger")
        return redirect(url_for("dashboard"))

    conn = None
    cursor = None

    try:

        conn = get_db_connection()
        cursor = conn.cursor(
            pymysql.cursors.DictCursor
        )

        search = request.args.get(
            "search",
            ""
        ).strip()

        if search:

            search_value = f"%{search}%"

            cursor.execute("""
                SELECT
                    id,
                    name,
                    email,
                    role
                FROM users
                WHERE name LIKE %s
                   OR email LIKE %s
                ORDER BY id DESC
            """, (
                search_value,
                search_value
            ))

        else:

            cursor.execute("""
                SELECT
                    id,
                    name,
                    email,
                    role
                FROM users
                ORDER BY id DESC
            """)

        users = cursor.fetchall()

        return render_template(
            "admin/users.html",
            users=users,
            search=search
        )

    except Exception:

        app.logger.exception(
            "Admin users error"
        )

        flash(
            "Unable to load users.",
            "danger"
        )

        return redirect(
            url_for("admin_dashboard")
        )

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =========================================================
# ADMIN — CHANGE USER ROLE
# =========================================================
# =========================================================
# ADMIN — DELETE USER
# =========================================================
# =========================================================
# ADMIN — MOCK QUESTIONS
# =========================================================

@app.route("/admin/mock-questions")
@app.route("/admin/mock_questions")
def admin_mock_questions():

    if not admin_required():
        flash("Admin access required.", "danger")
        return redirect(url_for("dashboard"))

    conn = None
    cursor = None

    try:

        conn = get_db_connection()
        cursor = conn.cursor(
            pymysql.cursors.DictCursor
        )

        category = request.args.get(
            "category",
            ""
        ).strip()

        search = request.args.get(
            "search",
            ""
        ).strip()

        conditions = []
        params = []

        if category:

            conditions.append(
                "category = %s"
            )

            params.append(category)

        if search:

            conditions.append("""
                question LIKE %s
            """)

            params.append(
                f"%{search}%"
            )

        where_clause = ""

        if conditions:

            where_clause = (
                "WHERE "
                + " AND ".join(conditions)
            )

        cursor.execute(
            f"""
            SELECT
                id,
                question,
                option1,
                option2,
                option3,
                option4,
                answer,
                category,
                level
            FROM mock_questions
            {where_clause}
            ORDER BY id DESC
            LIMIT 200
            """,
            tuple(params)
        )

        questions = cursor.fetchall()

        return render_template(
            "admin/mock_questions.html",
            questions=questions,
            category=category,
            search=search
        )

    except Exception:

        app.logger.exception(
            "Admin mock questions error"
        )

        flash(
            "Unable to load mock questions.",
            "danger"
        )

        return redirect(
            url_for("admin_dashboard")
        )

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =========================================================
# ADMIN — ADD MOCK QUESTION
# =========================================================

@app.route(
    "/admin/mock-questions/add",
    methods=["POST"]
)
def admin_add_mock_question():

    if not admin_required():

        return jsonify({
            "success": False,
            "message": "Admin access required."
        }), 403

    data = request.get_json(
        silent=True
    )

    if not data:
        data = request.form.to_dict()

    question = data.get(
        "question",
        ""
    ).strip()

    option1 = data.get(
        "option1",
        ""
    ).strip()

    option2 = data.get(
        "option2",
        ""
    ).strip()

    option3 = data.get(
        "option3",
        ""
    ).strip()

    option4 = data.get(
        "option4",
        ""
    ).strip()

    answer = data.get(
        "answer",
        ""
    ).strip()

    category = data.get(
        "category",
        ""
    ).strip()

    level = data.get(
        "level",
        "Basic"
    ).strip()

    if not question:

        return jsonify({
            "success": False,
            "message": "Question is required."
        }), 400

    if not all([
        option1,
        option2,
        option3,
        option4
    ]):

        return jsonify({
            "success": False,
            "message": "All four options are required."
        }), 400

    if not answer:

        return jsonify({
            "success": False,
            "message": "Correct answer is required."
        }), 400

    conn = None
    cursor = None

    try:

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO mock_questions
            (
                question,
                option1,
                option2,
                option3,
                option4,
                answer,
                category,
                level
            )
            VALUES
            (
                %s, %s, %s, %s,
                %s, %s, %s, %s
            )
        """, (
            question,
            option1,
            option2,
            option3,
            option4,
            answer,
            category,
            level
        ))

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Mock question added successfully."
        })

    except Exception:

        if conn:
            conn.rollback()

        app.logger.exception(
            "Add mock question error"
        )

        return jsonify({
            "success": False,
            "message": "Unable to add question."
        }), 500

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =========================================================
# ADMIN — DELETE MOCK QUESTION
# =========================================================

@app.route(
    "/admin/mock-questions/<int:question_id>/delete",
    methods=["POST", "DELETE"]
)
def admin_delete_mock_question(question_id):

    if not admin_required():

        return jsonify({
            "success": False,
            "message": "Admin access required."
        }), 403

    conn = None
    cursor = None

    try:

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM mock_questions
            WHERE id = %s
        """, (question_id,))

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Question deleted successfully."
        })

    except Exception:

        if conn:
            conn.rollback()

        app.logger.exception(
            "Delete mock question error"
        )

        return jsonify({
            "success": False,
            "message": "Unable to delete question."
        }), 500

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =========================================================
# ADMIN — INTERVIEW QUESTIONS
# =========================================================

@app.route("/admin/interview-questions")
@app.route("/admin/interview_questions")
def admin_interview_questions():

    if not admin_required():
        flash("Admin access required.", "danger")
        return redirect(url_for("dashboard"))

    conn = None
    cursor = None

    try:

        conn = get_db_connection()
        cursor = conn.cursor(
            pymysql.cursors.DictCursor
        )

        search = request.args.get(
            "search",
            ""
        ).strip()

        category = request.args.get(
            "category",
            ""
        ).strip()

        conditions = []
        params = []

        if search:

            conditions.append("""
                (
                    question LIKE %s
                    OR answer LIKE %s
                )
            """)

            search_value = f"%{search}%"

            params.extend([
                search_value,
                search_value
            ])

        if category:

            conditions.append(
                "category = %s"
            )

            params.append(category)

        where_clause = ""

        if conditions:

            where_clause = (
                "WHERE "
                + " AND ".join(conditions)
            )

        cursor.execute(
            f"""
            SELECT
                id,
                question,
                answer,
                category,
                level
            FROM interview_questions
            {where_clause}
            ORDER BY id DESC
            LIMIT 200
            """,
            tuple(params)
        )

        questions = cursor.fetchall()

        return render_template(
            "admin/interview_questions.html",
            questions=questions,
            search=search,
            category=category
        )

    except Exception:

        app.logger.exception(
            "Admin interview questions error"
        )

        flash(
            "Unable to load interview questions.",
            "danger"
        )

        return redirect(
            url_for("admin_dashboard")
        )

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()
# =========================================================
# ADMIN — ADD INTERVIEW QUESTION
# =========================================================
# =========================================================
# ADMIN — DELETE INTERVIEW QUESTION
# =========================================================
# =========================================================
# PART 7 — ADMIN DASHBOARD + ADMIN MANAGEMENT
# =========================================================
# =========================================================
# ADMIN ACCESS HELPER
# =========================================================
def admin_required():
    if "user_id" not in session:
        return False
    role = session.get("role", "")
    return role.lower() == "admin"
# =========================================================
# ADMIN DASHBOARD
# =========================================================
@app.route("/admin")
@app.route("/admin/dashboard")
def admin_dashboard():

    if not admin_required():
        flash("Admin access required.", "danger")
        return redirect(url_for("dashboard"))

    conn = None
    cursor = None

    try:

        conn = get_db_connection()
        cursor = conn.cursor(
            pymysql.cursors.DictCursor
        )

        # -------------------------------------------------
        # TOTAL USERS
        # -------------------------------------------------

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM users
        """)

        total_users = cursor.fetchone()["total"]

        # -------------------------------------------------
        # TOTAL MOCK QUESTIONS
        # -------------------------------------------------

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM mock_questions
        """)

        total_mock_questions = (
            cursor.fetchone()["total"]
        )

        # -------------------------------------------------
        # TOTAL INTERVIEW QUESTIONS
        # -------------------------------------------------

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM interview_questions
        """)

        total_interview_questions = (
            cursor.fetchone()["total"]
        )

        # -------------------------------------------------
        # TOTAL TEST ATTEMPTS
        # -------------------------------------------------

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM results
        """)

        total_test_attempts = (
            cursor.fetchone()["total"]
        )

        # -------------------------------------------------
        # RECENT USERS
        # -------------------------------------------------

        cursor.execute("""
            SELECT
                id,
                name,
                email,
                role
            FROM users
            ORDER BY id DESC
            LIMIT 10
        """)

        recent_users = cursor.fetchall()

        # -------------------------------------------------
        # RECENT RESULTS
        # -------------------------------------------------

        cursor.execute("""
            SELECT
                r.id,
                r.score,
                r.total_questions,
                r.percentage,
                r.test_date,
                u.name,
                u.email
            FROM results r
            LEFT JOIN users u
                ON r.user_id = u.id
            ORDER BY r.test_date DESC
            LIMIT 10
        """)

        recent_results = cursor.fetchall()

        return render_template(
            "admin/dashboard.html",
            total_users=total_users,
            total_mock_questions=total_mock_questions,
            total_interview_questions=total_interview_questions,
            total_test_attempts=total_test_attempts,
            recent_users=recent_users,
            recent_results=recent_results
        )

    except Exception:

        app.logger.exception(
            "Admin dashboard error"
        )

        flash(
            "Unable to load admin dashboard.",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =========================================================
# ADMIN — USERS
# =========================================================
# =========================================================
# ADMIN — CHANGE USER ROLE
# =========================================================

@app.route(
    "/admin/users/<int:user_id>/role",
    methods=["POST"]
)
def admin_change_role(user_id):

    if not admin_required():

        return jsonify({
            "success": False,
            "message": "Admin access required."
        }), 403

    current_user_id = session["user_id"]

    # -----------------------------------------------------
    # PREVENT SELF ROLE CHANGE
    # -----------------------------------------------------

    if user_id == current_user_id:

        return jsonify({
            "success": False,
            "message": "You cannot change your own role."
        }), 400

    data = request.get_json(
        silent=True
    ) or {}

    new_role = str(
        data.get("role", "")
    ).strip().lower()

    allowed_roles = {
        "user",
        "admin"
    }

    if new_role not in allowed_roles:

        return jsonify({
            "success": False,
            "message": "Invalid role."
        }), 400

    conn = None
    cursor = None

    try:

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE users
            SET role = %s
            WHERE id = %s
        """, (
            new_role,
            user_id
        ))

        conn.commit()

        return jsonify({
            "success": True,
            "message": "User role updated."
        })

    except Exception:

        if conn:
            conn.rollback()

        app.logger.exception(
            "Change user role error"
        )

        return jsonify({
            "success": False,
            "message": "Unable to update role."
        }), 500

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =========================================================
# ADMIN — DELETE USER
# =========================================================

@app.route(
    "/admin/users/<int:user_id>/delete",
    methods=["POST", "DELETE"]
)
def admin_delete_user(user_id):

    if not admin_required():

        return jsonify({
            "success": False,
            "message": "Admin access required."
        }), 403

    current_user_id = session["user_id"]

    if user_id == current_user_id:

        return jsonify({
            "success": False,
            "message": "You cannot delete your own account."
        }), 400

    conn = None
    cursor = None

    try:

        conn = get_db_connection()
        cursor = conn.cursor()

        # -------------------------------------------------
        # DELETE USER
        # -------------------------------------------------

        cursor.execute("""
            DELETE FROM users
            WHERE id = %s
        """, (user_id,))

        conn.commit()

        return jsonify({
            "success": True,
            "message": "User deleted successfully."
        })

    except Exception:

        if conn:
            conn.rollback()

        app.logger.exception(
            "Admin delete user error"
        )

        return jsonify({
            "success": False,
            "message": "Unable to delete user."
        }), 500

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =========================================================
# ADMIN — MOCK QUESTIONS
# =========================================================

# =========================================================
# ADMIN — ADD MOCK QUESTION
# =========================================================
# =========================================================
# ADMIN — DELETE MOCK QUESTION
# =========================================================
# =========================================================
# ADMIN — INTERVIEW QUESTIONS
# =========================================================


# =========================================================
# ADMIN — ADD INTERVIEW QUESTION
# =========================================================

@app.route(
    "/admin/interview-questions/add",
    methods=["POST"]
)
def admin_add_interview_question():

    if not admin_required():

        return jsonify({
            "success": False,
            "message": "Admin access required."
        }), 403

    data = request.get_json(
        silent=True
    )

    if not data:
        data = request.form.to_dict()

    question = data.get(
        "question",
        ""
    ).strip()

    answer = data.get(
        "answer",
        ""
    ).strip()

    category = data.get(
        "category",
        ""
    ).strip()

    level = data.get(
        "level",
        "Basic"
    ).strip()

    if not question:

        return jsonify({
            "success": False,
            "message": "Question is required."
        }), 400

    if not answer:

        return jsonify({
            "success": False,
            "message": "Answer is required."
        }), 400

    conn = None
    cursor = None

    try:

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO interview_questions
            (
                question,
                answer,
                category,
                level
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s
            )
        """, (
            question,
            answer,
            category,
            level
        ))

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Interview question added successfully."
        })

    except Exception:

        if conn:
            conn.rollback()

        app.logger.exception(
            "Add interview question error"
        )

        return jsonify({
            "success": False,
            "message": "Unable to add interview question."
        }), 500

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =========================================================
# ADMIN — DELETE INTERVIEW QUESTION
# =========================================================

@app.route(
    "/admin/interview-questions/<int:question_id>/delete",
    methods=["POST", "DELETE"]
)
def admin_delete_interview_question(
    question_id
):

    if not admin_required():

        return jsonify({
            "success": False,
            "message": "Admin access required."
        }), 403

    conn = None
    cursor = None

    try:

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM interview_questions
            WHERE id = %s
        """, (question_id,))

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Interview question deleted."
        })

    except Exception:

        if conn:
            conn.rollback()

        app.logger.exception(
            "Delete interview question error"
        )

        return jsonify({
            "success": False,
            "message": "Unable to delete question."
        }), 500

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()
            # =========================================================
# PART 9 — AI COACH + AI INTERVIEW + AI RESUME ASSISTANT
# =========================================================


# =========================================================
# AI HELPER
# =========================================================

def get_ai_response(prompt):
    """
    Central AI helper.

    Priority:
    1. Existing gemini_ai.py helper, if available
    2. Return a safe fallback response

    IMPORTANT:
    API key ko app.py mein hard-code mat karna.
    """

    try:

        # -------------------------------------------------
        # EXISTING GEMINI MODULE
        # -------------------------------------------------

        import gemini_ai

        # Try common function names
        if hasattr(gemini_ai, "generate_response"):

            return gemini_ai.generate_response(
                prompt
            )

        if hasattr(gemini_ai, "ask_gemini"):

            return gemini_ai.ask_gemini(
                prompt
            )

        if hasattr(gemini_ai, "generate_ai_response"):

            return gemini_ai.generate_ai_response(
                prompt
            )

    except Exception:

        app.logger.exception(
            "AI helper error"
        )

    return None


# =========================================================
# AI COACH PAGE
# =========================================================

@app.route("/ai-coach")
@app.route("/ai_coach")
def ai_coach():

    if "user_id" not in session:
        flash("Please login first.", "warning")
        return redirect(url_for("login"))

    return render_template(
        "ai_coach.html"
    )


# =========================================================
# AI COACH CHAT
# =========================================================

@app.route(
    "/api/ai-coach",
    methods=["POST"]
)
@app.route(
    "/api/ai_coach",
    methods=["POST"]
)
def ai_coach_api():

    if "user_id" not in session:

        return jsonify({
            "success": False,
            "message": "Unauthorized"
        }), 401

    data = request.get_json(
        silent=True
    ) or {}

    message = str(
        data.get("message", "")
    ).strip()

    if not message:

        return jsonify({
            "success": False,
            "message": "Message is required."
        }), 400

    # -----------------------------------------------------
    # LIMIT INPUT SIZE
    # -----------------------------------------------------

    if len(message) > 4000:

        return jsonify({
            "success": False,
            "message": "Message is too long."
        }), 400

    # -----------------------------------------------------
    # AI SYSTEM PROMPT
    # -----------------------------------------------------

    prompt = f"""
You are an AI Placement Coach inside a student
Placement Training Portal.

Help the student with:
- Java
- Python
- HTML
- CSS
- JavaScript
- SQL
- DBMS
- Data Structures
- Algorithms
- Interview preparation
- Resume preparation
- Communication skills
- Placement preparation

Rules:
1. Give clear and practical answers.
2. Keep normal answers concise.
3. For programming questions, provide correct examples.
4. Do not invent facts.
5. Encourage learning rather than blindly copying answers.

Student message:
{message}
"""

    response = get_ai_response(
        prompt
    )

    if not response:

        return jsonify({
            "success": False,
            "message": (
                "AI service is currently unavailable."
            )
        }), 503

    return jsonify({
        "success": True,
        "response": str(response).strip()
    })


# =========================================================
# AI INTERVIEW PAGE
# =========================================================

@app.route("/ai-interview")
@app.route("/ai_interview")
def ai_interview():

    if "user_id" not in session:
        flash("Please login first.", "warning")
        return redirect(url_for("login"))

    return render_template(
        "ai_interview.html"
    )


# =========================================================
# AI GENERATE INTERVIEW QUESTION
# =========================================================
@app.route(
    "/api/ai-interview/question",
    methods=["POST"]
)
def ai_interview_question():

    if "user_id" not in session:

        return jsonify({
            "success": False,
            "message": "Unauthorized"
        }), 401

    data = request.get_json(
        silent=True
    ) or {}

    category = str(
        data.get(
            "category",
            "Technical"
        )
    ).strip()

    level = str(
        data.get(
            "level",
            "Medium"
        )
    ).strip()

    prompt = f"""
Generate ONE interview question for a student
preparing for placements.

Category: {category}
Difficulty: {level}

Return only:
1. The interview question
2. A short list of what a good answer should cover

Do not provide a long explanation.
"""

    response = get_ai_response(
        prompt
    )

    if not response:

        return jsonify({
            "success": False,
            "message": "AI service unavailable."
        }), 503

    return jsonify({
        "success": True,
        "question": str(response).strip(),
        "category": category,
        "level": level
    })


# =========================================================
# AI INTERVIEW ANSWER EVALUATION
# =========================================================

@app.route(
    "/api/ai-interview/evaluate",
    methods=["POST"]
)
def ai_interview_evaluate():

    if "user_id" not in session:

        return jsonify({
            "success": False,
            "message": "Unauthorized"
        }), 401

    data = request.get_json(
        silent=True
    ) or {}

    question = str(
        data.get("question", "")
    ).strip()

    answer = str(
        data.get("answer", "")
    ).strip()

    if not question:

        return jsonify({
            "success": False,
            "message": "Question is required."
        }), 400

    if not answer:

        return jsonify({
            "success": False,
            "message": "Answer is required."
        }), 400

    if len(answer) > 8000:

        return jsonify({
            "success": False,
            "message": "Answer is too long."
        }), 400

    prompt = f"""
You are an interview evaluator.

Evaluate the student's interview answer.

Interview Question:
{question}

Student Answer:
{answer}

Evaluate:
- Correctness
- Technical understanding
- Clarity
- Communication
- Missing points
- Improvement suggestions

Give a score out of 10.

Keep the feedback constructive and concise.
"""

    response = get_ai_response(
        prompt
    )

    if not response:

        return jsonify({
            "success": False,
            "message": "AI service unavailable."
        }), 503

    return jsonify({
        "success": True,
        "feedback": str(response).strip()
    })


# =========================================================
# AI RESUME ASSISTANT
# =========================================================

@app.route("/ai-resume")
@app.route("/ai_resume")
def ai_resume():

    if "user_id" not in session:
        flash("Please login first.", "warning")
        return redirect(url_for("login"))

    return render_template(
        "ai_resume.html"
    )


# =========================================================
# AI RESUME SUMMARY
# =========================================================

@app.route(
    "/api/ai-resume/summary",
    methods=["POST"]
)
def ai_resume_summary():

    if "user_id" not in session:

        return jsonify({
            "success": False,
            "message": "Unauthorized"
        }), 401

    data = request.get_json(
        silent=True
    ) or {}

    skills = str(
        data.get("skills", "")
    ).strip()

    education = str(
        data.get("education", "")
    ).strip()

    projects = str(
        data.get("projects", "")
    ).strip()

    experience = str(
        data.get("experience", "")
    ).strip()

    if not any([
        skills,
        education,
        projects,
        experience
    ]):

        return jsonify({
            "success": False,
            "message": (
                "Please provide some resume information."
            )
        }), 400

    prompt = f"""
Create a professional resume summary for a
student applying for software/IT placement opportunities.

Education:
{education}

Skills:
{skills}

Projects:
{projects}

Experience:
{experience}

Requirements:
- Professional
- Concise
- Suitable for a fresher/student
- Do not invent experience
- Highlight genuine technical skills
"""

    response = get_ai_response(
        prompt
    )

    if not response:

        return jsonify({
            "success": False,
            "message": "AI service unavailable."
        }), 503

    return jsonify({
        "success": True,
        "summary": str(response).strip()
    })


# =========================================================
# AI PROJECT DESCRIPTION
# =========================================================

@app.route(
    "/api/ai-resume/project",
    methods=["POST"]
)
def ai_project_description():

    if "user_id" not in session:

        return jsonify({
            "success": False,
            "message": "Unauthorized"
        }), 401

    data = request.get_json(
        silent=True
    ) or {}

    project_name = str(
        data.get("project_name", "")
    ).strip()

    technologies = str(
        data.get("technologies", "")
    ).strip()

    project_details = str(
        data.get("details", "")
    ).strip()

    if not project_name:

        return jsonify({
            "success": False,
            "message": "Project name is required."
        }), 400

    prompt = f"""
Write a concise professional resume project
description.

Project:
{project_name}

Technologies:
{technologies}

Details:
{project_details}

Rules:
- Do not invent features.
- Use professional resume language.
- Focus on what was actually built.
- Keep it concise.
"""

    response = get_ai_response(
        prompt
    )

    if not response:

        return jsonify({
            "success": False,
            "message": "AI service unavailable."
        }), 503

    return jsonify({
        "success": True,
        "description": str(response).strip()
    })


# =========================================================
# AI SKILL GAP ANALYSIS
# =========================================================

@app.route(
    "/api/ai/skill-gap",
    methods=["POST"]
)
def ai_skill_gap():

    if "user_id" not in session:

        return jsonify({
            "success": False,
            "message": "Unauthorized"
        }), 401

    data = request.get_json(
        silent=True
    ) or {}

    current_skills = str(
        data.get(
            "current_skills",
            ""
        )
    ).strip()

    target_role = str(
        data.get(
            "target_role",
            "Software Developer"
        )
    ).strip()

    if not current_skills:

        return jsonify({
            "success": False,
            "message": "Current skills are required."
        }), 400

    prompt = f"""
You are a placement preparation coach.

Student's current skills:
{current_skills}

Target role:
{target_role}

Identify:
1. Strong existing areas
2. Important missing skills
3. Suggested learning order
4. Interview preparation topics

Do not claim the student has skills
that were not provided.
"""

    response = get_ai_response(
        prompt
    )

    if not response:

        return jsonify({
            "success": False,
            "message": "AI service unavailable."
        }), 503

    return jsonify({
        "success": True,
        "analysis": str(response).strip()
    })


# =========================================================
# AI COMMUNICATION PRACTICE
# =========================================================

@app.route(
    "/api/ai/communication",
    methods=["POST"]
)
def ai_communication():

    if "user_id" not in session:

        return jsonify({
            "success": False,
            "message": "Unauthorized"
        }), 401

    data = request.get_json(
        silent=True
    ) or {}

    text = str(
        data.get("text", "")
    ).strip()

    if not text:

        return jsonify({
            "success": False,
            "message": "Text is required."
        }), 400

    prompt = f"""
Act as an English communication coach.

Student's sentence/answer:
{text}

Give:
1. Grammar correction
2. More natural version
3. One short explanation
4. One pronunciation or speaking tip

Keep it encouraging and concise.
"""

    response = get_ai_response(
        prompt
    )

    if not response:

        return jsonify({
            "success": False,
            "message": "AI service unavailable."
        }), 503

    return jsonify({
        "success": True,
        "feedback": str(response).strip()
    })


# =========================================================
# AI CHAT HISTORY — SESSION BASED
# =========================================================

@app.route("/api/ai/history")
def ai_history():

    if "user_id" not in session:

        return jsonify({
            "success": False,
            "message": "Unauthorized"
        }), 401

    history = session.get(
        "ai_history",
        []
    )

    return jsonify({
        "success": True,
        "history": history[-20:]
    })


# =========================================================
# SAVE AI CHAT MESSAGE
# =========================================================

@app.route(
    "/api/ai/history",
    methods=["POST"]
)
def save_ai_history():

    if "user_id" not in session:

        return jsonify({
            "success": False,
            "message": "Unauthorized"
        }), 401

    data = request.get_json(
        silent=True
    ) or {}

    user_message = str(
        data.get("user_message", "")
    ).strip()

    ai_message = str(
        data.get("ai_message", "")
    ).strip()

    if not user_message or not ai_message:

        return jsonify({
            "success": False,
            "message": "Both messages are required."
        }), 400

    history = session.get(
        "ai_history",
        []
    )

    history.append({
        "user": user_message,
        "assistant": ai_message
    })

    # Keep only latest 20 conversations
    session["ai_history"] = history[-20:]

    return jsonify({
        "success": True,
        "message": "AI conversation saved."
    })


# =========================================================
# CLEAR AI HISTORY
# =========================================================

@app.route(
    "/api/ai/history/clear",
    methods=["POST"]
)
def clear_ai_history():

    if "user_id" not in session:

        return jsonify({
            "success": False,
            "message": "Unauthorized"
        }), 401

    session.pop(
        "ai_history",
        None
    )

    return jsonify({
        "success": True,
        "message": "AI history cleared."
    })
    # =========================================================
# PART 10 — SEARCH + CONTACT + FEEDBACK + FINAL STARTUP
# =========================================================


# =========================================================
# GLOBAL SEARCH PAGE
# =========================================================

@app.route("/search")
def global_search():

    if "user_id" not in session:
        flash("Please login first.", "warning")
        return redirect(url_for("login"))

    query = request.args.get(
        "q",
        ""
    ).strip()

    results = {
        "interview": [],
        "mock": [],
        "coding": []
    }

    if not query:
        return render_template(
            "search.html",
            query=query,
            results=results
        )

    if len(query) > 100:
        query = query[:100]

    conn = None
    cursor = None

    try:

        conn = get_db_connection()
        cursor = conn.cursor(
            pymysql.cursors.DictCursor
        )

        search_value = f"%{query}%"

        # -------------------------------------------------
        # INTERVIEW SEARCH
        # -------------------------------------------------

        try:

            cursor.execute("""
                SELECT
                    id,
                    question,
                    category,
                    level
                FROM interview_questions
                WHERE question LIKE %s
                   OR answer LIKE %s
                ORDER BY id DESC
                LIMIT 20
            """, (
                search_value,
                search_value
            ))

            results["interview"] = (
                cursor.fetchall()
            )

        except Exception:

            results["interview"] = []

        # -------------------------------------------------
        # MOCK QUESTION SEARCH
        # -------------------------------------------------

        try:

            cursor.execute("""
                SELECT
                    id,
                    question,
                    category,
                    level
                FROM mock_questions
                WHERE question LIKE %s
                ORDER BY id DESC
                LIMIT 20
            """, (
                search_value,
            ))

            results["mock"] = (
                cursor.fetchall()
            )

        except Exception:

            results["mock"] = []

        # -------------------------------------------------
        # CODING SEARCH
        # -------------------------------------------------

        try:

            cursor.execute("""
                SELECT
                    id,
                    title,
                    description,
                    category,
                    difficulty
                FROM coding_questions
                WHERE title LIKE %s
                   OR description LIKE %s
                ORDER BY id DESC
                LIMIT 20
            """, (
                search_value,
                search_value
            ))

            results["coding"] = (
                cursor.fetchall()
            )

        except Exception:

            results["coding"] = []

        return render_template(
            "search.html",
            query=query,
            results=results
        )

    except Exception:

        app.logger.exception(
            "Global search error"
        )

        flash(
            "Search could not be completed.",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =========================================================
# GLOBAL SEARCH API
# =========================================================

@app.route("/api/search")
def global_search_api():

    if "user_id" not in session:

        return jsonify({
            "success": False,
            "message": "Unauthorized"
        }), 401

    query = request.args.get(
        "q",
        ""
    ).strip()

    if not query:

        return jsonify({
            "success": True,
            "results": []
        })

    if len(query) > 100:
        query = query[:100]

    search_value = f"%{query}%"

    conn = None
    cursor = None

    results = []

    try:

        conn = get_db_connection()
        cursor = conn.cursor(
            pymysql.cursors.DictCursor
        )

        # -------------------------------------------------
        # INTERVIEW
        # -------------------------------------------------

        try:

            cursor.execute("""
                SELECT
                    id,
                    question,
                    category,
                    level
                FROM interview_questions
                WHERE question LIKE %s
                LIMIT 10
            """, (
                search_value,
            ))

            rows = cursor.fetchall()

            for row in rows:

                results.append({
                    "type": "interview",
                    "id": row["id"],
                    "title": row["question"],
                    "category": row["category"],
                    "level": row["level"]
                })

        except Exception:

            pass

        # -------------------------------------------------
        # MOCK
        # -------------------------------------------------

        try:

            cursor.execute("""
                SELECT
                    id,
                    question,
                    category,
                    level
                FROM mock_questions
                WHERE question LIKE %s
                LIMIT 10
            """, (
                search_value,
            ))

            rows = cursor.fetchall()

            for row in rows:

                results.append({
                    "type": "mock",
                    "id": row["id"],
                    "title": row["question"],
                    "category": row["category"],
                    "level": row["level"]
                })

        except Exception:

            pass

        # -------------------------------------------------
        # CODING
        # -------------------------------------------------

        try:

            cursor.execute("""
                SELECT
                    id,
                    title,
                    category,
                    difficulty
                FROM coding_questions
                WHERE title LIKE %s
                LIMIT 10
            """, (
                search_value,
            ))

            rows = cursor.fetchall()

            for row in rows:

                results.append({
                    "type": "coding",
                    "id": row["id"],
                    "title": row["title"],
                    "category": row["category"],
                    "level": row["difficulty"]
                })

        except Exception:

            pass

        return jsonify({
            "success": True,
            "results": results[:30]
        })

    except Exception:

        app.logger.exception(
            "Global search API error"
        )

        return jsonify({
            "success": False,
            "message": "Search failed."
        }), 500

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =========================================================
# CONTACT PAGE
# =========================================================

@app.route("/contact")
def contact():

    return render_template(
        "contact.html"
    )


# =========================================================
# CONTACT FORM
# =========================================================

@app.route(
    "/api/contact",
    methods=["POST"]
)
def contact_api():

    data = request.get_json(
        silent=True
    )

    if not data:
        data = request.form.to_dict()

    name = str(
        data.get("name", "")
    ).strip()

    email = str(
        data.get("email", "")
    ).strip()

    subject = str(
        data.get("subject", "")
    ).strip()

    message = str(
        data.get("message", "")
    ).strip()

    # -----------------------------------------------------
    # VALIDATION
    # -----------------------------------------------------

    if not name:
        return jsonify({
            "success": False,
            "message": "Name is required."
        }), 400

    if not email:
        return jsonify({
            "success": False,
            "message": "Email is required."
        }), 400

    if not message:
        return jsonify({
            "success": False,
            "message": "Message is required."
        }), 400

    if len(message) > 5000:

        return jsonify({
            "success": False,
            "message": "Message is too long."
        }), 400

    conn = None
    cursor = None

    try:

        conn = get_db_connection()
        cursor = conn.cursor()

        # -------------------------------------------------
        # SAVE CONTACT MESSAGE
        # -------------------------------------------------

        try:

            cursor.execute("""
                INSERT INTO contact_messages
                (
                    name,
                    email,
                    subject,
                    message
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s
                )
            """, (
                name,
                email,
                subject,
                message
            ))

            conn.commit()

        except Exception:

            if conn:
                conn.rollback()

            app.logger.exception(
                "Contact table error"
            )

            return jsonify({
                "success": False,
                "message": (
                    "Contact form storage is not configured."
                )
            }), 500

        return jsonify({
            "success": True,
            "message": (
                "Your message has been sent successfully."
            )
        })

    except Exception:

        if conn:
            conn.rollback()

        app.logger.exception(
            "Contact form error"
        )

        return jsonify({
            "success": False,
            "message": "Unable to send message."
        }), 500

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =========================================================
# FEEDBACK PAGE
# =========================================================

@app.route("/feedback")
def feedback():

    if "user_id" not in session:
        flash("Please login first.", "warning")
        return redirect(url_for("login"))

    return render_template(
        "feedback.html"
    )


# =========================================================
# SUBMIT FEEDBACK
# =========================================================

@app.route(
    "/api/feedback",
    methods=["POST"]
)
def submit_feedback():

    if "user_id" not in session:

        return jsonify({
            "success": False,
            "message": "Please login first."
        }), 401

    user_id = session["user_id"]

    data = request.get_json(
        silent=True
    )

    if not data:
        data = request.form.to_dict()

    rating = data.get(
        "rating",
        0
    )

    message = str(
        data.get("message", "")
    ).strip()

    try:

        rating = int(rating)

    except (
        ValueError,
        TypeError
    ):

        rating = 0

    if rating < 1 or rating > 5:

        return jsonify({
            "success": False,
            "message": "Rating must be between 1 and 5."
        }), 400

    if not message:

        return jsonify({
            "success": False,
            "message": "Feedback message is required."
        }), 400

    if len(message) > 3000:

        return jsonify({
            "success": False,
            "message": "Feedback is too long."
        }), 400

    conn = None
    cursor = None

    try:

        conn = get_db_connection()
        cursor = conn.cursor()

        # -------------------------------------------------
        # SAVE FEEDBACK
        # -------------------------------------------------

        cursor.execute("""
            INSERT INTO feedback
            (
                user_id,
                rating,
                message
            )
            VALUES
            (
                %s,
                %s,
                %s
            )
        """, (
            user_id,
            rating,
            message
        ))

        conn.commit()

        return jsonify({
            "success": True,
            "message": (
                "Thank you for your feedback!"
            )
        })

    except Exception:

        if conn:
            conn.rollback()

        app.logger.exception(
            "Feedback submission error"
        )

        return jsonify({
            "success": False,
            "message": "Unable to submit feedback."
        }), 500

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =========================================================
# FAQ PAGE
# =========================================================

@app.route("/faq")
@app.route("/faqs")
def faq():

    return render_template(
        "faq.html"
    )


# =========================================================
# SIMPLE PAGINATION HELPER
# =========================================================

def get_pagination(
    page,
    per_page,
    total_items
):

    try:
        page = int(page)
    except (
        ValueError,
        TypeError
    ):
        page = 1

    try:
        per_page = int(per_page)
    except (
        ValueError,
        TypeError
    ):
        per_page = 20

    if page < 1:
        page = 1

    if per_page < 1:
        per_page = 20

    if per_page > 100:
        per_page = 100

    total_pages = (
        (total_items + per_page - 1)
        // per_page
    )

    if total_pages > 0 and page > total_pages:
        page = total_pages

    offset = (
        (page - 1)
        * per_page
    )

    return {
        "page": page,
        "per_page": per_page,
        "offset": offset,
        "total_items": total_items,
        "total_pages": total_pages
    }


# =========================================================
# TEMPLATE GLOBAL VARIABLES
# =========================================================

@app.context_processor
def inject_global_data():

    return {
        "logged_in": (
            "user_id" in session
        ),
        "current_user_name": session.get(
            "name",
            ""
        ),
        "current_user_email": session.get(
            "email",
            ""
        ),
        "current_user_role": session.get(
            "role",
            ""
        )
    }


@app.route("/courses")
def courses():

    if "user_id" not in session:
        return redirect(url_for("login"))

    courses = [
        {
            "name": "Java",
            "icon": "☕",
            "days": 30
        },
        {
            "name": "Python",
            "icon": "🐍",
            "days": 30
        },
        {
            "name": "HTML",
            "icon": "🌐",
            "days": 15
        },
        {
            "name": "CSS",
            "icon": "🎨",
            "days": 20
        },
        {
            "name": "JavaScript",
            "icon": "⚡",
            "days": 30
        },
        {
            "name": "DBMS",
            "icon": "🗄️",
            "days": 20
        },
        {
            "name": "SQL",
            "icon": "📊",
            "days": 20
        },
        {
            "name": "Operating System",
            "icon": "💻",
            "days": 25
        },
        {
            "name": "Computer Networks",
            "icon": "🌍",
            "days": 20
        },
        {
            "name": "DSA",
            "icon": "📚",
            "days": 45
        }
    ]

    return render_template(
        "courses.html",
        courses=courses
    )

@app.route("/course/<course_name>")
def course_learning(course_name):

    if "user_id" not in session:
        return redirect(url_for("login"))

    course_name = course_name.strip()

    course_days = {
        "Java": 30,
        "Python": 30,
        "HTML": 15,
        "CSS": 20,
        "JavaScript": 30,
        "SQL": 25,
        "DBMS": 25,
        "Operating System": 25
    }

    day_count = course_days.get(course_name, 30)

    return render_template(
        "course_learning.html",
        course_name=course_name,
        day_count=day_count
    )

@app.route("/notes")
def notes():

    if "user_id" not in session:
        return redirect(url_for("login"))

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                id,
                title,
                slug,
                category,
                description,
                icon,
                level,
                topics,
                topic_count,
                page_url
            FROM notes
            WHERE is_active = TRUE
            ORDER BY id ASC
        """)

        notes_data = cursor.fetchall()

        cursor.close()
        conn.close()

        return render_template(
            "notes.html",
            notes=notes_data
        )

    except Exception as e:
        print("NOTES ERROR:", e)

        flash("Unable to load notes.", "error")

        return render_template(
            "notes.html",
            notes=[]
        )
    
@app.route("/leaderboard")
def leaderboard():
    return render_template("leaderboard.html")

@app.route("/results")
def results():
    if "user_id" not in session:
        flash("Please login first.", "warning")
        return redirect(url_for("login"))

    user_id = session["user_id"]

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        cursor.execute("""
            SELECT
                id,
                score,
                total_questions,
                percentage,
                test_date
            FROM results
            WHERE user_id = %s
            ORDER BY test_date DESC
        """, (user_id,))

        results_data = cursor.fetchall()

        return render_template(
            "results.html",
            results=results_data
        )

    except Exception as e:
        print("Results error:", e)
        flash("Unable to load results.", "danger")
        return redirect(url_for("dashboard"))

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# ============================================================
# COURSE / NOTES ROUTES
# ============================================================

@app.route("/java")
def java():
    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template("java.html")


@app.route("/python")
def python():
    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template("python.html")


@app.route("/dsa")
def dsa():
    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template("dsa.html")


@app.route("/c")
def c():
    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template("c.html")


@app.route("/html")
def html():
    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template("html.html")


@app.route("/css")
def css():
    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template("css.html")


@app.route("/javascript")
def javascript():
    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template("javascript.html")


@app.route("/frontend")
def frontend():
    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template("frontend.html")


@app.route("/backend")
def backend():
    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template("backend.html")


@app.route("/full-stack-java")
def full_stack_java():
    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template("full_stack_java.html")


@app.route("/full-stack-python")
def full_stack_python():
    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template("full_stack_python.html")


@app.route("/dbms")
def dbms():
    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template("dbms.html")


# @app.route("/os")
# def os():
#     if "user_id" not in session:
#         return redirect(url_for("login"))

#     return render_template("os.html")


@app.route("/cn")
def cn():
    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template("cn.html")


@app.route("/software-engineering")
def software_engineering():
    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template("software_engineering.html")
# =========================================================
# APPLICATION STARTUP
# =========================================================

if __name__ == "__main__":

    # -----------------------------------------------------
    # ENVIRONMENT
    # -----------------------------------------------------

    port = int(
        os.getenv(
            "PORT",
            5000
        )
    )

    host = os.getenv(
        "HOST",
        "0.0.0.0"
    )

    debug = (
        os.getenv(
            "FLASK_DEBUG",
            "False"
        ).lower()
        == "true"
    )

    # -----------------------------------------------------
    # START FLASK
    # -----------------------------------------------------

    app.run(
        host=host,
        port=port,
        debug=debug
    )
