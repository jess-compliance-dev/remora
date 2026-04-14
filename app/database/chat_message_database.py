from app.extensions.db import db
from app.models.chat_message import ChatMessage


class ChatMessageDatabase:
    """
    Database layer for chat messages.
    """

    def get_all(self):
        """Return all chat messages."""
        return ChatMessage.query.all()

    def get_by_id(self, message_id: int):
        """Return a chat message by ID."""
        return ChatMessage.query.get(message_id)

    def get_by_session_id(self, session_id: int):
        """Return all messages for a session ordered by message_order."""
        return (
            ChatMessage.query
            .filter_by(session_id=session_id)
            .order_by(ChatMessage.message_order.asc())
            .all()
        )

    def create(self, data: dict):
        """Create a new chat message."""
        message = ChatMessage(**data)
        db.session.add(message)
        db.session.commit()
        return message

    def delete(self, message):
        """Delete a chat message."""
        db.session.delete(message)
        db.session.commit()
