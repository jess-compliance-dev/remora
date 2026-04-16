from flask import Blueprint, request, jsonify

from app.services.story_media_service import StoryMediaService

story_media_bp = Blueprint("story_media", __name__)
story_media_service = StoryMediaService()


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


@story_media_bp.route("", methods=["GET"])
def get_story_media():
    """
    Retrieve all story media entries.
    """
    media_entries = story_media_service.get_media()
    return jsonify([serialize_story_media(media) for media in media_entries]), 200


@story_media_bp.route("/<int:media_id>", methods=["GET"])
def get_story_media_by_id(media_id):
    """
    Retrieve a single story media entry by ID.
    """
    media = story_media_service.get_media_by_id(media_id)

    if not media:
        return jsonify({"error": "Media not found"}), 404

    return jsonify(serialize_story_media(media)), 200


@story_media_bp.route("", methods=["POST"])
def create_story_media():
    """
    Create a new story media entry.
    """
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    media = story_media_service.create_media(data)

    if not media:
        return jsonify({"error": "Unable to create media"}), 400

    return jsonify(serialize_story_media(media)), 201


@story_media_bp.route("/<int:media_id>", methods=["DELETE"])
def delete_story_media(media_id):
    """
    Delete a story media entry.
    """
    deleted = story_media_service.delete_media(media_id)

    if not deleted:
        return jsonify({"error": "Media not found"}), 404

    return jsonify({"message": "Story media deleted successfully"}), 200


@story_media_bp.route("/story/<int:story_id>", methods=["GET"])
def get_media_by_story(story_id):
    """
    Retrieve all media entries for a specific story.
    """
    media_entries = story_media_service.get_media_by_story_id(story_id)
    return jsonify([serialize_story_media(media) for media in media_entries]), 200
