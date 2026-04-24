from datetime import datetime, UTC

from app.extensions.db import db
from app.models.chat_session import ChatSession


class ChatSessionService:
    def get_sessions(self):
        return (
            ChatSession.query
            .order_by(ChatSession.started_at.desc())
            .all()
        )

    def get_session_by_id(self, session_id):
        return ChatSession.query.get(session_id)

    def get_sessions_by_profile_id(self, profile_id):
        return (
            ChatSession.query
            .filter_by(profile_id=profile_id)
            .order_by(ChatSession.started_at.desc())
            .all()
        )

    def create_session(self, data):
        try:
            session = ChatSession(
                profile_id=data.get("profile_id"),
                user_id=data.get("user_id"),
                category=data.get("category"),
                status=data.get("status", "active"),
            )

            db.session.add(session)
            db.session.commit()
            return session

        except Exception as e:
            db.session.rollback()
            print("Create session error:", repr(e))
            raise

    def update_session(self, session_id, data):
        session = self.get_session_by_id(session_id)
        if not session:
            return None

        try:
            if "profile_id" in data:
                session.profile_id = data["profile_id"]

            if "category" in data:
                session.category = data["category"]

            if "status" in data and data["status"] in ["active", "ended"]:
                session.status = data["status"]

                if data["status"] == "ended" and not session.ended_at:
                    session.ended_at = datetime.now(UTC)

                if data["status"] == "active":
                    session.ended_at = None

            db.session.commit()
            return session

        except Exception:
            db.session.rollback()
            return None

    def delete_session(self, session_id):
        session = self.get_session_by_id(session_id)
        if not session:
            return False

        try:
            db.session.delete(session)
            db.session.commit()
            return True

        except Exception:
            db.session.rollback()
            return False


    def generate_story_from_session(self, session_id):
        return None
