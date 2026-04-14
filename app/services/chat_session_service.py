from app.database.chat_session_database import ChatSessionDatabase


class ChatSessionService:
    """
    Service layer for chat session business logic.
    """

    def __init__(self):
        self.session_db = ChatSessionDatabase()

    def get_sessions(self):
        """Get all chat sessions."""
        return self.session_db.get_all()

    def get_session_by_id(self, session_id: int):
        """Get chat session by ID."""
        return self.session_db.get_by_id(session_id)

    def get_sessions_by_profile_id(self, profile_id: int):
        """Get all sessions for a profile."""
        return self.session_db.get_by_profile_id(profile_id)

    def create_session(self, data: dict):
        """Create a new chat session."""
        return self.session_db.create(data)

    def update_session(self, session_id: int, data: dict):
        """Update an existing chat session."""
        session = self.session_db.get_by_id(session_id)

        if not session:
            return None

        return self.session_db.update(session, data)

    def delete_session(self, session_id: int):
        """Delete a chat session."""
        session = self.session_db.get_by_id(session_id)

        if not session:
            return False

        self.session_db.delete(session)
        return True
    