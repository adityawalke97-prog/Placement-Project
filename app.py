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
from flask import abort
from flask_bcrypt import Bcrypt
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import timedelta
from functools import wraps
import pymysql
import secrets
import math
import os
import json
import csv
import random
import io
from functools import wraps
from datetime import datetime
from zoneinfo import ZoneInfo
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer
)
from reportlab.lib.styles import getSampleStyleSheet
load_dotenv()
app = Flask(__name__)
bcrypt = Bcrypt(app)
from flask import send_from_directory
@app.route('/google198ac2c96cde6243.html')
def google_verification():
    return send_from_directory(
        app.root_path,
        'google198ac2c96cde6243.html'
    )
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
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CA = os.path.join(BASE_DIR, "ca.pem")
IS_RENDER = bool(os.getenv("RENDER"))
def get_db_connection():
    ca_path = os.getenv("DB_CA", DEFAULT_CA)
    if not os.path.isabs(ca_path):
        ca_path = os.path.join(BASE_DIR, ca_path)
    return pymysql.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", "4000")),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        cursorclass=pymysql.cursors.DictCursor,
        ssl={
            "ca": ca_path
        },
        connect_timeout=30,
        read_timeout=30,
        write_timeout=30,
        autocommit=False
    )
app.config.update(
    SESSION_COOKIE_SECURE=IS_RENDER,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    PERMANENT_SESSION_LIFETIME=timedelta(days=7),
    PREFERRED_URL_SCHEME="https" if IS_RENDER else "http"
)
oauth = OAuth(app)
google = oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url=(
        "https://accounts.google.com/"
        ".well-known/openid-configuration"
    ),
    client_kwargs={
        "scope": "openid email profile"
    }
)
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash(
                "Please login first.",
                "warning"
            )
            return redirect(
                url_for("login")
            )
        return f(*args, **kwargs)
    return decorated_function
@app.route("/")
def home():
    return redirect(
        url_for("login")
    )
def get_google_redirect_uri():
    if IS_RENDER:
        return (
            "https://placement-projectadityaw.onrender.com"
            "/login/google/callback"
        )
    return (
        "http://localhost:5000"
        "/login/google/callback"
    )
@app.route("/login/google")
def google_login():
    session.permanent = True
    redirect_uri = get_google_redirect_uri()
    print(
        "GOOGLE REDIRECT URI:",
        redirect_uri
    )
    return google.authorize_redirect(
        redirect_uri
    )
@app.route("/login/google/callback")
def google_callback():
    conn = None
    cur = None
    try:
        token = google.authorize_access_token()
        print(
            "GOOGLE TOKEN RECEIVED"
        )
        userinfo = token.get(
            "userinfo"
        )
        if not userinfo:
            resp = google.get(
                "https://openidconnect.googleapis.com/v1/userinfo"
            )
            resp.raise_for_status()
            userinfo = resp.json()
        print(
            "GOOGLE USERINFO:",
            userinfo
        )
        name = userinfo.get("name")
        email = userinfo.get("email")
        google_id = userinfo.get("sub")
        picture = userinfo.get("picture")
        verified = userinfo.get(
            "email_verified",
            False
        )
        if not email or not google_id:
            raise Exception(
                "Google account information incomplete"
            )
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT *
            FROM users
            WHERE email=%s
            LIMIT 1
            """,
            (email,)
        )
        user = cur.fetchone()
        if user:
            cur.execute(
                """
                UPDATE users
                SET
                    google_id=%s,
                    profile_pic=%s,
                    email_verified=%s,
                    login_provider='google'
                WHERE email=%s
                """,
                (
                    google_id,
                    picture,
                    1 if verified else 0,
                    email
                )
            )
            conn.commit()
            user_id = user["id"]
            user_name = user["name"]
        else:
            random_password = secrets.token_hex(32)
            hashed_password = bcrypt.generate_password_hash(
                random_password
            ).decode("utf-8")
            cur.execute(
                """
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
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    'google'
                )
                """,
                (
                    name,
                    email,
                    hashed_password,
                    google_id,
                    picture,
                    1 if verified else 0
                )
            )
            conn.commit()
            user_id = cur.lastrowid
            user_name = name
        session.clear()
        session.permanent = True
        session["user_id"] = user_id
        session["name"] = user_name
        session["email"] = email
        session["profile_pic"] = picture
        session["login_provider"] = "google"
        print(
            "GOOGLE LOGIN SUCCESS:",
            email
        )
        return redirect(
            url_for("dashboard")
        )
    except Exception as e:
        import traceback
        print("================================")
        print("GOOGLE LOGIN ERROR:", repr(e))
        traceback.print_exc()
        print("================================")
        return redirect(url_for("login"))
    except Exception as e:
        print(
            "================================"
        )
        print(
            "GOOGLE LOGIN ERROR:",
            repr(e)
        )
        print(
            "================================"
        )
        if conn:
            try:
                conn.rollback()
            except Exception:
                pass
        flash(
            "Google Login Failed. Please try again.",
            "danger"
        )
        return redirect(
            url_for("login")
        )
    finally:
        if cur:
            try:
                cur.close()
            except Exception:
                pass
        if conn:
            try:
                conn.close()
            except Exception:
                pass
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        if not name or not email or not password or not confirm_password:
            flash("Please fill all fields.")
            return redirect(url_for('signup'))
        if password != confirm_password:
            flash("Passwords do not match!")
            return redirect(url_for('signup'))
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, name, email, password FROM users WHERE email = %s",
                (email,)
            )
            existing_user = cursor.fetchone()
            if existing_user:
                flash("Email already registered. Please login.")
                return redirect(url_for('login'))
            hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
            cursor.execute(
                """
                INSERT INTO users (name, email, password)
                VALUES (%s, %s, %s)
                """,
                (name, email, hashed_password)
            )
            conn.commit()
            flash("Account created successfully! Please login.", "success")
            return redirect(url_for('login'))
        except pymysql.err.IntegrityError:
            if conn:
                conn.rollback()
            flash("Email already registered. Please login.")
            return redirect(url_for('login'))
        except Exception as e:
            if conn:
                conn.rollback()
            print("SIGNUP ERROR:", e)
            flash("Something went wrong. Please try again.")
            return redirect(url_for('signup'))
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    return render_template('signup.html')
@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        current_role = str(
            session.get("role", "student")
        ).strip().lower()
        if current_role == "admin":
            return redirect(url_for("admin_dashboard"))
        return redirect(url_for("dashboard"))
    if request.method == "GET":
        return render_template("login.html")
    conn = None
    cursor = None
    try:
        email = request.form.get(
            "email", ""
        ).strip().lower()
        password = request.form.get(
            "password", ""
        )
        selected_role = request.form.get(
            "role", ""
        ).strip().lower()
        remember = (
            request.form.get("remember") == "on"
        )
        if not email or not password:
            flash(
                "Please enter email and password.",
                "warning"
            )
            return redirect(url_for("login"))
        if selected_role not in ("student", "admin"):
            flash(
                "Please select Student or Admin.",
                "warning"
            )
            return redirect(url_for("login"))
        conn = get_db_connection()
        cursor = conn.cursor(
            pymysql.cursors.DictCursor
        )
        cursor.execute("""
            SELECT
                id,
                name,
                email,
                password,
                role
            FROM users
            WHERE LOWER(email) = %s
            LIMIT 1
        """, (email,))
        user = cursor.fetchone()
        if not user:
            flash(
                "Invalid email or password.",
                "danger"
            )
            return redirect(url_for("login"))
        if not bcrypt.check_password_hash(
            user["password"],
            password
        ):
            flash(
                "Invalid email or password.",
                "danger"
            )
            return redirect(url_for("login"))
        user_role = str(
            user.get("role") or "student"
        ).strip().lower()
        if user_role not in ("student", "admin"):
            flash(
                "Your account has an invalid role. Contact administrator.",
                "danger"
            )
            return redirect(url_for("login"))
        if selected_role != user_role:
            flash(
                "Selected account type does not match your account.",
                "danger"
            )
            return redirect(url_for("login"))
        session.clear()
        session["user_id"] = user["id"]
        session["user_name"] = user["name"]
        session["user_email"] = user["email"]
        session["role"] = user_role
        session.permanent = remember
        if user_role == "admin":
            flash(
                "Welcome Admin! Login successful.",
                "success"
            )
            return redirect(
                url_for("admin_dashboard")
            )
        flash(
            "Login successful. Welcome back!",
            "success"
        )
        return redirect(
            url_for("dashboard")
        )
    except Exception:
        app.logger.exception(
            "LOGIN ROUTE ERROR"
        )
        flash(
            "Something went wrong during login. Please try again.",
            "danger"
        )
        return redirect(url_for("login"))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    user_id = session["user_id"]
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute(
            "SELECT * FROM users WHERE id=%s",
            (user_id,)
        )
        user = cursor.fetchone()
        cursor.execute("""
            SELECT
                COUNT(*) total_tests,
                IFNULL(AVG(percentage),0) avg_score,
                IFNULL(MAX(percentage),0) best_score
            FROM results
            WHERE user_id=%s
        """, (user_id,))
        stats = cursor.fetchone()
        cursor.execute("""
            SELECT
                category,
                score,
                total_questions,
                percentage,
                test_date
            FROM results
            WHERE user_id=%s
            ORDER BY test_date DESC
            LIMIT 5
        """, (user_id,))
        recent_tests = cursor.fetchall()
        try:
            cursor.execute(
                "SELECT * FROM communication_progress WHERE user_id=%s",
                (user_id,)
            )
            communication = cursor.fetchone()
        except:
            communication = {}
        try:
            cursor.execute(
                "SELECT * FROM course_progress WHERE user_id=%s",
                (user_id,)
            )
            course = cursor.fetchone()
        except:
            course = {}
        try:
            cursor.execute(
                "SELECT * FROM interview_progress WHERE user_id=%s",
                (user_id,)
            )
            interview = cursor.fetchone()
        except:
            interview = {}
        try:
            cursor.execute(
                "SELECT * FROM resume WHERE user_id=%s",
                (user_id,)
            )
            resume = cursor.fetchone()
        except:
            resume = {}
        try:
            cursor.execute(
                "SELECT * FROM daily_goals WHERE user_id=%s",
                (user_id,)
            )
            goals = cursor.fetchall()
        except:
            goals = []
        try:
            cursor.execute(
                "SELECT * FROM companies ORDER BY company_name"
            )
            company_progress = cursor.fetchall()
        except:
            company_progress = []
        try:
            cursor.execute("""
                SELECT
                    u.name,
                    ROUND(AVG(r.percentage),2) percentage
                FROM users u
                JOIN results r
                ON u.id=r.user_id
                GROUP BY u.id
                ORDER BY percentage DESC
                LIMIT 10
            """)
            leaderboard = cursor.fetchall()
        except:
            leaderboard = []
        xp = int(stats["total_tests"]) * 20
        level = max(1, xp // 100 + 1)
        streak = 0
        rank = 1
        completed_courses = 0
        study_hours = 0
        ats_score = 80
        skills = [
            {"subject":"Java","progress":70,"icon":"fas fa-coffee"},
            {"subject":"Python","progress":60,"icon":"fab fa-python"},
            {"subject":"DBMS","progress":65,"icon":"fas fa-database"},
            {"subject":"OS","progress":55,"icon":"fas fa-desktop"},
            {"subject":"Aptitude","progress":75,"icon":"fas fa-brain"}
        ]
        ai_title = "Today's Recommendation"
        ai_message = "Solve one mock test and practice interview questions."
        ai_tasks = [
            "Complete one mock test",
            "Practice Java interview",
            "Improve communication"
        ]
        weekly_chart = {
            "labels": ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"],
            "scores": [40,55,65,70,75,80,90]
        }
        subject_chart = {
            "labels": ["Java","Python","DBMS","OS","HR"],
            "scores": [80,70,75,65,85]
        }
        return render_template(
            "dashboard.html",
            user=user,
            total_tests=stats["total_tests"],
            avg_score=round(stats["avg_score"],2),
            best_score=stats["best_score"],
            streak=streak,
            rank=rank,
            companies=len(company_progress),
            completed_courses=completed_courses,
            study_hours=study_hours,
            ats_score=ats_score,
            recent_tests=recent_tests,
            communication=communication,
            course=course,
            interview=interview,
            resume=resume,
            goals=goals,
            company_progress=company_progress,
            leaderboard=leaderboard,
            xp=xp,
            level=level,
            skills=skills,
            ai_title=ai_title,
            ai_message=ai_message,
            ai_tasks=ai_tasks,
            weekly_chart=weekly_chart,
            subject_chart=subject_chart
        )
    except Exception as e:
        app.logger.exception(
            "DASHBOARD ERROR: %s",
            e
        )
        flash(
            "Dashboard loading failed.",
            "danger"
        )
        return redirect(
            url_for("login")
        )
def get_mock_user_id():
    """Get logged-in user ID."""
    return session.get("user_id")
def mock_login_required():
    """Check whether user is logged in."""
    user_id = get_mock_user_id()
    if not user_id:
        flash("Please login to continue.", "warning")
        return False
    return True
@app.route("/mock-tests")
def mock_test_dashboard():
    if not mock_login_required():
        return redirect(url_for("login"))
    user_id = get_mock_user_id()
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT
                id,
                course_name,
                education_level,
                level_group,
                slug
            FROM mock_catalog_courses
            WHERE is_active = 1
            ORDER BY sort_order, course_name
        """)
        courses = cursor.fetchall()
        cursor.execute("""
            SELECT
                t.id,
                t.title,
                t.description,
                t.question_count,
                t.duration_minutes,
                t.visibility,
                t.status,
                t.share_token,
                t.scheduled_start_at,
                t.scheduled_end_at,
                t.created_at,
                (
                    SELECT COUNT(*)
                    FROM mock_test_participants p
                    WHERE p.test_id = t.id
                    AND p.status != 'Left'
                ) AS participant_count
            FROM mock_test_catalog t
            WHERE t.creator_user_id = %s
            ORDER BY t.created_at DESC
        """, (user_id,))
        created_tests = cursor.fetchall()
        for test in created_tests:
            status = str(test.get("status") or "").lower()
            if status in ("completed", "ended", "cancelled"):
                test["display_status"] = "Ended"
            elif test.get("scheduled_start_at") is None:
                test["display_status"] = "Waiting"
            else:
                test["display_status"] = "In Progress"
        return render_template(
            "mock_test/mock_test_dashboard.html",
            courses=courses,
            created_tests=created_tests
        )
    except Exception as e:
        print("MOCK TEST DASHBOARD ERROR:", str(e))
        return "Unable to load mock test dashboard.", 500
    finally:
        cursor.close()
        conn.close()
