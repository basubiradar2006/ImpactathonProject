import json
import re
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

from flask import Flask, redirect, render_template, request, session, url_for

from ai import evaluate_skill_answers, generate_skill_test
from auth import login_bp, register_bp
from auth.store import (
    create_project,
    create_skill,
    get_project_by_student,
    find_student_by_id,
    get_projects_by_student,
    get_skills_by_student,
    update_project,
    update_skill,
    update_student_profile,
)
from certifications import (
    create_certification,
    create_hackathon,
    get_certifications_by_student,
    get_hackathons_by_student,
)

app = Flask(__name__)
app.secret_key = "placement-ready-dev-key"
app.register_blueprint(register_bp)
app.register_blueprint(login_bp)

analyzer_data = {
    "target_role": "Full Stack Developer",
    "location": "Not added yet",
    "readiness_score": 72,
    "readiness_level": "Placement Ready With Gaps",
    "resume_score": 78,
    "project_depth": 86,
    "hackathon_score": 68,
    "cloud_readiness": 38,
    "coding_score": 74,
    "hackathons": [
        {"name": "Impactathon 2026", "role": "Team Lead", "result": "Finalist"},
        {"name": "Smart Campus Sprint", "role": "Backend Developer", "result": "Top 10"},
    ],
    "certifications": [
        "Python for Everybody",
        "Responsive Web Design",
        "SQL Intermediate",
    ],
    "recommended_skills": [
        {"skill": "Docker", "reason": "Needed to package and deploy full-stack projects consistently.", "timeline": "2 weeks"},
        {"skill": "AWS", "reason": "Cloud deployment is weak for the selected full-stack role.", "timeline": "3 weeks"},
        {"skill": "System Design", "reason": "Improves interview readiness for scalable application discussions.", "timeline": "4 weeks"},
        {"skill": "Python DSA", "reason": "Strengthens coding round performance.", "timeline": "Daily practice"},
    ],
}

TECH_FILE_PATTERNS = {
    "package.json": ["Node.js", "JavaScript"],
    "vite.config.js": ["Vite"],
    "vite.config.ts": ["Vite", "TypeScript"],
    "next.config.js": ["Next.js"],
    "next.config.mjs": ["Next.js"],
    "requirements.txt": ["Python"],
    "pyproject.toml": ["Python"],
    "Pipfile": ["Python"],
    "manage.py": ["Django"],
    "app.py": ["Flask", "Python"],
    "main.py": ["Python"],
    "Dockerfile": ["Docker"],
    "docker-compose.yml": ["Docker"],
    "docker-compose.yaml": ["Docker"],
    "pom.xml": ["Java", "Maven"],
    "build.gradle": ["Java", "Gradle"],
    "Cargo.toml": ["Rust"],
    "go.mod": ["Go"],
    "composer.json": ["PHP"],
    "Gemfile": ["Ruby"],
    "pubspec.yaml": ["Flutter", "Dart"],
    "tailwind.config.js": ["Tailwind CSS"],
    "tailwind.config.ts": ["Tailwind CSS"],
}

LANGUAGE_TECH = {
    "JavaScript": "JavaScript",
    "TypeScript": "TypeScript",
    "Python": "Python",
    "HTML": "HTML",
    "CSS": "CSS",
    "Java": "Java",
    "C++": "C++",
    "C": "C",
    "C#": "C#",
    "Dart": "Dart",
    "Go": "Go",
    "PHP": "PHP",
    "Ruby": "Ruby",
    "Rust": "Rust",
    "Kotlin": "Kotlin",
    "Swift": "Swift",
}


def format_year(year):
    if not year:
        return "Not added yet"
    return f"Year {year}"


