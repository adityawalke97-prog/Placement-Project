from flask import Blueprint, render_template

communication = Blueprint(
    'communication',
    __name__
)

@communication.route('/communication')
def communication_page():
    return render_template(
        'communication.html'
    )