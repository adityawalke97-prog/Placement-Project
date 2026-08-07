from flask import (
    Flask,
    render_template,
    request,
    redirect,
    session,
    flash,
    send_file,
    Response,
    url_for
)

from authlib.integrations.flask_client import OAuth
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv
from werkzeug.middleware.proxy_fix import ProxyFix
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

# --------------------------------------------------
# LOAD ENV
# --------------------------------------------------

load_dotenv()

# --------------------------------------------------
# FLASK APP
# --------------------------------------------------

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

        port=int(os.getenv("DB_PORT",4000)),

        ssl={
            "ca":"/etc/ssl/certs/ca-certificates.crt"
        },

        connect_timeout=30,

        cursorclass=pymysql.cursors.DictCursor

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
        "scope":"openid email profile"
    }

)

# --------------------------------------------------
# HOME
# --------------------------------------------------
# --------------------------------------------------
# HOME
# --------------------------------------------------

# --------------------------------------------------
# HOME
# --------------------------------------------------

@app.route("/")
def home():
    return redirect("/login")


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

        existing = cur.fetchone()

        if existing:

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

            session["user_id"] = existing["id"]
            session["name"] = existing["name"]
            session["email"] = existing["email"]
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

        return redirect("/dashboard")

    except Exception as e:

        print("GOOGLE LOGIN ERROR:", e)

        flash("Google Login Failed", "danger")

        return redirect("/login")


# --------------------------------------------------
# SIGNUP
# --------------------------------------------------

@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            "SELECT id FROM users WHERE email=%s",
            (email,)
        )

        if cur.fetchone():

            flash("Email already exists", "danger")

            cur.close()
            conn.close()

            return redirect("/login")

        password = bcrypt.generate_password_hash(
            password
        ).decode("utf-8")

        cur.execute("""
            INSERT INTO users
            (name,email,password)
            VALUES(%s,%s,%s)
        """, (
            name,
            email,
            password
        ))

        conn.commit()

        cur.close()
        conn.close()

        flash("Account Created Successfully", "success")

        return redirect("/login")

    return render_template("signup.html")

@app.route("/resume_builder", methods=["GET", "POST"])
@login_required
def resume_builder():
    if request.method == "POST":
        # Resume data save/generate
        return redirect(url_for("dashboard"))

    return render_template("resume_builder.html")
# --------------------------------------------------
# LOGIN
# --------------------------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

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

            session["user_id"] = user["id"]
            session["name"] = user["name"]
            session["email"] = user["email"]
            session["profile_pic"] = user.get("profile_pic")

            return redirect("/dashboard")

        flash("Invalid Email or Password", "danger")

    return render_template("login.html")

# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------

@app.route("/dashboard")
def dashboard():


    return render_template(

        "dashboard.html",

        logged_in="user_id" in session,

        name=session.get("name"),

        profile_pic=session.get(
            "profile_pic"
        )

    )




# ==============================
# INTERVIEW QUESTIONS
# ==============================


@app.route("/interview_questions")
def interview_questions():


    page = request.args.get(
        "page",
        1,
        type=int
    )


    per_page = 20

    offset = (
        page - 1
    ) * per_page



    conn = get_db_connection()

    cur = conn.cursor()



    cur.execute("""

    SELECT COUNT(*) AS total

    FROM interview_questions

    """)


    total = cur.fetchone()["total"]



    total_pages = math.ceil(
        total / per_page
    )



    cur.execute("""

    SELECT

        id,
        question,
        answer,
        category


    FROM interview_questions


    ORDER BY id


    LIMIT %s OFFSET %s


    """,

    (
        per_page,
        offset
    ))



    questions = cur.fetchall()



    cur.close()

    conn.close()



    return render_template(

        "interview_questions.html",

        questions=questions,

        page=page,

        total_pages=total_pages

    )





# ==============================
# MOCK TEST
# ==============================