@app.route("/mock-tests/course/<int:course_id>")
def mock_course_subjects(course_id):
    if not mock_login_required():
        return redirect(url_for("login"))
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT id, course_name
            FROM mock_catalog_courses
            WHERE id = %s AND is_active = 1
        """, (course_id,))
        course = cursor.fetchone()
        if not course:
            abort(404)
        cursor.execute("""
            SELECT id, subject_name, sort_order
            FROM mock_catalog_subjects
            WHERE course_id = %s
            ORDER BY sort_order, subject_name
        """, (course_id,))
        subjects = cursor.fetchall()
        return render_template(
            "mock_test/mock_subjects.html",
            course=course,
            subjects=subjects
        )
    finally:
        cursor.close()
        conn.close()
@app.route("/mock-test/<share_token>")
def attempt_mock_test(share_token):
    if not mock_login_required():
        return redirect(url_for("login", next=request.url))
    user_id = get_mock_user_id()
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute("""
            SELECT *
            FROM mock_test_catalog
            WHERE share_token = %s AND status = 'Published'
            LIMIT 1
        """, (share_token,))
        test = cursor.fetchone()
        if not test:
            abort(404)
        if test["visibility"] == "Private" and int(test["creator_user_id"]) != int(user_id):
            abort(403)
        cursor.execute("""
            SELECT id, status
            FROM mock_test_participants
            WHERE test_id = %s AND user_id = %s
            LIMIT 1
        """, (test["id"], user_id))
        participant = cursor.fetchone()
        if participant and participant["status"] == "Left":
            flash("Please rejoin the test before starting.", "warning")
            return redirect(url_for("mock_test_join", share_token=share_token))
        if not participant:
            cursor.execute("""
                INSERT INTO mock_test_participants (test_id, user_id, status)
                VALUES (%s, %s, 'Started')
            """, (test["id"], user_id))
        elif participant["status"] != "Completed":
            cursor.execute("""
                UPDATE mock_test_participants
                SET status = 'Started'
                WHERE id = %s
            """, (participant["id"],))
        cursor.execute("""
            SELECT id, status
            FROM mock_attempts
            WHERE test_id = %s AND user_id = %s
            ORDER BY id DESC
            LIMIT 1
        """, (test["id"], user_id))
        existing_attempt = cursor.fetchone()
        if existing_attempt and existing_attempt["status"] in ("Submitted", "Auto Submitted"):
            conn.commit()
            return redirect(url_for("mock_test_result", attempt_id=existing_attempt["id"]))
        cursor.execute("""
            SELECT qb.id, qb.question_text, qb.option_a, qb.option_b,
                   qb.option_c, qb.option_d, mtq.question_order, mtq.marks
            FROM mock_test_questions mtq
            JOIN mock_question_bank qb ON qb.id = mtq.question_id
            WHERE mtq.test_id = %s AND qb.is_active = 1
            ORDER BY mtq.question_order ASC
        """, (test["id"],))
        questions = cursor.fetchall()
        question_count = len(questions)
        if question_count == 0:
            conn.rollback()
            flash("No questions are available for this test.", "warning")
            return redirect(url_for("mock_test_dashboard"))
        total_marks = sum(float(q["marks"] or 1) for q in questions)
        if question_count != int(test["question_count"] or 0):
            flash("Some questions are unavailable. Available questions are displayed below.", "warning")
        if existing_attempt and existing_attempt["status"] == "In Progress":
            attempt_id = existing_attempt["id"]
        else:
            cursor.execute("""
                INSERT INTO mock_attempts (
                    test_id, user_id, total_questions, total_marks, status
                )
                VALUES (%s, %s, %s, %s, 'In Progress')
            """, (test["id"], user_id, question_count, total_marks))
            attempt_id = cursor.lastrowid
        conn.commit()
        return render_template(
            "mock_test_attempt.html",
            test=test,
            questions=questions,
            attempt_id=attempt_id,
            no_questions=False,
            question_count=question_count,
            total_marks=total_marks,
            exam_state="active",
            remaining_seconds=int(test["duration_minutes"] or 20) * 60
        )
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        app.logger.exception("Mock test attempt failed: %s", e)
        flash("Unable to open mock test. Please try again.", "danger")
        return redirect(url_for("mock_test_dashboard"))
    finally:
        cursor.close()
        conn.close()
@app.route("/mock-test/<share_token>/join", methods=["GET", "POST"])
def mock_test_join(share_token):
    if not mock_login_required():
        return redirect(url_for("login", next=request.url))
    user_id = get_mock_user_id()
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute("""
            SELECT id, creator_user_id, title, visibility, status
            FROM mock_test_catalog
            WHERE share_token = %s
            LIMIT 1
        """, (share_token,))
        test = cursor.fetchone()
        if not test:
            abort(404)
        if test["status"] != "Published":
            flash("This mock test is not available.", "warning")
            return redirect(url_for("mock_test_dashboard"))
        if test["visibility"] == "Private" and int(test["creator_user_id"]) != int(user_id):
            abort(403)
        cursor.execute("""
            SELECT id, status
            FROM mock_test_participants
            WHERE test_id = %s AND user_id = %s
            LIMIT 1
            FOR UPDATE
        """, (test["id"], user_id))
        participant = cursor.fetchone()
        if participant:
            if participant["status"] == "Left":
                cursor.execute("""
                    UPDATE mock_test_participants
                    SET status = 'Joined'
                    WHERE id = %s
                """, (participant["id"],))
        else:
            cursor.execute("""
                INSERT INTO mock_test_participants (test_id, user_id, status)
                VALUES (%s, %s, 'Joined')
            """, (test["id"], user_id))
        conn.commit()
        return redirect(url_for("mock_test_waiting_room", share_token=share_token))
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        app.logger.exception("Mock test join failed: %s", e)
        flash("Unable to join mock test. Please try again.", "danger")
        return redirect(url_for("mock_test_dashboard"))
    finally:
        cursor.close()
        conn.close()
from flask import abort
from werkzeug.exceptions import HTTPException
@app.route("/mock-test/<share_token>/waiting-room")
def mock_test_waiting_room(share_token):
    if not mock_login_required():
        return redirect(url_for("login", next=request.url))
    user_id = get_mock_user_id()
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT
                id,
                creator_user_id,
                title,
                description,
                question_count,
                duration_minutes,
                visibility,
                status,
                scheduled_start_at,
                scheduled_end_at,
                share_token
            FROM mock_test_catalog
            WHERE share_token = %s
            LIMIT 1
        """, (share_token,))
        test = cursor.fetchone()
        if not test:
            abort(404)
        if test["visibility"] == "Private" and test["creator_user_id"] != user_id:
            abort(403)
        cursor.execute("""
            SELECT id
            FROM mock_test_participants
            WHERE test_id = %s
            AND user_id = %s
            AND status != 'Left'
            LIMIT 1
        """, (test["id"], user_id))
        participant = cursor.fetchone()
        if not participant:
            return redirect(
                url_for(
                    "mock_test_join",
                    share_token=share_token
                )
            )
        cursor.execute("""
            SELECT
                p.id,
                p.user_id,
                p.joined_at,
                p.status,
                u.name
            FROM mock_test_participants p
            INNER JOIN users u ON u.id = p.user_id
            WHERE p.test_id = %s
            AND p.status != 'Left'
            ORDER BY p.joined_at ASC
        """, (test["id"],))
        participants = cursor.fetchall()
        is_host = test["creator_user_id"] == user_id
        print("========== WAITING ROOM DEBUG ==========")
        print("SESSION USER ID:", session.get("user_id"))
        print("SESSION USER NAME:", session.get("user_name"))
        print("TEST HOST ID:", test["creator_user_id"])
        print("CURRENT USER ID:", user_id)
        print("SHARE TOKEN:", share_token)
        print("========================================")
        return render_template(
            "mock_test/waiting_room.html",
            test=test,
            share_token=share_token,
            participants=participants,
            is_host=is_host,
            current_user_id=user_id,
            participant_count=len(participants)
        )
    except HTTPException:
        raise
    except Exception as e:
        print("MOCK TEST WAITING ROOM ERROR:", str(e))
        return "Waiting Room Error: " + str(e), 500
    finally:
        cursor.close()
        conn.close()
@app.route("/mock-test/<share_token>/participants", methods=["GET"])
def mock_test_participants_api(share_token):
    conn = None
    cursor = None
    try:
        if not mock_login_required():
            return jsonify({
                "success": False,
                "message": "Login required.",
                "login_required": True
            }), 401
        user_id = get_mock_user_id()
        if not user_id:
            return jsonify({
                "success": False,
                "message": "User session not found.",
                "login_required": True
            }), 401
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("""
            SELECT
                id,
                creator_user_id,
                scheduled_start_at,
                title
            FROM mock_test_catalog
            WHERE share_token = %s
            LIMIT 1
        """, (share_token,))
        test = cursor.fetchone()
        if not test:
            return jsonify({
                "success": False,
                "message": "Mock test not found."
            }), 404
        is_host = int(test["creator_user_id"]) == int(user_id)
        cursor.execute("""
            SELECT id, status
            FROM mock_test_participants
            WHERE test_id = %s
            AND user_id = %s
            AND status != 'Left'
            LIMIT 1
        """, (test["id"], user_id))
        current_participant = cursor.fetchone()
        if not is_host and not current_participant:
            return jsonify({
                "success": False,
                "message": "You are not a participant in this test."
            }), 403
        cursor.execute("""
            SELECT
                p.id,
                p.user_id,
                p.status,
                p.joined_at,
                u.name
            FROM mock_test_participants p
            INNER JOIN users u ON u.id = p.user_id
            WHERE p.test_id = %s
            AND p.status != 'Left'
            ORDER BY p.joined_at ASC
        """, (test["id"],))
        participants = cursor.fetchall()
        ready_count = 0
        completed_count = 0
        for participant in participants:
            participant["is_host"] = (
                int(participant["user_id"]) == int(test["creator_user_id"])
            )
            participant["is_current_user"] = (
                int(participant["user_id"]) == int(user_id)
            )
            if participant["status"] == "Ready":
                ready_count += 1
            if participant["status"] == "Completed":
                completed_count += 1
        total = len(participants)
        cursor.execute("""
            SELECT COUNT(DISTINCT p.user_id) AS total,
                   COUNT(DISTINCT CASE
                       WHEN p.status = 'Completed' AND EXISTS (
                           SELECT 1
                           FROM mock_attempts a
                           WHERE a.test_id = p.test_id
                             AND a.user_id = p.user_id
                             AND a.status IN ('Submitted', 'Auto Submitted')
                       ) THEN p.user_id
                   END) AS completed
            FROM mock_test_participants p
            WHERE p.test_id = %s AND p.status <> 'Left'
        """, (test["id"],))
        release_stats = cursor.fetchone()
        total = int(release_stats["total"] or 0)
        completed_count = int(release_stats["completed"] or 0)
        results_released = total > 0 and completed_count == total
        return jsonify({
            "success": True,
            "test_title": test["title"],
            "started": test["scheduled_start_at"] is not None,
            "is_host": is_host,
            "participants": participants,
            "total": total,
            "ready_count": ready_count,
            "completed_count": completed_count,
            "pending_count": total - completed_count,
            "results_released": results_released
        }), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        print("PARTICIPANTS API ERROR:", repr(e))
        return jsonify({
            "success": False,
            "message": "Unable to load participants.",
            "error": str(e)
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
@app.route("/mock-test/<share_token>/ready", methods=["POST"])
def mock_test_participant_ready(share_token):
    if not mock_login_required():
        return jsonify({"success": False, "message": "Login required."}), 401
    user_id = get_mock_user_id()
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT id, scheduled_start_at
            FROM mock_test_catalog
            WHERE share_token = %s
            LIMIT 1
        """, (share_token,))
        test = cursor.fetchone()
        if not test:
            return jsonify({
                "success": False,
                "message": "Mock test not found."
            }), 404
        if test["scheduled_start_at"] is not None:
            return jsonify({
                "success": False,
                "message": "Test has already started."
            }), 400
        cursor.execute("""
            SELECT id, status
            FROM mock_test_participants
            WHERE test_id = %s
            AND user_id = %s
            AND status != 'Left'
            LIMIT 1
        """, (test["id"], user_id))
        participant = cursor.fetchone()
        if not participant:
            return jsonify({
                "success": False,
                "message": "You are not a participant in this test."
            }), 404
        new_status = "Joined" if participant["status"] == "Ready" else "Ready"
        cursor.execute("""
            UPDATE mock_test_participants
            SET status = %s
            WHERE id = %s
        """, (new_status, participant["id"]))
        conn.commit()
        return jsonify({
            "success": True,
            "status": new_status,
            "message": "You are now " + new_status + "."
        })
    except Exception as e:
        conn.rollback()
        print("READY API ERROR:", str(e))
        return jsonify({
            "success": False,
            "message": "Something went wrong. Please try again."
        }), 500
    finally:
        cursor.close()
        conn.close()
@app.route("/mock-test/<share_token>/start", methods=["POST"])
def start_mock_test(share_token):
    if not mock_login_required():
        return jsonify({"success": False}), 401
    user_id = get_mock_user_id()
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT id, creator_user_id, scheduled_start_at
            FROM mock_test_catalog
            WHERE share_token = %s
            LIMIT 1
        """, (share_token,))
        test = cursor.fetchone()
        if not test:
            return jsonify({"success": False}), 404
        if test["creator_user_id"] != user_id:
            return jsonify({
                "success": False,
                "message": "Only the host can start the test."
            }), 403
        if test["scheduled_start_at"] is not None:
            return jsonify({
                "success": False,
                "message": "Test has already started."
            }), 400
        cursor.execute("""
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN status = 'Ready' THEN 1 ELSE 0 END) AS ready_count
            FROM mock_test_participants
            WHERE test_id = %s
            AND status != 'Left'
        """, (test["id"],))
        result = cursor.fetchone()
        total = result["total"] or 0
        ready_count = result["ready_count"] or 0
        if total == 0 or total != ready_count:
            return jsonify({
                "success": False,
                "message": "All participants must be ready before starting."
            }), 400
        cursor.execute("""
            UPDATE mock_test_catalog
            SET scheduled_start_at = NOW()
            WHERE id = %s
            AND scheduled_start_at IS NULL
        """, (test["id"],))
        if cursor.rowcount == 0:
            conn.rollback()
            return jsonify({
                "success": False,
                "message": "Test could not be started."
            }), 400
        cursor.execute("""
            UPDATE mock_test_participants
            SET status = 'Started'
            WHERE test_id = %s
            AND status = 'Ready'
        """, (test["id"],))
        conn.commit()
        return jsonify({
            "success": True,
            "message": "Test started successfully."
        })
    except Exception as e:
        conn.rollback()
        print("START MOCK TEST ERROR:", str(e))
        return jsonify({"success": False}), 500
    finally:
        cursor.close()
        conn.close()
@app.route("/mock-tests/subject/<int:subject_id>/start", methods=["POST"])
def start_subject_mock_test(subject_id):
    if not mock_login_required():
        return redirect(url_for("login"))
    user_id = get_mock_user_id()
    conn = get_db_connection()
    cursor = conn.cursor()
    subject = None
    try:
        cursor.execute("""
            SELECT
                s.id AS subject_id,
                s.subject_name,
                c.id AS course_id,
                c.course_name
            FROM mock_catalog_subjects s
            JOIN mock_catalog_courses c
                ON c.id = s.course_id
            WHERE s.id = %s
            AND c.is_active = 1
        """, (subject_id,))
        subject = cursor.fetchone()
        if not subject:
            abort(404)
        cursor.execute("""
            SELECT id
            FROM mock_question_bank
            WHERE subject_id = %s
            AND is_active = 1
            ORDER BY RAND()
            LIMIT 20
        """, (subject_id,))
        questions = cursor.fetchall()
        question_count = len(questions)
        title = subject["subject_name"] + " Mock Test"
        duration = max(10, question_count)
        share_token = secrets.token_urlsafe(32)
        conn.begin()
        cursor.execute("""
            INSERT INTO mock_test_catalog (
                creator_user_id,
                course_id,
                title,
                description,
                difficulty,
                question_count,
                duration_minutes,
                share_token,
                visibility,
                status
            )
            VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s
            )
        """, (
            user_id,
            subject["course_id"],
            title,
            "Subject-wise practice mock test",
            "Mixed",
            question_count,
            duration,
            share_token,
            "Link",
            "Published"
        ))
        test_id = cursor.lastrowid
        cursor.execute("""
            INSERT INTO mock_test_participants
            (test_id, user_id, status)
            VALUES (%s, %s, 'Ready')
        """, (test_id, user_id))
        cursor.execute("""
            INSERT INTO mock_test_subjects (
                test_id,
                subject_id
            )
            VALUES (%s, %s)
        """, (
            test_id,
            subject_id
        ))
        if question_count > 0:
            for index, question in enumerate(questions, start=1):
                cursor.execute("""
                    INSERT INTO mock_test_questions (
                        test_id,
                        question_id,
                        question_order,
                        marks
                    )
                    VALUES (%s, %s, %s, %s)
                """, (
                    test_id,
                    question["id"],
                    index,
                    1
                ))
            print(
                f"MOCK TEST CREATED: {question_count} questions found."
            )
        else:
            print(
                f"MOCK TEST CREATED: No questions found for subject {subject_id}."
            )
        conn.commit()
        if question_count == 0:
            flash(
                "No questions found for this subject yet. "
                "You can view the mock test page, but questions "
                "are not available right now.",
                "warning"
            )
        return redirect(
            url_for(
                "attempt_mock_test",
                share_token=share_token
            )
        )
    except Exception as e:
        conn.rollback()
        print("SUBJECT MOCK TEST ERROR:", e)
        flash(
            "Unable to start subject mock test. Please try again.",
            "danger"
        )
        if subject:
            return redirect(
                url_for(
                    "mock_course_subjects",
                    course_id=subject["course_id"]
                )
            )
        return redirect(url_for("mock_test_dashboard"))
    finally:
        cursor.close()
        conn.close()
@app.route("/mock-test/<share_token>/invite")
def mock_test_invite(share_token):
    if not mock_login_required():
        return redirect(url_for("login"))
    user_id = get_mock_user_id()
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT *
            FROM mock_test_catalog
            WHERE share_token = %s
            LIMIT 1
        """, (share_token,))
        test = cursor.fetchone()
        if not test:
            abort(404)
        if test["creator_user_id"] != user_id:
            return redirect(
                url_for(
                    "mock_test_waiting_room",
                    share_token=share_token
                )
            )
        cursor.execute("""
            SELECT
                u.id,
                u.name,
                u.email,
                COALESCE(
                    NULLIF(u.profile_pic, ''),
                    NULLIF(u.picture, '')
                ) AS picture
            FROM friend_requests fr
            JOIN users u
                ON u.id = CASE
                    WHEN fr.sender_id = %s THEN fr.receiver_id
                    ELSE fr.sender_id
                END
            WHERE (
                fr.sender_id = %s
                OR fr.receiver_id = %s
            )
            AND fr.status = 'accepted'
            AND u.id != %s
            ORDER BY u.name ASC
        """, (user_id, user_id, user_id, user_id))
        friends = cursor.fetchall()
        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM mock_test_participants
            WHERE test_id = %s
            AND status != 'Left'
        """, (test["id"],))
        participant_count = cursor.fetchone()["total"]
        invite_link = request.host_url.rstrip("/") + url_for(
            "mock_test_join",
            share_token=share_token
        )
        return render_template(
            "mock_test/invite.html",
            test=test,
            friends=friends,
            invite_link=invite_link,
            participant_count=participant_count
        )
    except Exception as e:
        print("MOCK TEST INVITE ERROR:", str(e))
        traceback.print_exc()
        abort(500)
    finally:
        cursor.close()
        conn.close()