def build_student_profile(db_student=None):
    profile = dict(analyzer_data)

    if not db_student:
        profile.update(
            {
                "id": None,
                "name": "Student",
                "student_id": "Not assigned",
                "college_name": "Not added yet",
                "degree": "Not added yet",
                "department": "Not added yet",
                "year": "Not added yet",
                "current_year": "",
                "email": "Not added yet",
                "phone": "Not added yet",
                "phone_number": "",
                "cgpa": "Not added yet",
            }
        )
        return profile

    profile.update(
        {
            "id": db_student.get("id"),
            "name": db_student.get("full_name") or "Student",
            "student_id": f"STU-{db_student.get('id')}" if db_student.get("id") else "Not assigned",
            "college_name": db_student.get("college_name") or "Not added yet",
            "degree": db_student.get("degree") or "Not added yet",
            "department": db_student.get("department") or "Not added yet",
            "year": format_year(db_student.get("current_year")),
            "current_year": db_student.get("current_year") or "",
            "email": db_student.get("email") or "Not added yet",
            "phone": db_student.get("phone_number") or "Not added yet",
            "phone_number": db_student.get("phone_number") or "",
            "cgpa": db_student.get("cgpa") if db_student.get("cgpa") is not None else "Not added yet",
        }
    )
    return profile


def parse_project_form(form):
    completion_level = form.get("completion_level", "").strip()

    return {
        "project_title": form.get("project_title", "").strip(),
        "project_description": form.get("project_description", "").strip() or None,
        "domain": form.get("domain", "").strip() or None,
        "tech_stack": form.get("tech_stack", "").strip() or None,
        "github_link": form.get("github_link", "").strip() or None,
        "live_link": form.get("live_link", "").strip() or None,
        "team_project": form.get("team_project") == "on",
        "completion_level": int(completion_level) if completion_level else None,
    }


def validate_project(project_data):
    if not project_data["project_title"]:
        return "Project title is required."
    if (
        project_data["completion_level"] is not None
        and not 0 <= project_data["completion_level"] <= 100
    ):
        return "Completion level must be between 0 and 100."
    return None


def parse_skill_form(form):
    skill_score = form.get("skill_score", "").strip()
    progress_percentage = form.get("progress_percentage", "").strip()

    return {
        "skill_name": form.get("skill_name", "").strip(),
        "skill_description": form.get("skill_description", "").strip() or None,
        "skill_level": form.get("skill_level", "").strip() or "beginner",
        "skill_score": int(skill_score) if skill_score else 0,
        "progress_percentage": int(progress_percentage) if progress_percentage else 0,
        "verified": form.get("verified") == "on",
    }


def validate_skill(skill_data):
    if not skill_data["skill_name"]:
        return "Skill name is required."
    if skill_data["skill_level"] not in {"beginner", "intermediate", "advanced", None}:
        return "Skill level must be beginner, intermediate, or advanced."
    if skill_data["skill_score"] is not None and not 0 <= skill_data["skill_score"] <= 100:
        return "Skill score must be between 0 and 100."
    if (
        skill_data["progress_percentage"] is not None
        and not 0 <= skill_data["progress_percentage"] <= 100
    ):
        return "Progress percentage must be between 0 and 100."
    return None


def parse_hackathon_form(form):
    team_size = form.get("team_size", "").strip()

    return {
        "hackathon_name": form.get("hackathon_name", "").strip(),
        "organizer": form.get("organizer", "").strip() or None,
        "role": form.get("role", "").strip() or None,
        "domain": form.get("domain", "").strip() or None,
        "project_title": form.get("project_title", "").strip() or None,
        "start_date": form.get("start_date", "").strip() or None,
        "end_date": form.get("end_date", "").strip() or None,
        "achievement": form.get("achievement", "").strip() or None,
        "team_size": int(team_size) if team_size else None,
        "github_link": form.get("github_link", "").strip() or None,
        "demo_link": form.get("demo_link", "").strip() or None,
        "certificate_link": form.get("certificate_link", "").strip() or None,
        "skills_used": form.get("skills_used", "").strip() or None,
    }


def validate_hackathon(hackathon_data):
    if not hackathon_data["hackathon_name"]:
        return "Hackathon name is required."
    if hackathon_data["team_size"] is not None and hackathon_data["team_size"] < 1:
        return "Team size must be at least 1."
    return None


