from flask import request, jsonify, session
import json

@app.route("/api/communication/coach", methods=["POST"])
def communication_coach_api():
    if not session.get("user_id"):
        return jsonify({"success": False, "error": "Please log in again to use the communication coach."}), 401

    data = request.get_json(silent=True) or {}
    mode = (data.get("mode") or "").strip().lower()

    if mode == "chat":
        message = (data.get("message") or "").strip()
        if not message or len(message) > 600:
            return jsonify({"success": False, "error": "Enter a question of up to 600 characters."}), 400

        prompt = f"""
You are a patient, practical English communication coach for a college student preparing for internships and placement interviews.
Help the student communicate in clear, natural, professional English. Be encouraging but honest.
Use simple explanations. If the student writes an incorrect sentence, show a corrected natural version and briefly explain the change.
Give realistic examples and invite the student to practise. Do not claim to hear pronunciation or analyse audio; you only receive text.
Student message: {message}
Reply in a concise, useful way.
"""
        try:
            response = gemini_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            return jsonify({"success": True, "reply": (response.text or "").strip()})
        except Exception:
            app.logger.exception("Communication coach chat failed")
            return jsonify({"success": False, "error": "AI coach is temporarily unavailable. Check the Gemini API configuration and server logs."}), 503

    if mode == "evaluate":
        answer = (data.get("answer") or "").strip()
        speaking_prompt = (data.get("prompt") or "").strip()
        scenario = (data.get("scenario") or "general").strip()
        if len(answer) < 15 or len(answer) > 8000:
            return jsonify({"success": False, "error": "Your answer must contain 15 to 8,000 characters."}), 400

        instruction = f"""
You are an expert spoken-English and workplace communication coach helping a college student prepare for placement interviews.
Review the student's transcript for communication quality only. The transcript may contain speech-recognition errors, so do not assume every odd word is the student's mistake.
Do not infer accent, pronunciation, vocal confidence, speaking speed, body language or tone from text. State that these require audio/video assessment if relevant.
Evaluate relevance, clarity, structure, grammar, vocabulary and professional phrasing. Be specific, kind and practical.
Scenario: {scenario}
Practice prompt: {speaking_prompt}
Student transcript: {answer}

Return ONLY valid JSON with this exact structure:
{{
  "score": 0,
  "strengths": ["specific strength"],
  "improvements": ["specific improvement with an example"],
  "better_version": "A natural improved version that keeps the student's meaning and does not invent experience.",
  "next_exercise": "One short exercise the student should do next.",
  "summary": "A brief encouraging and honest coach note."
}}
Score the transcript out of 100 based on its text, not pronunciation. Keep each list to 2-4 useful items. Do not add markdown fences.
"""
        try:
            response = gemini_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=instruction
            )
            raw = (response.text or "").strip()
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
            feedback = json.loads(raw)
            score = max(0, min(100, int(feedback.get("score", 0))))
            feedback["score"] = score
            return jsonify({"success": True, "feedback": feedback})
        except (ValueError, TypeError, json.JSONDecodeError):
            app.logger.exception("Communication coach returned invalid JSON")
            return jsonify({"success": False, "error": "The AI returned an unreadable review. Please try again."}), 502
        except Exception:
            app.logger.exception("Communication coach evaluation failed")
            return jsonify({"success": False, "error": "AI feedback is temporarily unavailable. Check the Gemini API configuration and server logs."}), 503

    return jsonify({"success": False, "error": "Unsupported coach request."}), 400
