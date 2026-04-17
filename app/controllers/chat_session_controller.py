from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.services.chat_session_service import ChatSessionService

chat_session_bp = Blueprint("chat_sessions", __name__)
chat_session_service = ChatSessionService()


def serialize_session(session):
    if session is None:
        return None

    return {
        "session_id": session.session_id,
        "profile_id": session.profile_id,
        "user_id": session.user_id,
        "category": session.category,
        "status": session.status,
        "started_at": session.started_at.isoformat() if session.started_at else None,
        "ended_at": session.ended_at.isoformat() if session.ended_at else None,
        "created_at": session.created_at.isoformat() if getattr(session, "created_at", None) else None,
        "updated_at": session.updated_at.isoformat() if getattr(session, "updated_at", None) else None,
        "is_active": session.status == "active",
    }


def json_error(message, status_code=400, details=None):
    payload = {"error": message}
    if details:
        payload["details"] = details
    return jsonify(payload), status_code


def is_owner(session, user_id):
    if session is None:
        return False
    return str(session.user_id) == str(user_id)


@chat_session_bp.route("", methods=["GET"])
@jwt_required()
def get_sessions():
    user_id = get_jwt_identity()
    sessions = chat_session_service.get_sessions()

    own_sessions = [
        session for session in sessions
        if str(session.user_id) == str(user_id)
    ]

    return jsonify([serialize_session(session) for session in own_sessions]), 200


@chat_session_bp.route("/<int:session_id>", methods=["GET"])
@jwt_required()
def get_session(session_id):
    user_id = get_jwt_identity()

    session = chat_session_service.get_session_by_id(session_id)
    if not session or not is_owner(session, user_id):
        return json_error("Session not found", 404)

    return jsonify(serialize_session(session)), 200


@chat_session_bp.route("", methods=["POST"])
@jwt_required()
def create_session():
    data = request.get_json(silent=True)
    if data is None:
        return json_error("Request body must be valid JSON", 400)

    profile_id = data.get("profile_id")
    category = (data.get("category") or "memory_chat").strip()

    if profile_id is None:
        return json_error("profile_id is required", 400)

    user_id = get_jwt_identity()

    payload = {
        "profile_id": profile_id,
        "category": category,
        "status": "active",
        "user_id": int(user_id),
    }

    session = chat_session_service.create_session(payload)
    if not session:
        return json_error("Unable to create session", 400)

    return jsonify(serialize_session(session)), 201


@chat_session_bp.route("/<int:session_id>", methods=["PUT"])
@jwt_required()
def update_session(session_id):
    user_id = get_jwt_identity()

    existing_session = chat_session_service.get_session_by_id(session_id)
    if not existing_session or not is_owner(existing_session, user_id):
        return json_error("Session not found", 404)

    data = request.get_json(silent=True)
    if data is None:
        return json_error("Request body must be valid JSON", 400)

    # Schutz: Session-Status nicht beliebig von außen manipulieren
    data.pop("user_id", None)
    data.pop("session_id", None)
    data.pop("created_at", None)
    data.pop("updated_at", None)
    data.pop("started_at", None)
    data.pop("ended_at", None)

    # Falls beendet, nicht wieder normal bearbeitbar machen
    if existing_session.status == "ended":
        allowed_fields = {"category"}
        data = {key: value for key, value in data.items() if key in allowed_fields}

    # Status nur auf erlaubte Werte setzen
    if "status" in data and data["status"] not in ["active", "ended"]:
        return json_error("status must be 'active' or 'ended'", 400)

    session = chat_session_service.update_session(session_id, data)
    if not session:
        return json_error("Session not found", 404)

    return jsonify(serialize_session(session)), 200


@chat_session_bp.route("/<int:session_id>", methods=["DELETE"])
@jwt_required()
def delete_session(session_id):
    user_id = get_jwt_identity()

    existing_session = chat_session_service.get_session_by_id(session_id)
    if not existing_session or not is_owner(existing_session, user_id):
        return json_error("Session not found", 404)

    deleted = chat_session_service.delete_session(session_id)
    if not deleted:
        return json_error("Session not found", 404)

    return jsonify({"message": "Session deleted successfully"}), 200


@chat_session_bp.route("/profile/<int:profile_id>", methods=["GET"])
@jwt_required()
def get_sessions_by_profile(profile_id):
    user_id = get_jwt_identity()

    sessions = chat_session_service.get_sessions_by_profile_id(profile_id)
    own_sessions = [
        session for session in sessions
        if str(session.user_id) == str(user_id)
    ]

    return jsonify([serialize_session(session) for session in own_sessions]), 200


@chat_session_bp.route("/<int:session_id>/generate-story", methods=["POST"])
@jwt_required()
def generate_story(session_id):
    user_id = get_jwt_identity()

    session = chat_session_service.get_session_by_id(session_id)
    if not session or not is_owner(session, user_id):
        return json_error("Session not found", 404)

    story = chat_session_service.generate_story_from_session(session_id)
    if not story:
        return json_error("Unable to generate story", 400)

    return jsonify(
        {
            "message": "Story generated successfully",
            "story_id": story.story_id,
        }
    ), 201
