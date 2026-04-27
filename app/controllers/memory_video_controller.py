from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.services.memory_video_service import MemoryVideoService

memory_video_bp = Blueprint("memory_videos", __name__)
memory_video_service = MemoryVideoService()


def serialize_memory_video(video):
    if video is None:
        return None

    return {
        "video_id": video.video_id,
        "profile_id": video.profile_id,
        "story_id": video.story_id,
        "created_by": video.created_by,
        "title": video.title,
        "status": video.status,
        "storyboard_json": video.storyboard_json,
        "music_prompt": video.music_prompt,
        "music_url": video.music_url,
        "mubert_track_id": video.mubert_track_id,
        "creatomate_render_id": video.creatomate_render_id,
        "video_url": video.video_url,
        "error_message": video.error_message,
        "created_at": video.created_at.isoformat() if video.created_at else None,
        "updated_at": video.updated_at.isoformat() if video.updated_at else None,
    }


def json_error(message, status_code=400):
    return jsonify({"error": message}), status_code


@memory_video_bp.route("/from-story/<int:story_id>", methods=["POST"])
@jwt_required()
def create_memory_video_from_story(story_id):
    user_id = get_jwt_identity()

    video, error = memory_video_service.create_video_from_story(
        story_id=story_id,
        user_id=user_id,
    )

    if error and not video:
        if error == "Forbidden":
            return json_error(error, 403)

        if "not found" in error.lower():
            return json_error(error, 404)

        return json_error(error, 400)

    status_code = 202 if video and video.status != "failed" else 400

    return jsonify(
        {
            "message": "Memory video generation started" if status_code == 202 else "Memory video generation failed",
            "video": serialize_memory_video(video),
            "error": error,
        }
    ), status_code


@memory_video_bp.route("/<int:video_id>", methods=["GET"])
@jwt_required()
def get_memory_video(video_id):
    user_id = get_jwt_identity()

    video, error = memory_video_service.get_video_by_id(
        video_id=video_id,
        user_id=user_id,
    )

    if error:
        if error == "Forbidden":
            return json_error("Memory video not found", 404)

        if "not found" in error.lower():
            return json_error(error, 404)

        return json_error(error, 400)

    return jsonify(serialize_memory_video(video)), 200


@memory_video_bp.route("/story/<int:story_id>", methods=["GET"])
@jwt_required()
def get_memory_videos_by_story(story_id):
    user_id = get_jwt_identity()

    videos, error = memory_video_service.get_videos_by_story_id(
        story_id=story_id,
        user_id=user_id,
    )

    if error:
        if error == "Forbidden":
            return json_error("Life story not found", 404)

        if "not found" in error.lower():
            return json_error(error, 404)

        return json_error(error, 400)

    return jsonify([serialize_memory_video(video) for video in videos]), 200


@memory_video_bp.route("/<int:video_id>/refresh-status", methods=["POST"])
@jwt_required()
def refresh_memory_video_status(video_id):
    user_id = get_jwt_identity()

    video, error = memory_video_service.refresh_render_status(
        video_id=video_id,
        user_id=user_id,
    )

    if error and not video:
        if error == "Forbidden":
            return json_error("Memory video not found", 404)

        if "not found" in error.lower():
            return json_error(error, 404)

        return json_error(error, 400)

    return jsonify(
        {
            "message": "Memory video status refreshed",
            "video": serialize_memory_video(video),
            "error": error,
        }
    ), 200
