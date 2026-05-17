import json
import os

from dotenv import load_dotenv

try:
    from google import genai
except ImportError:
    genai = None


load_dotenv()


def _get_model():
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    if not genai:
        raise RuntimeError("google-genai is not installed. Run: pip install google-genai")
    if not api_key:
        raise RuntimeError("Missing GEMINI_API_KEY or GOOGLE_API_KEY in .env")

    _disable_broken_local_proxy()
    return genai.Client(api_key=api_key)


def _disable_broken_local_proxy():
    proxy_vars = (
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "ALL_PROXY",
        "http_proxy",
        "https_proxy",
        "all_proxy",
    )
    for proxy_var in proxy_vars:
        proxy_value = os.getenv(proxy_var, "")
        if proxy_value.startswith("http://127.0.0.1:9"):
            os.environ.pop(proxy_var, None)


def _extract_json(text):
    try:
        start = text.index("[")
        end = text.rindex("]") + 1
        return json.loads(text[start:end])
    except Exception:
        raise ValueError("AI response did not include valid JSON.")


def generate_skill_test(skill_name, skill_description=None):
    clean_skill = (skill_name or "").strip()

    if not clean_skill:
        raise ValueError("Skill name is required to generate a test.")

    model = _get_model()

    prompt = f"""
Create exactly 5 multiple-choice questions to test a student's practical, placement-ready knowledge of this skill.

Skill: {clean_skill}

Student context:
{skill_description or "No extra context"}

Return ONLY valid JSON in this exact format:

[
  {{
    "question": "Question text",
    "options": [
      "Option A",
      "Option B",
      "Option C",
      "Option D"
    ],
    "answer": 0
  }}
]

Rules:
- answer must be the zero-based index of the correct option
- each question must have exactly 4 options
- every question must be scenario-based or implementation-based
- avoid generic learning advice questions
- avoid trivia and definition-only questions
- include realistic debugging, project, interview, or workplace situations
- do not return markdown
- do not return explanation text
"""

    response = model.models.generate_content(
        model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite"),
        contents=prompt,
    )
    questions = _extract_json(response.text)
    normalized = normalize_questions(questions, clean_skill)

    if len(normalized) < 5:
        raise ValueError("Gemini did not return 5 valid practical questions. Please try again.")

    return normalized


def normalize_questions(questions, skill_name):
    normalized = []

    for item in questions:
        options = item.get("options") or []
        answer = item.get("answer")

        if (
            not item.get("question")
            or len(options) != 4
            or not isinstance(answer, int)
            or answer not in range(4)
        ):
            continue

        normalized.append(
            {
                "question": str(item["question"]).strip(),
                "options": [str(option).strip() for option in options],
                "answer": answer,
            }
        )

    return normalized[:5]


def generate_mock_interview_questions(student, skills, projects, interview_config):
    client = _get_model()
    skill_names = [skill.get("skill_name") for skill in skills if skill.get("skill_name")]
    project_summaries = [
        {
            "title": project.get("project_title"),
            "domain": project.get("domain"),
            "tech_stack": project.get("tech_stack"),
            "description": project.get("project_description"),
        }
        for project in projects[:5]
    ]

    focus = interview_config.get("focus") or "Overall profile"
    role = interview_config.get("role") or "Software Engineer"
    difficulty = interview_config.get("difficulty_level") or "medium"
    total_questions = interview_config.get("total_questions") or 5
    question_mode = interview_config.get("question_mode") or "theoretical"

    prompt = f"""
Create exactly {total_questions} practical mock interview questions for a student.

Student profile:
- Name: {student.get("full_name") or "Student"}
- Degree: {student.get("degree") or "Not added"}
- Department: {student.get("department") or "Not added"}
- CGPA: {student.get("cgpa") or "Not added"}

Interview target:
- Role: {role}
- Focus: {focus}
- Difficulty: {difficulty}
- Question mode: {question_mode}

Known skills:
{json.dumps(skill_names, default=str)}

Projects:
{json.dumps(project_summaries, default=str)}

Return ONLY valid JSON in this exact shape:
[
  {{
    "question": "Question text",
    "question_type": "technical",
    "topic": "Python",
    "difficulty": "medium",
    "expected_answer": "Concise expected answer or scoring points",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "answer": 0
  }}
]

Rules:
- Questions must be practical, interview-style, and answerable in 4-8 sentences.
- Mix technical, project, problem-solving, and communication questions when focus is overall.
- Use resume/profile context when focus is overall profile or skills already added.
- If focus is a language/framework, ask implementation and debugging questions for that focus.
- If question mode is multiple_choice, every question_type must be "multiple_choice" and every question must include exactly 4 options and a zero-based answer index.
- If question mode is theoretical, do not include options and every question_type must be "theoretical".
- If question mode is both, mix multiple_choice and theoretical questions.
- Do not return markdown or explanation outside JSON.
"""

    response = client.models.generate_content(
        model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite"),
        contents=prompt,
    )
    questions = normalize_interview_questions(_extract_json(response.text))
    if len(questions) < total_questions:
        raise ValueError("Gemini did not return enough valid interview questions. Please try again.")
    return questions[:total_questions]


