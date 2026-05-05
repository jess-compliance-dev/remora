from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.models.memory import Memory
from app.models.memory_video import MemoryVideo
from app.services.life_story_book_service import LifeStoryBookService
from app.services.profile_service import ProfileService
from app.services.story_service import StoryService

story_bp = Blueprint("stories", __name__)
story_service = StoryService()
profile_service = ProfileService()
life_story_book_service = LifeStoryBookService()


def get_profile_life_span(profile_id):
    profile = profile_service.get_profile_by_id(profile_id)

    if profile is None:
        return {
            "birth_date": None,
            "death_date": None,
        }

    return {
        "birth_date": profile.birth_date.isoformat()
        if getattr(profile, "birth_date", None)
        else None,
        "death_date": profile.death_date.isoformat()
        if getattr(profile, "death_date", None)
        else None,
    }


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
        "summary_json": getattr(story, "summary_json", None),
        "theme": story.theme,
        "emotion_tag": story.emotion_tag,
        "profile_life_span": get_profile_life_span(story.profile_id),
        "is_featured": story.is_featured,
        "created_at": story.created_at.isoformat() if story.created_at else None,
        "updated_at": story.updated_at.isoformat() if story.updated_at else None,
    }


def serialize_profile_for_life_story(profile):
    if profile is None:
        return None

    return {
        "profile_id": getattr(profile, "profile_id", None),
        "full_name": getattr(profile, "full_name", None),
        "relationship": getattr(profile, "relationship", None),
        "birth_date": profile.birth_date.isoformat()
        if getattr(profile, "birth_date", None)
        else None,
        "death_date": profile.death_date.isoformat()
        if getattr(profile, "death_date", None)
        else None,
        "status": getattr(profile, "status", None),
        "short_description": getattr(profile, "short_description", None),
        "profile_image_url": getattr(profile, "profile_image_url", None),
    }


def serialize_memory_for_life_story(memory):
    if memory is None:
        return None

    return {
        "memory_id": memory.memory_id,
        "owner_id": memory.owner_id,
        "profile_id": memory.profile_id,
        "memory_type": memory.memory_type,
        "file_url": memory.file_url,
        "original_filename": memory.original_filename,
        "created_at": memory.created_at.isoformat()
        if getattr(memory, "created_at", None)
        else None,
        "updated_at": memory.updated_at.isoformat()
        if getattr(memory, "updated_at", None)
        else None,
    }


def serialize_memory_video_for_life_story(video):
    if video is None:
        return None

    return {
        "video_id": getattr(video, "video_id", None),
        "profile_id": getattr(video, "profile_id", None),
        "story_id": getattr(video, "story_id", None),
        "created_by": getattr(video, "created_by", None),
        "title": getattr(video, "title", None),
        "status": getattr(video, "status", None),
        "video_url": getattr(video, "video_url", None),
        "created_at": video.created_at.isoformat()
        if getattr(video, "created_at", None)
        else None,
        "updated_at": video.updated_at.isoformat()
        if getattr(video, "updated_at", None)
        else None,
    }


def json_error(message, status_code=400):
    return jsonify({"error": message}), status_code


def current_user_id():
    return str(get_jwt_identity())


def story_belongs_to_user(story, user_id):
    if story is None:
        return False

    return str(story.created_by) == str(user_id)


def story_belongs_to_current_user(story):
    return story_belongs_to_user(story, current_user_id())


def profile_belongs_to_user(profile_id, user_id):
    profile = profile_service.get_profile_by_id(profile_id)

    if profile is None:
        return False

    return str(profile.owner_id) == str(user_id)


def sanitize_story_payload(data, *, allow_profile_id=False):
    """
    Prevent clients from changing ownership/system-managed fields.

    allow_profile_id=True is only intended for create_story(), where the client
    may provide the profile the story belongs to. The profile ownership is still
    checked server-side before the story is created.
    """
    sanitized = dict(data)

    protected_fields = {
        "story_id",
        "created_by",
        "source_session_id",
        "created_at",
        "updated_at",
        "profile_life_span",
        "birth_date",
        "death_date",
        "life_period",
        "location",
        "happened_at",
    }

    if not allow_profile_id:
        protected_fields.add("profile_id")

    for field in protected_fields:
        sanitized.pop(field, None)

    return sanitized


