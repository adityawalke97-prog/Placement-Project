from flask import Flask, render_template, request, redirect, session, flash, send_file
from flask_bcrypt import Bcrypt
import pymysql
import os
from dotenv import load_dotenv
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# Load environment variables
load_dotenv()

# Flask App
app = Flask(__name__)
app.secret_key = "placement_secret_key"

# Initialize Bcrypt
bcrypt = Bcrypt(app)

# Database Connection
def get_db_connection():
    return pymysql.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        port=int(os.getenv("DB_PORT", 4000)),
        ssl={
            "ca": "/etc/ssl/certs/ca-certificates.crt"
        },
        connect_timeout=30,
        cursorclass=pymysql.cursors.DictCursor
    )


# ---------------- HOME ----------------
@app.route('/')
def home():
    return render_template('index.html')


# ---------------- SIGNUP ----------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()
        cur = conn.cursor()

        # Check email
        cur.execute("SELECT id FROM users WHERE email=%s", (email,))
        existing = cur.fetchone()

        if existing:
            flash("Email already registered. Please login.", "danger")
            cur.close()
            conn.close()
            return redirect("/login")

        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

        cur.execute(
            "INSERT INTO users (name, email, password) VALUES (%s,%s,%s)",
            (name, email, hashed_password)
        )

        conn.commit()
        cur.close()
        conn.close()

        flash("Account created successfully.", "success")
        return redirect("/login")

    return render_template("signup.html")
# ---------------- LOGIN ----------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cur.fetchone()
        cur.close()

        if user and bcrypt.check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['name'] = user['name']
            return redirect('/dashboard')

        flash("Invalid Email or Password")

    return render_template('login.html')


# ---------------- DASHBOARD ----------------
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')

    return render_template(
        'dashboard.html',
        name=session['name']
    )

# ---------------- INTERVIEW QUESTIONS ----------------
@app.route('/interview_questions')
def interview_questions():

    conn = get_db_connection()
    cur = conn.cursor(pymysql.cursors.DictCursor)

    cur.execute("""
        SELECT
            id,
            question,
            answer,
            category
        FROM interview_questions
        ORDER BY id
    """)

    questions = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "interview_questions.html",
        questions=questions
    )
@app.route("/mock_test")
def mock_test():

    conn = get_db_connection()  

    cur = conn.cursor()

    cur.execute("SELECT * FROM questions")

    data = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("mock_test.html", questions=data)
@app.route('/submit_test', methods=['POST'])
def submit_test():

    if 'user_id' not in session:
        return redirect('/login')

    conn = get_db_connection()   # ✅ Add this line

    cur = conn.cursor()

    cur.execute("SELECT * FROM questions LIMIT 10")
    questions = cur.fetchall()

    score = 0

    for q in questions:
        selected = request.form.get(f'q{q["id"]}')

        if selected == q['answer']:
            score += 1

    cur.execute(
        """
        INSERT INTO results(user_id, score, total_questions)
        VALUES(%s,%s,%s)
        """,
        (session['user_id'], score, len(questions))
    )

    conn.commit()

    cur.close()
    conn.close()   

    return render_template(
        'result.html',
        score=score,
        total=len(questions)
    )
