from flask import Blueprint, render_template, session, redirect

dashboard = Blueprint(
    'dashboard',
    __name__
)

@dashboard.route('/dashboard')
def home():

    if 'user_id' not in session:
        return redirect('/login')

    return render_template(
        'dashboard.html',
        name=session['name']
    )