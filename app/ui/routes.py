from flask import Blueprint, render_template, request, redirect, url_for

from app.services.profile_service import ProfileService

ui_bp = Blueprint("ui", __name__)
profile_service = ProfileService()


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
    """
    Dashboard state is handled client-side via /api/profiles
    because the JWT currently lives in localStorage.
    """
    return render_template("dashboard/index.html")


@ui_bp.route("/ui/profiles")
def profiles():
    """
    Profiles list is loaded client-side from /api/profiles.
    """
    return render_template("profiles/list.html")


@ui_bp.route("/ui/profiles/create")
def create_profile():
    return render_template("profiles/create.html")


@ui_bp.route("/ui/profiles/<int:profile_id>")
def profile_detail(profile_id):
    return render_template("profiles/detail.html", profile_id=profile_id)


@ui_bp.route("/ui/life-stories")
def life_stories():
    return render_template("stories/list.html")


@ui_bp.route("/ui/chat/<int:session_id>")
def chat(session_id):
    return render_template("chat/session.html", session_id=session_id)


@ui_bp.route("/ui/story/<int:story_id>")
def story(story_id):
    return render_template("stories/detail.html", story_id=story_id)


@ui_bp.route("/ui/memories/select-profile")
def select_memory_profile():
    """
    Profiles are loaded client-side from /api/profiles.
    """
    return render_template("memories/select_profile.html")


@ui_bp.route("/ui/memories/create")
def create_memory():
    profile_id = request.args.get("profile_id", type=int)

    if not profile_id:
        return redirect(url_for("ui.select_memory_profile"))

    profile = profile_service.get_profile_by_id(profile_id)

    if not profile:
        return redirect(url_for("ui.select_memory_profile"))

    return render_template(
        "memories/create.html",
        profile=profile,
        profile_id=profile_id
    )


@ui_bp.route("/ui/chat/start")
def start_chat():
    profile_id = request.args.get("profile_id", type=int)

    if not profile_id:
        return redirect(url_for("ui.select_memory_profile"))

    profile = profile_service.get_profile_by_id(profile_id)

    if not profile:
        return redirect(url_for("ui.select_memory_profile"))

    return render_template("chat/start.html", profile=profile, profile_id=profile_id)