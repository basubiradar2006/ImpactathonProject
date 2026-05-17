from db import get_supabase


def find_student_by_email(email):
    response = (
        get_supabase()
        .table("students")
        .select("*")
        .eq("email", email)
        .limit(1)
        .execute()
    )

    if not response.data:
        return None

    return response.data[0]


def find_student_by_id(student_id):
    response = (
        get_supabase()
        .table("students")
        .select("*")
        .eq("id", student_id)
        .limit(1)
        .execute()
    )

    if not response.data:
        return None

    return response.data[0]


def create_student(full_name, email, hashed_password):
    student_data = {
        "full_name": full_name,
        "email": email,
        "password": hashed_password,
    }

    response = (
        get_supabase()
        .table("students")
        .insert(student_data)
        .execute()
    )

    if not response.data:
        return None

    return response.data[0]


def update_student_profile(student_id, profile_data):
    response = (
        get_supabase()
        .table("students")
        .update(profile_data)
        .eq("id", student_id)
        .execute()
    )

    if not response.data:
        return None

    return response.data[0]


def get_colleges():
    response = (
        get_supabase()
        .table("colleges")
        .select("*")
        .order("college_name")
        .execute()
    )

    return response.data or []


def get_college_by_name(college_name):
    if not college_name:
        return None

    response = (
        get_supabase()
        .table("colleges")
        .select("*")
        .eq("college_name", college_name)
        .limit(1)
        .execute()
    )

    if not response.data:
        return None

    return response.data[0]


def get_companies_by_college_name(college_name):
    college = get_college_by_name(college_name)
    if not college:
        return []

    response = (
        get_supabase()
        .table("college_companies")
        .select("visit_year, active, companies(*)")
        .eq("college_id", college["id"])
        .eq("active", True)
        .order("visit_year", desc=True)
        .execute()
    )

    companies = []
    for item in response.data or []:
        company = item.get("companies") or {}
        company["visit_year"] = item.get("visit_year")
        company["active"] = item.get("active")
        companies.append(company)

    return companies


def get_projects_by_student(student_id):
    response = (
        get_supabase()
        .table("projects")
        .select("*")
        .eq("student_id", student_id)
        .order("created_at", desc=True)
        .execute()
    )

    return response.data or []


def get_project_by_student(student_id, project_id):
    response = (
        get_supabase()
        .table("projects")
        .select("*")
        .eq("id", project_id)
        .eq("student_id", student_id)
        .limit(1)
        .execute()
    )

    if not response.data:
        return None

    return response.data[0]


def create_project(student_id, project_data):
    response = (
        get_supabase()
        .table("projects")
        .insert({"student_id": student_id, **project_data})
        .execute()
    )

    if not response.data:
        return None

    return response.data[0]


def update_project(student_id, project_id, project_data):
    response = (
        get_supabase()
        .table("projects")
        .update(project_data)
        .eq("id", project_id)
        .eq("student_id", student_id)
        .execute()
    )

    if not response.data:
        return None

    return response.data[0]


def get_skills_by_student(student_id):
    response = (
        get_supabase()
        .table("skills")
        .select("*")
        .eq("student_id", student_id)
        .order("created_at", desc=True)
        .execute()
    )

    return response.data or []


def create_skill(student_id, skill_data):
    response = (
        get_supabase()
        .table("skills")
        .insert({"student_id": student_id, **skill_data})
        .execute()
    )

    if not response.data:
        return None

    return response.data[0]


def update_skill(student_id, skill_id, skill_data):
    response = (
        get_supabase()
        .table("skills")
        .update(skill_data)
        .eq("id", skill_id)
        .eq("student_id", student_id)
        .execute()
    )

    if not response.data:
        return None

    return response.data[0]


def create_interview(student_id, interview_data):
    response = (
        get_supabase()
        .table("interviews")
        .insert({"student_id": student_id, **interview_data})
        .execute()
    )

    if not response.data:
        return None

    return response.data[0]


def create_interview_questions(interview_id, questions):
    rows = [{"interview_id": interview_id, **question} for question in questions]
    response = (
        get_supabase()
        .table("interview_questions")
        .insert(rows)
        .execute()
    )

    return response.data or []


def get_interviews_by_student(student_id):
    response = (
        get_supabase()
        .table("interviews")
        .select("*")
        .eq("student_id", student_id)
        .order("created_at", desc=True)
        .execute()
    )

    return response.data or []


def get_interview_by_student(student_id, interview_id):
    response = (
        get_supabase()
        .table("interviews")
        .select("*")
        .eq("id", interview_id)
        .eq("student_id", student_id)
        .limit(1)
        .execute()
    )

    if not response.data:
        return None

    return response.data[0]


def get_interview_questions(interview_id):
    response = (
        get_supabase()
        .table("interview_questions")
        .select("*")
        .eq("interview_id", interview_id)
        .order("id")
        .execute()
    )

    return response.data or []
