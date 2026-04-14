from app.database.chat_message_database import ChatMessageDatabase


class ChatMessageService:
    """
    Service layer for chat message business logic.
    """

    def __init__(self):
        self.message_db = ChatMessageDatabase()

    def get_messages(self):
        """Get all chat messages."""
        return self.message_db.get_all()

    def get_message_by_id(self, message_id: int):
        """Get chat message by ID."""
        return self.message_db.get_by_id(message_id)

    def get_messages_by_session_id(self, session_id: int):
        """Get all messages for a session."""
        return self.message_db.get_by_session_id(session_id)

    def create_message(self, data: dict):
        """Create a new chat message."""
        return self.message_db.create(data)

    def delete_message(self, message_id: int):
        """Delete a chat message."""
        message = self.message_db.get_by_id(message_id)

        if not message:
            return False

        self.message_db.delete(message)
        return True