@app.route("/mock-test/<share_token>/send-invitations", methods=["POST"])
@app.route("/mock-test/<share_token>/invite/send-invitations", methods=["POST"])
def send_mock_test_invitations(share_token):
    if not mock_login_required():
        return jsonify({
            "success": False,
            "message": "Please login first."
        }), 401
    user_id = get_mock_user_id()
    data = request.get_json(silent=True) or {}
    friend_ids = data.get("friend_ids", [])
    if not isinstance(friend_ids, list) or not friend_ids:
        return jsonify({
            "success": False,
            "message": "Please select at least one friend."
        }), 400
    try:
        friend_ids = list(set(int(fid) for fid in friend_ids))
    except (ValueError, TypeError):
        return jsonify({
            "success": False,
            "message": "Invalid friend selection."
        }), 400
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT id, creator_user_id, title
            FROM mock_test_catalog
            WHERE share_token = %s
            AND status = 'Published'
            LIMIT 1
        """, (share_token,))
        test = cursor.fetchone()
        if not test:
            return jsonify({
                "success": False,
                "message": "Mock test not found."
            }), 404
        if int(test["creator_user_id"]) != int(user_id):
            return jsonify({
                "success": False,
                "message": "Only the test creator can send invitations."
            }), 403
        invite_link = request.host_url.rstrip("/") + url_for(
            "mock_test_join",
            share_token=share_token
        )
        sent = []
        already_invited = []
        failed = []
        for friend_id in friend_ids:
            if friend_id == user_id:
                failed.append(friend_id)
                continue
            if not are_friends(cursor, user_id, friend_id):
                failed.append(friend_id)
                continue
            cursor.execute("""
                SELECT id
                FROM notifications
                WHERE user_id = %s
                AND type = 'mock_test_invite'
                AND link = %s
                LIMIT 1
            """, (friend_id, invite_link))
            existing = cursor.fetchone()
            if existing:
                already_invited.append(friend_id)
                continue
            try:
                create_social_notification(
                    cursor,
                    friend_id,
                    "Mock Test Invitation",
                    f"You have been invited to join '{test['title']}'. Click to join the mock test.",
                    "mock_test_invite",
                    invite_link
                )
                sent.append(friend_id)
            except Exception as e:
                print("INVITATION ERROR:", str(e))
                failed.append(friend_id)
        conn.commit()
        return jsonify({
            "success": True,
            "sent": sent,
            "sent_count": len(sent),
            "already_invited": already_invited,
            "already_invited_count": len(already_invited),
            "failed": failed,
            "failed_count": len(failed),
            "message": "Invitation process completed."
        })
    except Exception as e:
        conn.rollback()
        print("SEND MOCK INVITATIONS ERROR:", str(e))
        traceback.print_exc()
        return jsonify({
            "success": False,
            "message": "Unable to send invitations."
        }), 500
    finally:
        cursor.close()
        conn.close()
@app.route("/mock-test/result/<int:attempt_id>")
def mock_test_result(attempt_id):
    if not mock_login_required():
        return redirect(url_for("login", next=request.url))
    user_id = get_mock_user_id()
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute("""
            SELECT a.*, t.title, t.share_token, t.creator_user_id,
                   u.name
            FROM mock_attempts a
            JOIN mock_test_catalog t ON t.id = a.test_id
            JOIN users u ON u.id = a.user_id
            WHERE a.id = %s
            LIMIT 1
        """, (attempt_id,))
        result = cursor.fetchone()
        if not result:
            abort(404)
        is_owner = int(result["user_id"]) == int(user_id)
        is_creator = int(result["creator_user_id"]) == int(user_id)
        if not is_owner and not is_creator:
            abort(403)
        if result["status"] not in ("Submitted", "Auto Submitted"):
            flash("This examination has not been submitted yet.", "warning")
            return redirect(url_for("mock_test_dashboard"))
        participants_total = 0
        participants_completed = 0
        participants_pending = 0
        leaderboard = []
        rank = None
        results_released = True
        if result.get("share_token"):
            cursor.execute("""
                SELECT
                    p.user_id,
                    u.name,
                    p.status AS participant_status,
                    a.id AS attempt_id,
                    a.obtained_marks,
                    a.total_marks,
                    a.percentage,
                    a.correct_answers,
                    a.wrong_answers,
                    a.unanswered_questions,
                    a.submitted_at,
                    CASE
                        WHEN a.id IS NULL THEN 'Pending'
                        ELSE 'Submitted'
                    END AS status
                FROM mock_test_participants p
                LEFT JOIN users u
                    ON u.id = p.user_id
                LEFT JOIN (
                    SELECT latest_attempt.*
                    FROM mock_attempts latest_attempt
                    INNER JOIN (
                        SELECT user_id, MAX(id) AS latest_id
                        FROM mock_attempts
                        WHERE test_id = %s
                          AND status IN ('Submitted', 'Auto Submitted')
                        GROUP BY user_id
                    ) latest
                        ON latest.latest_id = latest_attempt.id
                ) a
                    ON a.test_id = p.test_id
                   AND a.user_id = p.user_id
                WHERE p.test_id = %s
                  AND p.status <> 'Left'
                ORDER BY
                    CASE WHEN a.id IS NULL THEN 1 ELSE 0 END ASC,
                    a.obtained_marks DESC,
                    a.percentage DESC,
                    a.submitted_at ASC,
                    p.id ASC
            """, (result["test_id"], result["test_id"]))
            leaderboard = cursor.fetchall()
            participants_total = len(leaderboard)
            for student in leaderboard:
                if student.get("status") == "Submitted":
                    participants_completed += 1
            participants_pending = max(
                0,
                participants_total - participants_completed
            )
            results_released = (
                participants_total > 0
                and participants_pending == 0
            )
            previous_score = None
            current_rank = 0
            for index, student in enumerate(leaderboard, start=1):
                if student.get("status") == "Pending":
                    student["rank"] = None
                    student["rank_title"] = "Pending"
                    continue
                score = (
                    float(student.get("obtained_marks") or 0),
                    float(student.get("percentage") or 0)
                )
                if score != previous_score:
                    current_rank = index
                    previous_score = score
                student["rank"] = current_rank
                if current_rank == 1:
                    student["rank_title"] = "🥇 1st Place"
                elif current_rank == 2:
                    student["rank_title"] = "🥈 2nd Place"
                elif current_rank == 3:
                    student["rank_title"] = "🥉 3rd Place"
                else:
                    student["rank_title"] = f"{current_rank}th Place"
                if int(student.get("attempt_id") or 0) == int(attempt_id):
                    rank = current_rank
        answers = []
        if results_released:
            cursor.execute("""
                SELECT
                    aa.question_id,
                    aa.selected_option,
                    aa.correct_option,
                    aa.is_correct,
                    aa.marks_awarded,
                    qb.question_text,
                    qb.option_a,
                    qb.option_b,
                    qb.option_c,
                    qb.option_d,
                    qb.explanation
                FROM mock_attempt_answers aa
                JOIN mock_question_bank qb
                    ON qb.id = aa.question_id
                WHERE aa.attempt_id = %s
                ORDER BY aa.id ASC
            """, (attempt_id,))
            answers = cursor.fetchall()
        leaderboard_url = (
            url_for(
                "mock_test_leaderboard",
                share_token=result["share_token"]
            )
            if result.get("share_token") else None
        )
        return render_template(
            "mock_test/result.html",
            result=result,
            answers=answers,
            is_creator=is_creator,
            results_released=results_released,
            participants_total=participants_total,
            participants_completed=participants_completed,
            participants_pending=participants_pending,
            leaderboard=leaderboard,
            rank=rank,
            leaderboard_url=leaderboard_url
        )
    except HTTPException:
        raise
    except Exception as e:
        app.logger.exception("Mock result loading failed: %s", e)
        flash("Result loading failed. Please try again.", "danger")
        return redirect(url_for("mock_test_dashboard"))
    finally:
        cursor.close()
        conn.close()
@app.route("/mock-test/<share_token>/leaderboard")
def mock_test_leaderboard(share_token):
    if not mock_login_required():
        return redirect(url_for("login", next=request.url))
    user_id = get_mock_user_id()
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute("""
            SELECT id, title, creator_user_id, share_token
            FROM mock_test_catalog
            WHERE share_token = %s
            LIMIT 1
        """, (share_token,))
        test = cursor.fetchone()
        if not test:
            abort(404)
        is_host = int(test["creator_user_id"]) == int(user_id)
        cursor.execute("""
            SELECT id, status
            FROM mock_test_participants
            WHERE test_id = %s
              AND user_id = %s
              AND status <> 'Left'
            LIMIT 1
        """, (test["id"], user_id))
        current_participant = cursor.fetchone()
        if not is_host and not current_participant:
            abort(403)
        cursor.execute("""
            SELECT
                COUNT(DISTINCT p.user_id) AS total,
                COUNT(DISTINCT CASE
                    WHEN EXISTS (
                        SELECT 1
                        FROM mock_attempts a
                        WHERE a.test_id = p.test_id
                          AND a.user_id = p.user_id
                          AND a.status IN ('Submitted', 'Auto Submitted')
                    )
                    THEN p.user_id
                END) AS completed
            FROM mock_test_participants p
            WHERE p.test_id = %s
              AND p.status <> 'Left'
        """, (test["id"],))
        stats = cursor.fetchone()
        total_participants = int(stats["total"] or 0)
        submitted_participants = int(stats["completed"] or 0)
        results_released = (
            total_participants > 0
            and submitted_participants == total_participants
        )
        if not results_released:
            flash(
                "Leaderboard will be available after every participant submits the test.",
                "info"
            )
            return redirect(
                url_for("mock_test_waiting_room", share_token=share_token)
            )
        cursor.execute("""
            SELECT
                p.user_id,
                u.name,
                p.status AS participant_status,
                a.id AS attempt_id,
                a.obtained_marks,
                a.total_marks,
                a.percentage,
                a.correct_answers,
                a.wrong_answers,
                a.unanswered_questions,
                a.submitted_at,
                a.status AS attempt_status
            FROM mock_test_participants p
            LEFT JOIN users u ON u.id = p.user_id
            LEFT JOIN (
                SELECT a1.*
                FROM mock_attempts a1
                INNER JOIN (
                    SELECT user_id, MAX(id) AS latest_id
                    FROM mock_attempts
                    WHERE test_id = %s
                      AND status IN ('Submitted', 'Auto Submitted')
                    GROUP BY user_id
                ) latest ON latest.latest_id = a1.id
            ) a ON a.user_id = p.user_id
            WHERE p.test_id = %s
              AND p.status <> 'Left'
            ORDER BY
                a.obtained_marks DESC,
                a.percentage DESC,
                a.submitted_at ASC,
                p.joined_at ASC
        """, (test["id"], test["id"]))
        leaderboard = cursor.fetchall()
        current_rank = 0
        previous_score = None
        submitted_position = 0
        for student in leaderboard:
            if student["attempt_id"] is None:
                student["rank"] = None
                student["result_status"] = "Not Submitted"
                continue
            submitted_position += 1
            score = (
                float(student["obtained_marks"] or 0),
                float(student["percentage"] or 0)
            )
            if score != previous_score:
                current_rank = submitted_position
                previous_score = score
            student["rank"] = current_rank
            student["result_status"] = student["attempt_status"]
        submitted_count = sum(
            1 for student in leaderboard
            if student["attempt_id"] is not None
        )
        pending_count = total_participants - submitted_count
        average_percentage = round(
            sum(
                float(student["percentage"] or 0)
                for student in leaderboard
                if student["attempt_id"] is not None
            ) / submitted_count,
            2
        ) if submitted_count else 0
        return render_template(
            "mock_test/mock_test_leaderboard.html",
            test=test,
            leaderboard=leaderboard,
            total_participants=total_participants,
            submitted_count=submitted_count,
            pending_count=pending_count,
            average_percentage=average_percentage,
            results_released=results_released
        )
    except HTTPException:
        raise
    except Exception as e:
        app.logger.exception("Mock leaderboard loading failed: %s", e)
        flash("Unable to load leaderboard. Please try again.", "danger")
        return redirect(url_for("mock_test_dashboard"))
    finally:
        cursor.close()
        conn.close()
@app.route("/interview")
@app.route("/interview_questions")
def interview_questions():
    if "user_id" not in session:
        flash("Please login first.", "warning")
        return redirect(url_for("login"))
    category = request.args.get("category", "").strip()
    level = request.args.get("level", "").strip()
    company = request.args.get("company", "").strip()
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
        if company:
            conditions.append(
                "company = %s"
            )
            params.append(company)
        if search:
            conditions.append("""
                (
                    question LIKE %s
                    OR answer LIKE %s
                    OR category LIKE %s
                    OR company LIKE %s
                    OR topic LIKE %s
                )
            """)
            search_value = f"%{search}%"
            params.extend([
                search_value,
                search_value,
                search_value,
                search_value,
                search_value
            ])
        where_clause = ""
        if conditions:
            where_clause = (
                "WHERE " +
                " AND ".join(conditions)
            )
        count_query = f"""
            SELECT COUNT(*) AS total
            FROM interview_questions
            {where_clause}
        """
        cursor.execute(
            count_query,
            tuple(params)
        )
        count_result = cursor.fetchone()
        total_questions = 0
        if count_result:
            total_questions = int(
                count_result.get("total", 0)
            )
        total_pages = (
            (total_questions + per_page - 1)
            // per_page
        )
        if total_pages > 0 and page > total_pages:
            page = total_pages
            offset = (page - 1) * per_page
        questions_query = f"""
            SELECT
                id,
                question,
                answer,
                category,
                level,
                company,
                topic,
                expected_time,
                explanation,
                followup_question,
                tips
            FROM interview_questions
            {where_clause}
            ORDER BY id DESC
            LIMIT %s OFFSET %s
        """
        question_params = tuple(params) + (
            per_page,
            offset
        )
        cursor.execute(
            questions_query,
            question_params
        )
        questions = cursor.fetchall()
        cursor.execute("""
            SELECT DISTINCT category
            FROM interview_questions
            WHERE category IS NOT NULL
              AND category != ''
            ORDER BY category ASC
        """)
        category_rows = cursor.fetchall()
        categories = [
            row["category"]
            for row in category_rows
            if row.get("category")
        ]
        cursor.execute("""
            SELECT DISTINCT level
            FROM interview_questions
            WHERE level IS NOT NULL
              AND level != ''
            ORDER BY level ASC
        """)
        level_rows = cursor.fetchall()
        levels = [
            row["level"]
            for row in level_rows
            if row.get("level")
        ]
        cursor.execute("""
            SELECT DISTINCT company
            FROM interview_questions
            WHERE company IS NOT NULL
              AND company != ''
            ORDER BY company ASC
        """)
        company_rows = cursor.fetchall()
        companies = [
            row["company"]
            for row in company_rows
            if row.get("company")
        ]
        total_categories = len(categories)
        total_companies = len(companies)
        return render_template(
            "interview_questions.html",
            questions=questions,
            categories=categories,
            levels=levels,
            companies=companies,
            category=category,
            level=level,
            company=company,
            search=search,
            page=page,
            per_page=per_page,
            total_questions=total_questions,
            total_pages=total_pages,
            total_categories=total_categories,
            total_companies=total_companies
        )
    except Exception as e:
        app.logger.exception(
            "Interview questions loading error"
        )
        flash(
            "Unable to load interview questions.",
            "danger"
        )
        return redirect(
            url_for("dashboard")
        )
    finally:
        if cursor:
            try:
                cursor.close()
            except Exception:
                pass
        if conn:
            try:
                conn.close()
            except Exception:
                pass
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
    experience = data.get(
        "experience",
        ""
    ).strip()
    projects = data.get(
        "projects",
        ""
    ).strip()
    certifications = data.get(
        "certifications",
        ""
    ).strip()
    achievements = data.get(
        "achievements",
        ""
    ).strip()
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id
            FROM resumes
            WHERE user_id = %s
            ORDER BY id DESC
            LIMIT 1
        """, (user_id,))
        existing = cursor.fetchone()
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
    if not resume_text:
        return jsonify({
            "success": False,
            "message": "Resume content is required."
        }), 400
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
    if keywords:
        keyword_score = (
            len(matched_keywords)
            / len(keywords)
        ) * 100
    else:
        keyword_score = 0
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
        cursor.execute("""
            SELECT DISTINCT category
            FROM coding_questions
            WHERE category IS NOT NULL
              AND category != ''
            ORDER BY category
        """)
        categories = cursor.fetchall()
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
@app.route("/mock-test/submit/<int:attempt_id>", methods=["POST"])
def submit_mock_test(attempt_id):
    if not mock_login_required():
        return redirect(url_for("login", next=request.url))
    user_id = get_mock_user_id()
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        conn.begin()
        cursor.execute("""
            SELECT *
            FROM mock_attempts
            WHERE id = %s AND user_id = %s
            LIMIT 1
            FOR UPDATE
        """, (attempt_id, user_id))
        attempt = cursor.fetchone()
        if not attempt:
            conn.rollback()
            abort(404)
        if attempt["status"] in ("Submitted", "Auto Submitted"):
            conn.rollback()
            return redirect(url_for("mock_test_result", attempt_id=attempt_id))
        if attempt["status"] != "In Progress":
            conn.rollback()
            flash("This attempt cannot be submitted.", "warning")
            return redirect(url_for("mock_test_dashboard"))
        cursor.execute("""
            SELECT id, status
            FROM mock_test_participants
            WHERE test_id = %s AND user_id = %s
            ORDER BY id DESC
            LIMIT 1
            FOR UPDATE
        """, (attempt["test_id"], user_id))
        participant = cursor.fetchone()
        if not participant or participant["status"] == "Left":
            conn.rollback()
            flash("You are not an active participant in this test. Please rejoin before submitting.", "warning")
            return redirect(url_for("mock_test_join", share_token=request.args.get("share_token", ""))) if request.args.get("share_token") else redirect(url_for("mock_test_dashboard"))
        if participant["status"] == "Completed":
            conn.rollback()
            flash("Your test has already been marked as completed.", "info")
            return redirect(url_for("mock_test_dashboard"))
        cursor.execute("""
            SELECT qb.id, qb.correct_option, mtq.marks
            FROM mock_test_questions mtq
            JOIN mock_question_bank qb ON qb.id = mtq.question_id
            WHERE mtq.test_id = %s
            ORDER BY mtq.question_order ASC
        """, (attempt["test_id"],))
        questions = cursor.fetchall()
        if not questions:
            conn.rollback()
            flash("No questions found for this test.", "danger")
            return redirect(url_for("mock_test_dashboard"))
        attempted = 0
        correct = 0
        wrong = 0
        unanswered = 0
        obtained_marks = 0
        total_marks = 0
        for question in questions:
            question_id = question["id"]
            selected_option = request.form.get(f"question_{question_id}") or request.form.get(f"answers[{question_id}]")
            selected_option = selected_option.strip().upper() if selected_option else None
            correct_option = str(question["correct_option"] or "").strip().upper()
            marks = int(question["marks"] or 0)
            total_marks += marks
            is_correct = 0
            marks_awarded = 0
            if selected_option in ("A", "B", "C", "D"):
                attempted += 1
                if selected_option == correct_option:
                    correct += 1
                    is_correct = 1
                    marks_awarded = marks
                    obtained_marks += marks
                else:
                    wrong += 1
            else:
                selected_option = None
                unanswered += 1
            cursor.execute("""
                INSERT INTO mock_attempt_answers (
                    attempt_id, question_id, selected_option, correct_option,
                    is_correct, marks_awarded, answered_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
            """, (attempt_id, question_id, selected_option, correct_option, is_correct, marks_awarded))
        total_questions = len(questions)
        percentage = round((float(obtained_marks) / float(total_marks)) * 100, 2) if total_marks > 0 else 0
        cursor.execute("""
            UPDATE mock_attempts
            SET attempted_questions = %s,
                correct_answers = %s,
                wrong_answers = %s,
                unanswered_questions = %s,
                obtained_marks = %s,
                total_marks = %s,
                total_questions = %s,
                percentage = %s,
                submitted_at = NOW(),
                time_taken_seconds = GREATEST(0, TIMESTAMPDIFF(SECOND, started_at, NOW())),
                status = 'Submitted'
            WHERE id = %s AND user_id = %s AND status = 'In Progress'
        """, (attempted, correct, wrong, unanswered, obtained_marks, total_marks, total_questions, percentage, attempt_id, user_id))
        if cursor.rowcount != 1:
            conn.rollback()
            flash("Your test could not be submitted. Please try again.", "danger")
            return redirect(url_for("mock_test_dashboard"))
        cursor.execute("""
            UPDATE mock_test_participants
            SET status = 'Completed'
            WHERE id = %s AND status <> 'Left'
        """, (participant["id"],))
        if cursor.rowcount != 1:
            conn.rollback()
            flash("Participant status could not be updated. Please contact the test host.", "danger")
            return redirect(url_for("mock_test_dashboard"))
        conn.commit()
        return redirect(url_for("mock_test_result", attempt_id=attempt_id))
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        app.logger.exception("Mock test submission failed: %s", e)
        flash("Unable to submit mock test. Please try again.", "danger")
        return redirect(url_for("mock_test_dashboard"))
    finally:
        cursor.close()
        conn.close()