def get_latest_completed_video(profile_id, story_id, user_id):
    query = MemoryVideo.query.filter_by(
        profile_id=profile_id,
        created_by=int(user_id),
    )

    if story_id is not None:
        query = query.filter_by(story_id=story_id)

    videos = query.order_by(MemoryVideo.created_at.desc()).all()

    for video in videos:
        if video.status == "completed" and video.video_url:
            return video

    for video in videos:
        if video.video_url:
            return video

    return None


@story_bp.route("/life-story/profile/<int:profile_id>", methods=["GET"])
@jwt_required()
def get_life_story_book(profile_id):
    user_id = current_user_id()

    if not profile_belongs_to_user(profile_id, user_id):
        return json_error("Profile not found", 404)

    profile = profile_service.get_profile_by_id(profile_id)

    stories = story_service.get_stories_by_profile_id(profile_id) or []
    user_stories = [
        story for story in stories
        if story_belongs_to_user(story, user_id)
    ]

    featured_story = None

    for story in user_stories:
        if getattr(story, "is_featured", False):
            featured_story = story
            break

    if featured_story is None and user_stories:
        featured_story = user_stories[0]

    if featured_story is None:
        payload = {
            "profile": serialize_profile_for_life_story(profile),
            "story": None,
            "video": None,
            "chapters": life_story_book_service.build_chapters(
                profile=profile,
                story=None,
                memories=[],
            ),
            "memories": [],
            "empty_state": {
                "title": "No Life Story yet",
                "message": "Create or update a Life Story first, then return here.",
            },
        }
        return jsonify(payload), 200

    memories = (
        Memory.query
        .filter_by(profile_id=profile_id, owner_id=int(user_id))
        .order_by(Memory.created_at.asc())
        .all()
    )

    latest_video = get_latest_completed_video(
        profile_id=profile_id,
        story_id=featured_story.story_id,
        user_id=user_id,
    )

    chapters = life_story_book_service.build_chapters(
        profile=profile,
        story=featured_story,
        memories=memories,
    )

    payload = {
        "profile": serialize_profile_for_life_story(profile),
        "story": serialize_story(featured_story),
        "video": serialize_memory_video_for_life_story(latest_video),
        "chapters": chapters,
        "memories": [
            serialize_memory_for_life_story(memory)
            for memory in memories
        ],
        "empty_state": None,
    }

    return jsonify(payload), 200


@story_bp.route("", methods=["GET"])
@jwt_required()
def get_stories():
    user_id = current_user_id()

    stories = story_service.get_stories()
    user_stories = [
        story for story in stories
        if story_belongs_to_user(story, user_id)
    ]

    return jsonify([serialize_story(story) for story in user_stories]), 200


@story_bp.route("/<int:story_id>", methods=["GET"])
@jwt_required()
def get_story(story_id):
    story = story_service.get_story_by_id(story_id)

    if not story_belongs_to_current_user(story):
        return json_error("Story not found", 404)

    return jsonify(serialize_story(story)), 200


@story_bp.route("/profile/<int:profile_id>", methods=["GET"])
@jwt_required()
def get_stories_by_profile(profile_id):
    user_id = current_user_id()

    if not profile_belongs_to_user(profile_id, user_id):
        return json_error("Profile not found", 404)

    stories = story_service.get_stories_by_profile_id(profile_id)
    user_stories = [
        story for story in stories
        if story_belongs_to_user(story, user_id)
    ]

    return jsonify([serialize_story(story) for story in user_stories]), 200


