from app.database.story_database import StoryDatabase
from app.models.chat_message import ChatMessage
from app.models.chat_session import ChatSession
from app.services.profile_service import ProfileService
from app.services.story_ai_service import StoryAIService


class StoryService:
    """
    Service layer for life story business logic.
    """

    def __init__(self):
        self.story_db = StoryDatabase()
        self.story_ai = StoryAIService()
        self.profile_service = ProfileService()

    def get_stories(self):
        return self.story_db.get_all()

    def get_story_by_id(self, story_id):
        return self.story_db.get_by_id(story_id)

    def get_stories_by_profile_id(self, profile_id):
        return self.story_db.get_by_profile_id(profile_id)

    def create_story(self, data):
        return self.story_db.create(data)

    def update_story(self, story_id, data):
        story = self.story_db.get_by_id(story_id)

        if not story:
            return None

        return self.story_db.update(story, data)

    def delete_story(self, story_id):
        story = self.story_db.get_by_id(story_id)

        if not story:
            return False

        return self.story_db.delete(story)

    def create_story_from_chat_session(self, session_id, user_id):
        """
        Create one automatic life story from one specific chat session.
        """

        session = ChatSession.query.get(session_id)

        if not session:
            return None, "Chat session not found"

        if str(session.user_id) != str(user_id):
            return None, "Forbidden"

        profile = self.profile_service.get_profile_by_id(session.profile_id)

        if not profile:
            return None, "Profile not found"

        if str(profile.owner_id) != str(user_id):
            return None, "Forbidden"

        existing_story = self.story_db.get_by_session_id(session_id)

        if existing_story:
            return existing_story, None

        messages = self._get_messages_for_session(session_id)

        if not messages:
            return None, "No chat messages found"

        if not self._has_enough_user_content(messages):
            return None, "Not enough chat content to create a life story"

        story = self._create_story_from_messages(
            session=session,
            profile=profile,
            messages=messages,
            user_id=user_id,
        )

        if not story:
            return None, "Unable to save life story"

        return story, None

    def auto_create_stories_for_profile(self, profile_id, user_id):
        """
        Create missing life stories from all chat sessions for one profile.

        This is used by the Life Stories page button.
        It does not create duplicates:
        if a chat session already has a story, it is skipped.
        """

        profile = self.profile_service.get_profile_by_id(profile_id)

        if not profile:
            return None, "Profile not found"

        if str(profile.owner_id) != str(user_id):
            return None, "Forbidden"

        sessions = (
            ChatSession.query
            .filter_by(profile_id=profile_id, user_id=int(user_id))
            .order_by(ChatSession.started_at.desc())
            .all()
        )

        if not sessions:
            return self.get_stories_by_profile_id(profile_id), None

        for session in sessions:
            existing_story = self.story_db.get_by_session_id(session.session_id)

            if existing_story:
                continue

            messages = self._get_messages_for_session(session.session_id)

            if not messages:
                continue

            if not self._has_enough_user_content(messages):
                continue

            self._create_story_from_messages(
                session=session,
                profile=profile,
                messages=messages,
                user_id=user_id,
            )

        stories = self.get_stories_by_profile_id(profile_id)

        return stories, None

    def _get_messages_for_session(self, session_id):
        """
        Return all messages for a chat session in the correct order.
        """

        return (
            ChatMessage.query
            .filter_by(session_id=session_id)
            .order_by(ChatMessage.message_order.asc(), ChatMessage.created_at.asc())
            .all()
        )

    def _has_enough_user_content(self, messages):
        """
        Avoid creating stories from empty or very short chats.
        """

        user_messages = []

        for message in messages:
            if message.role != "user":
                continue

            text = (message.message_text or "").strip()

            if text:
                user_messages.append(text)

        combined_text = " ".join(user_messages).strip()

        if len(user_messages) < 2:
            return False

        if len(combined_text) < 80:
            return False

        return True

    def _create_story_from_messages(self, session, profile, messages, user_id):
        """
        Generate story data with AI and save it into life_stories.
        """

        story_data = self.story_ai.generate_life_story_from_chat(
            chat_messages=messages,
            profile=profile,
        )

        if not story_data:
            return None

        story_data["profile_id"] = session.profile_id
        story_data["created_by"] = int(user_id)
        story_data["source_session_id"] = session.session_id
        story_data["source_type"] = "chat"
        story_data["is_featured"] = False

        return self.story_db.create(story_data)
