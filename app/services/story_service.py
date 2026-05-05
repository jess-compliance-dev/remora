from app.database.story_database import StoryDatabase
from app.models.chat_message import ChatMessage
from app.models.chat_session import ChatSession
from app.services.profile_service import ProfileService
from app.services.story_ai_service import StoryAIService


class StoryService:
    """
    Service layer for life stories.
    """

    def __init__(self):
        self.story_db = StoryDatabase()
        self.profile_service = ProfileService()
        self.story_ai_service = StoryAIService()

    def get_stories(self):
        return self.story_db.get_all()

    def get_story_by_id(self, story_id):
        return self.story_db.get_by_id(story_id)

    def get_stories_by_profile_id(self, profile_id):
        return self.story_db.get_by_profile_id(profile_id)

    def create_story(self, data):
        allowed_fields = {
            "profile_id",
            "created_by",
            "source_session_id",
            "title",
            "prompt_question",
            "story_text",
            "source_type",
            "audio_url",
            "summary",
            "summary_json",
            "theme",
            "emotion_tag",
            "is_featured",
        }

        clean_data = {
            key: value
            for key, value in (data or {}).items()
            if key in allowed_fields
        }

        if not clean_data.get("profile_id"):
            return None

        if not clean_data.get("title"):
            return None

        if not clean_data.get("story_text"):
            return None

        return self.story_db.create(clean_data)

    def update_story(self, story_id, data):
        story = self.story_db.get_by_id(story_id)

        if not story:
            return None

        allowed_fields = {
            "title",
            "prompt_question",
            "story_text",
            "source_type",
            "audio_url",
            "summary",
            "summary_json",
            "theme",
            "emotion_tag",
            "is_featured",
        }

        clean_data = {
            key: value
            for key, value in (data or {}).items()
            if key in allowed_fields
        }

        return self.story_db.update(story, clean_data)

    def delete_story(self, story_id):
        story = self.story_db.get_by_id(story_id)

        if not story:
            return False

        return self.story_db.delete(story)

    def _user_owns_profile(self, profile, user_id):
        if not profile:
            return False

        return str(getattr(profile, "owner_id", None)) == str(user_id)

    def _get_profile_or_error(self, profile_id, user_id):
        profile = self.profile_service.get_profile_by_id(profile_id)

        if not profile:
            return None, "Profile not found"

        if not self._user_owns_profile(profile, user_id):
            return None, "Forbidden"

        return profile, None

    def _get_all_messages_for_profile(self, profile_id):
        sessions = (
            ChatSession.query
            .filter_by(profile_id=profile_id)
            .order_by(ChatSession.started_at.asc(), ChatSession.created_at.asc())
            .all()
        )

        if not sessions:
            return []

        session_ids = [
            session.session_id
            for session in sessions
            if getattr(session, "session_id", None) is not None
        ]

        if not session_ids:
            return []

        return (
            ChatMessage.query
            .filter(ChatMessage.session_id.in_(session_ids))
            .order_by(
                ChatMessage.created_at.asc(),
                ChatMessage.session_id.asc(),
                ChatMessage.message_order.asc(),
            )
            .all()
        )

    def _has_new_messages_since_story_update(self, story, messages):
        if not story or not messages:
            return False

        story_updated_at = getattr(story, "updated_at", None)

        if not story_updated_at:
            return True

        for message in messages:
            message_created_at = getattr(message, "created_at", None)

            if message_created_at and message_created_at > story_updated_at:
                return True

        return False

    def create_story_from_chat_session(self, session_id, user_id):
        session = ChatSession.query.get(session_id)

        if not session:
            return None, "Chat session not found"

        profile, error = self._get_profile_or_error(session.profile_id, user_id)

        if error:
            return None, error

        existing_story = self.story_db.get_by_session_id(session_id)

        if existing_story:
            return existing_story, None

        messages = (
            ChatMessage.query
            .filter_by(session_id=session_id)
            .order_by(ChatMessage.message_order.asc(), ChatMessage.created_at.asc())
            .all()
        )

        if not messages:
            return None, "No chat messages found for this session"

        story_data = self.story_ai_service.generate_life_story_from_chat(
            chat_messages=messages,
            profile=profile,
        )

        if not story_data:
            return None, "Unable to generate life story"

        story_data.update(
            {
                "profile_id": session.profile_id,
                "created_by": int(user_id) if user_id is not None else None,
                "source_session_id": session.session_id,
                "source_type": "chat",
            }
        )

        story = self.create_story(story_data)

        if not story:
            return None, "Unable to save life story"

        return story, None

    def auto_create_stories_for_profile(self, profile_id, user_id):
        profile, error = self._get_profile_or_error(profile_id, user_id)

        if error:
            return None, error

        sessions = (
            ChatSession.query
            .filter_by(profile_id=profile_id)
            .order_by(ChatSession.started_at.asc(), ChatSession.created_at.asc())
            .all()
        )

        if not sessions:
            return [], None

        stories = []

        for session in sessions:
            story, story_error = self.create_story_from_chat_session(
                session_id=session.session_id,
                user_id=user_id,
            )

            if story:
                stories.append(story)
            elif story_error:
                print("AUTO CREATE STORY ERROR:", story_error)

        return stories, None

    def create_combined_story_for_profile(self, profile_id, user_id):
        """
        Create ONE connected life story from all chat sessions/messages connected
        to one memorial profile.
        """
        profile, error = self._get_profile_or_error(profile_id, user_id)

        if error:
            return None, error

        existing_story = self.story_db.get_combined_story_by_profile_id(profile_id)

        if existing_story:
            return existing_story, None

        messages = self._get_all_messages_for_profile(profile_id)

        if not messages:
            return None, "No chat messages found for this profile"

        story_data = self.story_ai_service.generate_combined_life_story_from_messages(
            chat_messages=messages,
            profile=profile,
        )

        if not story_data:
            return None, "Unable to generate combined life story"

        story_data.update(
            {
                "profile_id": profile_id,
                "created_by": int(user_id) if user_id is not None else None,
                "source_session_id": None,
                "source_type": "combined_chat",
            }
        )

        story = self.create_story(story_data)

        if not story:
            return None, "Unable to save combined life story"

        return story, None

    def update_combined_story_for_profile(self, profile_id, user_id):
        """
        Update the existing combined life story if new chat messages exist.

        Returns:
        - story
        - error
        - update_status: "updated" or "no_changes"
        """
        profile, error = self._get_profile_or_error(profile_id, user_id)

        if error:
            return None, error, None

        existing_story = self.story_db.get_combined_story_by_profile_id(profile_id)

        if not existing_story:
            return None, "Combined life story not found", None

        messages = self._get_all_messages_for_profile(profile_id)

        if not messages:
            return None, "No chat messages found for this profile", None

        has_new_messages = self._has_new_messages_since_story_update(
            story=existing_story,
            messages=messages,
        )

        if not has_new_messages:
            return existing_story, None, "no_changes"

        story_data = self.story_ai_service.generate_combined_life_story_from_messages(
            chat_messages=messages,
            profile=profile,
        )

        if not story_data:
            return None, "Unable to update combined life story", None

        updated_story = self.story_db.update(
            existing_story,
            {
                "title": story_data.get("title"),
                "prompt_question": story_data.get("prompt_question"),
                "story_text": story_data.get("story_text"),
                "summary": story_data.get("summary"),
                "summary_json": story_data.get("summary_json"),
                "theme": story_data.get("theme"),
                "emotion_tag": story_data.get("emotion_tag"),
            },
        )

        if not updated_story:
            return None, "Unable to save updated life story", None

        return updated_story, None, "updated"
