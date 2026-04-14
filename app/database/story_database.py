from app.extensions.db import db
from app.models.life_story import LifeStory


class StoryDatabase:
    """
    Database layer for life stories.
    """

    def get_all(self):
        """Return all life stories."""
        return LifeStory.query.all()

    def get_by_id(self, story_id: int):
        """Return a story by ID."""
        return LifeStory.query.get(story_id)

    def get_by_profile_id(self, profile_id: int):
        """Return stories for a profile."""
        return LifeStory.query.filter_by(profile_id=profile_id).all()

    def create(self, data: dict):
        """Create new life story."""
        story = LifeStory(**data)
        db.session.add(story)
        db.session.commit()
        return story

    def update(self, story, data: dict):
        """Update existing story."""
        for key, value in data.items():
            setattr(story, key, value)

        db.session.commit()
        return story

    def delete(self, story):
        """Delete story."""
        db.session.delete(story)
        db.session.commit()