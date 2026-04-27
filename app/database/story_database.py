from app.extensions.db import db
from app.models.life_story import LifeStory


class StoryDatabase:
    """
    Database layer for life stories.
    """

    def get_all(self):
        return (
            LifeStory.query
            .order_by(LifeStory.created_at.desc())
            .all()
        )

    def get_by_id(self, story_id):
        return LifeStory.query.get(story_id)

    def get_by_profile_id(self, profile_id):
        return (
            LifeStory.query
            .filter_by(profile_id=profile_id)
            .order_by(LifeStory.created_at.desc())
            .all()
        )

    def get_by_session_id(self, session_id):
        return (
            LifeStory.query
            .filter_by(source_session_id=session_id)
            .order_by(LifeStory.created_at.desc())
            .first()
        )

    def get_combined_story_by_profile_id(self, profile_id):
        return (
            LifeStory.query
            .filter_by(
                profile_id=profile_id,
                source_type="combined_chat",
            )
            .order_by(LifeStory.created_at.desc())
            .first()
        )

    def create(self, data):
        try:
            story = LifeStory(**data)
            db.session.add(story)
            db.session.commit()
            return story
        except Exception as error:
            db.session.rollback()
            print("CREATE STORY ERROR:", repr(error))
            return None

    def update(self, story, data):
        try:
            for key, value in data.items():
                if hasattr(story, key):
                    setattr(story, key, value)

            db.session.commit()
            return story
        except Exception as error:
            db.session.rollback()
            print("UPDATE STORY ERROR:", repr(error))
            return None

    def delete(self, story):
        try:
            db.session.delete(story)
            db.session.commit()
            return True
        except Exception as error:
            db.session.rollback()
            print("DELETE STORY ERROR:", repr(error))
            return False