def normalize_interview_questions(questions):
    normalized = []
    for item in questions:
        if not item.get("question") or not item.get("expected_answer"):
            continue
        question_type = str(item.get("question_type") or "technical").strip().lower().replace("-", "_").replace(" ", "_")
        options = item.get("options") or []
        answer = item.get("answer")
        if question_type in {"mcq", "multiplechoice"}:
            question_type = "multiple_choice"
        elif options and isinstance(answer, int):
            question_type = "multiple_choice"
        normalized_options = []
        normalized_answer = None
        if question_type == "multiple_choice":
            if len(options) != 4 or not isinstance(answer, int) or answer not in range(4):
                continue
            normalized_options = [str(option).strip() for option in options]
            normalized_answer = answer
        normalized.append(
            {
                "question": str(item.get("question", "")).strip(),
                "question_type": question_type,
                "topic": str(item.get("topic") or "General").strip(),
                "difficulty": str(item.get("difficulty") or "medium").strip(),
                "expected_answer": str(item.get("expected_answer", "")).strip(),
                "options": normalized_options,
                "answer": normalized_answer,
            }
        )
    return normalized


def evaluate_mock_interview_answers(questions, interview_config):
    client = _get_model()
    prompt = f"""
Evaluate this mock interview attempt.

Interview config:
{json.dumps(interview_config, default=str)}

Questions and answers:
{json.dumps(questions, default=str)}

Return ONLY valid JSON in this exact shape:
{{
  "total_score": 0,
  "communication_score": 0,
  "technical_score": 0,
  "confidence_score": 0,
  "feedback_summary": "Short overall feedback",
  "weak_areas": ["Area 1", "Area 2"],
  "question_results": [
    {{
      "score": 0,
      "ai_feedback": "Specific feedback",
      "is_correct": false
    }}
  ]
}}

Rules:
- total_score, communication_score, technical_score, confidence_score must be 0 to 100.
- each question score must be 0 to 10.
- is_correct should be true when answer is mostly correct and complete.
- For multiple_choice questions, compare selected_answer_index with answer and mark is_correct from that.
- Evaluate practical correctness, clarity, confidence, and missing points.
- question_results length must match the number of questions.
- Do not return markdown or explanation outside JSON.
"""

    response = client.models.generate_content(
        model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite"),
        contents=prompt,
    )
    return normalize_interview_evaluation(_extract_object_json(response.text), len(questions))


def _extract_object_json(text):
    try:
        start = text.index("{")
        end = text.rindex("}") + 1
        return json.loads(text[start:end])
    except Exception:
        raise ValueError("AI response did not include valid JSON.")


def normalize_interview_evaluation(evaluation, question_count):
    def score(value, maximum=100):
        try:
            return max(0, min(maximum, round(float(value))))
        except (TypeError, ValueError):
            return 0

    results = evaluation.get("question_results") or []
    normalized_results = []
    for index in range(question_count):
        item = results[index] if index < len(results) else {}
        normalized_results.append(
            {
                "score": score(item.get("score"), 10),
                "ai_feedback": str(item.get("ai_feedback") or "No feedback returned.").strip(),
                "is_correct": bool(item.get("is_correct")),
            }
        )

    return {
        "total_score": score(evaluation.get("total_score")),
        "communication_score": score(evaluation.get("communication_score")),
        "technical_score": score(evaluation.get("technical_score")),
        "confidence_score": score(evaluation.get("confidence_score")),
        "feedback_summary": str(evaluation.get("feedback_summary") or "Interview completed.").strip(),
        "weak_areas": [
            str(area).strip()
            for area in (evaluation.get("weak_areas") or [])
            if str(area).strip()
        ][:5],
        "question_results": normalized_results,
    }


