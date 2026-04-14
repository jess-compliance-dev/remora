from app.database.chat_session_database import ChatSessionDatabase
from app.services.chat_message_service import ChatMessageService
from app.services.story_service import StoryService
from app.services.story_ai_service import StoryAIService


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

    def generate_story_from_session(self, session_id: int):
        """
        Generate a life story from a chat session.
        """

        session = self.session_db.get_by_id(session_id)

        if not session:
            return None

        message_service = ChatMessageService()
        story_service = StoryService()
        ai_service = StoryAIService()

        messages = message_service.get_messages_by_session_id(session_id)

        if not messages:
            return None

        # collect only user answers
        user_answers = [
            m.message_text
            for m in messages
            if m.role == "user" and m.message_text
        ]

        if not user_answers:
            return None

        story_text = "\n\n".join(user_answers)

        # AI enrichment
        title = ai_service.generate_title(story_text)
        summary = ai_service.generate_summary(story_text)
        emotion = ai_service.detect_emotion(story_text)
        theme = ai_service.detect_theme(story_text)

        story_data = {
            "profile_id": session.profile_id,
            "created_by": session.user_id,
            "title": title,
            "story_text": story_text,
            "summary": summary,
            "theme": theme,
            "emotion_tag": emotion,
            "life_period": session.category,
            "source_type": "chat",
            "is_featured": False
        }

        story = story_service.create_story(story_data)

        # mark session completed
        self.session_db.update(
            session,
            {
                "status": "completed"
            }
        )

        return story
