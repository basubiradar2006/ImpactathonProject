from flask import Flask, render_template

app = Flask(__name__)

student_profile = {
    "name": "Ananya Sharma",
    "student_id": "CSE2026-041",
    "department": "Computer Science Engineering",
    "year": "Final Year",
    "email": "ananya.sharma@college.edu",
    "phone": "+91 98765 43210",
    "target_role": "Full Stack Developer",
    "location": "Bengaluru, India",
    "cgpa": 8.4,
    "readiness_score": 72,
    "readiness_level": "Placement Ready With Gaps",
    "resume_score": 78,
    "project_depth": 86,
    "hackathon_score": 68,
    "cloud_readiness": 38,
    "coding_score": 74,
    "skills": [
        {"name": "Python", "level": 82, "status": "Strong"},
        {"name": "React", "level": 76, "status": "Good"},
        {"name": "SQL", "level": 70, "status": "Good"},
        {"name": "Docker", "level": 42, "status": "Needs Work"},
        {"name": "AWS", "level": 35, "status": "Priority Gap"},
        {"name": "System Design", "level": 45, "status": "Needs Work"},
    ],
    "projects": [
        {
            "title": "Campus Placement Tracker",
            "tech": "Flask, SQLite, Bootstrap",
            "impact": "Tracked student applications and placement status for a department demo.",
        },
        {
            "title": "AI Resume Matcher",
            "tech": "Python, NLP, Streamlit",
            "impact": "Compared resumes with job descriptions and generated missing keyword reports.",
        },
        {
            "title": "Student Attendance Analytics",
            "tech": "React, REST API, PostgreSQL",
            "impact": "Visualized attendance risk patterns for mentor review.",
        },
    ],
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

@app.route('/')
def home():
    return render_template('home.html', student=student_profile)

@app.route('/profile')
def profile():
    return render_template('profile.html', student=student_profile)

if __name__ == '__main__':
    app.run(debug=True)
