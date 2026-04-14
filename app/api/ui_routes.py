from flask import Blueprint, render_template

ui_bp = Blueprint("ui", __name__, template_folder="../templates", static_folder="../static")


@ui_bp.route("/ui/login")
def ui_login():
    return render_template("auth/login.html")


@ui_bp.route("/ui/register")
def ui_register():
    return render_template("auth/register.html")


@ui_bp.route("/ui/profiles")
def ui_profiles():
    profiles = [
        {"id": 1, "name": "Mom", "subtitle": "Always with you", "stories": 12},
        {"id": 2, "name": "Erika", "subtitle": "Grandmother", "stories": 8},
        {"id": 3, "name": "Paul", "subtitle": "Father", "stories": 5},
    ]
    return render_template("profiles/list.html", profiles=profiles)


@ui_bp.route("/ui/profiles/<int:profile_id>")
def ui_profile_detail(profile_id):
    profile = {
        "id": profile_id,
        "name": "Mom",
        "subtitle": "Always with you",
        "years": "March 3, 1958 – June 12, 2020",
        "bio": "Loving mom, endless heart, forever here.",
        "stories_count": 48,
    }
    return render_template("profiles/detail.html", profile=profile)


@ui_bp.route("/ui/chat")
def ui_chat():
    messages = [
        {"role": "assistant", "text": "Hi, I'm here. Tell me about a childhood memory that still feels vivid."},
        {"role": "user", "text": "She used to wake me up at night to watch the stars."},
        {"role": "assistant", "text": "That sounds beautiful. How old were you at the time?"},
        {"role": "user", "text": "Maybe eleven or twelve."},
    ]
    referenced = [
        {"type": "Photo", "title": "Family Dinner", "date": "Mar 18, 2023"},
        {"type": "Voice", "title": "Voice Note", "date": "Apr 2, 2022"},
        {"type": "Photo", "title": "Garden Night", "date": "May 12, 2021"},
    ]
    return render_template("chat/session.html", messages=messages, referenced=referenced)


@ui_bp.route("/ui/stories/<int:story_id>")
def ui_story_detail(story_id):
    story = {
        "id": story_id,
        "title": "The Night of Falling Stars",
        "summary": "A quiet childhood memory of watching the night sky together.",
        "theme": "family",
        "emotion": "nostalgic",
        "text": "She used to wake me up after midnight, wrap me in a blanket, and take me out to the garden to watch the stars. We would sit quietly in the cold air, and she would tell me that beautiful things reveal themselves to patient people.",
    }
    media = [
        {"type": "image", "url": "/static/img/story-photo.svg", "caption": "Garden memory"},
        {"type": "audio", "url": "#", "caption": "Voice note"},
    ]
    return render_template("stories/detail.html", story=story, media=media)
