from datetime import UTC, datetime
from app.extensions.db import db


class StoryMedia(db.Model):
    """
    Database model for media attached to a life story.

    This model is currently kept for future use.
    The current Life Story Video MVP can also scan local uploads directly.
    """

    __tablename__ = "story_media"

    media_id = db.Column(
        db.Integer,
        primary_key=True,
    )

    story_id = db.Column(
        db.Integer,
        db.ForeignKey("life_stories.story_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    media_type = db.Column(
        db.String(50),
        nullable=True,
    )

    file_url = db.Column(
        db.Text,
        nullable=False,
    )

    caption = db.Column(
        db.Text,
        nullable=True,
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=db.text("now()"),
    )

    def __repr__(self):
        return (
            f"<StoryMedia "
            f"media_id={self.media_id} "
            f"story_id={self.story_id} "
            f"media_type={self.media_type!r}>"
        )
