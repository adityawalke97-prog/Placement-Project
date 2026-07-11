from flask import Flask, render_template, request, redirect, session, flash
from flask_mysqldb import MySQL
from flask_bcrypt import Bcrypt
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer
)
from reportlab.lib.styles import getSampleStyleSheet
from flask import send_file
import os

app = Flask(__name__)
app.secret_key = "placement_secret_key"

app.config['MYSQL_HOST'] = 'gateway01.ap-northeast-1.prod.aws.tidbcloud.com'
app.config['MYSQL_PORT'] = 4000
app.config['MYSQL_USER'] = 'CotGjksA2G9iDYQ.root'
app.config['MYSQL_PASSWORD'] = 'YOUR_ACTUAL_PASSWORD'
app.config['MYSQL_DB'] = 'placement_training'


import pymysql
import os

conn = pymysql.connect(
    host='gateway01.ap-northeast-1.prod.aws.tidbcloud.com',
    port=4000,
    user='CotGjksA2G9iDYQ.root',
    password=os.getenv('DB_PASSWORD'),
    database='placement_training',
    ssl_verify_identity=False
)
# ---------------- HOME ----------------
@app.route('/')
def home():
    return render_template('index.html')


# ---------------- SIGNUP ----------------
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        cur = mysql.connection.cursor()
        cur.execute(
            "INSERT INTO users(name, email, password) VALUES(%s,%s,%s)",
            (name, email, hashed_password)
        )
        mysql.connection.commit()
        cur.close()

        flash("Account created successfully!")
        return redirect('/login')

    return render_template('signup.html')


# ---------------- LOGIN ----------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cur.fetchone()
        cur.close()

        if user and bcrypt.check_password_hash(user[3], password):
            session['user_id'] = user[0]
            session['name'] = user[1]
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
    if 'user_id' not in session:
        return redirect('/login')

    return render_template('interview_questions.html')


# ---------------- COMMUNICATION ----------------
@app.route('/communication')
def communication():
    if 'user_id' not in session:
        return redirect('/login')

    return render_template('communication.html')


# ---------------- RESUME BUILDER ----------------
@app.route('/resume_builder')
def resume_builder():
    if 'user_id' not in session:
        return redirect('/login')

    return render_template('resume_builder.html')
@app.route('/mock_test')
def mock_test():
    if 'user_id' not in session:
        return redirect('/login')

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM questions LIMIT 10")
    questions = cur.fetchall()
    cur.close()

    return render_template(
        'mock_test.html',
        questions=questions
    )


@app.route('/submit_test', methods=['POST'])
def submit_test():
    if 'user_id' not in session:
        return redirect('/login')

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM questions LIMIT 10")
    questions = cur.fetchall()

    score = 0

    for q in questions:
        selected = request.form.get(f'q{q[0]}')

        if selected == q[6]:
            score += 1

    cur.execute(
        """
        INSERT INTO results(user_id, score, total_questions)
        VALUES(%s,%s,%s)
        """,
        (session['user_id'], score, len(questions))
    )

    mysql.connection.commit()
    cur.close()

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

    cur = mysql.connection.cursor()

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

    mysql.connection.commit()
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

        cur = mysql.connection.cursor()

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

        mysql.connection.commit()
        cur.close()

        flash("Question Added Successfully")
        return redirect('/admin/questions')

    return render_template('admin_questions.html')
@app.route('/leaderboard')
def leaderboard():
    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT users.name,
               MAX(results.score) AS best_score
        FROM results
        JOIN users
        ON users.id = results.user_id
        GROUP BY users.id
        ORDER BY best_score DESC
        LIMIT 20
    """)

    leaders = cur.fetchall()
    cur.close()

    return render_template(
        'leaderboard.html',
        leaders=leaders
    )
    
@app.route('/resume/pdf/<int:user_id>')
def resume_pdf(user_id):

    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT name, email, mobile,
               objective, education,
               skills, projects, certifications
        FROM resume
        WHERE user_id=%s
    """, (user_id,))

    resume = cur.fetchone()
    cur.close()

    if not resume:
        flash("Resume not found")
        return redirect('/resume_builder')

    filename = f"resume_{user_id}.pdf"
    filepath = os.path.join("uploads", filename)

    doc = SimpleDocTemplate(filepath)
    styles = getSampleStyleSheet()

    elements = []

    elements.append(
        Paragraph(f"<b>{resume[0]}</b>", styles['Title'])
    )
    elements.append(
        Paragraph(f"Email: {resume[1]}", styles['Normal'])
    )
    elements.append(
        Paragraph(f"Mobile: {resume[2]}", styles['Normal'])
    )

    elements.append(Spacer(1, 20))
    elements.append(
        Paragraph("<b>Career Objective</b>",
                  styles['Heading2'])
    )
    elements.append(
        Paragraph(resume[3], styles['Normal'])
    )

    elements.append(Spacer(1, 20))
    elements.append(
        Paragraph("<b>Education</b>",
                  styles['Heading2'])
    )
    elements.append(
        Paragraph(resume[4], styles['Normal'])
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

    cur = mysql.connection.cursor()

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
# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


if __name__ == '__main__':
    app.run(debug=True)