@story_bp.route("", methods=["POST"])
@jwt_required()
def create_story():
    data = request.get_json(silent=True)

    if data is None:
        return json_error("Request body must be valid JSON", 400)

    user_id = current_user_id()
    payload = sanitize_story_payload(data, allow_profile_id=True)

    profile_id = payload.get("profile_id")
    if profile_id is None:
        return json_error("profile_id is required", 400)

    if not profile_belongs_to_user(profile_id, user_id):
        return json_error("Profile not found", 404)

    payload["profile_id"] = int(profile_id)
    payload["created_by"] = int(user_id)

    story = story_service.create_story(payload)

    if not story:
        return json_error("Unable to create story", 400)

    if not story_belongs_to_user(story, user_id):
        return json_error("Unable to create story", 400)

    return jsonify(serialize_story(story)), 201


@story_bp.route("/from-chat-session/<int:session_id>", methods=["POST"])
@jwt_required()
def create_story_from_chat_session(session_id):
    user_id = get_jwt_identity()

    story, error = story_service.create_story_from_chat_session(
        session_id=session_id,
        user_id=user_id,
    )

    if error:
        if error == "Forbidden":
            return json_error("Story not found", 404)

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
    user_id = get_jwt_identity()

    if not profile_belongs_to_user(profile_id, user_id):
        return json_error("Profile not found", 404)

    stories, error = story_service.auto_create_stories_for_profile(
        profile_id=profile_id,
        user_id=user_id,
    )

    if error:
        if error == "Forbidden":
            return json_error("Profile not found", 404)

        if "not found" in error.lower():
            return json_error(error, 404)

        return json_error(error, 400)

    return jsonify(
        {
            "message": "Life stories checked successfully",
            "stories": [serialize_story(story) for story in stories],
        }
    ), 200


@story_bp.route("/create-combined/profile/<int:profile_id>", methods=["POST"])
@jwt_required()
def create_combined_story_for_profile(profile_id):
    user_id = get_jwt_identity()

    if not profile_belongs_to_user(profile_id, user_id):
        return json_error("Profile not found", 404)

    story, error = story_service.create_combined_story_for_profile(
        profile_id=profile_id,
        user_id=user_id,
    )

    if error:
        if error == "Forbidden":
            return json_error("Profile not found", 404)

        if "not found" in error.lower():
            return json_error(error, 404)

        return json_error(error, 400)

    return jsonify(
        {
            "message": "Combined life story created successfully",
            "story": serialize_story(story),
        }
    ), 201


@story_bp.route("/update-combined/profile/<int:profile_id>", methods=["POST"])
@jwt_required()
def update_combined_story_for_profile(profile_id):
    user_id = get_jwt_identity()

    if not profile_belongs_to_user(profile_id, user_id):
        return json_error("Profile not found", 404)

    story, error, update_status = story_service.update_combined_story_for_profile(
        profile_id=profile_id,
        user_id=user_id,
    )

    if error:
        if error == "Forbidden":
            return json_error("Profile not found", 404)

        if "not found" in error.lower():
            return json_error(error, 404)

        return json_error(error, 400)

    message = "Life story updated"

    if update_status == "no_changes":
        message = "No new memories or photos found"

    return jsonify(
        {
            "message": message,
            "update_status": update_status,
            "story": serialize_story(story),
        }
    ), 200


@story_bp.route("/<int:story_id>", methods=["PUT"])
@jwt_required()
def update_story(story_id):
    user_id = current_user_id()

    existing_story = story_service.get_story_by_id(story_id)

    if not story_belongs_to_user(existing_story, user_id):
        return json_error("Story not found", 404)

    data = request.get_json(silent=True)

    if data is None:
        return json_error("Request body must be valid JSON", 400)

    payload = sanitize_story_payload(data, allow_profile_id=False)

    story = story_service.update_story(story_id, payload)

    if not story:
        return json_error("Story not found", 404)

    if not story_belongs_to_user(story, user_id):
        return json_error("Story not found", 404)

    return jsonify(serialize_story(story)), 200


@story_bp.route("/<int:story_id>", methods=["DELETE"])
@jwt_required()
def delete_story(story_id):
    user_id = current_user_id()

    existing_story = story_service.get_story_by_id(story_id)

    if not story_belongs_to_user(existing_story, user_id):
        return json_error("Story not found", 404)

    deleted = story_service.delete_story(story_id)

    if not deleted:
        return json_error("Story not found", 404)

    return jsonify({"message": "Story deleted successfully"}), 200
