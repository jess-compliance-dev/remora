from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.services.chat_ai_service import ChatAIService
from app.services.chat_message_service import ChatMessageService
from app.services.chat_session_service import ChatSessionService
from app.services.profile_service import ProfileService

import traceback

chat_ai_bp = Blueprint("chat_ai", __name__)

chat_ai_service = ChatAIService()
chat_message_service = ChatMessageService()
chat_session_service = ChatSessionService()
profile_service = ProfileService()


def serialize_message(message):
    if message is None:
        return None

    return {
        "message_id": getattr(message, "message_id", None),
        "session_id": getattr(message, "session_id", None),
        "profile_id": getattr(message, "profile_id", None),
        "user_id": getattr(message, "user_id", None),
        "role": getattr(message, "role", None),
        "message_text": getattr(message, "message_text", None),
        "audio_url": getattr(message, "audio_url", None),
        "related_prompt_id": getattr(message, "related_prompt_id", None),
        "related_story_id": getattr(message, "related_story_id", None),
        "message_order": getattr(message, "message_order", None),
        "created_at": message.created_at.isoformat() if getattr(message, "created_at", None) else None,
    }


def serialize_session(session):
    if session is None:
        return None

    return {
        "session_id": getattr(session, "session_id", None),
        "user_id": getattr(session, "user_id", None),
        "profile_id": getattr(session, "profile_id", None),
        "title": getattr(session, "title", None),
        "is_active": session.is_active(),
        "started_at": session.started_at.isoformat() if getattr(session, "started_at", None) else None,
        "ended_at": session.ended_at.isoformat() if getattr(session, "ended_at", None) else None,
        "created_at": session.created_at.isoformat() if getattr(session, "created_at", None) else None,
    }


def json_error(message, status_code=400, details=None):
    payload = {"error": message}
    if details:
        payload["details"] = details
    return jsonify(payload), status_code


@chat_ai_bp.route("/chat/ai/<int:session_id>/messages", methods=["GET"])
@jwt_required()
def get_ai_session_messages(session_id):
    try:
        user_id = get_jwt_identity()

        session = chat_session_service.get_session_by_id(session_id)
        if not session:
            return json_error("Chat session not found", 404)

        session_user_id = getattr(session, "user_id", None)
        if session_user_id is not None and str(session_user_id) != str(user_id):
            return json_error("Chat session not found", 404)

        messages = chat_message_service.get_messages_by_session_id(session_id) or []

        return jsonify({
            "session": serialize_session(session),
            "messages": [serialize_message(msg) for msg in messages]
        }), 200

    except Exception as e:
        traceback.print_exc()
        return json_error("Failed to load chat messages", 500, str(e))


@chat_ai_bp.route("/chat/ai/<int:session_id>/message", methods=["POST"])
@jwt_required()
def send_ai_message(session_id):
    try:
        user_id = get_jwt_identity()

        data = request.get_json(silent=True)
        if data is None:
            return json_error("Request body must be valid JSON", 400)

        profile_id = data.get("profile_id")
        message_text = (data.get("message_text") or "").strip()

        if not profile_id:
            return json_error("profile_id is required", 400)

        if not message_text:
            return json_error("message_text is required", 400)

        session = chat_session_service.get_session_by_id(session_id)
        if not session:
            return json_error("Chat session not found", 404)

        session_user_id = getattr(session, "user_id", None)
        if session_user_id is not None and str(session_user_id) != str(user_id):
            return json_error("Chat session not found", 404)

        profile = profile_service.get_profile_by_id(profile_id)
        if not profile:
            return json_error("Profile not found", 404)

        existing_messages = chat_message_service.get_messages_by_session_id(session_id) or []
        next_order = len(existing_messages) + 1

        try:
            parsed_user_id = int(user_id) if user_id is not None else None
        except (TypeError, ValueError):
            parsed_user_id = None

        user_message = chat_message_service.create_message(
            {
                "session_id": session_id,
                "profile_id": profile_id,
                "user_id": parsed_user_id,
                "role": "user",
                "message_text": message_text,
                "message_order": next_order,
            }
        )

        if not user_message:
            return json_error("Failed to save user message", 500)

        updated_messages = chat_message_service.get_messages_by_session_id(session_id) or []

        ai_messages = []
        for msg in updated_messages:
            role = getattr(msg, "role", None)
            content = getattr(msg, "message_text", None)

            if not role or not content:
                continue

            ai_messages.append(
                {
                    "role": role,
                    "content": content,
                }
            )

        if not ai_messages:
            return json_error("No valid messages available for AI reply generation", 500)

        assistant_reply = chat_ai_service.generate_reply(ai_messages, profile=profile)

        if assistant_reply is None:
            return json_error("AI service returned no response", 500)

        assistant_reply = str(assistant_reply).strip()
        if not assistant_reply:
            return json_error("AI service returned an empty response", 500)

        assistant_message = chat_message_service.create_message(
            {
                "session_id": session_id,
                "profile_id": profile_id,
                "user_id": None,
                "role": "assistant",
                "message_text": assistant_reply,
                "message_order": next_order + 1,
            }
        )

        if not assistant_message:
            return json_error("Failed to save assistant message", 500)

        final_messages = chat_message_service.get_messages_by_session_id(session_id) or []

        return jsonify(
            {
                "session": serialize_session(session),
                "user_message": serialize_message(user_message),
                "assistant_message": serialize_message(assistant_message),
                "messages": [serialize_message(msg) for msg in final_messages],
            }
        ), 200

    except Exception as e:
        traceback.print_exc()
        return json_error("Internal server error", 500, str(e))
