from flask import Blueprint, render_template

ui_bp = Blueprint("ui", __name__)

@ui_bp.route("/ui/login")
def login():
    return render_template("auth/login.html")

@ui_bp.route("/ui/register")
def register():
    return render_template("auth/register.html")

@ui_bp.route("/ui/check-email")
def check_email():
    return render_template("auth/check_email.html")

@ui_bp.route("/ui/email-confirmed")
def email_confirmed():
    return render_template("auth/email_confirmed.html")

@ui_bp.route("/ui/dashboard")
def dashboard():
    return render_template("dashboard/index.html")

@ui_bp.route("/ui/profiles")
def profiles():
    return render_template("profiles/list.html")

@ui_bp.route("/ui/profiles/create")
def create_profile():
    return render_template("profiles/create.html")

@ui_bp.route("/ui/profiles/<int:profile_id>")
def profile_detail(profile_id):
    return render_template("profiles/detail.html", profile_id=profile_id)

@ui_bp.route("/ui/chat")
def chat():
    return render_template("chat/session.html")

@ui_bp.route("/ui/story")
def story():
    return render_template("stories/detail.html")

@ui_bp.route("/ui/memories/create")
def create_memory():
    return render_template("memories/create.html")