@app.route('/save_resume', methods=['POST'])
def save_resume():
    if 'user_id' not in session:
        return redirect('/login')

    name = request.form['name']
    email = request.form['email']
    mobile = request.form['mobile']
    objective = request.form['objective']
    education = request.form['education']
    skills = request.form['skills']
    projects = request.form['projects']
    certifications = request.form['certifications']

    conn = get_db_connection() 

    cur = conn.cursor()
    cur.execute("""
        INSERT INTO resume
        (user_id,name,email,mobile,objective,
         education,skills,projects,certifications)
        VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        session['user_id'],
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

    flash("Resume Saved Successfully")
    return redirect('/dashboard')

@app.route('/admin/questions', methods=['GET', 'POST'])
def admin_questions():

    if request.method == 'POST':
        question = request.form['question']
        option1 = request.form['option1']
        option2 = request.form['option2']
        option3 = request.form['option3']
        option4 = request.form['option4']
        answer = request.form['answer']
        category = request.form['category']

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO questions
            (question, option1, option2,
             option3, option4, answer, category)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
        """, (
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

        flash("Question Added Successfully")
        return redirect('/admin/questions')

    return render_template('admin_questions.html')
@app.route('/leaderboard')
def leaderboard():

    conn = get_db_connection()   # ✅ Add this

    cur = conn.cursor()

    cur.execute("""
        SELECT * FROM results
        ORDER BY score DESC
    """)

    data = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "leaderboard.html",
        data=data
 )
@app.route('/resume/pdf/<int:user_id>')
def resume_pdf(user_id):

    cconn = get_db_connection() 
    cur = cconn.cursor()
    cur.execute("""
        SELECT name, email, mobile,
               objective, education,
               skills, projects, certifications
        FROM resume
        WHERE user_id=%s
    """, (user_id,))

    resume = cur.fetchone()
    cur.close()    
    cconn.close()

    if not resume:
        flash("Resume not found")
        return redirect('/resume_builder')

    filename = f"resume_{user_id}.pdf"
    filepath = os.path.join("uploads", filename)

    doc = SimpleDocTemplate(filepath)
    styles = getSampleStyleSheet()

    elements = []

    elements.append(
        Paragraph(f"<b>{resume['name']}</b>", styles['Title'])
    )
    elements.append(
        Paragraph(f"Email: {resume['email']}", styles['Normal'])
    )
    elements.append(
        Paragraph(f"Mobile: {resume['mobile']}", styles['Normal'])
    )

    elements.append(Spacer(1, 20))
    elements.append(
        Paragraph("<b>Career Objective</b>",
                  styles['Heading2'])
    )
    elements.append(
        Paragraph(resume['objective'], styles['Normal'])
    )

    elements.append(Spacer(1, 20))
    elements.append(
        Paragraph("<b>Education</b>",
                  styles['Heading2'])
    )
    elements.append(
        Paragraph(resume['education'], styles['Normal'])
    )

    elements.append(Spacer(1, 20))
    elements.append(
        Paragraph("<b>Skills</b>",
                  styles['Heading2'])
    )
    elements.append(
        Paragraph(resume[5], styles['Normal'])
    )

    elements.append(Spacer(1, 20))
    elements.append(
        Paragraph("<b>Projects</b>",
                  styles['Heading2'])
    )
    elements.append(
        Paragraph(resume[6], styles['Normal'])
    )

    elements.append(Spacer(1, 20))
    elements.append(
        Paragraph("<b>Certifications</b>",
                  styles['Heading2'])
    )
    elements.append(
        Paragraph(resume[7], styles['Normal'])
    )

    doc.build(elements)

    return send_file(
        filepath,
        as_attachment=True
    )
@app.route('/certificate/<int:user_id>')
def certificate(user_id):

    cconn = get_db_connection()
    cur = cconn.cursor()

    cur.execute(
        "SELECT name FROM users WHERE id=%s",
        (user_id,)
    )
    user = cur.fetchone()

    cur.execute("""
        SELECT MAX(score)
        FROM results
        WHERE user_id=%s
    """, (user_id,))

    result = cur.fetchone()
    cur.close()

    if not user:
        return "User not found"

    score = result[0] if result[0] else 0

    filename = f"certificate_{user_id}.pdf"
    filepath = os.path.join(
        "uploads",
        filename
    )

    doc = SimpleDocTemplate(filepath)
    styles = getSampleStyleSheet()

    elements = []

    elements.append(
        Paragraph(
            "<b>Certificate of Completion</b>",
            styles['Title']
        )
    )

    elements.append(Spacer(1, 40))

    elements.append(
        Paragraph(
            f"This certificate is awarded to <b>{user[0]}</b>",
            styles['Heading2']
        )
    )

    elements.append(Spacer(1, 20))

    elements.append(
        Paragraph(
            f"For successfully completing the Placement Training Test with score <b>{score}</b>.",
            styles['Normal']
        )
    )

    elements.append(Spacer(1, 30))

    elements.append(
        Paragraph(
            "Placement Training Portal",
            styles['Heading3']
        )
    )

    doc.build(elements)

    return send_file(
        filepath,
        as_attachment=True
    )
    
@app.route('/mock-test-history')
def mock_test_history():
    # Maan lete hain ki aapne user session me 'user_id' store kiya hai
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login')) # Agar login nahi hai toh login page par bhej do

    conn = sqlite3.connect('database.db') # Apne DB ka sahi naam likhein
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # User ke saare test attempts naye se purane (DESC) order me fetch karein
    cursor.execute('''
        SELECT subject, score, total_questions, percentage, attempt_date 
        FROM mock_tests 
        WHERE user_id = ? 
        ORDER BY attempt_date DESC
    ''', (user_id,))
    
    history = cursor.fetchall()
    conn.close()

    return render_template('mock_history.html', history=history)


@app.route("/courses")
def courses():
    return render_template("course.html")

@app.route("/courses/java")
def java_course():
    return render_template("java.html")

@app.route("/courses/python")
def python_course():
    return render_template("python.html")

@app.route("/courses/html")
def html_course():
    return render_template("html.html")

@app.route("/courses/css")
def css_course():
    return render_template("css.html")

@app.route("/courses/fullstack-java")
def fullstack_java():
    return render_template("fullstack_java.html")

@app.route("/courses/fullstack-python")
def fullstack_python():
    return render_template("fullstack_python.html")
@app.route("/courses/<course_name>/<int:day>")
def course_day(course_name, day):
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT notes FROM course_notes WHERE course_name=%s AND day_number=%s", (course_name, day))
    result = cursor.fetchone()
    cursor.close()

    if result:
        notes = result[0]
    else:
        notes = "No notes available for this day."

    return render_template("course_day.html", course_name=course_name, day=day, notes=notes)

# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", 5000)),
        debug=True
    )
