from flask import Blueprint, current_app, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

from auth.store import find_student_by_email


login_bp = Blueprint("auth_login", __name__)


@login_bp.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        try:
            student = find_student_by_email(email)

            if not student or not check_password_hash(student["password"], password):
                error = "Invalid email or password."
            else:
                session["student_id"] = student["id"]
                session["student_email"] = student["email"]
                session["student_name"] = student["full_name"]
                return redirect(url_for("profile"))
        except Exception as exc:
            current_app.logger.exception("Student login failed")
            error = f"Login failed: {exc}"

    return render_template("login.html", error=error)


@login_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))
