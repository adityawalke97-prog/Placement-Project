from flask import Blueprint, render_template, request, redirect, session, flash
from app import mysql, bcrypt

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute(
            "SELECT * FROM users WHERE email=%s",
            (email,)
        )

        user = cur.fetchone()
        cur.close()

        if user and bcrypt.check_password_hash(
            user[3],
            password
        ):
            session['user_id'] = user[0]
            session['name'] = user[1]

            return redirect('/dashboard')

        flash("Invalid Email or Password")

    return render_template('login.html')


@auth.route('/signup', methods=['GET', 'POST'])
def signup():

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        password = bcrypt.generate_password_hash(
            password
        ).decode('utf-8')

        cur = mysql.connection.cursor()

        cur.execute(
            """
            INSERT INTO users(name,email,password)
            VALUES(%s,%s,%s)
            """,
            (name, email, password)
        )

        mysql.connection.commit()
        cur.close()

        flash("Account Created Successfully")
        return redirect('/login')

    return render_template('signup.html')


@auth.route('/logout')
def logout():
    session.clear()
    return redirect('/')