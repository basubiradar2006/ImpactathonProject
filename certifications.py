from db import get_supabase


def get_hackathons_by_student(student_id):
    response = (
        get_supabase()
        .table("hackathons")
        .select("*")
        .eq("student_id", student_id)
        .order("created_at", desc=True)
        .execute()
    )

    return response.data or []


def create_hackathon(student_id, hackathon_data):
    response = (
        get_supabase()
        .table("hackathons")
        .insert({"student_id": student_id, **hackathon_data})
        .execute()
    )

    if not response.data:
        return None

    return response.data[0]


def update_hackathon(student_id, hackathon_id, hackathon_data):
    response = (
        get_supabase()
        .table("hackathons")
        .update(hackathon_data)
        .eq("id", hackathon_id)
        .eq("student_id", student_id)
        .execute()
    )

    if not response.data:
        return None

    return response.data[0]


def get_certifications_by_student(student_id):
    response = (
        get_supabase()
        .table("certifications")
        .select("*")
        .eq("student_id", student_id)
        .order("created_at", desc=True)
        .execute()
    )

    return response.data or []


def create_certification(student_id, certification_data):
    response = (
        get_supabase()
        .table("certifications")
        .insert({"student_id": student_id, **certification_data})
        .execute()
    )

    if not response.data:
        return None

    return response.data[0]


def update_certification(student_id, certification_id, certification_data):
    response = (
        get_supabase()
        .table("certifications")
        .update(certification_data)
        .eq("id", certification_id)
        .eq("student_id", student_id)
        .execute()
    )

    if not response.data:
        return None

    return response.data[0]
