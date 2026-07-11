from flask import Blueprint, render_template

resume = Blueprint(
    'resume',
    __name__
)

@resume.route('/resume_builder')
def resume_builder():
    return render_template(
        'resume_builder.html'
    )