@app.route("/my-mock-tests")
def my_mock_tests():
    if not mock_login_required():
        return redirect(url_for("login"))
    user_id = get_mock_user_id()
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT
                t.*,
                (
                    SELECT COUNT(*)
                    FROM mock_attempts a
                    WHERE a.test_id = t.id
                    AND a.status IN ('Submitted', 'Auto Submitted')
                ) AS total_attempts
            FROM mock_test_catalog t
            WHERE t.creator_user_id = %s
            ORDER BY t.created_at DESC
        """, (user_id,))
        tests = cursor.fetchall()
        return render_template("mock_test/my_tests.html", tests=tests)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print("MY MOCK TESTS ERROR:", str(e))
        return "My Mock Tests Error: " + str(e), 500
    finally:
        cursor.close()
        conn.close()
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
        cursor.execute("""
            SELECT
                COUNT(*) AS total_tests,
                COALESCE(AVG(percentage), 0) AS average_score,
                COALESCE(MAX(percentage), 0) AS best_score
            FROM results
            WHERE user_id = %s
        """, (user_id,))
        mock_progress = cursor.fetchone()
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
from flask import session, redirect, url_for, flash
from functools import wraps
def admin_required(view_func=None):
    def decorator(func):
        @wraps(func)
        def decorated_view(*args, **kwargs):
            if not session.get("user_id"):
                flash("Please login first.", "warning")
                return redirect(url_for("login"))
            user_role = str(
                session.get("role", "")
            ).strip().lower()
            if user_role != "admin":
                flash("Admin access required.", "danger")
                return redirect(url_for("dashboard"))
            return func(*args, **kwargs)
        return decorated_view
    if view_func is None:
        return decorator
    return decorator(view_func)
@app.route('/admin/users')
@admin_required()
def admin_users():
    conn = None
    cursor = None
    try:
        search = request.args.get('search', '').strip()
        role_filter = request.args.get('role', '').strip()
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        query = """
            SELECT
                u.id,
                u.name,
                u.email,
                u.role,
                u.created_at,
                u.age,
                u.address,
                u.profile_pic,
                u.last_active,
                COALESCE(r.total_attempts, 0) AS total_attempts,
                COALESCE(r.average_percentage, 0) AS average_percentage,
                COALESCE(r.best_percentage, 0) AS best_percentage,
                COALESCE(a.total_activity_seconds, 0)
                    AS total_activity_seconds
            FROM users u
            LEFT JOIN (
                SELECT
                    user_id,
                    COUNT(*) AS total_attempts,
                    AVG(percentage) AS average_percentage,
                    MAX(percentage) AS best_percentage
                FROM results
                GROUP BY user_id
            ) r ON u.id = r.user_id
            LEFT JOIN (
                SELECT
                    user_id,
                    SUM(duration_seconds) AS total_activity_seconds
                FROM user_activity
                GROUP BY user_id
            ) a ON u.id = a.user_id
            WHERE 1=1
        """
        params = []
        if search:
            query += """
                AND (
                    u.name LIKE %s
                    OR u.email LIKE %s
                )
            """
            params.extend([f"%{search}%", f"%{search}%"])
        if role_filter:
            query += " AND u.role = %s"
            params.append(role_filter)
        query += " ORDER BY u.created_at DESC"
        cursor.execute(query, tuple(params))
        users = cursor.fetchall()
        for user in users:
            seconds = int(user.get('total_activity_seconds') or 0)
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            user['activity_time_display'] = (
                f"{hours}h {minutes}m"
            )
            user['last_active'] = (
                user.get('last_active') or 'Never'
            )
            user['average_percentage'] = round(
                float(user.get('average_percentage') or 0), 2
            )
            user['best_percentage'] = round(
                float(user.get('best_percentage') or 0), 2
            )
        cursor.execute("SELECT COUNT(*) AS total FROM users")
        total_users = cursor.fetchone()['total']
        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM users
            WHERE role = 'student'
        """)
        students_count = cursor.fetchone()['total']
        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM users
            WHERE role = 'admin'
        """)
        admins_count = cursor.fetchone()['total']
        return render_template(
            'admin_users.html',
            users=users,
            search=search,
            role_filter=role_filter,
            total_users=total_users,
            students_count=students_count,
            admins_count=admins_count
        )
    except Exception as e:
        print("ADMIN USERS ERROR:", str(e))
        flash("Unable to load users.", "danger")
        return redirect(url_for('admin_dashboard'))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
@app.route('/admin/user/<int:user_id>')
@admin_required()
def admin_user_profile(user_id):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("""
            SELECT
                id,
                name,
                email,
                role,
                created_at,
                age,
                address,
                profile_pic,
                last_active
            FROM users
            WHERE id = %s
        """, (user_id,))
        user = cursor.fetchone()
        if not user:
            flash("User not found.", "danger")
            return redirect(url_for('admin_users'))
        cursor.execute("""
            SELECT
                COUNT(*) AS total_attempts,
                COALESCE(AVG(percentage), 0) AS average_percentage,
                COALESCE(MAX(percentage), 0) AS best_percentage
            FROM results
            WHERE user_id = %s
        """, (user_id,))
        stats = cursor.fetchone()
        cursor.execute("""
            SELECT
                COALESCE(SUM(duration_seconds), 0) AS total_seconds
            FROM user_activity
            WHERE user_id = %s
        """, (user_id,))
        activity = cursor.fetchone()
        total_seconds = int(activity['total_seconds'] or 0)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        activity_time = f"{hours}h {minutes}m"
        return render_template(
            'admin_user_profile.html',
            user=user,
            stats=stats,
            activity_time=activity_time
        )
    except Exception as e:
        print("ADMIN USER PROFILE ERROR:", str(e))
        flash("Unable to load user profile.", "danger")
        return redirect(url_for('admin_users'))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
@app.route("/admin/mock-questions")
def admin_mock_questions():
    if not admin_required():
        flash("Admin access required.", "danger")
        return redirect(url_for("dashboard"))
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("""
            SELECT *
            FROM mock_questions
            ORDER BY id DESC
        """)
        questions = cursor.fetchall()
        return render_template(
            "admin_questions.html",
            questions=questions,
            total_questions=len(questions)
        )
    except Exception:
        app.logger.exception("ADMIN MOCK QUESTIONS ERROR")
        flash("Unable to load mock questions.", "danger")
        return redirect(url_for("admin_dashboard"))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
@app.route("/admin/mock-questions/add", methods=["POST"])
def admin_add_mock_question():
    if not admin_required():
        flash("Admin access required.", "danger")
        return redirect(url_for("dashboard"))
    conn = None
    cursor = None
    try:
        question = request.form.get("question", "").strip()
        option1 = request.form.get("option1", "").strip()
        option2 = request.form.get("option2", "").strip()
        option3 = request.form.get("option3", "").strip()
        option4 = request.form.get("option4", "").strip()
        answer = request.form.get("answer", "").strip()
        if not all([
            question,
            option1,
            option2,
            option3,
            option4,
            answer
        ]):
            flash("Please fill in all question fields.", "warning")
            return redirect(url_for("admin_mock_questions"))
        valid_answers = [option1, option2, option3, option4]
        if answer not in valid_answers:
            flash("Correct answer must match one of the options.", "warning")
            return redirect(url_for("admin_mock_questions"))
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO mock_questions
                (question, option1, option2, option3, option4, answer)
            VALUES
                (%s, %s, %s, %s, %s, %s)
        """, (
            question,
            option1,
            option2,
            option3,
            option4,
            answer
        ))
        conn.commit()
        flash("Mock question added successfully.", "success")
        return redirect(url_for("admin_mock_questions"))
    except Exception:
        if conn:
            conn.rollback()
        app.logger.exception("ADMIN ADD MOCK QUESTION ERROR")
        flash("Unable to add mock question. Check server logs.", "danger")
        return redirect(url_for("admin_mock_questions"))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
@app.route("/admin/mock-questions/delete", methods=["POST"])
@app.route("/admin/mock-questions/delete/<int:question_id>", methods=["POST"])
def admin_delete_mock_question(question_id=None):
    if not admin_required():
        flash("Admin access required.", "danger")
        return redirect(url_for("dashboard"))
    conn = None
    cursor = None
    try:
        if question_id is None:
            question_id = request.form.get("question_id", type=int)
        if not question_id:
            flash("Invalid question ID.", "warning")
            return redirect(url_for("admin_mock_questions"))
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM mock_questions
            WHERE id = %s
        """, (question_id,))
        if cursor.rowcount == 0:
            flash("Mock question not found.", "warning")
            return redirect(url_for("admin_mock_questions"))
        conn.commit()
        flash("Mock question deleted successfully.", "success")
        return redirect(url_for("admin_mock_questions"))
    except Exception:
        if conn:
            conn.rollback()
        app.logger.exception("ADMIN DELETE MOCK QUESTION ERROR")
        flash("Unable to delete mock question.", "danger")
        return redirect(url_for("admin_mock_questions"))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
@app.route("/admin/interview-questions")
def admin_interview_questions():
    if not admin_required():
        flash("Admin access required.", "danger")
        return redirect(url_for("dashboard"))
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("""
            SELECT
                id,
                question,
                answer,
                category,
                container_id,
                level,
                company
            FROM interview_questions
            ORDER BY id DESC
        """)
        questions = cursor.fetchall()
        return render_template(
            "admin_interview_questions.html",
            questions=questions,
            total_questions=len(questions)
        )
    except Exception:
        app.logger.exception("ADMIN INTERVIEW QUESTIONS ERROR")
        flash("Unable to load interview questions.", "danger")
        return redirect(url_for("admin_dashboard"))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
@app.route("/admin")
@app.route("/admin/dashboard")
def admin_dashboard():
    from datetime import date, datetime, timedelta
    if not admin_required():
        flash("Admin access required.", "danger")
        return redirect(url_for("dashboard"))
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("""
            SELECT
                COUNT(*) AS total_users,
                COALESCE(SUM(CASE WHEN LOWER(COALESCE(role, 'student')) = 'student' THEN 1 ELSE 0 END), 0) AS total_students,
                COALESCE(SUM(CASE WHEN LOWER(COALESCE(role, 'student')) = 'admin' THEN 1 ELSE 0 END), 0) AS total_admins
            FROM users
        """)
        user_stats = cursor.fetchone() or {}
        total_users = int(user_stats.get("total_users") or 0)
        total_students = int(user_stats.get("total_students") or 0)
        total_admins = int(user_stats.get("total_admins") or 0)
        cursor.execute("SELECT COUNT(*) AS total FROM mock_questions")
        total_mock_questions = int((cursor.fetchone() or {}).get("total") or 0)
        cursor.execute("SELECT COUNT(*) AS total FROM interview_questions")
        total_interview_questions = int((cursor.fetchone() or {}).get("total") or 0)
        cursor.execute("""
            SELECT COUNT(*) AS total_results,
                   COALESCE(AVG(percentage), 0) AS average_score
            FROM results
        """)
        result_stats = cursor.fetchone() or {}
        total_results = int(result_stats.get("total_results") or 0)
        average_score = round(float(result_stats.get("average_score") or 0), 2)
        cursor.execute("""
            SELECT id, name, email, role, created_at, subscription_status
            FROM users
            WHERE LOWER(COALESCE(role, 'student')) = 'student'
            ORDER BY created_at DESC, id DESC
            LIMIT 10
        """)
        recent_students = cursor.fetchall() or []
        cursor.execute("""
            SELECT DATE(created_at) AS registration_day, COUNT(*) AS total
            FROM users
            WHERE created_at >= DATE_SUB(CURDATE(), INTERVAL 29 DAY)
            GROUP BY DATE(created_at)
            ORDER BY registration_day
        """)
        registration_rows = cursor.fetchall() or []
        registration_map = {
            row["registration_day"].strftime("%Y-%m-%d"): int(row["total"] or 0)
            for row in registration_rows
            if row.get("registration_day")
        }
        today = date.today()
        registration_labels = []
        registration_data = []
        for offset in range(29, -1, -1):
            day = today - timedelta(days=offset)
            key = day.strftime("%Y-%m-%d")
            registration_labels.append(day.strftime("%d %b"))
            registration_data.append(registration_map.get(key, 0))
        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM users
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
        """)
        new_users_30d = int((cursor.fetchone() or {}).get("total") or 0)
        cursor.execute("""
            SELECT COALESCE(NULLIF(category, ''), 'General') AS category,
                   COUNT(*) AS attempts,
                   ROUND(AVG(percentage), 2) AS average_percentage
            FROM results
            GROUP BY COALESCE(NULLIF(category, ''), 'General')
            ORDER BY attempts DESC
            LIMIT 8
        """)
        category_rows = cursor.fetchall() or []
        performance_labels = [str(row.get("category") or "General") for row in category_rows]
        performance_data = [round(float(row.get("average_percentage") or 0), 2) for row in category_rows]
        cursor.execute("""
            SELECT name, email, created_at
            FROM users
            WHERE created_at IS NOT NULL
            ORDER BY created_at DESC
            LIMIT 8
        """)
        registration_events = cursor.fetchall() or []
        cursor.execute("""
            SELECT u.name, u.email, r.category, r.percentage, r.test_date AS created_at
            FROM results r
            INNER JOIN users u ON u.id = r.user_id
            WHERE r.test_date IS NOT NULL
            ORDER BY r.test_date DESC
            LIMIT 10
        """)
        test_events = cursor.fetchall() or []
        recent_activity = []
        for row in registration_events:
            recent_activity.append({
                "name": row.get("name") or "A user",
                "action": "registered a new account",
                "created_at": row.get("created_at"),
                "icon": "fa-solid fa-user-plus"
            })
        for row in test_events:
            category = row.get("category") or "General"
            percentage = row.get("percentage")
            score_text = f" with {float(percentage):.1f}% score" if percentage is not None else ""
            recent_activity.append({
                "name": row.get("name") or "A student",
                "action": f"submitted a {category} test{score_text}",
                "created_at": row.get("created_at"),
                "icon": "fa-solid fa-clipboard-check"
            })
        def activity_time_key(item):
            value = item.get("created_at")
            if value is None:
                return 0.0
            if hasattr(value, "timestamp"):
                try:
                    return value.timestamp()
                except (OSError, ValueError):
                    return 0.0
            try:
                return datetime.fromisoformat(str(value)).timestamp()
            except (TypeError, ValueError, OSError):
                return 0.0
        recent_activity.sort(key=activity_time_key, reverse=True)
        recent_activity = recent_activity[:12]
        return render_template(
            "admin.html",
            total_users=total_users,
            total_students=total_students,
            total_admins=total_admins,
            total_mock_questions=total_mock_questions,
            total_interview_questions=total_interview_questions,
            total_results=total_results,
            average_score=average_score,
            recent_students=recent_students,
            registration_labels=registration_labels,
            registration_data=registration_data,
            performance_labels=performance_labels,
            performance_data=performance_data,
            recent_activity=recent_activity,
            new_users_30d=new_users_30d
        )
    except Exception:
        if conn:
            conn.rollback()
        app.logger.exception("ADMIN DASHBOARD ERROR")
        flash("Unable to load admin dashboard. Check server logs.", "danger")
        return redirect(url_for("dashboard"))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
