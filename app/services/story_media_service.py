from app.database.story_media_database import StoryMediaDatabase


class StoryMediaService:
    """
    Service layer for story media business logic.
    """

    def __init__(self):
        self.story_media_db = StoryMediaDatabase()

    def get_media(self):
        """
        Get all media entries.
        """
        return self.story_media_db.get_all()

    def get_media_by_id(self, media_id: int):
        """
        Get a single media entry by ID.
        """
        return self.story_media_db.get_by_id(media_id)

    def get_media_by_story_id(self, story_id: int):
        """
        Get all media entries for a specific story.
        """
        return self.story_media_db.get_by_story_id(story_id)

    def create_media(self, data: dict):
        """
        Create a new media entry.
        """
        return self.story_media_db.create(data)

    def delete_media(self, media_id: int):
        """
        Delete a media entry by ID.
        """
        media = self.story_media_db.get_by_id(media_id)

        if not media:
            return False

        self.story_media_db.delete(media)
        return True
    