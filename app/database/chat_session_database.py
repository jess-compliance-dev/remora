from app.extensions.db import db
from app.models.chat_session import ChatSession


class ChatSessionDatabase:
    """
    Database layer for chat sessions.
    """

    def get_all(self):
        """Return all chat sessions."""
        return ChatSession.query.all()

    def get_by_id(self, session_id: int):
        """Return a chat session by ID."""
        return ChatSession.query.get(session_id)

    def get_by_profile_id(self, profile_id: int):
        """Return all chat sessions for a profile."""
        return ChatSession.query.filter_by(profile_id=profile_id).all()

    def create(self, data: dict):
        """Create a new chat session."""
        session = ChatSession(**data)
        db.session.add(session)
        db.session.commit()
        return session

    def update(self, session, data: dict):
        """Update a chat session."""
        for key, value in data.items():
            setattr(session, key, value)

        db.session.commit()
        return session

    def delete(self, session):
        """Delete a chat session."""
        db.session.delete(session)
        db.session.commit()
        