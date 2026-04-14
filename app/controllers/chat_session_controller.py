from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.services.chat_session_service import ChatSessionService

chat_session_bp = Blueprint("chat_sessions", __name__)
chat_session_service = ChatSessionService()


def serialize_session(session):
    """
    Convert a ChatSession object into a JSON-serializable dictionary.
    """
    return {
        "session_id": session.session_id,
        "profile_id": session.profile_id,
        "user_id": session.user_id,
        "category": session.category,
        "status": session.status,
        "started_at": session.started_at.isoformat(),
        "ended_at": session.ended_at.isoformat() if session.ended_at else None,
    }


@chat_session_bp.route("", methods=["GET"])
def get_sessions():
    """
    Retrieve all chat sessions.
    """
    sessions = chat_session_service.get_sessions()
    return jsonify([serialize_session(session) for session in sessions]), 200


@chat_session_bp.route("/<int:session_id>", methods=["GET"])
def get_session(session_id):
    """
    Retrieve a single chat session by ID.
    """
    session = chat_session_service.get_session_by_id(session_id)

    if not session:
        return jsonify({"error": "Session not found"}), 404

    return jsonify(serialize_session(session)), 200


@chat_session_bp.route("", methods=["POST"])
@jwt_required()
def create_session():
    """
    Create a new guided chat session for the currently authenticated user.
    """
    data = request.get_json()
    user_id = get_jwt_identity()

    data["user_id"] = user_id

    session = chat_session_service.create_session(data)
    return jsonify(serialize_session(session)), 201


@chat_session_bp.route("/<int:session_id>", methods=["PUT"])
@jwt_required()
def update_session(session_id):
    """
    Update a chat session.
    """
    data = request.get_json()
    session = chat_session_service.update_session(session_id, data)

    if not session:
        return jsonify({"error": "Session not found"}), 404

    return jsonify(serialize_session(session)), 200


@chat_session_bp.route("/<int:session_id>", methods=["DELETE"])
@jwt_required()
def delete_session(session_id):
    """
    Delete a chat session.
    """
    deleted = chat_session_service.delete_session(session_id)

    if not deleted:
        return jsonify({"error": "Session not found"}), 404

    return jsonify({"message": "Session deleted successfully"}), 200


@chat_session_bp.route("/profile/<int:profile_id>", methods=["GET"])
def get_sessions_by_profile(profile_id):
    """
    Retrieve all chat sessions for a memorial profile.
    """
    sessions = chat_session_service.get_sessions_by_profile_id(profile_id)
    return jsonify([serialize_session(session) for session in sessions]), 200


@chat_session_bp.route("/<int:session_id>/generate-story", methods=["POST"])
@jwt_required()
def generate_story(session_id):
    """
    Generate a life story from a chat session.
    """
    story = chat_session_service.generate_story_from_session(session_id)

    if not story:
        return jsonify({"error": "Unable to generate story"}), 400

    return jsonify({
        "message": "Story generated successfully",
        "story_id": story.story_id
    }), 201