def parse_certification_form(form):
    duration_hours = form.get("duration_hours", "").strip()

    return {
        "certificate_name": form.get("certificate_name", "").strip(),
        "provider": form.get("provider", "").strip() or None,
        "domain": form.get("domain", "").strip() or None,
        "issue_date": form.get("issue_date", "").strip() or None,
        "expiry_date": form.get("expiry_date", "").strip() or None,
        "credential_id": form.get("credential_id", "").strip() or None,
        "certificate_url": form.get("certificate_url", "").strip() or None,
        "skill_level": form.get("skill_level", "").strip() or None,
        "duration_hours": int(duration_hours) if duration_hours else None,
        "verified": form.get("verified") == "on",
    }


def validate_certification(certification_data):
    if not certification_data["certificate_name"]:
        return "Certificate name is required."
    if certification_data["skill_level"] not in {"beginner", "intermediate", "advanced", None}:
        return "Certification skill level must be beginner, intermediate, or advanced."
    if certification_data["duration_hours"] is not None and certification_data["duration_hours"] < 1:
        return "Duration hours must be at least 1."
    return None


def parse_github_repo_url(github_url):
    parsed = urlparse(github_url.strip())
    if parsed.netloc.lower() not in {"github.com", "www.github.com"}:
        raise ValueError("Please enter a valid GitHub repository link.")

    parts = [part for part in parsed.path.strip("/").split("/") if part]
    if len(parts) < 2:
        raise ValueError("GitHub link must include owner and repository name.")

    owner, repo = parts[0], parts[1].removesuffix(".git")
    if not re.match(r"^[A-Za-z0-9_.-]+$", owner) or not re.match(r"^[A-Za-z0-9_.-]+$", repo):
        raise ValueError("GitHub repository link has unsupported characters.")

    return owner, repo


