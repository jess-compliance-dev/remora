from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.services.chat_ai_service import ChatAIService
from app.services.chat_message_service import ChatMessageService
from app.services.chat_session_service import ChatSessionService

chat_ai_bp = Blueprint("chat_ai", __name__)
chat_ai_service = ChatAIService()
chat_message_service = ChatMessageService()
chat_session_service = ChatSessionService()


def serialize_message(message):
    if message is None:
        return None

    return {
        "message_id": message.message_id,
        "session_id": message.session_id,
        "profile_id": message.profile_id,
        "user_id": message.user_id,
        "role": message.role,
        "message_text": message.message_text,
        "audio_url": message.audio_url,
        "related_prompt_id": message.related_prompt_id,
        "related_story_id": message.related_story_id,
        "message_order": message.message_order,
        "created_at": message.created_at.isoformat() if message.created_at else None,
    }


@chat_ai_bp.route("/chat/ai/<int:session_id>/message", methods=["POST"])
@jwt_required()
def send_ai_message(session_id):
    """
    Add a user message to a session, generate the AI reply, save both,
    and return the full updated message list.
    """
    user_id = get_jwt_identity()
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    profile_id = data.get("profile_id")
    message_text = data.get("message_text")

    if not profile_id or not message_text:
        return jsonify({"error": "profile_id and message_text are required"}), 400

    session = chat_session_service.get_session_by_id(session_id)

    if not session:
        return jsonify({"error": "Chat session not found"}), 404

    existing_messages = chat_message_service.get_messages_by_session_id(session_id)
    next_order = len(existing_messages) + 1

    chat_message_service.create_message({
        "session_id": session_id,
        "profile_id": profile_id,
        "user_id": int(user_id),
        "role": "user",
        "message_text": message_text,
        "message_order": next_order,
    })

    updated_messages = chat_message_service.get_messages_by_session_id(session_id)

    ai_messages = [
        {
            "role": msg.role,
            "content": msg.message_text or "",
        }
        for msg in updated_messages
        if msg.message_text
    ]

    assistant_reply = chat_ai_service.generate_reply(ai_messages)

    chat_message_service.create_message({
        "session_id": session_id,
        "profile_id": profile_id,
        "user_id": None,
        "role": "assistant",
        "message_text": assistant_reply,
        "message_order": next_order + 1,
    })

    final_messages = chat_message_service.get_messages_by_session_id(session_id)

    return jsonify({
        "messages": [serialize_message(msg) for msg in final_messages]
    }), 200
