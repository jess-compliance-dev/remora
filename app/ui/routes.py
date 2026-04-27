from flask import Blueprint, render_template, request, redirect, url_for

from app.services.profile_service import ProfileService
from app.services.story_service import StoryService

ui_bp = Blueprint("ui", __name__)

profile_service = ProfileService()
story_service = StoryService()


def render_ui(template_name, *, active_tab=None, show_bottom_nav=False, **context):
    return render_template(
        template_name,
        active_tab=active_tab,
        show_bottom_nav=show_bottom_nav,
        **context
    )


# -----------------------------------------------------------------------------
# Auth pages
# -----------------------------------------------------------------------------

@ui_bp.route("/ui/login")
def login():
    return render_ui(
        "auth/login.html",
        show_bottom_nav=False,
        show_topbar=False
    )


@ui_bp.route("/ui/register")
def register():
    return render_ui(
        "auth/register.html",
        show_bottom_nav=False,
        show_topbar=False
    )


@ui_bp.route("/ui/check-email")
def check_email():
    return render_ui(
        "auth/check_email.html",
        show_bottom_nav=False
    )


@ui_bp.route("/ui/email-confirmed")
def email_confirmed():
    return render_ui(
        "auth/email_confirmed.html",
        show_bottom_nav=False
    )


# -----------------------------------------------------------------------------
# Profile selection and dashboard
# -----------------------------------------------------------------------------

@ui_bp.route("/ui/select-profiles")
def select_profiles():
    return render_ui(
        "profiles/select.html",
        active_tab=None,
        show_bottom_nav=False
    )


@ui_bp.route("/ui/dashboard")
def dashboard():
    return render_ui(
        "dashboard/index.html",
        show_bottom_nav=False
    )


@ui_bp.route("/ui/profiles")
def profiles():
    return redirect(url_for("ui.select_profiles"))


@ui_bp.route("/ui/profiles/create")
def create_profile():
    return render_ui(
        "profiles/create.html",
        show_bottom_nav=False
    )


@ui_bp.route("/ui/profiles/<int:profile_id>")
def profile_detail(profile_id):
    return render_ui(
        "profiles/profile_setting.html",
        profile_id=profile_id,
        active_tab="profile",
        show_bottom_nav=True
    )


# -----------------------------------------------------------------------------
# Chat pages
# -----------------------------------------------------------------------------

@ui_bp.route("/ui/chat-home")
def chat_home():
    return render_ui(
        "chat/home.html",
        active_tab="chat",
        show_bottom_nav=True
    )


@ui_bp.route("/ui/chat/start")
def start_chat():
    profile_id = request.args.get("profile_id", type=int)

    if not profile_id:
        return redirect(url_for("ui.select_profiles"))

    profile = profile_service.get_profile_by_id(profile_id)

    if not profile:
        return redirect(url_for("ui.select_profiles"))

    return render_ui(
        "chat/start.html",
        profile=profile,
        profile_id=profile_id,
        active_tab="chat",
        show_bottom_nav=True
    )


@ui_bp.route("/ui/chat/<int:session_id>")
def chat(session_id):
    profile_id = request.args.get("profile_id", type=int)
    profile = profile_service.get_profile_by_id(profile_id) if profile_id else None

    return render_ui(
        "chat/session.html",
        session_id=session_id,
        profile_id=profile_id,
        profile=profile,
        active_tab="chat",
        show_bottom_nav=True
    )


# -----------------------------------------------------------------------------
# Life story pages
# -----------------------------------------------------------------------------

@ui_bp.route("/ui/life-stories")
def life_stories_legacy():
    """
    Old route.
    If profile_id is provided, redirect to the new profile-specific Life Stories page.
    Otherwise return to dashboard.
    """

    profile_id = request.args.get("profile_id", type=int)

    if profile_id:
        return redirect(url_for("ui.profile_life_stories", profile_id=profile_id))

    return redirect(url_for("ui.dashboard"))


