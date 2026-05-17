import json
import os
import re

from dotenv import load_dotenv

try:
    from google import genai
except ImportError:
    genai = None


load_dotenv()


ROLE_SKILLS = {
    "Full Stack Developer": [
        "HTML",
        "CSS",
        "JavaScript",
        "Python",
        "Flask",
        "React",
        "SQL",
        "Git",
        "REST API",
        "Deployment",
    ],
    "Software Engineer": [
        "DSA",
        "OOP",
        "SQL",
        "Git",
        "Java",
        "Python",
        "System Design",
        "Testing",
    ],
    "Data Analyst": [
        "Python",
        "SQL",
        "Excel",
        "Statistics",
        "Power BI",
        "Data Visualization",
    ],
}


def _get_model():
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    if not genai or not api_key:
        return None

    return genai.Client(api_key=api_key)


def _clamp(value, minimum=0, maximum=100):
    return max(minimum, min(maximum, round(value)))


def _safe_percent(values):
    clean_values = [value for value in values if value is not None]
    if not clean_values:
        return 0
    return _clamp(sum(clean_values) / len(clean_values))


def _score_hackathons(hackathons):
    if not hackathons:
        return 0

    total = 0
    for hackathon in hackathons:
        score = 30
        achievement = (hackathon.get("achievement") or "").lower()
        role = (hackathon.get("role") or "").lower()

        if achievement:
            score += 15
        if any(word in achievement for word in ("winner", "runner", "top", "finalist")):
            score += 15
        if role in {"team lead", "lead", "developer", "designer", "presenter", "winner"}:
            score += 10
        if hackathon.get("github_link"):
            score += 10
        if hackathon.get("demo_link"):
            score += 10
        if hackathon.get("certificate_link"):
            score += 5
        if hackathon.get("skills_used"):
            score += 5

        total += _clamp(score)

    count_bonus = min(len(hackathons) * 5, 15)
    return _clamp((total / len(hackathons)) + count_bonus)


def _split_stack(tech_stack):
    if not tech_stack:
        return []
    return [part.strip() for part in re.split(r"[,/|]", tech_stack) if part.strip()]


def _normalize(value):
    return re.sub(r"[^a-z0-9+#.]+", "", (value or "").lower())


def _fallback_roadmap(missing_skills, weak_skills, target_role):
    priorities = missing_skills[:4] or [skill.get("skill_name", "Core skill") for skill in weak_skills[:4]]
    if not priorities:
        priorities = ["DSA", "SQL", "Project documentation", "Deployment"]

    return [
        {
            "title": skill,
            "why": f"Strengthens your {target_role} readiness and fills a visible learning gap.",
            "actions": [
                f"Learn the core concepts of {skill}",
                "Build or upgrade one small project feature using it",
                "Add proof in GitHub, README, or profile notes",
            ],
            "timeline": "1-2 weeks",
        }
        for skill in priorities
    ]


def _extract_roadmap_json(text):
    try:
        start = text.index("[")
        end = text.rindex("]") + 1
        return json.loads(text[start:end])
    except Exception:
        raise ValueError("Gemini response did not include valid roadmap JSON.")


def _generate_gemini_roadmap(student, projects, skills, companies, analysis):
    model = _get_model()
    if not model:
        return None

    prompt = f"""
Create a concise personal learning roadmap for a placement student.
Return only valid JSON as a list of 4 objects with keys: title, why, actions, timeline.
actions must be a list of exactly 3 short action strings.

Student:
- Name: {student.get("full_name") or "Student"}
- College: {student.get("college_name") or "Not selected"}
- Department: {student.get("department") or "Not added"}
- CGPA: {student.get("cgpa") or "Not added"}

Target role: {analysis["target_role"]}
Readiness score: {analysis["readiness_score"]}
Missing role skills: {", ".join(analysis["missing_skills"]) or "None"}
Weak skills: {", ".join(skill.get("skill_name", "") for skill in analysis["weak_skills"]) or "None"}
Projects: {json.dumps(projects[:5], default=str)}
Skills: {json.dumps(skills[:8], default=str)}
Placement companies for college: {json.dumps(companies[:5], default=str)}
"""

    response = model.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=prompt,
    )

    roadmap = _extract_roadmap_json(response.text)
    cleaned = []
    for item in roadmap:
        actions = item.get("actions") or []
        if not item.get("title") or not item.get("why") or len(actions) < 1:
            continue
        cleaned.append(
            {
                "title": str(item["title"]).strip(),
                "why": str(item["why"]).strip(),
                "actions": [str(action).strip() for action in actions[:3]],
                "timeline": str(item.get("timeline") or "1-2 weeks").strip(),
            }
        )
    return cleaned[:4] or None


