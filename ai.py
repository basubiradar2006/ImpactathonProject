import json
import os
import re

from dotenv import load_dotenv

try:
    import google.generativeai as genai
except ImportError:
    genai = None


load_dotenv()


def _get_model():
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not genai or not api_key:
        return None

    genai.configure(api_key=api_key)
    return genai.GenerativeModel("gemini-2.5-flash-lite")


def _extract_json(text):
    match = re.search(r"\[[\s\S]*\]", text or "")
    if not match:
        raise ValueError("AI response did not include a question list.")
    return json.loads(match.group(0))


def _fallback_questions(skill_name):
    return [
        {
            "question": f"What is the best first step when learning {skill_name}?",
            "options": [
                "Understand the core concepts and practice with small examples",
                "Memorize random definitions only",
                "Skip basics and copy complete projects",
                "Avoid reading error messages",
            ],
            "answer": 0,
        },
        {
            "question": "Which habit shows stronger practical skill?",
            "options": [
                "Building and explaining a working project",
                "Only watching videos",
                "Never testing the output",
                "Ignoring documentation",
            ],
            "answer": 0,
        },
        {
            "question": "Why are tests or sample checks useful in a project?",
            "options": [
                "They help confirm the feature works as expected",
                "They make code slower by default",
                "They replace the need to understand code",
                "They are only for very large companies",
            ],
            "answer": 0,
        },
        {
            "question": "What should a good project README include?",
            "options": [
                "Problem, setup steps, usage, and important screenshots or examples",
                "Only the project title",
                "Only private passwords",
                "Nothing if the code is present",
            ],
            "answer": 0,
        },
        {
            "question": f"What is the best way to prove {skill_name} knowledge in placements?",
            "options": [
                "Show a project, explain decisions, and answer practical questions",
                "Mention the skill without examples",
                "Avoid discussing mistakes",
                "Use only copied definitions",
            ],
            "answer": 0,
        },
    ]


def generate_skill_test(skill_name, skill_description=None):
    clean_skill = (skill_name or "").strip()
    if not clean_skill:
        raise ValueError("Skill name is required to generate a test.")

    model = _get_model()
    if not model:
        return _fallback_questions(clean_skill)

    prompt = f"""
Create exactly 5 multiple-choice questions to test a student's practical knowledge of this skill.
Skill: {clean_skill}
Student context: {skill_description or "No extra context"}

Return only valid JSON in this exact shape:
[
  {{
    "question": "Question text",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "answer": 0
  }}
]

Rules:
- answer must be the zero-based index of the correct option.
- each question must have exactly 4 options.
- questions should test practical placement-ready understanding, not trivia.
"""

    response = model.generate_content(prompt)
    questions = _extract_json(response.text)
    return normalize_questions(questions, clean_skill)


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

    return normalized[:5] or _fallback_questions(skill_name)


def evaluate_skill_answers(questions, submitted_answers):
    total = len(questions)
    correct = 0

    for index, question in enumerate(questions):
        selected = submitted_answers.get(f"answer_{index}")
        if selected is not None and selected.isdigit() and int(selected) == question["answer"]:
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