@app.route('/mock_test')
def mock_test():

    category = request.args.get('category')

    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    if category:
        cursor.execute("""
            SELECT *
            FROM mock_questions
            WHERE category=%s
            ORDER BY RAND()
            LIMIT 20
        """, (category,))
    else:
        cursor.execute("""
            SELECT *
            FROM mock_questions
            ORDER BY RAND()
            LIMIT 20
        """)

    questions = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        'mock_test.html',
        questions=questions,
        category=category
    )
# ==============================
# SUBMIT MOCK TEST
# ==============================


@app.route(
    "/submit_test",
    methods=["POST"]
)

def submit_test():


    if "user_id" not in session:

        return redirect("/login")



    conn = get_db_connection()

    cur = conn.cursor()



    cur.execute("""

    SELECT

        id,

        correct_answer


    FROM mock_questions


    LIMIT 20


    """)



    answers = cur.fetchall()



    score = 0

    total = len(answers)



    for q in answers:


        question_id = q["id"]

        correct = q["correct_answer"]



        user_answer = request.form.get(

            f"q{question_id}"

        )



        if user_answer == correct:

            score += 1



    percentage = 0


    if total > 0:

        percentage = (
            score / total
        ) * 100




    cur.execute("""

    INSERT INTO results

    (

        user_id,

        total_questions,

        score,

        percentage

    )


    VALUES

    (%s,%s,%s,%s)


    """,

    (

        session["user_id"],

        total,

        score,

        percentage

    ))



    conn.commit()



    cur.close()

    conn.close()



    return render_template(

        "result.html",

        score=score,

        total=total,

        percentage=round(
            percentage,
            2
        )

    )
    # ==============================
# SAVE RESUME
# ==============================

@app.route("/save_resume", methods=["POST"])
def save_resume():

    if "user_id" not in session:
        return redirect("/login")


    name = request.form["name"]
    email = request.form["email"]
    mobile = request.form["mobile"]

    objective = request.form["objective"]

    education = request.form["education"]

    skills = request.form["skills"]

    projects = request.form["projects"]

    certifications = request.form["certifications"]



    conn = get_db_connection()

    cur = conn.cursor()



    cur.execute("""

    INSERT INTO resume

    (

    user_id,

    name,

    email,

    mobile,

    objective,

    education,

    skills,

    projects,

    certifications

    )


    VALUES

    (%s,%s,%s,%s,%s,%s,%s,%s,%s)


    """,

    (

        session["user_id"],

        name,

        email,

        mobile,

        objective,

        education,

        skills,

        projects,

        certifications

    ))



    conn.commit()

    cur.close()

    conn.close()



    flash(
        "Resume Saved Successfully",
        "success"
    )


    return redirect("/dashboard")





# ==============================
# ADMIN ADD QUESTIONS
# ==============================


@app.route(
    "/admin/questions",
    methods=["GET","POST"]
)

def admin_questions():


    if request.method == "POST":


        question = request.form["question"]

        option1 = request.form["option1"]

        option2 = request.form["option2"]

        option3 = request.form["option3"]

        option4 = request.form["option4"]

        answer = request.form["answer"]

        category = request.form["category"]




        conn = get_db_connection()

        cur = conn.cursor()



        cur.execute("""

        INSERT INTO mock_questions

        (

        question,

        option1,

        option2,

        option3,

        option4,

        correct_answer,

        category

        )


        VALUES

        (%s,%s,%s,%s,%s,%s,%s)


        """,

        (

            question,

            option1,

            option2,

            option3,

            option4,

            answer,

            category

        ))



        conn.commit()


        cur.close()

        conn.close()



        flash(
            "Question Added Successfully",
            "success"
        )


        return redirect(
            "/admin/questions"
        )



    return render_template(
        "admin_questions.html"
    )





# ==============================
# LEADERBOARD
# ==============================


@app.route("/leaderboard")
def leaderboard():


    conn = get_db_connection()

    cur = conn.cursor()



    cur.execute("""

    SELECT

        users.name,

        results.score,

        results.percentage


    FROM results


    JOIN users

    ON users.id = results.user_id


    ORDER BY score DESC


    """)



    data = cur.fetchall()



    cur.close()

    conn.close()



    return render_template(

        "leaderboard.html",

        data=data

    )





