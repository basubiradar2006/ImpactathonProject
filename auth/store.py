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
