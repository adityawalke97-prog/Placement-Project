import os
import json
import uuid
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, make_response
import pymysql
from google import genai
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from io import BytesIO

ROLES = ["Python Developer", "Java Developer", "Full Stack Developer", "Frontend Developer", "Backend Developer", "Data Analyst"]
LEVELS = ["Fresher", "Intermediate", "Advanced"]
LANGUAGES = ["English", "Hindi", "Hinglish"]

def create_interview_blueprint(get_db_connection):
    bp = Blueprint("ai_interview", __name__)
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    def current_user_id():
        return session.get("user_id")

    def db_cursor(conn):
        return conn.cursor(pymysql.cursors.DictCursor)

    def ensure_tables(cursor):
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_interview_sessions (
                id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                session_token VARCHAR(64) NOT NULL UNIQUE,
                user_id BIGINT NOT NULL,
                role VARCHAR(100) NOT NULL,
                difficulty VARCHAR(30) NOT NULL,
                language VARCHAR(30) NOT NULL,
                duration_minutes INT NOT NULL,
                overall_score INT NULL,
                technical_score INT NULL,
                communication_score INT NULL,
                confidence_score INT NULL,
                problem_solving_score INT NULL,
                performance_status VARCHAR(60) NULL,
                summary TEXT NULL,
                total_questions INT NOT NULL DEFAULT 0,
                attempted_questions INT NOT NULL DEFAULT 0,
                report_json LONGTEXT NULL,
                status VARCHAR(30) NOT NULL DEFAULT 'In Progress',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP NULL,
                INDEX idx_ai_interview_user (user_id),
                INDEX idx_ai_interview_created (created_at)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_interview_answers (
                id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                session_token VARCHAR(64) NOT NULL,
                user_id BIGINT NOT NULL,
                question_number INT NOT NULL,
                question_text TEXT NOT NULL,
                answer_text LONGTEXT NULL,
                expected_answer LONGTEXT NULL,
                score INT NULL,
                feedback TEXT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_ai_answers_session (session_token),
                INDEX idx_ai_answers_user (user_id)
            )
        """)

    def gemini_client():
        key = os.getenv("GEMINI_API_KEY")
        if not key:
            raise RuntimeError("GEMINI_API_KEY is missing in environment variables.")
        return genai.Client(api_key=key)

    def generate_json(prompt):
        client = gemini_client()
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "temperature": 0.5
            }
        )
        raw = response.text or "{}"
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            start = raw.find("{")
            end = raw.rfind("}")
            if start >= 0 and end > start:
                return json.loads(raw[start:end + 1])
            raise RuntimeError("Gemini returned an invalid JSON response.")

    def load_session(token, user_id):
        conn = get_db_connection()
        try:
            cursor = db_cursor(conn)
            ensure_tables(cursor)
            cursor.execute(
                "SELECT * FROM ai_interview_sessions WHERE session_token=%s AND user_id=%s",
                (token, user_id)
            )
            row = cursor.fetchone()
            return row
        finally:
            conn.close()

    @bp.route("/interview", methods=["GET"])
    def interview_home():
        if not current_user_id():
            return redirect(url_for("login", next=request.url))
        return render_template("interview.html", roles=ROLES, levels=LEVELS, languages=LANGUAGES)

    @bp.route("/ai-interview/start", methods=["POST"])
    def start_interview():
        if not current_user_id():
            return jsonify({"error": "Please log in again."}), 401
        data = request.get_json(silent=True) or {}
        role = data.get("role")
        difficulty = data.get("difficulty")
        language = data.get("language", "English")
        duration = data.get("duration", 15)
        if role not in ROLES or difficulty not in LEVELS or language not in LANGUAGES:
            return jsonify({"error": "Invalid interview settings."}), 400
        try:
            duration = max(10, min(30, int(duration)))
        except (TypeError, ValueError):
            duration = 15
        try:
            generated = generate_json(
                "Act as a professional technical interviewer. Create exactly 5 original interview questions for "
                + role + " at " + difficulty + " level. Use " + language + " for the questions. "
                "Return JSON with key questions, an array of objects each containing question and focus_area. "
                "Questions must be specific to the selected role, progressively challenging, and suitable for a real placement interview."
            )
            questions = generated.get("questions", [])
            if len(questions) < 3:
                raise RuntimeError("AI did not generate enough interview questions.")
            token = uuid.uuid4().hex
            conn = get_db_connection()
            try:
                cursor = db_cursor(conn)
                ensure_tables(cursor)
                cursor.execute(
                    """INSERT INTO ai_interview_sessions
                    (session_token,user_id,role,difficulty,language,duration_minutes,total_questions,status)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,'In Progress')""",
                    (token, current_user_id(), role, difficulty, language, duration, len(questions))
                )
                conn.commit()
            finally:
                conn.close()
            session["active_ai_interview"] = {
                "token": token,
                "questions": questions,
                "index": 0,
                "answers": []
            }
            return jsonify({
                "token": token,
                "total_questions": len(questions),
                "question": questions[0].get("question", ""),
                "question_number": 1,
                "focus_area": questions[0].get("focus_area", "")
            })
        except Exception as exc:
            return jsonify({"error": str(exc)}), 500

    @bp.route("/ai-interview/answer", methods=["POST"])
    def save_answer():
        if not current_user_id():
            return jsonify({"error": "Please log in again."}), 401
        active = session.get("active_ai_interview")
        data = request.get_json(silent=True) or {}
        if not active or data.get("token") != active.get("token"):
            return jsonify({"error": "Interview session not found. Start a new interview."}), 400
        answer = (data.get("answer") or "").strip()
        if not answer:
            return jsonify({"error": "Please provide an answer before continuing."}), 400
        index = active["index"]
        questions = active["questions"]
        if index >= len(questions):
            return jsonify({"error": "All questions have already been answered."}), 400
        question = questions[index]
        active["answers"].append({
            "question": question.get("question", ""),
            "focus_area": question.get("focus_area", ""),
            "answer": answer
        })
        active["index"] += 1
        session["active_ai_interview"] = active
        conn = get_db_connection()
        try:
            cursor = db_cursor(conn)
            ensure_tables(cursor)
            cursor.execute(
                """INSERT INTO ai_interview_answers
                (session_token,user_id,question_number,question_text,answer_text)
                VALUES (%s,%s,%s,%s,%s)""",
                (active["token"], current_user_id(), index + 1, question.get("question", ""), answer)
            )
            conn.commit()
        finally:
            conn.close()
        if active["index"] < len(questions):
            next_question = questions[active["index"]]
            return jsonify({
                "complete": False,
                "question": next_question.get("question", ""),
                "question_number": active["index"] + 1,
                "total_questions": len(questions),
                "focus_area": next_question.get("focus_area", "")
            })
        return jsonify({"complete": True, "message": "All questions answered. Submit your interview for AI evaluation."})

    @bp.route("/ai-interview/finish", methods=["POST"])
    def finish_interview():
        if not current_user_id():
            return jsonify({"error": "Please log in again."}), 401
        active = session.get("active_ai_interview")
        data = request.get_json(silent=True) or {}
        if not active or data.get("token") != active.get("token"):
            return jsonify({"error": "Interview session not found."}), 400
        if not active["answers"]:
            return jsonify({"error": "Answer at least one question before submitting."}), 400
        token = active["token"]
        conn = get_db_connection()
        try:
            cursor = db_cursor(conn)
            ensure_tables(cursor)
            cursor.execute(
                "SELECT role,difficulty,language,duration_minutes FROM ai_interview_sessions WHERE session_token=%s AND user_id=%s",
                (token, current_user_id())
            )
            details = cursor.fetchone()
            if not details:
                return jsonify({"error": "Interview record not found."}), 404
            prompt = (
                "Evaluate this technical mock interview fairly as a senior placement interviewer. "
                "Do not infer voice confidence or body language from text; assess confidence only from clarity and certainty of wording. "
                "Score each answer from 0 to 10. Overall and category scores must be integers from 0 to 100. "
                "Do not invent content from the candidate. Be constructive and specific. "
                "Return JSON with keys overall_score, technical_score, communication_score, confidence_score, "
                "problem_solving_score, performance_status, summary, strengths (array of strings), "
                "weaknesses (array of strings), recommendations (array of strings), "
                "questions (array of objects containing question, answer, expected_answer, score, feedback). "
                "Role: " + details["role"] + ". Difficulty: " + details["difficulty"] + ". Language: " + details["language"] +
                ". Interview answers: " + json.dumps(active["answers"], ensure_ascii=False)
            )
            report = generate_json(prompt)
            numeric_keys = ["overall_score", "technical_score", "communication_score", "confidence_score", "problem_solving_score"]
            for key in numeric_keys:
                try:
                    report[key] = max(0, min(100, int(report.get(key, 0))))
                except (TypeError, ValueError):
                    report[key] = 0
            report["questions"] = report.get("questions", [])
            report["strengths"] = report.get("strengths", [])
            report["weaknesses"] = report.get("weaknesses", [])
            report["recommendations"] = report.get("recommendations", [])
            for idx, item in enumerate(report["questions"]):
                if idx < len(active["answers"]):
                    item["question"] = active["answers"][idx]["question"]
                    item["answer"] = active["answers"][idx]["answer"]
            report["role"] = details["role"]
            report["difficulty"] = details["difficulty"]
            report["duration"] = str(details["duration_minutes"]) + " minutes"
            report["total_questions"] = len(active["questions"])
            report["attempted_questions"] = len(active["answers"])
            report["created_at"] = datetime.now().strftime("%d %b %Y, %I:%M %p")
            report["correct_answers"] = sum(1 for q in report["questions"] if int(q.get("score") or 0) >= 7)
            report["weak_answers"] = sum(1 for q in report["questions"] if int(q.get("score") or 0) < 5)
            cursor.execute(
                """UPDATE ai_interview_sessions SET overall_score=%s,technical_score=%s,
                communication_score=%s,confidence_score=%s,problem_solving_score=%s,
                performance_status=%s,summary=%s,attempted_questions=%s,report_json=%s,
                status='Completed',completed_at=NOW() WHERE session_token=%s AND user_id=%s""",
                (
                    report["overall_score"], report["technical_score"], report["communication_score"],
                    report["confidence_score"], report["problem_solving_score"],
                    str(report.get("performance_status", "Evaluated")),
                    str(report.get("summary", "")),
                    len(active["answers"]), json.dumps(report, ensure_ascii=False), token, current_user_id()
                )
            )
            for idx, item in enumerate(report["questions"]):
                cursor.execute(
                    """UPDATE ai_interview_answers SET expected_answer=%s,score=%s,feedback=%s
                    WHERE session_token=%s AND user_id=%s AND question_number=%s""",
                    (item.get("expected_answer", ""), item.get("score", 0), item.get("feedback", ""), token, current_user_id(), idx + 1)
                )
            conn.commit()
            session.pop("active_ai_interview", None)
            return jsonify({"redirect": url_for("ai_interview.interview_result", token=token)})
        except Exception as exc:
            conn.rollback()
            return jsonify({"error": str(exc)}), 500
        finally:
            conn.close()

    @bp.route("/ai-interview/result/<token>")
    def interview_result(token):
        if not current_user_id():
            return redirect(url_for("login", next=request.url))
        conn = get_db_connection()
        try:
            cursor = db_cursor(conn)
            ensure_tables(cursor)
            cursor.execute(
                "SELECT * FROM ai_interview_sessions WHERE session_token=%s AND user_id=%s AND status='Completed'",
                (token, current_user_id())
            )
            record = cursor.fetchone()
            if not record:
                return "Interview result not found.", 404
            report = json.loads(record["report_json"] or "{}")
            return render_template(
                "interview_result.html",
                result=report,
                questions=report.get("questions", []),
                strengths=report.get("strengths", []),
                weaknesses=report.get("weaknesses", []),
                recommendations=report.get("recommendations", [])
            )
        finally:
            conn.close()

    @bp.route("/ai-interview/history")
    def interview_history():
        if not current_user_id():
            return redirect(url_for("login", next=request.url))
        conn = get_db_connection()
        try:
            cursor = db_cursor(conn)
            ensure_tables(cursor)
            cursor.execute(
                """SELECT session_token,role,difficulty,overall_score,performance_status,
                created_at,completed_at FROM ai_interview_sessions
                WHERE user_id=%s AND status='Completed' ORDER BY completed_at DESC LIMIT 50""",
                (current_user_id(),)
            )
            records = cursor.fetchall()
            return render_template("interview_history.html", interviews=records)
        finally:
            conn.close()

    @bp.route("/ai-interview/report/<token>.pdf")
    def interview_pdf(token):
        if not current_user_id():
            return redirect(url_for("login", next=request.url))
        conn = get_db_connection()
        try:
            cursor = db_cursor(conn)
            ensure_tables(cursor)
            cursor.execute(
                "SELECT report_json FROM ai_interview_sessions WHERE session_token=%s AND user_id=%s AND status='Completed'",
                (token, current_user_id())
            )
            row = cursor.fetchone()
            if not row:
                return "Interview result not found.", 404
            report = json.loads(row["report_json"] or "{}")
        finally:
            conn.close()
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=18*mm, leftMargin=18*mm, topMargin=18*mm, bottomMargin=18*mm)
        styles = getSampleStyleSheet()
        story = [
            Paragraph("AI Interview Performance Report", styles["Title"]),
            Spacer(1, 8),
            Paragraph("Role: " + str(report.get("role", "")) + " | Level: " + str(report.get("difficulty", "")), styles["Normal"]),
            Spacer(1, 10)
        ]
        score_data = [
            ["Overall", "Technical", "Communication", "Confidence", "Problem Solving"],
            [str(report.get("overall_score", "--")), str(report.get("technical_score", "--")),
             str(report.get("communication_score", "--")), str(report.get("confidence_score", "--")),
             str(report.get("problem_solving_score", "--"))]
        ]
        table = Table(score_data, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#5140cb")),
            ("TEXTCOLOR", (0,0), (-1,0), colors.white),
            ("GRID", (0,0), (-1,-1), .4, colors.lightgrey),
            ("ALIGN", (0,0), (-1,-1), "CENTER"),
            ("PADDING", (0,0), (-1,-1), 8)
        ]))
        story.extend([table, Spacer(1, 14), Paragraph("Summary", styles["Heading2"]), Paragraph(str(report.get("summary", "")), styles["BodyText"]), Spacer(1, 10)])
        for heading, key in [("Strengths", "strengths"), ("Areas to Improve", "weaknesses"), ("Recommendations", "recommendations")]:
            story.append(Paragraph(heading, styles["Heading2"]))
            for item in report.get(key, []):
                story.append(Paragraph("• " + str(item), styles["BodyText"]))
            story.append(Spacer(1, 8))
        story.append(Paragraph("Question-wise Evaluation", styles["Heading2"]))
        for i, item in enumerate(report.get("questions", []), 1):
            story.append(Paragraph("Q" + str(i) + ". " + str(item.get("question", "")), styles["Heading3"]))
            story.append(Paragraph("Your answer: " + str(item.get("answer", "")), styles["BodyText"]))
            story.append(Paragraph("Expected answer: " + str(item.get("expected_answer", "")), styles["BodyText"]))
            story.append(Paragraph("Score: " + str(item.get("score", "--")) + "/10", styles["BodyText"]))
            story.append(Paragraph("Feedback: " + str(item.get("feedback", "")), styles["BodyText"]))
            story.append(Spacer(1, 8))
        doc.build(story)
        response = make_response(buffer.getvalue())
        response.headers["Content-Type"] = "application/pdf"
        response.headers["Content-Disposition"] = 'attachment; filename="AI_Interview_Report.pdf"'
        return response

    return bp