def analyze_student_learning(
    student,
    projects,
    skills,
    companies=None,
    hackathons=None,
    target_role="Full Stack Developer",
    include_roadmap=True,
):
    companies = companies or []
    hackathons = hackathons or []
    role_skills = ROLE_SKILLS.get(target_role, ROLE_SKILLS["Full Stack Developer"])
    owned_skill_names = {skill.get("skill_name", "") for skill in skills}
    owned_skill_keys = {_normalize(skill_name) for skill_name in owned_skill_names}

    project_techs = set()
    for project in projects:
        project_techs.update(_split_stack(project.get("tech_stack")))
    project_tech_keys = {_normalize(tech) for tech in project_techs}

    missing_skills = [
        skill
        for skill in role_skills
        if _normalize(skill) not in owned_skill_keys and _normalize(skill) not in project_tech_keys
    ]
    weak_skills = [
        skill
        for skill in skills
        if (skill.get("skill_score") or 0) < 60 or (skill.get("progress_percentage") or 0) < 60
    ]

    skill_score = _safe_percent([skill.get("skill_score") for skill in skills])
    progress_score = _safe_percent([skill.get("progress_percentage") for skill in skills])
    project_depth = _safe_percent([project.get("completion_level") for project in projects])
    hackathon_score = _score_hackathons(hackathons)
    completed_projects = sum(1 for project in projects if (project.get("completion_level") or 0) >= 80)
    verified_skills = sum(1 for skill in skills if skill.get("verified"))

    evidence_score = _clamp(
        (len(projects) * 12)
        + (completed_projects * 10)
        + (len(skills) * 6)
        + (verified_skills * 8)
        + (hackathon_score * 0.15)
    )
    coverage_score = _clamp(((len(role_skills) - len(missing_skills)) / len(role_skills)) * 100)
    readiness_score = _clamp(
        (skill_score * 0.25)
        + (progress_score * 0.2)
        + (project_depth * 0.25)
        + (coverage_score * 0.2)
        + (hackathon_score * 0.1)
        + (evidence_score * 0.1)
    )

    if readiness_score >= 80:
        readiness_level = "Placement ready"
    elif readiness_score >= 60:
        readiness_level = "Good progress with gaps"
    elif readiness_score >= 40:
        readiness_level = "Needs focused practice"
    else:
        readiness_level = "Build fundamentals first"

    analysis = {
        "target_role": target_role,
        "readiness_score": readiness_score,
        "readiness_level": readiness_level,
        "skill_score": skill_score,
        "progress_score": progress_score,
        "project_depth": project_depth,
        "hackathon_score": hackathon_score,
        "evidence_score": evidence_score,
        "coverage_score": coverage_score,
        "required_skills": role_skills,
        "covered_skills": sorted(owned_skill_names | project_techs),
        "missing_skills": missing_skills,
        "weak_skills": weak_skills[:5],
        "completed_projects": completed_projects,
        "verified_skills": verified_skills,
        "company_count": len(companies),
    }

    if include_roadmap:
        try:
            roadmap = _generate_gemini_roadmap(student, projects, skills, companies, analysis)
        except Exception:
            roadmap = None

        analysis["roadmap"] = roadmap or _fallback_roadmap(missing_skills, weak_skills, target_role)
    else:
        analysis["roadmap"] = []

    return analysis
