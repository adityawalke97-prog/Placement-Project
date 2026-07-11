from flask import Blueprint, render_template

interview = Blueprint(
    'interview',
    __name__
)

@interview.route('/interview_questions')
def interview_questions():
    return render_template(
        'interview_questions.html'
    )