def analyze_resume_with_gemini(resume_text, student, skills, projects, companies, target_company=None):
    client = _get_model()
    target_company_data = None
    if target_company:
        for company in companies:
            if (company.get("company_name") or "").lower() == target_company.lower():
                target_company_data = company
                break

    prompt = f"""
Analyze this student's resume for placement readiness.

Student profile:
- Name: {student.get("full_name") or "Student"}
- College: {student.get("college_name") or "Not selected"}
- Department: {student.get("department") or "Not added"}
- Degree: {student.get("degree") or "Not added"}
- CGPA: {student.get("cgpa") or "Not added"}

Saved skills:
{json.dumps(skills[:12], default=str)}

Saved projects:
{json.dumps(projects[:8], default=str)}

College placement companies:
{json.dumps(companies[:10], default=str)}

Target company:
{json.dumps(target_company_data or target_company or "Not selected", default=str)}

Resume text:
{resume_text}

Return ONLY valid JSON in this exact shape:
{{
  "resume_score": 0,
  "company_fit_score": 0,
  "summary": "Short summary",
  "strengths": ["Strength 1"],
  "weak_areas": ["Weak area 1"],
  "missing_skills": ["Skill 1"],
  "company_gap": "Specific company gap",
  "learning_recommendations": [
    {{
      "skill": "Skill name",
      "why": "Why this helps",
      "timeline": "2 weeks"
    }}
  ],
  "resume_improvements": ["Improve this resume point"],
  "follow_up_questions": ["Question to ask student"]
}}

Rules:
- Use target company data when available, especially required_skills, role, min_cgpa, and package_lpa.
- Compare resume text with saved skills and projects.
- Mention weak areas clearly and practically.
- Suggest skills that improve chance for the selected company or similar college placement companies.
- follow_up_questions should ask what is missing to better judge the company gap.
- Scores must be 0 to 100.
- Do not return markdown or explanation outside JSON.
"""

    response = client.models.generate_content(
        model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite"),
        contents=prompt,
    )
    return normalize_resume_analysis(_extract_object_json(response.text))


def normalize_resume_analysis(analysis):
    def score(value):
        try:
            return max(0, min(100, round(float(value))))
        except (TypeError, ValueError):
            return 0

    def string_list(value):
        return [str(item).strip() for item in (value or []) if str(item).strip()][:8]

    recommendations = []
    for item in analysis.get("learning_recommendations") or []:
        recommendations.append(
            {
                "skill": str(item.get("skill") or "Skill").strip(),
                "why": str(item.get("why") or "Improves placement readiness.").strip(),
                "timeline": str(item.get("timeline") or "1-2 weeks").strip(),
            }
        )

    return {
        "resume_score": score(analysis.get("resume_score")),
        "company_fit_score": score(analysis.get("company_fit_score")),
        "summary": str(analysis.get("summary") or "Resume analyzed.").strip(),
        "strengths": string_list(analysis.get("strengths")),
        "weak_areas": string_list(analysis.get("weak_areas")),
        "missing_skills": string_list(analysis.get("missing_skills")),
        "company_gap": str(analysis.get("company_gap") or "Select a company for a sharper gap analysis.").strip(),
        "learning_recommendations": recommendations[:6],
        "resume_improvements": string_list(analysis.get("resume_improvements")),
        "follow_up_questions": string_list(analysis.get("follow_up_questions")),
    }


def evaluate_skill_answers(questions, submitted_answers):
    total = len(questions)
    correct = 0

    for index, question in enumerate(questions):
        selected = submitted_answers.get(f"answer_{index}")

        if (
            selected is not None
            and selected.isdigit()
            and int(selected) == question["answer"]
        ):
            correct += 1

    score = round((correct / total) * 100) if total else 0

    if score >= 80:
        level = "advanced"
    elif score >= 50:
        level = "intermediate"
    else:
        level = "beginner"

    return {
        "correct": correct,
        "total": total,
        "score": score,
        "level": level,
        "progress": score,
    }
