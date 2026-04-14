from app.extensions.db import db
from app.models.story_media import StoryMedia


class StoryMediaDatabase:
    """
    Database layer for story media operations.
    """

    def get_all(self):
        """
        Return all story media entries.
        """
        return StoryMedia.query.all()

    def get_by_id(self, media_id: int):
        """
        Return a media entry by ID.
        """
        return StoryMedia.query.get(media_id)

    def get_by_story_id(self, story_id: int):
        """
        Return all media entries for a story.
        """
        return StoryMedia.query.filter_by(story_id=story_id).all()

    def create(self, data: dict):
        """
        Create a new story media entry.
        """
        media = StoryMedia(**data)
        db.session.add(media)
        db.session.commit()
        return media

    def delete(self, media):
        """
        Delete a story media entry.
        """
        db.session.delete(media)
        db.session.commit()
