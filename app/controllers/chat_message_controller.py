from flask import Blueprint, request, jsonify

from app.services.chat_message_service import ChatMessageService

chat_message_bp = Blueprint("chat_messages", __name__)
chat_message_service = ChatMessageService()


def serialize_message(message):
    """
    Convert a ChatMessage object into a JSON-serializable dictionary.
    """
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
        "created_at": message.created_at.isoformat(),
    }


@chat_message_bp.route("", methods=["GET"])
def get_messages():
    """
    Retrieve all chat messages.
    """
    messages = chat_message_service.get_messages()
    return jsonify([serialize_message(message) for message in messages]), 200


@chat_message_bp.route("/<int:message_id>", methods=["GET"])
def get_message(message_id):
    """
    Retrieve a single chat message by ID.
    """
    message = chat_message_service.get_message_by_id(message_id)

    if not message:
        return jsonify({"error": "Message not found"}), 404

    return jsonify(serialize_message(message)), 200


@chat_message_bp.route("", methods=["POST"])
def create_message():
    """
    Create a new chat message.
    """
    data = request.get_json()
    message = chat_message_service.create_message(data)
    return jsonify(serialize_message(message)), 201


@chat_message_bp.route("/<int:message_id>", methods=["DELETE"])
def delete_message(message_id):
    """
    Delete a chat message.
    """
    deleted = chat_message_service.delete_message(message_id)

    if not deleted:
        return jsonify({"error": "Message not found"}), 404

    return jsonify({"message": "Message deleted successfully"}), 200


@chat_message_bp.route("/session/<int:session_id>", methods=["GET"])
def get_messages_by_session(session_id):
    """
    Retrieve all messages for a chat session.
    """
    messages = chat_message_service.get_messages_by_session_id(session_id)
    return jsonify([serialize_message(message) for message in messages]), 200