from flask import render_template, request, redirect, url_for, flash, session
from decimal import Decimal, InvalidOperation
@app.route('/admin/subscription/monthly/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_monthly_subscription():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if request.method == 'POST':
            price = request.form.get('amount', '').strip()
            try:
                amount = Decimal(price)
                if not amount.is_finite() or amount <= 0 or amount > 100000:
                    raise ValueError()
                if amount * 100 != (amount * 100).to_integral_value():
                    raise ValueError()
                amount_paise = int(amount * 100)
            except (InvalidOperation, ValueError):
                flash('Please enter a valid price.', 'danger')
                return redirect(url_for('edit_monthly_subscription'))
            cursor.execute("""
                UPDATE subscription_plans
                SET amount = %s
                WHERE plan_name = 'Monthly'
            """, (amount_paise,))
            if cursor.rowcount == 0:
                cursor.execute("""
                    INSERT INTO subscription_plans
                    (plan_name, amount, duration_days, is_active)
                    VALUES ('Monthly', %s, 30, TRUE)
                """, (amount_paise,))
            conn.commit()
            flash('Monthly subscription price updated successfully!', 'success')
            return redirect(url_for('edit_monthly_subscription'))
        cursor.execute("""
            SELECT plan_name, amount, duration_days, is_active
            FROM subscription_plans
            WHERE plan_name = 'Monthly'
            LIMIT 1
        """)
        plan = cursor.fetchone()
        if not plan:
            flash('Monthly plan not found.', 'danger')
            return redirect(url_for('admin_dashboard'))
        return render_template(
            'admin_edit_monthly.html',
            plan=plan,
            amount_rupees=Decimal(str(plan['amount'])) / 100
        )
    finally:
        cursor.close()
        conn.close()
@app.route("/admin/change-role", methods=["POST"])
@app.route("/admin/change-role/<int:user_id>", methods=["POST"])
def admin_change_role(user_id=None):
    if not admin_required():
        flash("Admin access required.", "danger")
        return redirect(url_for("dashboard"))
    conn = None
    cursor = None
    try:
        if user_id is None:
            user_id = request.form.get("user_id", type=int)
        new_role = (
            request.form.get("role")
            or request.form.get("new_role")
            or ""
        ).strip().lower()
        if not user_id:
            flash("Invalid user ID.", "danger")
            return redirect(url_for("admin_users"))
        if new_role not in ("student", "admin"):
            flash("Invalid role selected.", "danger")
            return redirect(url_for("admin_users"))
        if int(user_id) == int(session.get("user_id")):
            flash("You cannot change your own admin role.", "warning")
            return redirect(url_for("admin_users"))
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute(
            "SELECT id, name, role FROM users WHERE id = %s",
            (user_id,)
        )
        target_user = cursor.fetchone()
        if not target_user:
            flash("User not found.", "danger")
            return redirect(url_for("admin_users"))
        cursor.execute(
            "UPDATE users SET role = %s WHERE id = %s",
            (new_role, user_id)
        )
        conn.commit()
        flash(
            f"Role updated successfully to {new_role}.",
            "success"
        )
        return redirect(url_for("admin_users"))
    except Exception:
        if conn:
            conn.rollback()
        app.logger.exception("ADMIN CHANGE ROLE ERROR")
        flash("Unable to update user role.", "danger")
        return redirect(url_for("admin_users"))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
@app.route("/admin/delete-user", methods=["POST"])
@app.route("/admin/delete-user/<int:user_id>", methods=["POST"])
def admin_delete_user(user_id=None):
    if not admin_required():
        flash("Admin access required.", "danger")
        return redirect(url_for("dashboard"))
    conn = None
    cursor = None
    try:
        if user_id is None:
            user_id = request.form.get("user_id", type=int)
        if not user_id:
            flash("Invalid user ID.", "danger")
            return redirect(url_for("admin_users"))
        if int(user_id) == int(session.get("user_id")):
            flash("You cannot delete your own account.", "warning")
            return redirect(url_for("admin_users"))
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("""
            SELECT id, name, email, role
            FROM users
            WHERE id = %s
        """, (user_id,))
        target_user = cursor.fetchone()
        if not target_user:
            flash("User not found.", "danger")
            return redirect(url_for("admin_users"))
        if str(target_user.get("role") or "").strip().lower() == "admin":
            cursor.execute("""
                SELECT COUNT(*) AS admin_count
                FROM users
                WHERE LOWER(COALESCE(role, 'student')) = 'admin'
            """)
            admin_count = cursor.fetchone()["admin_count"]
            if admin_count <= 1:
                flash(
                    "The last admin account cannot be deleted.",
                    "warning"
                )
                return redirect(url_for("admin_users"))
        cursor.execute("""
            DELETE FROM results
            WHERE user_id = %s
        """, (user_id,))
        cursor.execute("""
            DELETE FROM users
            WHERE id = %s
        """, (user_id,))
        conn.commit()
        flash(
            f"User {target_user['name']} deleted successfully.",
            "success"
        )
        return redirect(url_for("admin_users"))
    except Exception:
        if conn:
            conn.rollback()
        app.logger.exception("ADMIN DELETE USER ERROR")
        flash(
            "Unable to delete user. Check server logs.",
            "danger"
        )
        return redirect(url_for("admin_users"))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
@app.route("/admin/interview-questions/add", methods=["POST"])
def admin_add_interview_question():
    if not admin_required():
        flash("Admin access required.", "danger")
        return redirect(url_for("dashboard"))
    conn = None
    cursor = None
    try:
        question = request.form.get("question", "").strip()
        answer = request.form.get("answer", "").strip()
        category = request.form.get("category", "").strip()
        container_id = request.form.get("container_id", "").strip()
        level = request.form.get("level", "Basic").strip()
        company = request.form.get("company", "").strip()
        if not question:
            flash("Interview question is required.", "warning")
            return redirect(url_for("admin_interview_questions"))
        if not level:
            level = "Basic"
        if container_id:
            try:
                container_id = int(container_id)
            except ValueError:
                flash("Invalid container ID.", "warning")
                return redirect(url_for("admin_interview_questions"))
        else:
            container_id = None
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO interview_questions
                (
                    question,
                    answer,
                    category,
                    container_id,
                    level,
                    company
                )
            VALUES
                (%s, %s, %s, %s, %s, %s)
        """, (
            question,
            answer or None,
            category or None,
            container_id,
            level,
            company or None
        ))
        conn.commit()
        flash(
            "Interview question added successfully.",
            "success"
        )
        return redirect(url_for("admin_interview_questions"))
    except Exception:
        if conn:
            conn.rollback()
        app.logger.exception("ADMIN ADD INTERVIEW QUESTION ERROR")
        flash(
            "Unable to add interview question. Check server logs.",
            "danger"
        )
        return redirect(url_for("admin_interview_questions"))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
@app.route("/admin/interview-questions/delete", methods=["POST"])
@app.route("/admin/interview-questions/delete/<int:question_id>", methods=["POST"])
def admin_delete_interview_question(question_id=None):
    if not admin_required():
        flash("Admin access required.", "danger")
        return redirect(url_for("dashboard"))
    conn = None
    cursor = None
    try:
        if question_id is None:
            question_id = request.form.get("question_id", type=int)
        if not question_id:
            flash("Invalid question ID.", "warning")
            return redirect(url_for("admin_interview_questions"))
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM interview_questions
            WHERE id = %s
        """, (question_id,))
        if cursor.rowcount == 0:
            flash("Interview question not found.", "warning")
            return redirect(url_for("admin_interview_questions"))
        conn.commit()
        flash(
            "Interview question deleted successfully.",
            "success"
        )
        return redirect(url_for("admin_interview_questions"))
    except Exception:
        if conn:
            conn.rollback()
        app.logger.exception(
            "ADMIN DELETE INTERVIEW QUESTION ERROR"
        )
        flash(
            "Unable to delete interview question.",
            "danger"
        )
        return redirect(url_for("admin_interview_questions"))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
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
        import gemini_ai
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
@app.route("/ai-coach")
@app.route("/ai_coach")
def ai_coach():
    if "user_id" not in session:
        flash("Please login first.", "warning")
        return redirect(url_for("login"))
    return render_template(
        "ai_coach.html"
    )
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
    if len(message) > 4000:
        return jsonify({
            "success": False,
            "message": "Message is too long."
        }), 400
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
@app.route("/ai-interview")
@app.route("/ai_interview")
def ai_interview():
    if "user_id" not in session:
        flash("Please login first.", "warning")
        return redirect(url_for("login"))
    return render_template(
        "ai_interview.html"
    )
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
@app.route("/ai-resume")
@app.route("/ai_resume")
def ai_resume():
    if "user_id" not in session:
        flash("Please login first.", "warning")
        return redirect(url_for("login"))
    return render_template(
        "ai_resume.html"
    )
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
@app.route(
    "/api/ai/communication",
    methods=["POST"]
)
def ai_communications():
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
    session["ai_history"] = history[-20:]
    return jsonify({
        "success": True,
        "message": "AI conversation saved."
    })
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
@app.route("/contact")
def contact():
    return render_template(
        "contact.html"
    )
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
@app.route("/feedback")
def feedback():
    if "user_id" not in session:
        flash("Please login first.", "warning")
        return redirect(url_for("login"))
    return render_template(
        "feedback.html"
    )
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
@app.route("/faq")
@app.route("/faqs")
def faq():
    return render_template(
        "faq.html"
    )
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
from flask import request, jsonify, session
from flask import request, jsonify, session
@app.route("/api/course/progress", methods=["POST"])
def save_course_progress():
    if "user_id" not in session:
        return jsonify({"error": "Login required"}), 401
    data = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE course_progress
        SET lesson=%s,
            progress=%s,
            xp=%s,
            level=%s,
            streak=%s
        WHERE user_id=%s
    """, (
        data.get("lesson", 0),
        data.get("progress", 0),
        data.get("xp", 0),
        data.get("level", 1),
        data.get("streak", 0),
        session["user_id"]
    ))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({
        "success": True
    })
@app.route("/api/course/progress", methods=["GET"])
def get_course_progress():
    if "user_id" not in session:
        return jsonify({"error": "Login required"}), 401
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT lesson, progress, xp, level, streak
        FROM course_progress
        WHERE user_id=%s
    """, (session["user_id"],))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if row:
        return jsonify({
            "lesson": row["lesson"],
            "progress": row["progress"],
            "xp": row["xp"],
            "level": row["level"],
            "streak": row["streak"]
        })
    return jsonify({
        "lesson": 0,
        "progress": 0,
        "xp": 0,
        "level": 1,
        "streak": 0
    })
@app.route("/api/course/progress", methods=["GET"])
def load_course_progress():
    progress = session.get("course_progress", {
        "lesson": 0,
        "progress": 0,
        "xp": 0,
        "level": 1,
        "streak": 0
    })
    return jsonify(progress)
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
@app.route('/courses')
@login_required
def courses():
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        cursor.execute("""
            SELECT
                id,
                faculty_name,
                slug,
                description
            FROM pyq_faculties
            WHERE is_active = 1
            ORDER BY faculty_name
        """)
        faculties = cursor.fetchall()

        cursor.execute("""
            SELECT
                c.id,
                c.faculty_id,
                c.course_code,
                c.course_name,
                c.slug,
                c.course_level,
                c.total_semesters,
                c.description,
                f.faculty_name,
                f.slug AS faculty_slug
            FROM pyq_courses c
            INNER JOIN pyq_faculties f
                ON f.id = c.faculty_id
            WHERE c.is_active = 1
              AND f.is_active = 1
            ORDER BY f.faculty_name, c.course_name
        """)
        academic_courses = cursor.fetchall()

        cursor.execute("""
            SELECT
                s.id,
                s.course_id,
                s.semester_no,
                s.subject_code,
                s.subject_name,
                s.description
            FROM pyq_subjects s
            INNER JOIN pyq_courses c
                ON c.id = s.course_id
            WHERE s.is_active = 1
              AND c.is_active = 1
            ORDER BY s.course_id, s.semester_no, s.subject_name
        """)
        academic_subjects = cursor.fetchall()

        cursor.execute("""
            SELECT
                id,
                course_name,
                semester,
                subject_name,
                exam_year,
                exam_session,
                marks,
                paper_pattern,
                file_path
            FROM pyq_papers
            ORDER BY exam_year DESC, semester, subject_name
        """)
        academic_papers = cursor.fetchall()

        cursor.execute("""
            SELECT
                id,
                title,
                description,
                pdf_link,
                category,
                material_type,
                course_name,
                semester,
                subject_name
            FROM study_materials
            ORDER BY id DESC
        """)
        all_materials = cursor.fetchall()

        subjects_by_course = {}
        for subject in academic_subjects:
            course_id = subject["course_id"]
            subjects_by_course.setdefault(course_id, []).append(subject)

        papers_by_course = {}
        for paper in academic_papers:
            course_key = str(paper.get("course_name") or "").strip().lower()
            papers_by_course.setdefault(course_key, []).append(paper)

        courses_by_faculty = {}
        for course in academic_courses:
            course_id = course["id"]
            course_name = str(course.get("course_name") or "").strip()
            course_key = course_name.lower()

            course["subjects"] = subjects_by_course.get(course_id, [])
            course["papers"] = papers_by_course.get(course_key, [])

            semesters = {}
            for subject in course["subjects"]:
                semester_no = subject["semester_no"]
                semesters.setdefault(semester_no, []).append(subject)

            course["semesters"] = [
                {
                    "semester_no": semester_no,
                    "subjects": semester_subjects
                }
                for semester_no, semester_subjects in sorted(semesters.items())
            ]

            courses_by_faculty.setdefault(
                course["faculty_id"], []
            ).append(course)

        for faculty in faculties:
            faculty["courses"] = courses_by_faculty.get(faculty["id"], [])
            faculty["total_courses"] = len(faculty["courses"])
            faculty["total_subjects"] = sum(
                len(course["subjects"])
                for course in faculty["courses"]
            )
            faculty["total_papers"] = sum(
                len(course["papers"])
                for course in faculty["courses"]
            )

        pyq_papers = []
        for paper in academic_papers:
            pyq_papers.append({
                "id": paper["id"],
                "title": paper["subject_name"],
                "course_name": paper["course_name"],
                "subject_name": paper["subject_name"],
                "semester": paper["semester"],
                "exam_year": paper["exam_year"],
                "exam_session": paper["exam_session"],
                "marks": paper["marks"],
                "paper_pattern": paper["paper_pattern"],
                "pdf_url": paper["file_path"],
                "file_path": paper["file_path"]
            })

        study_materials = []
        for item in all_materials:
            material_type = str(
                item.get("material_type") or ""
            ).strip().lower()

            category = str(
                item.get("category") or ""
            ).strip().lower()

            if material_type in ("pyq", "question_bank") or category in (
                "pyq", "question_bank"
            ):
                continue

            study_materials.append({
                "id": item["id"],
                "title": item["title"],
                "description": item["description"],
                "filename": item["pdf_link"],
                "pdf_link": item["pdf_link"],
                "course_name": item["course_name"],
                "semester": item["semester"],
                "subject_name": item["subject_name"],
                "extension": "PDF",
                "size": ""
            })

        pyq_semesters = sorted({
            str(paper["semester"])
            for paper in pyq_papers
            if paper.get("semester") is not None
        })

        pyq_years = sorted({
            str(paper["exam_year"])
            for paper in pyq_papers
            if paper.get("exam_year") is not None
        }, reverse=True)

        total_faculties = len(faculties)
        total_academic_courses = len(academic_courses)
        total_academic_subjects = len(academic_subjects)
        total_academic_papers = len(academic_papers)

        courses_list = [
            {
                "id": course["id"],
                "name": course["course_name"],
                "course_name": course["course_name"],
                "slug": course["slug"],
                "faculty_id": course["faculty_id"],
                "faculty_name": course["faculty_name"],
                "total_semesters": course["total_semesters"],
                "course_level": course["course_level"]
            }
            for course in academic_courses
        ]

        return render_template(
            "courses.html",
            faculties=faculties,
            academic_courses=academic_courses,
            academic_subjects=academic_subjects,
            academic_papers=academic_papers,
            courses=courses_list,
            courses_list=courses_list,
            courses_by_faculty=courses_by_faculty,
            pyq_papers=pyq_papers,
            pyq_semesters=pyq_semesters,
            pyq_years=pyq_years,
            study_materials=study_materials,
            total_faculties=total_faculties,
            total_academic_courses=total_academic_courses,
            total_academic_subjects=total_academic_subjects,
            total_academic_papers=total_academic_papers
        )

    except Exception as e:
        app.logger.exception("ACADEMIC COURSES ERROR")
        flash("Unable to load academic courses. Please try again.", "danger")
        return redirect(url_for("dashboard"))

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
@app.route("/study-materials/file/<path:filename>")
@login_required
def open_study_material(filename):
    import os
    from flask import send_from_directory, request, abort
    materials_folder = os.path.join(
        app.root_path,
        "static",
        "uploads",
        "study_materials"
    )
    if not os.path.isdir(materials_folder):
        abort(404)
    return send_from_directory(
        materials_folder,
        filename,
        as_attachment=request.args.get("download") == "1"
    )