# ==============================
# RESUME PDF
# ==============================


@app.route(
    "/resume/pdf/<int:user_id>"
)

def resume_pdf(user_id):


    conn = get_db_connection()

    cur = conn.cursor()



    cur.execute("""

    SELECT

        name,

        email,

        mobile,

        objective,

        education,

        skills,

        projects,

        certifications


    FROM resume


    WHERE user_id=%s


    """,

    (user_id,))



    resume = cur.fetchone()



    cur.close()

    conn.close()



    if not resume:

        flash(
            "Resume not found",
            "danger"
        )

        return redirect(
            "/dashboard"
        )



    os.makedirs(
        "uploads",
        exist_ok=True
    )



    filename = f"resume_{user_id}.pdf"



    filepath = os.path.join(

        "uploads",

        filename

    )



    doc = SimpleDocTemplate(
        filepath
    )


    styles = getSampleStyleSheet()



    elements = []



    elements.append(

        Paragraph(

            resume["name"],

            styles["Title"]

        )

    )



    elements.append(

        Paragraph(

            "Email: " + resume["email"],

            styles["Normal"]

        )

    )


    elements.append(

        Paragraph(

            "Mobile: " + resume["mobile"],

            styles["Normal"]

        )

    )



    sections = [

        ("Career Objective", resume["objective"]),

        ("Education", resume["education"]),

        ("Skills", resume["skills"]),

        ("Projects", resume["projects"]),

        ("Certifications", resume["certifications"])

    ]



    for title,text in sections:


        elements.append(

            Spacer(1,20)

        )


        elements.append(

            Paragraph(

                title,

                styles["Heading2"]

            )

        )


        elements.append(

            Paragraph(

                text,

                styles["Normal"]

            )

        )



    doc.build(elements)



    return send_file(

        filepath,

        as_attachment=True

    )






# ==============================
# CERTIFICATE PDF
# ==============================


@app.route(
    "/certificate/<int:user_id>"
)

def certificate(user_id):


    conn = get_db_connection()

    cur = conn.cursor()



    cur.execute(

        "SELECT name FROM users WHERE id=%s",

        (user_id,)

    )


    user = cur.fetchone()



    cur.execute("""

    SELECT MAX(score) AS score

    FROM results

    WHERE user_id=%s


    """,

    (user_id,))



    result = cur.fetchone()



    cur.close()

    conn.close()



    if not user:

        return "User not found"



    score = result["score"] or 0



    os.makedirs(

        "uploads",

        exist_ok=True

    )



    filename = f"certificate_{user_id}.pdf"



    filepath = os.path.join(

        "uploads",

        filename

    )



    doc = SimpleDocTemplate(
        filepath
    )


    styles = getSampleStyleSheet()



    elements = []



    elements.append(

        Paragraph(

            "Certificate of Completion",

            styles["Title"]

        )

    )


    elements.append(

        Spacer(1,40)

    )


    elements.append(

        Paragraph(

            f"This certificate is awarded to <b>{user['name']}</b>",

            styles["Heading2"]

        )

    )



    elements.append(

        Spacer(1,20)

    )



    elements.append(

        Paragraph(

            f"Completed Placement Training Test with score <b>{score}</b>",

            styles["Normal"]

        )

    )


    elements.append(

        Spacer(1,30)

    )


    elements.append(

        Paragraph(

            "Placement Training Portal",

            styles["Heading3"]

        )

    )



    doc.build(elements)



    return send_file(

        filepath,

        as_attachment=True

    )



# ==============================
# DOWNLOAD HISTORY CSV
# ==============================