@ui_bp.route("/ui/stories")
def stories_home():
    """
    Fallback route for Life Stories.
    """

    profile_id = request.args.get("profile_id", type=int)

    if profile_id:
        return redirect(url_for("ui.profile_life_stories", profile_id=profile_id))

    return redirect(url_for("ui.dashboard"))


@ui_bp.route("/ui/stories/profile/<int:profile_id>")
def profile_life_stories(profile_id):
    """
    Life Stories overview page for one profile.

    Template:
    stories/index.html

    This page can:
    - show existing Life Stories
    - create Life Stories from saved chat sessions via the button
    """

    profile = profile_service.get_profile_by_id(profile_id)

    if not profile:
        return redirect(url_for("ui.select_profiles"))

    stories = story_service.get_stories_by_profile_id(profile_id)

    return render_ui(
        "stories/index.html",
        profile=profile,
        profile_id=profile_id,
        stories=stories,
        active_tab="life_stories",
        show_bottom_nav=True
    )


@ui_bp.route("/ui/stories/<int:story_id>")
def story_detail(story_id):
    """
    Single Life Story detail page.

    Template:
    stories/view_story.html
    """

    story = story_service.get_story_by_id(story_id)

    if not story:
        return redirect(url_for("ui.dashboard"))

    profile = profile_service.get_profile_by_id(story.profile_id)

    return render_ui(
        "stories/view_story.html",
        story=story,
        profile=profile,
        active_tab="life_stories",
        show_bottom_nav=True
    )


@ui_bp.route("/ui/story/<int:story_id>")
def story_legacy(story_id):
    """
    Old route for one story.
    Redirects to the new Life Story detail route.
    """

    return redirect(url_for("ui.story_detail", story_id=story_id))


# -----------------------------------------------------------------------------
# Memory pages
# -----------------------------------------------------------------------------

@ui_bp.route("/ui/memories")
def memories():
    profile_id = request.args.get("profile_id", type=int)

    if not profile_id:
        return redirect(url_for("ui.select_profiles"))

    profile = profile_service.get_profile_by_id(profile_id)

    if not profile:
        return redirect(url_for("ui.select_profiles"))

    return render_ui(
        "memories/list.html",
        profile=profile,
        profile_id=profile_id,
        active_tab="memories",
        show_bottom_nav=True
    )


@ui_bp.route("/ui/memories/select-profile")
def select_memory_profile():
    return render_ui(
        "memories/select_profile.html",
        active_tab="memories",
        show_bottom_nav=True
    )


@ui_bp.route("/ui/memories/create")
def create_memory():
    profile_id = request.args.get("profile_id", type=int)

    if not profile_id:
        return redirect(url_for("ui.select_profiles"))

    profile = profile_service.get_profile_by_id(profile_id)

    if not profile:
        return redirect(url_for("ui.select_profiles"))

    return render_ui(
        "memories/create.html",
        profile=profile,
        profile_id=profile_id,
        active_tab="memories",
        show_bottom_nav=True
    )


@ui_bp.route("/ui/memories/add")
def add_memory():
    profile_id = request.args.get("profile_id", type=int)

    if not profile_id:
        return redirect(url_for("ui.select_profiles"))

    profile = profile_service.get_profile_by_id(profile_id)

    if not profile:
        return redirect(url_for("ui.select_profiles"))

    return render_ui(
        "memories/add_memory.html",
        profile=profile,
        profile_id=profile_id,
        active_tab="memories",
        show_bottom_nav=True,
    )


@ui_bp.route("/ui/memories/<int:memory_id>")
def memory_detail(memory_id):
    return render_ui(
        "memories/profile_setting.html",
        memory_id=memory_id,
        active_tab="memories",
        show_bottom_nav=True
    )


# -----------------------------------------------------------------------------
# Time capsule
# -----------------------------------------------------------------------------

@ui_bp.route("/ui/time-capsule")
def time_capsule():
    return render_ui(
        "time_capsule/index.html",
        active_tab="time_capsule",
        show_bottom_nav=True
    )