@app.route("/course/<course_name>")
@login_required
def course(course_name):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("""
            SELECT *
            FROM courses
            WHERE LOWER(course_name) = LOWER(%s)
            LIMIT 1
        """, (course_name,))
        course_info = cursor.fetchone()
        if not course_info:
            flash("Course not found.", "danger")
            return redirect(url_for("courses"))
        cursor.execute("""
            SELECT
                id,
                day_number,
                title,
                notes,
                code_snippet,
                practice_task
            FROM course_lessons
            WHERE LOWER(course_name) = LOWER(%s)
            ORDER BY day_number ASC
        """, (course_name,))
        lessons = cursor.fetchall()
        cursor.execute("""
            SELECT current_day, completed
            FROM course_progress
            WHERE user_id = %s
            AND LOWER(course_name) = LOWER(%s)
            LIMIT 1
        """, (
            session["user_id"],
            course_name
        ))
        progress_data = cursor.fetchone()
        completed_days = []
        if progress_data:
            completed = int(progress_data.get("completed") or 0)
            if completed > 0:
                completed_days = list(range(1, completed + 1))
        total_days = len(lessons)
        progress = len(completed_days)
        percentage = (
            min(int((progress / total_days) * 100), 100)
            if total_days > 0 else 0
        )
        course_data = {
            "name": course_info.get("course_title") or course_info.get("course_name"),
            "level": course_info.get("level") or "Beginner",
            "description": course_info.get("description") or "",
            "projects": course_info.get("projects") or "0"
        }
        return render_template(
            "java.html",
            course=course_data,
            lessons=lessons,
            progress=progress,
            percentage=percentage,
            total_days=total_days,
            completed_days=completed_days
        )
    except Exception:
        app.logger.exception(
            "Course learning page failed: %s",
            course_name
        )
        flash("Unable to load course.", "danger")
        return redirect(url_for("courses"))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
@app.route("/course/<course_name>/<int:day>")
@login_required
def course_day(course_name, day):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("""
            SELECT course_name, course_title
            FROM courses
            WHERE LOWER(course_name) = LOWER(%s)
            LIMIT 1
        """, (course_name,))
        course_info = cursor.fetchone()
        if not course_info:
            flash("Course not found.", "danger")
            return redirect(url_for("courses"))
        cursor.execute("""
            SELECT
                id,
                day_number,
                title,
                notes,
                code_snippet,
                practice_task
            FROM course_lessons
            WHERE LOWER(course_name) = LOWER(%s)
            AND day_number = %s
            LIMIT 1
        """, (course_name, day))
        lesson = cursor.fetchone()
        if not lesson:
            flash("Lesson not found.", "warning")
            return redirect(
                url_for("course", course_name=course_name)
            )
        return render_template(
            "course_day.html",
            course_name=course_name,
            day=day,
            title=lesson["title"],
            notes=lesson["notes"],
            code_snippet=lesson["code_snippet"],
            practice_task=lesson["practice_task"]
        )
    except Exception:
        app.logger.exception(
            "Course day loading failed: %s, Day: %s",
            course_name,
            day
        )
        flash("Unable to load lesson.", "danger")
        return redirect(
            url_for("course", course_name=course_name)
        )
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
@app.route("/complete_day/<course_name>/<int:day>",methods=["POST"])
@login_required
def complete_day(course_name,day):
    cursor=mysql.connection.cursor()
    try:
        cursor.execute("""
        INSERT IGNORE INTO
        user_course_progress
        (
            user_id,
            course_name,
            completed_day
        )
        VALUES(%s,%s,%s)
        """,(
            session["user_id"],
            course_name.lower(),
            day
        ))
        mysql.connection.commit()
        return jsonify({
            "success":True
        })
    except Exception as e:
        mysql.connection.rollback()
        print(e)
        return jsonify({
            "success":False
        })
    finally:
        cursor.close()
@app.route("/notes")
def notes():
    if "user_id" not in session:
        return redirect(url_for("login"))
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
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
            WHERE is_active = 1
            ORDER BY id ASC
        """)
        notes_data = cursor.fetchall()
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
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
@app.route("/leaderboard")
def leaderboard():

    conn = None
    cursor = None

    leaderboard_data = []
    my_stats = None

    total_students = 0
    total_tests = 0
    average_score = 0
    active_students = 0

    current_user_id = session.get("user_id")

    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        cursor.execute("""
            SELECT
                u.id,
                u.name,
                u.profile_pic,
                u.created_at,
                COALESCE(a.completed_tests, 0) AS completed_tests,
                COALESCE(a.total_correct, 0) AS total_correct,
                COALESCE(a.total_wrong, 0) AS total_wrong,
                COALESCE(a.total_unanswered, 0) AS total_unanswered,
                COALESCE(a.total_obtained_marks, 0) AS total_obtained_marks,
                COALESCE(a.total_marks, 0) AS total_marks,
                COALESCE(a.average_percentage, 0) AS average_percentage,
                COALESCE(a.best_percentage, 0) AS best_percentage,
                COALESCE(a.total_xp, 0) AS total_xp,
                COALESCE(p.participation_count, 0) AS participation_count,
                a.last_submission
            FROM users u
            LEFT JOIN (
                SELECT
                    user_id,
                    COUNT(*) AS completed_tests,
                    SUM(correct_answers) AS total_correct,
                    SUM(wrong_answers) AS total_wrong,
                    SUM(unanswered_questions) AS total_unanswered,
                    SUM(obtained_marks) AS total_obtained_marks,
                    SUM(total_marks) AS total_marks,
                    AVG(percentage) AS average_percentage,
                    MAX(percentage) AS best_percentage,
                    SUM(correct_answers * 10) + COUNT(*) * 25 AS total_xp,
                    MAX(submitted_at) AS last_submission
                FROM mock_attempts
                WHERE status IN ('Submitted', 'Auto Submitted')
                  AND submitted_at IS NOT NULL
                GROUP BY user_id
            ) a ON a.user_id = u.id
            LEFT JOIN (
                SELECT
                    user_id,
                    COUNT(DISTINCT test_id) AS participation_count
                FROM mock_test_participants
                WHERE status != 'Left'
                GROUP BY user_id
            ) p ON p.user_id = u.id
            WHERE u.role = 'student'
            ORDER BY
                total_xp DESC,
                average_percentage DESC,
                completed_tests DESC,
                total_correct DESC
        """)

        students = cursor.fetchall() or []

        for student in students:
            student["total_xp"] = int(student["total_xp"] or 0)
            student["average_percentage"] = round(float(student["average_percentage"] or 0), 2)
            student["best_percentage"] = round(float(student["best_percentage"] or 0), 2)

            student["total_correct"] = int(student["total_correct"] or 0)
            student["total_wrong"] = int(student["total_wrong"] or 0)
            student["completed_tests"] = int(student["completed_tests"] or 0)
            student["participation_count"] = int(student["participation_count"] or 0)

            if student["completed_tests"] > 0:
                leaderboard_data.append(student)

        for index, student in enumerate(leaderboard_data, start=1):
            student["rank"] = index

            if current_user_id and int(student["id"]) == int(current_user_id):
                my_stats = student

        total_students = len(leaderboard_data)

        total_tests = sum(
            student["completed_tests"] for student in leaderboard_data
        )

        active_students = sum(
            1 for student in leaderboard_data
            if student["completed_tests"] > 0
        )

        if total_students:
            average_score = round(
                sum(student["average_percentage"] for student in leaderboard_data)
                / total_students,
                2
            )

        return render_template(
            "leaderboard.html",
            leaderboard=leaderboard_data,
            my_stats=my_stats,
            total_students=total_students,
            total_tests=total_tests,
            average_score=average_score,
            active_students=active_students
        )

    except Exception as e:
        print("LEADERBOARD ERROR:", str(e))

        return render_template(
            "leaderboard.html",
            leaderboard=[],
            my_stats=None,
            total_students=0,
            total_tests=0,
            average_score=0,
            active_students=0
        )

    finally:
        if cursor:
            cursor.close()

        if conn:
            conn.close()
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
import os
import requests
from flask import request, jsonify, render_template
from flask_login import login_required as flask_login_required
@app.route("/ai_communication")
@login_required
def ai_communication():
    return render_template("ai_communication.html")
@app.route("/api/ai/communication", methods=["POST"])
@login_required
def ai_communication_api():
    try:
        data = request.get_json(silent=True) or {}
        message = str(data.get("message") or "").strip()
        history = data.get("history") or []
        if not message:
            return jsonify({
                "success": False,
                "error": "Please enter a question."
            }), 400
        if len(message) > 4000:
            return jsonify({
                "success": False,
                "error": "Message is too long. Please keep it under 4000 characters."
            }), 400
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("ERROR: OPENAI_API_KEY is missing")
            return jsonify({
                "success": False,
                "error": "AI service is not configured on the server."
            }), 500
        model = os.getenv(
            "OPENAI_MODEL",
            "gpt-5.6-luna"
        )
        conversation = []
        if isinstance(history, list):
            for item in history[-10:]:
                if not isinstance(item, dict):
                    continue
                role = item.get("role")
                content = item.get("content")
                if role in ["user", "assistant"] and content:
                    conversation.append({
                        "role": role,
                        "content": str(content)[:4000]
                    })
        conversation.append({
            "role": "user",
            "content": message
        })
        payload = {
            "model": model,
            "instructions": (
                "You are the AI Communication Assistant inside a "
                "placement training portal.\n\n"
                "Help students with:\n"
                "- English communication\n"
                "- Interview preparation\n"
                "- HR interview questions\n"
                "- Technical interview communication\n"
                "- Self introduction\n"
                "- Resume interview questions\n"
                "- Mock interviews\n"
                "- Professional speaking\n"
                "- Grammar correction\n"
                "- Placement preparation\n\n"
                "Give practical and student-friendly answers.\n"
                "Keep answers concise and easy to speak.\n"
                "For interview answers, provide natural answers "
                "that a college student can actually speak.\n"
                "If the student's English is incorrect, politely "
                "give a corrected version and brief explanation.\n"
                "Be supportive, professional and clear."
            ),
            "input": conversation
        }
        print("AI REQUEST MODEL:", model)
        response = requests.post(
            "https://api.openai.com/v1/responses",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=60
        )
        if response.status_code >= 400:
            print(
                "OPENAI API ERROR:",
                response.status_code,
                response.text
            )
            try:
                error_data = response.json()
                error_message = (
                    error_data
                    .get("error", {})
                    .get("message")
                )
            except Exception:
                error_message = None
            return jsonify({
                "success": False,
                "error": error_message
                or "AI service temporarily unavailable."
            }), 502
        result = response.json()
        answer = ""
        if isinstance(result.get("output_text"), str):
            answer = result["output_text"].strip()
        if not answer:
            output = result.get("output", [])
            if isinstance(output, list):
                for item in output:
                    if not isinstance(item, dict):
                        continue
                    content_list = item.get("content", [])
                    if not isinstance(content_list, list):
                        continue
                    for content in content_list:
                        if not isinstance(content, dict):
                            continue
                        if content.get("type") == "output_text":
                            text = content.get("text")
                            if text:
                                answer += str(text)
            answer = answer.strip()
        if not answer:
            print("OPENAI EMPTY RESPONSE:")
            print(result)
            return jsonify({
                "success": False,
                "error": "AI returned an empty response."
            }), 502
        return jsonify({
            "success": True,
            "answer": answer
        }), 200
    except requests.Timeout:
        print("OPENAI TIMEOUT")
        return jsonify({
            "success": False,
            "error": "AI service took too long to respond. Please try again."
        }), 504
    except requests.RequestException as e:
        print(
            "OPENAI CONNECTION ERROR:",
            repr(e)
        )
        return jsonify({
            "success": False,
            "error": "Could not connect to AI service."
        }), 502
    except Exception as e:
        print(
            "AI COMMUNICATION ERROR:",
            repr(e)
        )
        return jsonify({
            "success": False,
            "error": "Something went wrong while processing your question."
        }), 500
@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    user_id = session.get("user_id")
    conn = None
    cursor = None
    defaults = {
        "language": "English",
        "timezone": "Asia/Kolkata",
        "date_format": "DD-MM-YYYY",
        "theme": "light",
        "accent_color": "#6366f1",
        "compact_layout": 0,
        "email_notifications": 1,
        "browser_notifications": 0,
        "message_notifications": 1,
        "friend_notifications": 1,
        "mock_test_notifications": 1,
        "interview_notifications": 1,
        "placement_notifications": 1,
        "profile_visibility": "public",
        "show_online_status": 1,
        "allow_friend_requests": 1
    }
    notification_fields = (
        "email_notifications",
        "browser_notifications",
        "message_notifications",
        "friend_notifications",
        "mock_test_notifications",
        "interview_notifications",
        "placement_notifications"
    )
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute(
            "SELECT * FROM users WHERE id = %s LIMIT 1",
            (user_id,)
        )
        user = cursor.fetchone()
        if not user:
            session.clear()
            flash("Please login again.", "warning")
            return redirect(url_for("login"))
        cursor.execute(
            "SELECT * FROM user_settings WHERE user_id = %s LIMIT 1",
            (user_id,)
        )
        saved_settings = cursor.fetchone() or {}
        current_settings = defaults.copy()
        current_settings.update({
            key: saved_settings.get(key, value)
            for key, value in defaults.items()
        })
        if request.method == "POST":
            section = request.form.get("section", "").strip().lower()
            if section == "general":
                language = request.form.get("language", "English").strip()
                timezone = request.form.get("timezone", "Asia/Kolkata").strip()
                date_format = request.form.get("date_format", "DD-MM-YYYY").strip()
                if not language or len(language) > 30:
                    return redirect(url_for("settings", error="Please select a valid language."))
                try:
                    ZoneInfo(timezone)
                except Exception:
                    return redirect(url_for("settings", error="Please select a valid timezone."))
                if date_format not in ("DD-MM-YYYY", "MM-DD-YYYY", "YYYY-MM-DD"):
                    return redirect(url_for("settings", error="Please select a valid date format."))
                current_settings.update({
                    "language": language,
                    "timezone": timezone,
                    "date_format": date_format
                })
            elif section == "appearance":
                theme = request.form.get("theme", "light").strip().lower()
                accent_color = request.form.get("accent_color", "#6366f1").strip()
                compact_layout = 1 if request.form.get("compact_layout") in ("on", "1", "true") else 0
                if theme not in ("light", "dark", "system"):
                    return redirect(url_for("settings", error="Please select a valid theme."))
                if len(accent_color) != 7 or not accent_color.startswith("#") or any(c not in "0123456789abcdefABCDEF" for c in accent_color[1:]):
                    return redirect(url_for("settings", error="Please select a valid accent color."))
                current_settings.update({
                    "theme": theme,
                    "accent_color": accent_color,
                    "compact_layout": compact_layout
                })
            elif section == "notifications":
                current_settings.update({
                    field: 1 if request.form.get(field) in ("on", "1", "true") else 0
                    for field in notification_fields
                })
            elif section == "privacy":
                profile_visibility = request.form.get("profile_visibility", "public").strip().lower()
                if profile_visibility not in ("public", "friends", "private"):
                    return redirect(url_for("settings", error="Please select a valid profile visibility."))
                current_settings.update({
                    "profile_visibility": profile_visibility,
                    "show_online_status": 1 if request.form.get("show_online_status") in ("on", "1", "true") else 0,
                    "allow_friend_requests": 1 if request.form.get("allow_friend_requests") in ("on", "1", "true") else 0
                })
            elif section == "security":
                if str(user.get("login_provider") or "").lower() == "google":
                    return redirect(url_for("settings", error="Google account passwords must be changed through Google."))
                current_password = request.form.get("current_password", "")
                new_password = request.form.get("new_password", "")
                confirm_password = request.form.get("confirm_password", "")
                if not current_password or not new_password or not confirm_password:
                    return redirect(url_for("settings", error="Please fill in all password fields."))
                if len(new_password) < 8:
                    return redirect(url_for("settings", error="New password must contain at least 8 characters."))
                if new_password != confirm_password:
                    return redirect(url_for("settings", error="New password and confirmation do not match."))
                if not user.get("password") or not bcrypt.check_password_hash(user["password"], current_password):
                    return redirect(url_for("settings", error="Your current password is incorrect."))
                new_password_hash = bcrypt.generate_password_hash(new_password).decode("utf-8")
                cursor.execute(
                    "UPDATE users SET password = %s WHERE id = %s",
                    (new_password_hash, user_id)
                )
                conn.commit()
                return redirect(url_for("settings", success="Password updated successfully."))
            else:
                return redirect(url_for("settings", error="Invalid settings section."))
            columns = list(defaults.keys())
            values = [current_settings[column] for column in columns]
            insert_columns = ["user_id"] + columns
            placeholders = ", ".join(["%s"] * len(insert_columns))
            update_clause = ", ".join(
                f"{column}=VALUES({column})" for column in columns
            )
            sql = (
                f"INSERT INTO user_settings ({', '.join(insert_columns)}) "
                f"VALUES ({placeholders}) "
                f"ON DUPLICATE KEY UPDATE {update_clause}"
            )
            cursor.execute(sql, [user_id] + values)
            conn.commit()
            return redirect(url_for("settings", success="Settings saved successfully."))
        account_name = user.get("name") or session.get("name") or session.get("user_name", "")
        account_email = user.get("email") or session.get("email") or session.get("user_email", "")
        profile_pic = user.get("profile_pic") or user.get("picture") or session.get("profile_pic", "")
        session["name"] = account_name
        session["email"] = account_email
        session["profile_pic"] = profile_pic
        session["login_provider"] = user.get("login_provider") or session.get("login_provider", "email")
        return render_template(
            "settings.html",
            settings=current_settings,
            account_name=account_name,
            account_email=account_email,
            profile_pic=profile_pic,
            login_provider=user.get("login_provider") or session.get("login_provider", "email")
        )
    except Exception:
        if conn:
            conn.rollback()
        app.logger.exception("SETTINGS ROUTE ERROR")
        return redirect(url_for("settings", error="Unable to load or save settings. Please try again."))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
@app.route("/profile")
def profile():
    if "email" not in session:
        return redirect(url_for("login"))
    return render_template("profile.html")
@app.route("/study-materials")
@login_required
def study_materials():
    materials_folder = os.path.join(
        app.root_path,
        "static",
        "uploads",
        "study_materials"
    )
    materials = []
    if os.path.isdir(materials_folder):
        for filename in os.listdir(materials_folder):
            file_path = os.path.join(materials_folder, filename)
            if not os.path.isfile(file_path):
                continue
            extension = os.path.splitext(filename)[1].lower()
            if extension not in [".pdf", ".doc", ".docx"]:
                continue
            materials.append({
                "filename": filename,
                "title": os.path.splitext(filename)[0]
                    .replace("_", " ")
                    .replace("-", " ")
                    .title(),
                "extension": extension.upper().replace(".", ""),
                "size": round(os.path.getsize(file_path) / 1024, 1)
            })
    materials.sort(key=lambda x: x["filename"].lower())
    return render_template(
        "study_materials.html",
        materials=materials
    )
def is_admin():
    return (
        bool(session.get("user_id"))
        and str(session.get("role", "")).strip().lower() == "admin"
    )
    def decorated_view(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please login first.", "warning")
            return redirect(url_for("login"))
        user_role = str(
            session.get("role", "")
        ).strip().lower()
        if user_role != "admin":
            flash("Admin access required.", "danger")
            return redirect(url_for("dashboard"))
        return view_func(*args, **kwargs)
    return decorated_view
import re
@app.route("/admin/pyq/courses", methods=["GET", "POST"])
def pyq_admin_courses():
    if not admin_required():
        flash("Admin access required.", "danger")
        return redirect(url_for("dashboard"))
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        if request.method == "POST":
            faculty_id = request.form.get("faculty_id", type=int)
            course_name = request.form.get(
                "course_name", ""
            ).strip()
            course_code = request.form.get(
                "course_code", ""
            ).strip()
            course_level = request.form.get(
                "course_level", "UG"
            ).strip()
            total_semesters = request.form.get(
                "total_semesters", 6, type=int
            )
            description = request.form.get(
                "description", ""
            ).strip()
            if not faculty_id or not course_name:
                flash(
                    "Faculty and course name are required.",
                    "danger"
                )
                return redirect(url_for("pyq_admin_courses"))
            if not total_semesters or not 1 <= total_semesters <= 12:
                flash("Invalid semester count.", "danger")
                return redirect(url_for("pyq_admin_courses"))
            slug = re.sub(
                r"[^a-z0-9]+",
                "-",
                course_name.lower()
            ).strip("-")
            try:
                cursor.execute("""
                    INSERT INTO pyq_courses (
                        faculty_id,
                        course_code,
                        course_name,
                        slug,
                        course_level,
                        total_semesters,
                        description,
                        is_active
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 1)
                """, (
                    faculty_id,
                    course_code or None,
                    course_name,
                    slug,
                    course_level,
                    total_semesters,
                    description or None
                ))
                conn.commit()
                flash(
                    "Course added successfully!",
                    "success"
                )
            except pymysql.err.IntegrityError:
                conn.rollback()
                flash(
                    "Course already exists or slug is duplicate.",
                    "danger"
                )
            return redirect(url_for("pyq_admin_courses"))
        cursor.execute("""
            SELECT
                id,
                faculty_name
            FROM pyq_faculties
            WHERE is_active = 1
            ORDER BY faculty_name
        """)
        faculties = cursor.fetchall()
        cursor.execute("""
            SELECT
                c.id,
                c.course_code,
                c.course_name,
                c.slug,
                c.course_level,
                c.total_semesters,
                c.description,
                c.is_active,
                f.faculty_name,
                (
                    SELECT COUNT(*)
                    FROM pyq_subjects s
                    WHERE s.course_id = c.id
                ) AS total_subjects
            FROM pyq_courses c
            INNER JOIN pyq_faculties f
                ON c.faculty_id = f.id
            ORDER BY c.created_at DESC
        """)
        courses = cursor.fetchall()
        total_courses = len(courses)
        active_courses = sum(
            1 for c in courses
            if c["is_active"]
        )
        inactive_courses = (
            total_courses - active_courses
        )
        return render_template(
            "admin/pyq_courses.html",
            faculties=faculties,
            courses=courses,
            total_courses=total_courses,
            active_courses=active_courses,
            inactive_courses=inactive_courses
        )
    except Exception:
        if conn:
            conn.rollback()
        app.logger.exception(
            "PYQ COURSE MANAGEMENT ERROR"
        )
        flash(
            "Unable to load course management.",
            "danger"
        )
        return redirect(url_for("dashboard"))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
def social_user_id():
    return session.get("user_id")
def social_login_required():
    if not social_user_id():
        flash("Please login to continue.", "warning")
        return False
    return True
def create_social_notification(
    cursor,
    user_id,
    title,
    message,
    notification_type="general",
    link=None
):
    cursor.execute("""
        INSERT INTO notifications
        (user_id, title, message, type, link, is_read, created_at)
        VALUES (%s, %s, %s, %s, %s, 0, CURRENT_TIMESTAMP)
    """, (
        user_id,
        title,
        message,
        notification_type,
        link
    ))
def are_friends(cursor, user1, user2):
    cursor.execute("""
        SELECT id
        FROM friend_requests
        WHERE (
            (sender_id=%s AND receiver_id=%s)
            OR
            (sender_id=%s AND receiver_id=%s)
        )
        AND status='accepted'
        LIMIT 1
    """, (user1, user2, user2, user1))
    return cursor.fetchone() is not None
@app.route("/friends")
def friends():
    if not social_login_required():
        return redirect(url_for("login"))
    user_id = social_user_id()
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute("""
            SELECT
                fr.id,
                fr.sender_id,
                fr.created_at,
                u.name,
                u.email,
                COALESCE(
                    NULLIF(u.profile_pic, ''),
                    NULLIF(u.picture, '')
                ) AS picture
            FROM friend_requests fr
            JOIN users u ON u.id = fr.sender_id
            WHERE fr.receiver_id=%s
            AND fr.status='pending'
            ORDER BY fr.created_at DESC
        """, (user_id,))
        pending_requests = cursor.fetchall()
        cursor.execute("""
            SELECT
                u.id,
                u.name,
                u.email,
                COALESCE(
                    NULLIF(u.profile_pic, ''),
                    NULLIF(u.picture, '')
                ) AS picture
            FROM friend_requests fr
            JOIN users u
            ON u.id = CASE
                WHEN fr.sender_id=%s
                THEN fr.receiver_id
                ELSE fr.sender_id
            END
            WHERE (
                fr.sender_id=%s
                OR fr.receiver_id=%s
            )
            AND fr.status='accepted'
            ORDER BY u.name
        """, (user_id, user_id, user_id))
        friends_list = cursor.fetchall()
        cursor.execute("""
            SELECT
                u.id,
                u.name,
                u.email,
                COALESCE(
                    NULLIF(u.profile_pic, ''),
                    NULLIF(u.picture, '')
                ) AS picture
            FROM users u
            WHERE u.id != %s
            AND NOT EXISTS (
                SELECT 1
                FROM friend_requests fr
                WHERE (
                    (fr.sender_id=%s AND fr.receiver_id=u.id)
                    OR
                    (fr.sender_id=u.id AND fr.receiver_id=%s)
                )
                AND fr.status IN ('pending', 'accepted')
            )
            ORDER BY u.name
            LIMIT 20
        """, (user_id, user_id, user_id))
        suggestions = cursor.fetchall()
        return render_template(
            "friends.html",
            pending_requests=pending_requests,
            friends=friends_list,
            suggestions=suggestions
        )
    finally:
        cursor.close()
        conn.close()
@app.route("/friends/send/<int:user_id>", methods=["POST"])
def send_friend_request(user_id):
    if not social_login_required():
        return redirect(url_for("login"))
    current_user = social_user_id()
    if current_user == user_id:
        flash("You cannot send a request to yourself.", "warning")
        return redirect(url_for("friends"))
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute(
            "SELECT id FROM users WHERE id=%s",
            (user_id,)
        )
        if not cursor.fetchone():
            flash("User not found.", "danger")
            return redirect(url_for("friends"))
        cursor.execute("""
            SELECT id, status
            FROM friend_requests
            WHERE (
                (sender_id=%s AND receiver_id=%s)
                OR
                (sender_id=%s AND receiver_id=%s)
            )
            AND status IN ('pending', 'accepted')
            LIMIT 1
        """, (current_user, user_id, user_id, current_user))
        existing = cursor.fetchone()
        if existing:
            flash("Request already exists or you are already friends.", "info")
            return redirect(url_for("friends"))
        cursor.execute("""
            INSERT INTO friend_requests
            (sender_id, receiver_id, status)
            VALUES (%s, %s, 'pending')
        """, (current_user, user_id))
        create_social_notification(
            cursor,
            user_id,
            "New Friend Request",
            "Someone sent you a friend request.",
            "friend_request",
            "/friends"
        )
        conn.commit()
        flash("Friend request sent successfully!", "success")
    except Exception:
        conn.rollback()
        flash("Unable to send friend request.", "danger")
        app.logger.exception("Friend request error")
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for("friends"))
@app.route(
    "/friends/accept/<int:request_id>",
    methods=["POST"]
)
def accept_friend_request(request_id):
    if not social_login_required():
        return redirect(url_for("login"))
    current_user = social_user_id()
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute("""
            SELECT id, sender_id
            FROM friend_requests
            WHERE id=%s
            AND receiver_id=%s
            AND status='pending'
        """, (request_id, current_user))
        friend_request = cursor.fetchone()
        if not friend_request:
            flash("Friend request not found.", "warning")
            return redirect(url_for("friends"))
        cursor.execute("""
            UPDATE friend_requests
            SET status='accepted'
            WHERE id=%s
        """, (request_id,))
        create_social_notification(
            cursor,
            friend_request["sender_id"],
            "Friend Request Accepted",
            "Your friend request has been accepted.",
            "friend_accepted",
            "/friends"
        )
        conn.commit()
        flash("Friend request accepted!", "success")
    except Exception:
        conn.rollback()
        flash("Unable to accept request.", "danger")
        app.logger.exception("Accept request error")
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for("friends"))
@app.route(
    "/friends/reject/<int:request_id>",
    methods=["POST"]
)
def reject_friend_request(request_id):
    if not social_login_required():
        return redirect(url_for("login"))
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            DELETE FROM friend_requests
            WHERE id=%s
            AND receiver_id=%s
            AND status='pending'
        """, (request_id, social_user_id()))
        conn.commit()
        flash("Friend request rejected.", "info")
    except Exception:
        conn.rollback()
        flash("Unable to reject request.", "danger")
        app.logger.exception("Reject request error")
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for("friends"))
@app.route("/messages")
def messages():
    if not social_login_required():
        return redirect(url_for("login"))
    current_user = social_user_id()
    selected_id = request.args.get("user", type=int)
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute("""
            SELECT
                u.id AS user_id,
                u.name,
                COALESCE(
                    NULLIF(u.profile_pic, ''),
                    NULLIF(u.picture, '')
                ) AS picture,
                (
                    SELECT m.message
                    FROM messages m
                    WHERE (
                        (m.sender_id=%s AND m.receiver_id=u.id)
                        OR
                        (m.sender_id=u.id AND m.receiver_id=%s)
                    )
                    ORDER BY m.created_at DESC, m.id DESC
                    LIMIT 1
                ) AS last_message
            FROM users u
            WHERE u.id IN (
                SELECT sender_id
                FROM messages
                WHERE receiver_id=%s
                UNION
                SELECT receiver_id
                FROM messages
                WHERE sender_id=%s
            )
            ORDER BY u.name
        """, (
            current_user,
            current_user,
            current_user,
            current_user
        ))
        conversations = cursor.fetchall()
        selected_user = None
        chat_messages = []
        if selected_id and selected_id != current_user:
            if are_friends(cursor, current_user, selected_id):
                cursor.execute("""
                    SELECT
                        id,
                        name,
                        COALESCE(
                            NULLIF(profile_pic, ''),
                            NULLIF(picture, '')
                        ) AS picture
                    FROM users
                    WHERE id=%s
                """, (selected_id,))
                selected_user = cursor.fetchone()
                if selected_user:
                    cursor.execute("""
                        SELECT
                            id,
                            sender_id,
                            receiver_id,
                            message,
                            created_at
                        FROM messages
                        WHERE (
                            (sender_id=%s AND receiver_id=%s)
                            OR
                            (sender_id=%s AND receiver_id=%s)
                        )
                        ORDER BY created_at ASC, id ASC
                    """, (
                        current_user,
                        selected_id,
                        selected_id,
                        current_user
                    ))
                    chat_messages = cursor.fetchall()
                    cursor.execute("""
                        UPDATE messages
                        SET is_read=1
                        WHERE sender_id=%s
                        AND receiver_id=%s
                    """, (selected_id, current_user))
                    conn.commit()
            else:
                flash("You can message your accepted friends only.", "warning")
        return render_template(
            "messages.html",
            conversations=conversations,
            selected_user=selected_user,
            messages=chat_messages
        )
    finally:
        cursor.close()
        conn.close()