@app.route("/download_history")
def download_history():

    if "user_id" not in session:

        return redirect("/login")


    conn = get_db_connection()

    cur = conn.cursor()



    cur.execute("""

    SELECT

        subject,
        score,
        total_questions,
        percentage,
        attempt_date


    FROM results


    WHERE user_id=%s


    ORDER BY attempt_date DESC


    """,

    (
        session["user_id"],
    ))



    history = cur.fetchall()



    cur.close()

    conn.close()



    output = io.StringIO()


    writer = csv.writer(output)



    writer.writerow([

        "Subject",

        "Score",

        "Total Questions",

        "Percentage",

        "Attempt Date"

    ])



    for row in history:


        writer.writerow([

            row.get("subject","Mock Test"),

            row["score"],

            row["total_questions"],

            row["percentage"],

            row["attempt_date"]

        ])



    return Response(

        output.getvalue(),

        mimetype="text/csv",

        headers={

            "Content-Disposition":

            "attachment; filename=mock_test_history.csv"

        }

    )





# ==============================
# COURSES
# ==============================

@app.route("/courses")
def courses():

    return redirect(
        "/course/Java"
    )

@app.route("/quiz/<course>/<int:day>")
def course_quiz(course,day):


    return render_template(

        "quiz.html",

        course=course,

        day=day

    )
@app.route("/my-learning")
def my_learning():


    if "user_id" not in session:

        return redirect("/login")



    conn=get_db_connection()

    cursor=conn.cursor(
        pymysql.cursors.DictCursor
    )


    cursor.execute(

    """
    SELECT *
    FROM learning_progress
    WHERE user_id=%s

    """,

    (
    session["user_id"],
    )

    )


    progress=cursor.fetchall()


    cursor.close()

    conn.close()



    return render_template(

        "my_learning.html",

        progress=progress

    )
@app.route("/course/<course_name>")
def course_page(course_name):

    conn = get_db_connection()

    cursor = conn.cursor(
        pymysql.cursors.DictCursor
    )


    cursor.execute(
        """
        SELECT *
        FROM course_content
        WHERE course_name=%s
        ORDER BY day_number
        """,
        (course_name,)
    )


    lessons = cursor.fetchall()


    cursor.close()
    conn.close()



    return render_template(
        "course.html",
        course_name=course_name,
        lessons=lessons,
        day_count=len(lessons)
    )
@app.route("/save-progress", methods=["POST"])
def save_progress():

    if "user_id" not in session:
        return {
            "status":"error",
            "message":"Login required"
        },401


    data = request.get_json()


    user_id = session["user_id"]

    course = data.get("course")

    day = data.get("day",1)

    xp = data.get("xp",0)

    streak = data.get("streak",1)



    try:

        conn = get_db_connection()

        cursor = conn.cursor()



        sql = """

        INSERT INTO learning_progress
        (
        user_id,
        course,
        day,
        xp,
        streak
        )

        VALUES
        (%s,%s,%s,%s,%s)


        ON DUPLICATE KEY UPDATE

        day=%s,
        xp=%s,
        streak=%s

        """



        cursor.execute(
            sql,
            (

            user_id,
            course,
            day,
            xp,
            streak,


            day,
            xp,
            streak

            )
        )


        conn.commit()



        cursor.close()

        conn.close()



        return {

            "status":"success",

            "message":
            "Progress saved"

        }



    except Exception as e:


        print(e)


        return {

            "status":"error",

            "message":
            str(e)

        },500

@app.route("/courses/java")
def java_course():


    conn = get_db_connection()

    cur = conn.cursor()



    cur.execute("""

    SELECT

        day,

        title,

        notes,

        code_snippet,

        practice_task


    FROM java_course


    ORDER BY day


    """)



    rows = cur.fetchall()



    cur.close()

    conn.close()



    course_data = {}



    for row in rows:


        course_data[row["day"]] = {


            "title": row["title"],

            "notes": row["notes"],

            "code_snippet": row["code_snippet"],

            "practice_task": row["practice_task"]

        }



    return render_template(

        "java.html",

        day_count=len(course_data),

        course_data_json=json.dumps(course_data)

    )





@app.route("/courses/python")
def python_course():

    return render_template(
        "python.html"
    )



