from flask import Blueprint, current_app, redirect, render_template, request, session, url_for
from werkzeug.security import generate_password_hash

from auth.store import create_student, find_student_by_email


register_bp = Blueprint("auth_register", __name__)


@register_bp.route("/signup", methods=["GET", "POST"])
def signup():
    error = None

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not full_name or not email or not password:
            error = "Please enter your name, email, and password."
        elif len(password) < 6:
            error = "Password must be at least 6 characters."
        else:
            try:
                existing_student = find_student_by_email(email)

                if existing_student:
                    error = "This email is already registered. Please login."
                else:
                    new_student = create_student(
                        full_name=full_name,
                        email=email,
                        hashed_password=generate_password_hash(password),
                    )

                    if not new_student:
                        error = "Could not create your account. Please try again."
                    else:
                        session["student_id"] = new_student["id"]
                        session["student_email"] = new_student["email"]
                        session["student_name"] = new_student["full_name"]
                        return redirect(url_for("profile"))
            except Exception as exc:
                current_app.logger.exception("Student registration failed")
                error = f"Registration failed: {exc}"

    return render_template("signup.html", error=error)