@app.route("/messages/send", methods=["POST"])
def send_message():
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
    if not social_login_required():
        if is_ajax:
            return jsonify({
                "success": False,
                "error": "Please login again."
            }), 401
        return redirect(url_for("login"))
    sender_id = social_user_id()
    receiver_id = request.form.get("receiver_id", type=int)
    message = request.form.get("message", "").strip()
    if not receiver_id or not message:
        if is_ajax:
            return jsonify({
                "success": False,
                "error": "Please enter a message."
            }), 400
        flash("Please enter a message.", "warning")
        return redirect(url_for("messages"))
    if len(message) > 2000:
        if is_ajax:
            return jsonify({
                "success": False,
                "error": "Message is too long."
            }), 400
        flash("Message is too long.", "warning")
        return redirect(url_for("messages", user=receiver_id))
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        if not are_friends(cursor, sender_id, receiver_id):
            if is_ajax:
                return jsonify({
                    "success": False,
                    "error": "You can message your accepted friends only."
                }), 403
            flash("You can message your accepted friends only.", "warning")
            return redirect(url_for("messages"))
        cursor.execute("""
            INSERT INTO messages
            (sender_id, receiver_id, message)
            VALUES (%s, %s, %s)
        """, (sender_id, receiver_id, message))
        message_id = cursor.lastrowid
        cursor.execute("""
            SELECT name
            FROM users
            WHERE id = %s
        """, (sender_id,))
        sender = cursor.fetchone()
        sender_name = sender["name"] if sender else "A friend"
        create_social_notification(
            cursor,
            receiver_id,
            "New Message",
            sender_name + " sent you a message.",
            "message",
            "/messages?user=" + str(sender_id)
        )
        conn.commit()
        if is_ajax:
            return jsonify({
                "success": True,
                "message": {
                    "id": message_id,
                    "sender_id": sender_id,
                    "message": message,
                    "created_at": "Just now"
                }
            })
        flash("Message sent!", "success")
    except Exception:
        conn.rollback()
        app.logger.exception("Send message error")
        if is_ajax:
            return jsonify({
                "success": False,
                "error": "Unable to send message. Please try again."
            }), 500
        flash("Unable to send message.", "danger")
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for("messages", user=receiver_id))
@app.route("/notifications")
def notifications():
    if not social_login_required():
        return redirect(url_for("login"))
    current_user = social_user_id()
    notification_filter = request.args.get("filter", "all")
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute("""
            SELECT COUNT(*) AS unread_count
            FROM notifications
            WHERE user_id = %s
            AND is_read = 0
        """, (current_user,))
        unread_count = cursor.fetchone()["unread_count"]
        condition = ""
        if notification_filter == "unread":
            condition = "AND is_read = 0"
        elif notification_filter == "read":
            condition = "AND is_read = 1"
        cursor.execute("""
            SELECT
                id,
                title,
                message,
                type,
                link,
                is_read,
                created_at
            FROM notifications
            WHERE user_id = %s
        """ + condition + """
            ORDER BY created_at DESC
            LIMIT 100
        """, (current_user,))
        notification_list = cursor.fetchall()
        return render_template(
            "notifications.html",
            notifications=notification_list,
            unread_count=unread_count
        )
    except Exception:
        app.logger.exception("Notification fetch error")
        flash("Unable to load notifications.", "danger")
        return redirect(url_for("dashboard"))
    finally:
        cursor.close()
        conn.close()