def fetch_github_json(api_url):
    request_obj = Request(
        api_url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "PlacementReady-Project-Analyzer",
        },
    )

    with urlopen(request_obj, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def detect_tech_stack(languages, paths):
    tech_stack = set()

    for language in languages:
        tech_stack.add(LANGUAGE_TECH.get(language, language))

    lowered_paths = {path.lower(): path for path in paths}
    for filename, technologies in TECH_FILE_PATTERNS.items():
        if any(path.endswith(filename.lower()) for path in lowered_paths):
            tech_stack.update(technologies)

    if any(path.startswith("templates/") for path in lowered_paths):
        tech_stack.add("Jinja")
    if any(path.startswith("static/") for path in lowered_paths):
        tech_stack.add("Frontend Assets")
    if any(".github/workflows/" in path for path in lowered_paths):
        tech_stack.add("GitHub Actions")
    if any("supabase" in path for path in lowered_paths):
        tech_stack.add("Supabase")
    if any("firebase" in path for path in lowered_paths):
        tech_stack.add("Firebase")

    return sorted(tech_stack)


def has_any_path(paths, checks):
    return any(any(check in path for check in checks) for path in paths)


def build_project_analysis(github_url):
    owner, repo = parse_github_repo_url(github_url)
    api_root = f"https://api.github.com/repos/{owner}/{repo}"

    try:
        repo_data = fetch_github_json(api_root)
        languages = fetch_github_json(f"{api_root}/languages")
        default_branch = quote(repo_data.get("default_branch", "main"), safe="")
        tree_data = fetch_github_json(f"{api_root}/git/trees/{default_branch}?recursive=1")
    except HTTPError as exc:
        if exc.code == 404:
            raise ValueError("Repository was not found or is private.")
        if exc.code == 403:
            raise ValueError("GitHub rate limit reached. Please try again after some time.")
        raise ValueError(f"GitHub could not analyze this repository right now. Error {exc.code}.")
    except (URLError, TimeoutError):
        raise ValueError("Could not connect to GitHub. Check internet access and try again.")

    tree = tree_data.get("tree") or []
    paths = [item.get("path", "").lower() for item in tree if item.get("path")]
    file_paths = [path for path in paths if "." in path.split("/")[-1]]
    directories = {path.split("/")[0] for path in paths if "/" in path}
    language_names = list(languages.keys())
    tech_stack = detect_tech_stack(language_names, paths)

    has_readme = any(path.split("/")[-1].startswith("readme") for path in paths)
    has_license = any(path.split("/")[-1] in {"license", "license.md", "license.txt"} for path in paths)
    has_tests = has_any_path(paths, ["test", "tests", "__tests__", "spec"])
    has_ci = has_any_path(paths, [".github/workflows", ".gitlab-ci", "jenkinsfile"])
    has_deploy = has_any_path(paths, ["dockerfile", "docker-compose", "vercel.json", "render.yaml", "netlify.toml", "procfile"])
    manifest_names = {name.lower() for name in TECH_FILE_PATTERNS}
    has_dependencies = any(path.split("/")[-1] in manifest_names for path in paths)
    has_docs = has_any_path(paths, ["docs/", "documentation", "wiki"])
    has_env_example = any(path.endswith(".env.example") or path.endswith("env.sample") for path in paths)
    has_separation = len(directories) >= 4

    scoring_checks = [
        ("README and setup clarity", 15, has_readme, "Add a README with problem statement, screenshots, setup, and usage."),
        ("Dependency manifest", 10, has_dependencies, "Add requirements.txt, package.json, pyproject.toml, or another dependency manifest."),
        ("Project structure", 12, has_separation, "Separate source, templates/static, tests, docs, or config into clear folders."),
        ("Testing evidence", 12, has_tests, "Add unit tests or integration tests for the main workflow."),
        ("Deployment readiness", 10, has_deploy, "Add Docker, Vercel, Render, Netlify, or Procfile deployment config."),
        ("CI workflow", 10, has_ci, "Add a GitHub Actions workflow for tests or lint checks."),
        ("Documentation depth", 8, has_docs, "Add a docs folder or architecture notes for reviewers."),
        ("Environment sample", 7, has_env_example, "Add .env.example so others can configure the project safely."),
        ("Multi-tech implementation", 8, len(tech_stack) >= 3, "Use and document frontend, backend, database, or deployment layers."),
        ("Repository size", 8, len(file_paths) >= 8, "Commit enough source files to show a complete working project."),
    ]

    earned_points = 0
    points = []
    missing = []
    for label, value, passed, advice in scoring_checks:
        earned = value if passed else 0
        earned_points += earned
        points.append({"label": label, "earned": earned, "total": value, "passed": passed})
        if not passed:
            missing.append(advice)

    depth_score = min(100, earned_points)
    if depth_score >= 80:
        depth_level = "Strong project depth"
    elif depth_score >= 60:
        depth_level = "Good project depth with gaps"
    elif depth_score >= 40:
        depth_level = "Basic project evidence"
    else:
        depth_level = "Needs stronger project evidence"

    language_total = sum(languages.values()) or 1
    language_breakdown = [
        {
            "name": language,
            "percent": round((bytes_used / language_total) * 100),
        }
        for language, bytes_used in sorted(languages.items(), key=lambda item: item[1], reverse=True)
    ]

    return {
        "url": github_url,
        "repo_name": repo_data.get("full_name", f"{owner}/{repo}"),
        "description": repo_data.get("description") or "No GitHub description added.",
        "depth_score": depth_score,
        "depth_level": depth_level,
        "points": points,
        "tech_stack": tech_stack or ["Tech stack not detected"],
        "languages": language_breakdown,
        "file_count": len(file_paths),
        "folder_count": len(directories),
        "stars": repo_data.get("stargazers_count", 0),
        "forks": repo_data.get("forks_count", 0),
        "missing": missing[:4],
    }


def render_profile(student_id, message=None, error=None):
    db_student = find_student_by_id(student_id)

    if not db_student:
        session.clear()
        return redirect(url_for("auth_login.login"))

    projects = get_projects_by_student(student_id)
    skills = get_skills_by_student(student_id)
    hackathons = get_hackathons_by_student(student_id)
    certifications = get_certifications_by_student(student_id)

    return render_template(
        'profile.html',
        student=build_student_profile(db_student),
        projects=projects,
        skills=skills,
        hackathons=hackathons,
        certifications=certifications,
        message=message,
        error=error,
    )


@app.route('/')
def home():
    student = None
    if session.get("student_id"):
        try:
            student = find_student_by_id(session["student_id"])
        except Exception:
            student = None
    return render_template('home.html', student=build_student_profile(student))

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if not session.get("student_id"):
        return redirect(url_for("auth_login.login"))

    message = request.args.get("message")
    error = request.args.get("error")

    try:
        db_student = find_student_by_id(session["student_id"])

        if not db_student:
            session.clear()
            return redirect(url_for("auth_login.login"))

        if request.method == 'POST':
            full_name = request.form.get("full_name", "").strip()
            college_name = request.form.get("college_name", "").strip() or None
            degree = request.form.get("degree", "").strip() or None
            department = request.form.get("department", "").strip() or None
            current_year = request.form.get("current_year", "").strip()
            cgpa = request.form.get("cgpa", "").strip()
            phone_number = request.form.get("phone_number", "").strip() or None

            update_data = {
                "full_name": full_name,
                "college_name": college_name,
                "degree": degree,
                "department": department,
                "current_year": int(current_year) if current_year else None,
                "cgpa": float(cgpa) if cgpa else None,
                "phone_number": phone_number,
            }

            if not full_name:
                error = "Full name is required."
            elif update_data["current_year"] is not None and not 1 <= update_data["current_year"] <= 6:
                error = "Current year must be between 1 and 6."
            elif update_data["cgpa"] is not None and not 0 <= update_data["cgpa"] <= 10:
                error = "CGPA must be between 0 and 10."
            else:
                db_student = update_student_profile(session["student_id"], update_data)
                session["student_name"] = db_student["full_name"]
                message = "Profile updated successfully."

        return render_profile(session["student_id"], message=message, error=error)
    except ValueError:
        error = "Please enter valid numbers for current year and CGPA."
    except Exception as exc:
        app.logger.exception("Profile load/update failed")
        error = f"Profile update failed: {exc}"

    return render_template(
        'profile.html',
        student=build_student_profile(),
        projects=[],
        skills=[],
        hackathons=[],
        certifications=[],
        message=message,
        error=error,
    )


@app.route('/projects/<int:project_id>')
def project_detail(project_id):
    if not session.get("student_id"):
        return redirect(url_for("auth_login.login"))

    try:
        project = get_project_by_student(session["student_id"], project_id)
        if not project:
            return redirect(url_for("profile", error="Project not found."))

        project_analysis = None
        analysis_error = None
        if project.get("github_link"):
            try:
                project_analysis = build_project_analysis(project["github_link"])
            except ValueError as exc:
                analysis_error = str(exc)

        return render_template(
            "project_detail.html",
            project=project,
            project_analysis=project_analysis,
            analysis_error=analysis_error,
        )
    except ValueError as exc:
        return redirect(url_for("profile", error=str(exc)))
    except Exception as exc:
        app.logger.exception("Project detail failed")
        return redirect(url_for("profile", error=f"Project detail failed: {exc}"))


@app.route('/projects/add', methods=['POST'])
def add_project():
    if not session.get("student_id"):
        return redirect(url_for("auth_login.login"))

    try:
        project_data = parse_project_form(request.form)
        error = validate_project(project_data)

        if error:
            return redirect(url_for("profile", error=error))

        create_project(session["student_id"], project_data)
        return redirect(url_for("profile", message="Project added successfully."))
    except ValueError:
        return redirect(url_for("profile", error="Completion level must be a valid number."))
    except Exception as exc:
        app.logger.exception("Project creation failed")
        return redirect(url_for("profile", error=f"Project add failed: {exc}"))


@app.route('/projects/<int:project_id>/edit', methods=['POST'])
def edit_project(project_id):
    if not session.get("student_id"):
        return redirect(url_for("auth_login.login"))

    try:
        project_data = parse_project_form(request.form)
        error = validate_project(project_data)

        if error:
            return redirect(url_for("profile", error=error))

        update_project(session["student_id"], project_id, project_data)
        return redirect(url_for("profile", message="Project updated successfully."))
    except ValueError:
        return redirect(url_for("profile", error="Completion level must be a valid number."))
    except Exception as exc:
        app.logger.exception("Project update failed")
        return redirect(url_for("profile", error=f"Project update failed: {exc}"))


@app.route('/hackathons/add', methods=['POST'])
def add_hackathon():
    if not session.get("student_id"):
        return redirect(url_for("auth_login.login"))

    try:
        hackathon_data = parse_hackathon_form(request.form)
        error = validate_hackathon(hackathon_data)

        if error:
            return redirect(url_for("profile", error=error))

        create_hackathon(session["student_id"], hackathon_data)
        return redirect(url_for("profile", message="Hackathon added successfully."))
    except ValueError:
        return redirect(url_for("profile", error="Team size must be a valid number."))
    except Exception as exc:
        app.logger.exception("Hackathon creation failed")
        return redirect(url_for("profile", error=f"Hackathon add failed: {exc}"))


@app.route('/certifications/add', methods=['POST'])
def add_certification():
    if not session.get("student_id"):
        return redirect(url_for("auth_login.login"))

    try:
        certification_data = parse_certification_form(request.form)
        error = validate_certification(certification_data)

        if error:
            return redirect(url_for("profile", error=error))

        create_certification(session["student_id"], certification_data)
        return redirect(url_for("profile", message="Certification added successfully."))
    except ValueError:
        return redirect(url_for("profile", error="Duration hours must be a valid number."))
    except Exception as exc:
        app.logger.exception("Certification creation failed")
        return redirect(url_for("profile", error=f"Certification add failed: {exc}"))


@app.route('/skills/add', methods=['POST'])
def add_skill():
    if not session.get("student_id"):
        return redirect(url_for("auth_login.login"))

    try:
        questions = json.loads(request.form.get("test_payload", "[]"))
        result = evaluate_skill_answers(questions, request.form)
        skill_name = request.form.get("skill_name", "").strip()
        skill_description = request.form.get("skill_description", "").strip()

        skill_data = {
            "skill_name": skill_name,
            "skill_description": (
                f"{skill_description}\n\n"
                f"Test result: {result['correct']}/{result['total']} correct. "
                f"Auto-assessed as {result['level'].title()}."
            ).strip(),
            "skill_level": result["level"],
            "skill_score": result["score"],
            "progress_percentage": result["progress"],
            "verified": True,
        }
        error = validate_skill(skill_data)

        if error:
            return redirect(url_for("profile", error=error))

        create_skill(session["student_id"], skill_data)
        return redirect(
            url_for(
                "profile",
                message=f"Skill test completed. Score: {result['score']}/100, Level: {result['level'].title()}.",
            )
        )
    except (ValueError, json.JSONDecodeError):
        return redirect(url_for("profile", error="Skill test could not be evaluated. Please generate the test again."))
    except Exception as exc:
        app.logger.exception("Skill creation failed")
        return redirect(url_for("profile", error=f"Skill add failed: {exc}"))


@app.route('/skills/test', methods=['POST'])
def prepare_skill_test():
    if not session.get("student_id"):
        return redirect(url_for("auth_login.login"))

    skill_name = request.form.get("skill_name", "").strip()
    skill_description = request.form.get("skill_description", "").strip()

    if not skill_name:
        return redirect(url_for("profile", error="Skill name is required before starting the test."))

    try:
        questions = generate_skill_test(skill_name, skill_description)
    except Exception as exc:
        app.logger.exception("Skill test generation failed")
        return redirect(url_for("profile", error=f"Could not generate skill test: {exc}"))

    return render_template(
        "skill_test.html",
        skill_name=skill_name,
        skill_description=skill_description,
        questions=questions,
    )


@app.route('/skills/<int:skill_id>/edit', methods=['POST'])
def edit_skill(skill_id):
    if not session.get("student_id"):
        return redirect(url_for("auth_login.login"))

    try:
        skill_data = parse_skill_form(request.form)
        error = validate_skill(skill_data)

        if error:
            return redirect(url_for("profile", error=error))

        update_skill(session["student_id"], skill_id, skill_data)
        return redirect(url_for("profile", message="Skill updated successfully."))
    except ValueError:
        return redirect(url_for("profile", error="Skill score and progress must be valid numbers."))
    except Exception as exc:
        app.logger.exception("Skill update failed")
        return redirect(url_for("profile", error=f"Skill update failed: {exc}"))

if __name__ == '__main__':
    app.run(debug=True)
