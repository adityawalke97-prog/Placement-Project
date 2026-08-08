```python
import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise RuntimeError("OPENAI_API_KEY is missing in .env")

client = OpenAI(api_key=api_key)


def ask_ai(prompt):
    response = client.responses.create(
        model="gpt-5-mini",
        input=prompt
    )

    return response.output_text.strip()


def improve_summary(summary, target_job="Software Engineer"):
    prompt = f"""
You are a professional resume writer.

Improve the following professional summary for an ATS-friendly resume.

Target Job:
{target_job}

Current Summary:
{summary}

Rules:
- Keep it professional.
- Do not invent experience.
- Do not invent skills.
- Use strong but truthful wording.
- Keep it between 50 and 90 words.
- Return ONLY the improved summary.
"""

    return ask_ai(prompt)


def improve_experience(description, target_job="Software Engineer"):
    prompt = f"""
You are an expert technical resume writer.

Rewrite the following work experience into strong ATS-friendly bullet points.

Target Job:
{target_job}

Experience:
{description}

Rules:
- Do not invent achievements.
- Do not invent numbers.
- Use action verbs.
- Focus on technologies, responsibilities and results.
- Return 3 to 5 bullet points.
- Return ONLY bullet points.
"""

    return ask_ai(prompt)


def improve_project(description, project_name="", technologies=""):
    prompt = f"""
You are an expert software engineering resume writer.

Improve this project description.

Project:
{project_name}

Technologies:
{technologies}

Current Description:
{description}

Rules:
- Do not invent functionality.
- Do not invent metrics.
- Explain what was built.
- Mention technologies naturally.
- Highlight technical contribution.
- Make it ATS-friendly.
- Return 3 to 5 bullet points.
"""

    return ask_ai(prompt)


def suggest_skills(target_job, job_description=""):
    prompt = f"""
You are an ATS resume expert.

Suggest technical skills for this target role.

Target Job:
{target_job}

Job Description:
{job_description}

Return JSON only:

{{
    "skills": [
        "skill1",
        "skill2",
        "skill3"
    ]
}}

Only suggest skills that are relevant to the job.
"""

    result = ask_ai(prompt)

    try:
        return json.loads(result)
    except Exception:
        return {"skills": []}


def analyze_job(resume_text, job_description):
    prompt = f"""
You are an ATS resume analyzer.

Compare this resume with the job description.

RESUME:
{resume_text}

JOB DESCRIPTION:
{job_description}

Return JSON only:

{{
    "match_score": 0,
    "keyword_score": 0,
    "skills_score": 0,
    "content_score": 0,
    "missing_keywords": [],
    "strengths": [],
    "improvements": []
}}

Rules:
- Scores must be between 0 and 100.
- Do not invent information.
- Missing keywords must come from the job description.
"""

    result = ask_ai(prompt)

    try:
        return json.loads(result)
    except Exception:
        return {
            "match_score": 0,
            "keyword_score": 0,
            "skills_score": 0,
            "content_score": 0,
            "missing_keywords": [],
            "strengths": [],
            "improvements": []
        }


def verify_resume(resume_text, job_description=""):
    prompt = f"""
You are an ATS resume verification system.

Analyze the following resume.

RESUME:
{resume_text}

TARGET JOB DESCRIPTION:
{job_description}

Return JSON only:

{{
    "score": 0,
    "keyword_score": 0,
    "content_score": 0,
    "format_score": 0,
    "skills_score": 0,
    "strengths": [],
    "improvements": [],
    "missing_keywords": []
}}

Evaluate:
1. ATS readability
2. Professional content
3. Relevant keywords
4. Technical skills
5. Job relevance
6. Resume structure

Do not invent facts.
Scores must be between 0 and 100.
"""

    result = ask_ai(prompt)

    try:
        return json.loads(result)
    except Exception:
        return {
            "score": 0,
            "keyword_score": 0,
            "content_score": 0,
            "format_score": 0,
            "skills_score": 0,
            "strengths": [],
            "improvements": [],
            "missing_keywords": []
        }


def generate_achievement(context):
    prompt = f"""
Create strong resume achievement bullet points from the information below.

Information:
{context}

Rules:
- Do not invent facts.
- Do not invent numbers.
- Do not claim awards that were not provided.
- Use professional action verbs.
- Return 3 possible bullet points.
"""

    return ask_ai(prompt)


def resume_suggestions(resume_text, target_job=""):
    prompt = f"""
Review this resume as a professional recruiter.

Target Job:
{target_job}

Resume:
{resume_text}

Give practical improvements for:
- Summary
- Skills
- Projects
- Experience
- ATS keywords
- Formatting
- Missing information

Return JSON only:

{{
    "suggestions": []
}}
"""

    result = ask_ai(prompt)

    try:
        return json.loads(result)
    except Exception:
        return {"suggestions": []}
```
