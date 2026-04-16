from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.services.story_service import StoryService
from app.services.story_media_service import StoryMediaService

story_bp = Blueprint("stories", __name__)
story_service = StoryService()
story_media_service = StoryMediaService()


def serialize_story(story):
    """
    Convert a LifeStory object into a JSON-serializable dictionary.
    """
    if story is None:
        return None

    return {
        "story_id": story.story_id,
        "profile_id": story.profile_id,
        "created_by": story.created_by,
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


def serialize_story_media(media):
    """
    Convert a StoryMedia object into a JSON-serializable dictionary.
    """
    if media is None:
        return None

    return {
        "media_id": media.media_id,
        "story_id": media.story_id,
        "media_type": media.media_type,
        "file_url": media.file_url,
        "caption": media.caption,
        "created_at": media.created_at.isoformat() if media.created_at else None,
    }


@story_bp.route("", methods=["GET"])
def get_stories():
    """
    Retrieve all life stories.
    """
    stories = story_service.get_stories()
    return jsonify([serialize_story(story) for story in stories]), 200


@story_bp.route("/<int:story_id>", methods=["GET"])
def get_story(story_id):
    """
    Retrieve a single life story by ID including attached media.
    """
    story = story_service.get_story_by_id(story_id)

    if not story:
        return jsonify({"error": "Story not found"}), 404

    media_entries = story_media_service.get_media_by_story_id(story_id)

    story_data = serialize_story(story)
    story_data["media"] = [serialize_story_media(media) for media in media_entries]

    return jsonify(story_data), 200


@story_bp.route("", methods=["POST"])
@jwt_required()
def create_story():
    """
    Create a new life story for the currently authenticated user.
    """
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    user_id = get_jwt_identity()
    data["created_by"] = user_id

    story = story_service.create_story(data)

    if not story:
        return jsonify({"error": "Unable to create story"}), 400

    return jsonify(serialize_story(story)), 201


@story_bp.route("/<int:story_id>", methods=["PUT"])
@jwt_required()
def update_story(story_id):
    """
    Update an existing life story.
    """
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    story = story_service.update_story(story_id, data)

    if not story:
        return jsonify({"error": "Story not found"}), 404

    return jsonify(serialize_story(story)), 200


@story_bp.route("/<int:story_id>", methods=["DELETE"])
@jwt_required()
def delete_story(story_id):
    """
    Delete a life story.
    """
    deleted = story_service.delete_story(story_id)

    if not deleted:
        return jsonify({"error": "Story not found"}), 404

    return jsonify({"message": "Story deleted successfully"}), 200


@story_bp.route("/profile/<int:profile_id>", methods=["GET"])
def get_stories_by_profile(profile_id):
    """
    Retrieve all life stories for a memorial profile.
    """
    stories = story_service.get_stories_by_profile_id(profile_id)
    return jsonify([serialize_story(story) for story in stories]), 200
