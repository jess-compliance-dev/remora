from app.extensions.db import db
from app.models.life_story import LifeStory


class StoryDatabase:
    """
    Database layer for life stories.
    This class only talks to the database.
    """

    def get_all(self):
        return (
            LifeStory.query
            .order_by(LifeStory.created_at.desc())
            .all()
        )

    def get_by_id(self, story_id: int):
        return LifeStory.query.get(story_id)

    def get_by_profile_id(self, profile_id: int):
        return (
            LifeStory.query
            .filter_by(profile_id=profile_id)
            .order_by(LifeStory.created_at.desc())
            .all()
        )

    def get_by_session_id(self, session_id: int):
        return (
            LifeStory.query
            .filter_by(source_session_id=session_id)
            .order_by(LifeStory.created_at.desc())
            .first()
        )

    def create(self, data: dict):
        try:
            story = LifeStory(**data)

            db.session.add(story)
            db.session.commit()

            return story

        except Exception as error:
            db.session.rollback()
            print("CREATE LIFE STORY ERROR:", repr(error))
            return None

    def update(self, story, data: dict):
        try:
            for key, value in data.items():
                if hasattr(story, key):
                    setattr(story, key, value)

            db.session.commit()

            return story

        except Exception as error:
            db.session.rollback()
            print("UPDATE LIFE STORY ERROR:", repr(error))
            return None

    def delete(self, story):
        try:
            db.session.delete(story)
            db.session.commit()
            return True

        except Exception as error:
            db.session.rollback()
            print("DELETE LIFE STORY ERROR:", repr(error))
            return False
