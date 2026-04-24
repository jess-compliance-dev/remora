from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.services.story_service import StoryService

story_bp = Blueprint("stories", __name__)
story_service = StoryService()


def serialize_story(story):
    if story is None:
        return None

    return {
        "story_id": story.story_id,
        "profile_id": story.profile_id,
        "created_by": story.created_by,
        "source_session_id": story.source_session_id,
        "title": story.title,
        "prompt_question": story.prompt_question,
        "story_text": story.story_text,
        "source_type": story.source_type,
        "audio_url": story.audio_url,
        "summary": story.summary,
        "theme": story.theme,
        "emotion_tag": story.emotion_tag,
        "life_period": story.life_period,
        "location": story.location,
        "happened_at": story.happened_at.isoformat() if story.happened_at else None,
        "is_featured": story.is_featured,
        "created_at": story.created_at.isoformat() if story.created_at else None,
        "updated_at": story.updated_at.isoformat() if story.updated_at else None,
    }


def json_error(message, status_code=400):
    return jsonify({"error": message}), status_code


@story_bp.route("", methods=["GET"])
@jwt_required()
def get_stories():
    """
    Return all stories.

    Note:
    This currently returns all stories from the database.
    Later you may want to restrict this to the logged-in user.
    """

    stories = story_service.get_stories()

    return jsonify([serialize_story(story) for story in stories]), 200


@story_bp.route("/<int:story_id>", methods=["GET"])
@jwt_required()
def get_story(story_id):
    """
    Return one story by story_id.
    """

    story = story_service.get_story_by_id(story_id)

    if not story:
        return json_error("Story not found", 404)

    return jsonify(serialize_story(story)), 200


@story_bp.route("/profile/<int:profile_id>", methods=["GET"])
@jwt_required()
def get_stories_by_profile(profile_id):
    """
    Return all stories for one memorial profile.
    """

    stories = story_service.get_stories_by_profile_id(profile_id)

    return jsonify([serialize_story(story) for story in stories]), 200


@story_bp.route("", methods=["POST"])
@jwt_required()
def create_story():
    """
    Manually create a story from request JSON.
    """

    data = request.get_json(silent=True)

    if data is None:
        return json_error("Request body must be valid JSON", 400)

    story = story_service.create_story(data)

    if not story:
        return json_error("Unable to create story", 400)

    return jsonify(serialize_story(story)), 201


@story_bp.route("/from-chat-session/<int:session_id>", methods=["POST"])
@jwt_required()
def create_story_from_chat_session(session_id):
    """
    Create one life story from one specific chat session.
    """

    user_id = get_jwt_identity()

    story, error = story_service.create_story_from_chat_session(
        session_id=session_id,
        user_id=user_id,
    )

    if error:
        if error == "Forbidden":
            return json_error(error, 403)

        if "not found" in error.lower():
            return json_error(error, 404)

        return json_error(error, 400)

    return jsonify(
        {
            "message": "Life story created successfully",
            "story": serialize_story(story),
        }
    ), 201


@story_bp.route("/auto-create/profile/<int:profile_id>", methods=["POST"])
@jwt_required()
def auto_create_stories_for_profile(profile_id):
    """
    Create missing life stories from existing chat sessions for one profile.

    This is used by:
    /ui/stories/profile/<profile_id>

    The frontend button "Create Life Stories" calls this endpoint.
    """

    user_id = get_jwt_identity()

    stories, error = story_service.auto_create_stories_for_profile(
        profile_id=profile_id,
        user_id=user_id,
    )

    if error:
        if error == "Forbidden":
            return json_error(error, 403)

        if "not found" in error.lower():
            return json_error(error, 404)

        return json_error(error, 400)

    return jsonify(
        {
            "message": "Life stories checked successfully",
            "stories": [serialize_story(story) for story in stories],
        }
    ), 200


@story_bp.route("/<int:story_id>", methods=["PUT"])
@jwt_required()
def update_story(story_id):
    """
    Update an existing story.
    """

    data = request.get_json(silent=True)

    if data is None:
        return json_error("Request body must be valid JSON", 400)

    story = story_service.update_story(story_id, data)

    if not story:
        return json_error("Story not found", 404)

    return jsonify(serialize_story(story)), 200


@story_bp.route("/<int:story_id>", methods=["DELETE"])
@jwt_required()
def delete_story(story_id):
    """
    Delete an existing story.
    """

    deleted = story_service.delete_story(story_id)

    if not deleted:
        return json_error("Story not found", 404)

    return jsonify({"message": "Story deleted successfully"}), 200
