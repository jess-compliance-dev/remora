from app.extensions.db import db
from app.models.memory_video import MemoryVideo


class MemoryVideoDatabase:
    """
    Database layer for memory videos.
    This class only talks to the database.
    """

    def get_all(self):
        return (
            MemoryVideo.query
            .order_by(MemoryVideo.created_at.desc())
            .all()
        )

    def get_by_id(self, video_id: int):
        return MemoryVideo.query.get(video_id)

    def get_by_story_id(self, story_id: int):
        return (
            MemoryVideo.query
            .filter_by(story_id=story_id)
            .order_by(MemoryVideo.created_at.desc())
            .all()
        )

    def get_by_profile_id(self, profile_id: int):
        return (
            MemoryVideo.query
            .filter_by(profile_id=profile_id)
            .order_by(MemoryVideo.created_at.desc())
            .all()
        )

    def create(self, data: dict):
        try:
            video = MemoryVideo(**data)
            db.session.add(video)
            db.session.commit()
            return video
        except Exception as error:
            db.session.rollback()
            print("CREATE MEMORY VIDEO ERROR:", repr(error))
            return None

    def update(self, video, data: dict):
        try:
            for key, value in data.items():
                if hasattr(video, key):
                    setattr(video, key, value)

            db.session.commit()
            return video
        except Exception as error:
            db.session.rollback()
            print("UPDATE MEMORY VIDEO ERROR:", repr(error))
            return None

    def delete(self, video):
        try:
            db.session.delete(video)
            db.session.commit()
            return True
        except Exception as error:
            db.session.rollback()
            print("DELETE MEMORY VIDEO ERROR:", repr(error))
            return False