@app.route("/debug-notifications")
def debug_notifications():
    if not social_login_required():
        return "Not logged in"
    user_id = social_user_id()
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM notifications
            WHERE user_id = %s AND is_read = 0
        """, (user_id,))
        result = cursor.fetchone()
        return {
            "logged_in_user_id": user_id,
            "unread_notifications": result["total"]
        }
    finally:
        cursor.close()
        conn.close()
@app.route("/mock-tests/create", methods=["GET", "POST"])
def create_mock_test():
    if not mock_login_required():
        return redirect(url_for("login"))
    user_id = get_mock_user_id()
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT id, course_name
            FROM mock_catalog_courses
            WHERE is_active = 1
            ORDER BY course_name
        """)
        courses = cursor.fetchall()
        cursor.execute("""
            SELECT s.id, s.course_id, s.subject_name
            FROM mock_catalog_subjects s
            INNER JOIN mock_catalog_courses c ON c.id = s.course_id
            WHERE c.is_active = 1
            ORDER BY s.subject_name
        """)
        subjects = cursor.fetchall()
        if request.method == "GET":
            return render_template(
                "mock_test/custom_create.html",
                courses=courses,
                subjects=subjects
            )
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        course_id = request.form.get("course_id", type=int)
        difficulty = request.form.get("difficulty", "Mixed")
        question_count = request.form.get("question_count", type=int)
        duration_minutes = request.form.get("duration_minutes", type=int)
        subject_ids = request.form.getlist("subject_ids")
        if not title:
            flash("Please enter test title.", "danger")
            return redirect(url_for("create_mock_test"))
        if not course_id or not question_count or not duration_minutes:
            flash("Please fill all required fields.", "danger")
            return redirect(url_for("create_mock_test"))
        if difficulty not in ["Easy", "Medium", "Hard", "Mixed"]:
            flash("Invalid difficulty selected.", "danger")
            return redirect(url_for("create_mock_test"))
        if not 1 <= question_count <= 200:
            flash("Question count must be between 1 and 200.", "danger")
            return redirect(url_for("create_mock_test"))
        if not 1 <= duration_minutes <= 300:
            flash("Duration must be between 1 and 300 minutes.", "danger")
            return redirect(url_for("create_mock_test"))
        if not subject_ids:
            flash("Please select at least one subject.", "danger")
            return redirect(url_for("create_mock_test"))
        try:
            subject_ids = list(set(int(sid) for sid in subject_ids))
        except (ValueError, TypeError):
            flash("Invalid subject selection.", "danger")
            return redirect(url_for("create_mock_test"))
        placeholders = ",".join(["%s"] * len(subject_ids))
        cursor.execute(f"""
            SELECT id
            FROM mock_catalog_subjects
            WHERE course_id = %s
            AND id IN ({placeholders})
        """, [course_id] + subject_ids)
        valid_subjects = cursor.fetchall()
        if len(valid_subjects) != len(subject_ids):
            flash("Invalid subject selection for this course.", "danger")
            return redirect(url_for("create_mock_test"))
        cursor.execute(f"""
            SELECT id
            FROM mock_question_bank
            WHERE subject_id IN ({placeholders})
            AND is_active = 1
            {"AND difficulty = %s" if difficulty != "Mixed" else ""}
        """, subject_ids + ([difficulty] if difficulty != "Mixed" else []))
        available_questions = cursor.fetchall()
        if len(available_questions) < question_count:
            flash(
                f"Only {len(available_questions)} questions are available for your selection.",
                "danger"
            )
            return redirect(url_for("create_mock_test"))
        selected_questions = random.sample(
            available_questions,
            question_count
        )
        share_token = secrets.token_urlsafe(32)
        cursor.execute("""
            INSERT INTO mock_test_catalog
            (
                creator_user_id,
                course_id,
                title,
                description,
                difficulty,
                question_count,
                duration_minutes,
                share_token,
                visibility,
                status
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            user_id,
            course_id,
            title,
            description,
            difficulty,
            question_count,
            duration_minutes,
            share_token,
            "Link",
            "Published"
        ))
        test_id = cursor.lastrowid
        cursor.execute("""
            INSERT IGNORE INTO mock_test_participants
            (test_id, user_id, status)
            VALUES (%s, %s, %s)
        """, (test_id, user_id, "Ready"))
        for subject_id in subject_ids:
            cursor.execute("""
                INSERT INTO mock_test_subjects
                (test_id, subject_id)
                VALUES (%s, %s)
            """, (test_id, subject_id))
        for index, question in enumerate(selected_questions, start=1):
            cursor.execute("""
                INSERT INTO mock_test_questions
                (
                    test_id,
                    question_id,
                    question_order,
                    marks
                )
                VALUES (%s, %s, %s, %s)
            """, (
                test_id,
                question["id"],
                index,
                1
            ))
        conn.commit()
        flash("Custom mock test created successfully!", "success")
        return redirect(
            url_for(
                "mock_test_invite",
                share_token=share_token
            )
        )
    except Exception as e:
        conn.rollback()
        print("CREATE MOCK TEST ERROR:", str(e))
        flash("Unable to create mock test. Please try again.", "danger")
        return redirect(url_for("create_mock_test"))
    finally:
        cursor.close()
        conn.close()
@app.route(
    "/notifications/read/<int:notification_id>",
    methods=["POST"]
)
def mark_notification_read(notification_id):
    if not social_login_required():
        return redirect(url_for("login"))
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE notifications
            SET is_read=1
            WHERE id=%s
            AND user_id=%s
        """, (notification_id, social_user_id()))
        conn.commit()
    except Exception:
        conn.rollback()
        app.logger.exception("Notification read error")
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for("notifications"))
@app.route(
    "/admin/pyq/courses/toggle/<int:course_id>",
    methods=["POST"]
)
def pyq_toggle_course(course_id):
    if not admin_required():
        flash("Admin access required.", "danger")
        return redirect(url_for("dashboard"))
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("""
            SELECT id, course_name, is_active
            FROM pyq_courses
            WHERE id = %s
        """, (course_id,))
        course = cursor.fetchone()
        if not course:
            flash("PYQ course not found.", "warning")
            return redirect(url_for("pyq_admin_courses"))
        new_status = 0 if course["is_active"] else 1
        cursor.execute("""
            UPDATE pyq_courses
            SET is_active = %s
            WHERE id = %s
        """, (new_status, course_id))
        conn.commit()
        if new_status == 1:
            flash(
                f"{course['course_name']} activated successfully.",
                "success"
            )
        else:
            flash(
                f"{course['course_name']} deactivated successfully.",
                "warning"
            )
        return redirect(url_for("pyq_admin_courses"))
    except Exception:
        if conn:
            conn.rollback()
        app.logger.exception("PYQ COURSE STATUS UPDATE ERROR")
        flash(
            "Unable to update course status.",
            "danger"
        )
        return redirect(url_for("pyq_admin_courses"))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
@app.route("/api/notifications/summary")
def notification_summary():
    if not social_login_required():
        return jsonify({
            "success": False,
            "error": "Login required"
        }), 401
    current_user = social_user_id()
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute("""
            SELECT COUNT(*) AS unread_count
            FROM notifications
            WHERE user_id = %s
            AND is_read = 0
        """, (current_user,))
        unread_count = cursor.fetchone()["unread_count"]
        cursor.execute("""
            SELECT
                id,
                title,
                message,
                type,
                link,
                is_read,
                created_at
            FROM notifications
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT 5
        """, (current_user,))
        notification_list = cursor.fetchall()
        for item in notification_list:
            item["created_at"] = (
                item["created_at"].strftime("%d %b, %I:%M %p")
                if item["created_at"] else ""
            )
        return jsonify({
            "success": True,
            "unread_count": unread_count,
            "notifications": notification_list
        })
    except Exception:
        app.logger.exception("Notification API error")
        return jsonify({
            "success": False,
            "error": "Unable to load notifications"
        }), 500
    finally:
        cursor.close()
        conn.close()
@app.route("/logout", methods=["GET", "POST"])
def logout():
    session.clear()
    flash("You have been logged out successfully.", "success")
    return redirect(url_for("login"))
import os
print("TEMPLATE FOLDER:", app.template_folder)
print("ROOT PATH:", app.root_path)
print("FILE EXISTS:", os.path.exists(
    os.path.join(app.root_path, "templates", "mock_tests", "my_tests.html")
))
def ensure_feedback_table(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            category VARCHAR(60) NOT NULL,
            rating TINYINT NOT NULL,
            subject VARCHAR(180) NOT NULL,
            message TEXT NOT NULL,
            is_anonymous TINYINT(1) NOT NULL DEFAULT 0,
            status VARCHAR(30) NOT NULL DEFAULT 'Pending',
            admin_reply TEXT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_feedback_user (user_id),
            INDEX idx_feedback_status (status),
            INDEX idx_feedback_created (created_at)
        )
    """)
@app.route("/feedback", methods=["GET", "POST"])
def student_feedback():

    if not session.get("user_id"):
        return redirect(url_for("login", next=request.url))

    user_id = session.get("user_id")

    categories = [
        "General Feedback",
        "Feature Request",
        "Bug Report",
        "Course Content",
        "Mock Tests",
        "Interview Preparation",
        "Other"
    ]

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        if request.method == "POST":

            category = request.form.get("category", "").strip()
            subject = request.form.get("subject", "").strip()
            message = request.form.get("message", "").strip()
            rating_value = request.form.get("rating", "").strip()
            is_anonymous = 1 if request.form.get("is_anonymous") else 0

            if category not in categories:
                flash("Please select a valid feedback category.", "error")
                return redirect(url_for("student_feedback"))

            if not rating_value.isdigit() or int(rating_value) not in range(1, 6):
                flash("Please select a rating between 1 and 5.", "error")
                return redirect(url_for("student_feedback"))

            if not subject or len(subject) > 180:
                flash("Subject is required and must be under 180 characters.", "error")
                return redirect(url_for("student_feedback"))

            if not message or len(message) > 5000:
                flash("Message is required and must be under 5000 characters.", "error")
                return redirect(url_for("student_feedback"))

            cursor.execute("""
                INSERT INTO feedback (
                    user_id,
                    category,
                    rating,
                    subject,
                    message,
                    is_anonymous,
                    status
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                user_id,
                category,
                int(rating_value),
                subject,
                message,
                is_anonymous,
                "Pending"
            ))

            conn.commit()

            flash("Your feedback has been submitted successfully!", "success")
            return redirect(url_for("student_feedback"))

        cursor.execute("""
            SELECT
                id,
                user_id,
                category,
                rating,
                subject,
                message,
                is_anonymous,
                status,
                admin_reply,
                created_at,
                updated_at
            FROM feedback
            WHERE user_id = %s
            ORDER BY created_at DESC, id DESC
        """, (user_id,))

        feedback_history = cursor.fetchall() or []

        print("FEEDBACK USER ID:", user_id)
        print("FEEDBACK HISTORY COUNT:", len(feedback_history))
        print("FEEDBACK HISTORY DATA:", feedback_history)

        return render_template(
            "feedback.html",
            feedback_history=feedback_history,
            categories=categories
        )

    except Exception as e:
        if conn:
            conn.rollback()

        print("STUDENT FEEDBACK ERROR:", str(e))

        flash("Unable to load feedback history. Please try again.", "error")
        return redirect(url_for("dashboard"))

    finally:
        if cursor:
            cursor.close()

        if conn:
            conn.close()
@app.route("/admin/feedback", methods=["GET"])
@admin_required()
def admin_feedback():

    conn = None
    cursor = None

    categories = [
        "General Feedback",
        "Feature Request",
        "Bug Report",
        "Course Content",
        "Mock Tests",
        "Interview Preparation",
        "Other"
    ]

    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        status_filter = request.args.get("status", "").strip()
        category_filter = request.args.get("category", "").strip()

        conditions = []
        params = []

        if status_filter in ["Pending", "Under Review", "Resolved"]:
            conditions.append("f.status = %s")
            params.append(status_filter)
        else:
            status_filter = ""

        if category_filter in categories:
            conditions.append("f.category = %s")
            params.append(category_filter)
        else:
            category_filter = ""

        where_sql = ""
        if conditions:
            where_sql = "WHERE " + " AND ".join(conditions)

        cursor.execute(f"""
            SELECT
                f.id,
                f.user_id,
                f.category,
                f.rating,
                f.subject,
                f.message,
                f.is_anonymous,
                f.status,
                f.admin_reply,
                f.created_at,
                f.updated_at,
                COALESCE(u.name, 'Unknown Student') AS student_name,
                COALESCE(u.email, 'Email unavailable') AS student_email
            FROM feedback f
            LEFT JOIN users u ON u.id = f.user_id
            {where_sql}
            ORDER BY f.created_at DESC, f.id DESC
            LIMIT 200
        """, tuple(params))

        feedback_items = cursor.fetchall() or []

        cursor.execute("""
            SELECT
                COUNT(*) AS total_feedback,
                COALESCE(AVG(rating), 0) AS average_rating,
                SUM(CASE WHEN status = 'Pending' THEN 1 ELSE 0 END) AS pending_count,
                SUM(CASE WHEN status = 'Under Review' THEN 1 ELSE 0 END) AS review_count,
                SUM(CASE WHEN status = 'Resolved' THEN 1 ELSE 0 END) AS resolved_count
            FROM feedback
        """)

        stats = cursor.fetchone() or {}

        return render_template(
            "admin_feedback.html",
            feedback_items=feedback_items,
            stats=stats,
            categories=categories,
            status_filter=status_filter,
            category_filter=category_filter,
            active_admin_page="feedback"
        )

    except Exception as e:
        print("ADMIN FEEDBACK ERROR:", str(e))
        flash("Unable to load feedback records.", "error")
        return redirect(url_for("admin_dashboard"))

    finally:
        if cursor:
            cursor.close()

        if conn:
            conn.close()
@app.route("/admin/feedback/<int:feedback_id>/update", methods=["POST"])
@admin_required()
def update_feedback(feedback_id):

    conn = None
    cursor = None

    try:
        status = request.form.get("status", "").strip()
        admin_reply = request.form.get("admin_reply", "").strip()

        allowed_statuses = {
            "Pending",
            "Under Review",
            "Resolved"
        }

        if status not in allowed_statuses:
            flash("Invalid feedback status.", "danger")
            return redirect(url_for("admin_feedback"))

        if len(admin_reply) > 5000:
            flash("Admin reply is too long.", "danger")
            return redirect(url_for("admin_feedback"))

        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        ensure_feedback_table(cursor)

        cursor.execute("""
            SELECT id
            FROM feedback
            WHERE id = %s
        """, (feedback_id,))

        feedback_record = cursor.fetchone()

        if not feedback_record:
            flash("Feedback record was not found.", "warning")
            return redirect(url_for("admin_feedback"))

        cursor.execute("""
            UPDATE feedback
            SET status = %s,
                admin_reply = %s
            WHERE id = %s
        """, (
            status,
            admin_reply or None,
            feedback_id
        ))

        conn.commit()

        flash("Feedback has been updated successfully.", "success")
        return redirect(url_for("admin_feedback"))

    except Exception:
        if conn:
            conn.rollback()

        app.logger.exception("UPDATE FEEDBACK ERROR")
        flash("Unable to update this feedback.", "danger")
        return redirect(url_for("admin_feedback"))

    finally:
        if cursor:
            cursor.close()

        if conn:
            conn.close()
def ensure_feedback_messages_table(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedback_messages (
            id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
            feedback_id INT NOT NULL,
            sender_user_id INT NOT NULL,
            sender_role VARCHAR(20) NOT NULL,
            message TEXT NOT NULL,
            is_read TINYINT(1) NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_feedback_messages_feedback (feedback_id),
            INDEX idx_feedback_messages_sender (sender_user_id),
            INDEX idx_feedback_messages_read (is_read)
        )
    """)

@app.route("/admin/feedback/<int:feedback_id>/chat", methods=["GET", "POST"])
@admin_required()
def admin_feedback_chat(feedback_id):

    admin_id = session.get("user_id")

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        ensure_feedback_messages_table(cursor)

        cursor.execute("""
            SELECT
                f.id,
                f.user_id,
                f.category,
                f.rating,
                f.subject,
                f.message,
                f.is_anonymous,
                f.status,
                f.admin_reply,
                f.created_at,
                CASE
                    WHEN f.is_anonymous = 1 THEN 'Anonymous Student'
                    ELSE COALESCE(u.name, 'Unknown Student')
                END AS student_name,
                CASE
                    WHEN f.is_anonymous = 1 THEN ''
                    ELSE COALESCE(u.email, '')
                END AS student_email
            FROM feedback f
            LEFT JOIN users u ON u.id = f.user_id
            WHERE f.id = %s
            LIMIT 1
        """, (feedback_id,))

        feedback = cursor.fetchone()

        if not feedback:
            flash("Feedback conversation not found.", "error")
            return redirect(url_for("admin_feedback"))

        if request.method == "POST":

            message = request.form.get("message", "").strip()

            if not message:
                flash("Please enter a message.", "error")
                return redirect(url_for(
                    "admin_feedback_chat",
                    feedback_id=feedback_id
                ))

            if len(message) > 5000:
                flash("Message cannot exceed 5000 characters.", "error")
                return redirect(url_for(
                    "admin_feedback_chat",
                    feedback_id=feedback_id
                ))

            cursor.execute("""
                INSERT INTO feedback_messages
                (
                    feedback_id,
                    sender_user_id,
                    sender_role,
                    message
                )
                VALUES (%s, %s, %s, %s)
            """, (
                feedback_id,
                admin_id,
                "admin",
                message
            ))

            conn.commit()

            return redirect(url_for(
                "admin_feedback_chat",
                feedback_id=feedback_id
            ))

        cursor.execute("""
            UPDATE feedback_messages
            SET is_read = 1
            WHERE feedback_id = %s
            AND sender_role = 'student'
        """, (feedback_id,))

        conn.commit()

        cursor.execute("""
            SELECT
                id,
                feedback_id,
                sender_user_id,
                sender_role,
                message,
                is_read,
                created_at
            FROM feedback_messages
            WHERE feedback_id = %s
            ORDER BY created_at ASC, id ASC
        """, (feedback_id,))

        chat_messages = cursor.fetchall() or []

        return render_template(
            "feedback_chat.html",
            feedback=feedback,
            messages=chat_messages,
            is_admin=True
        )

    except Exception as e:
        if conn:
            conn.rollback()

        print("ADMIN FEEDBACK CHAT ERROR:", str(e))
        flash("Unable to open the conversation.", "error")
        return redirect(url_for("admin_feedback"))

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
if __name__ == "__main__":
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
    app.run(
        host=host,
        port=port,
        debug=debug
    )
