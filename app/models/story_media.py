from datetime import datetime, UTC

from app.extensions.db import db


class StoryMedia(db.Model):
    """
    Database model for media attached to a life story.
    """

    __tablename__ = "story_media"

    media_id = db.Column(db.Integer, primary_key=True)

    story_id = db.Column(
        db.Integer,
        db.ForeignKey("life_stories.story_id", ondelete="CASCADE"),
        nullable=False
    )

    media_type = db.Column(db.String(50), nullable=True)
    file_url = db.Column(db.Text, nullable=False)
    caption = db.Column(db.Text, nullable=True)

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(UTC)
    )