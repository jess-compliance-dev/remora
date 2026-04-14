from flask import Blueprint, request, jsonify

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
def create_session():
    """
    Create a new chat session.
    """
    data = request.get_json()
    session = chat_session_service.create_session(data)
    return jsonify(serialize_session(session)), 201


@chat_session_bp.route("/<int:session_id>", methods=["PUT"])
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