@app.route("/courses/html")
def html_course():

    return render_template(
        "html.html"
    )



@app.route("/courses/css")
def css_course():

    return render_template(
        "css.html"
    )



@app.route("/courses/fullstack-java")
def fullstack_java():

    return render_template(
        "fullstack_java.html"
    )



@app.route("/courses/fullstack-python")
def fullstack_python():

    return render_template(
        "fullstack_python.html"
    )





@app.route(
    "/courses/<course_name>/<int:day>"
)

def course_day(course_name,day):


    conn = get_db_connection()

    cur = conn.cursor()



    cur.execute("""

    SELECT notes

    FROM course_notes


    WHERE course_name=%s

    AND day_number=%s


    """,

    (

        course_name,

        day

    ))



    result = cur.fetchone()



    cur.close()

    conn.close()



    if result:

        notes = result["notes"]

    else:

        notes = "No notes available."



    return render_template(

        "course_day.html",

        course_name=course_name,

        day=day,

        notes=notes

    )





# ==============================
# MOCK CATEGORY
# ==============================


@app.route("/mock_categories")
def mock_categories():


    conn = get_db_connection()

    cur = conn.cursor()



    cur.execute("""

    SELECT *

    FROM mock_category

    ORDER BY category_name


    """)



    categories = cur.fetchall()



    cur.close()

    conn.close()



    return render_template(

        "mock_categories.html",

        categories=categories

    )





# ==============================
# MOCK TEST HISTORY
# ==============================


@app.route("/mock_test_history")
def mock_test_history():


    if "user_id" not in session:


        flash(
            "Please login first",
            "warning"
        )


        return redirect("/login")



    conn = get_db_connection()

    cur = conn.cursor()



    cur.execute("""

    SELECT *

    FROM results


    WHERE user_id=%s


    ORDER BY id DESC


    """,

    (

        session["user_id"],

    ))



    history = cur.fetchall()



    cur.execute("""

    SELECT


        COUNT(*) AS total_tests,

        AVG(percentage) AS avg_percentage,

        MAX(score) AS highest_score


    FROM results


    WHERE user_id=%s


    """,

    (

        session["user_id"],

    ))



    stats = cur.fetchone()



    cur.close()

    conn.close()



    return render_template(

        "mock_test_history.html",

        history=history,

        total_tests=stats["total_tests"] or 0,

        avg_percentage=stats["avg_percentage"] or 0,

        highest_score=stats["highest_score"] or 0

    )





# ==============================
# VIEW RESULT
# ==============================


@app.route(
    "/result/<int:result_id>"
)

def view_result(result_id):


    if "user_id" not in session:

        return redirect("/login")



    conn = get_db_connection()

    cur = conn.cursor()



    cur.execute("""

    SELECT *

    FROM results


    WHERE id=%s

    AND user_id=%s


    """,

    (

        result_id,

        session["user_id"]

    ))



    result = cur.fetchone()



    cur.close()

    conn.close()



    if not result:

        flash(
            "Result not found",
            "danger"
        )

        return redirect(
            "/mock_test_history"
        )



    return render_template(

        "result.html",

        result=result

    )





# ==============================
# DELETE HISTORY
# ==============================


@app.route(
    "/delete_history/<int:result_id>"
)

def delete_history(result_id):


    if "user_id" not in session:

        return redirect("/login")



    conn = get_db_connection()

    cur = conn.cursor()



    cur.execute("""

    DELETE FROM results


    WHERE id=%s

    AND user_id=%s


    """,

    (

        result_id,

        session["user_id"]

    ))



    conn.commit()



    cur.close()

    conn.close()



    flash(
        "History deleted",
        "success"
    )



    return redirect(
        "/mock_test_history"
    )





# ==============================
# LOGOUT
# ==============================


@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")





# ==============================
# RUN APP
# ==============================


if __name__ == "__main__":

    app.run(

        host="0.0.0.0",

        port=int(
            os.getenv(
                "PORT",
                5000
            )
        ),

        debug=False

    )
