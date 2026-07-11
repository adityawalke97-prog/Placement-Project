from flask import Blueprint, render_template
from app import mysql

leaderboard = Blueprint(
    'leaderboard',
    __name__
)

@leaderboard.route('/leaderboard')
def leaderboard_page():

    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT users.name,
               MAX(results.score)
        FROM results
        JOIN users
        ON users.id = results.user_id
        GROUP BY users.id
        ORDER BY MAX(results.score) DESC
    """)

    leaders = cur.fetchall()
    cur.close()

    return render_template(
        'leaderboard.html',
        leaders=leaders
    )