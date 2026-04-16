from flask import Blueprint, render_template, request, redirect, url_for
from flask_jwt_extended import jwt_required, get_jwt_identity

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
@jwt_required(optional=True)
def dashboard():
    """
    Dashboard with the 4 core functions:
    1) Create a memorial profile
    2) View Profiles
    3) Add a memory
    4) View life stories
    """
    user_id = get_jwt_identity()
    profiles = []

    if user_id:
        # Falls dein Service nur get_profiles_by_owner_id hat, ist das korrekt so.
        profiles = profile_service.get_profiles_by_owner_id(user_id)

    has_profiles = len(profiles) > 0

    return render_template(
        "dashboard/index.html",
        profiles=profiles,
        has_profiles=has_profiles
    )


@ui_bp.route("/ui/profiles")
def profiles():
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
@jwt_required(optional=True)
def select_memory_profile():
    """
    Selecting the profile.
    """
    user_id = get_jwt_identity()
    profiles = []

    if user_id:
        profiles = profile_service.get_profiles_by_owner_id(user_id)

    if len(profiles) == 1:
        return redirect(url_for("ui.create_memory", profile_id=profiles[0].profile_id))

    return render_template(
        "memories/select_profile.html",
        profiles=profiles
    )


@ui_bp.route("/ui/memories/create")
@jwt_required(optional=True)
def create_memory():
    """
    Memory creation page.
    """
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
