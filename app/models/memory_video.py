from datetime import UTC, datetime

from app.extensions.db import db


class MemoryVideo(db.Model):
    """
    Database model for generated memory videos.

    A MemoryVideo is generated from a LifeStory and its StoryMedia.
    It stores the generated storyboard, music metadata, Creatomate render ID,
    final video URL and processing status.
    """

    __tablename__ = "memory_videos"

    video_id = db.Column(
        db.Integer,
        primary_key=True,
    )

    profile_id = db.Column(
        db.Integer,
        db.ForeignKey("memorial_profiles.profile_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    story_id = db.Column(
        db.Integer,
        db.ForeignKey("life_stories.story_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    created_by = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    title = db.Column(
        db.String(255),
        nullable=True,
    )

    status = db.Column(
        db.String(50),
        nullable=False,
        default="pending",
        server_default="pending",
        index=True,
    )

    storyboard_json = db.Column(
        db.JSON,
        nullable=True,
    )

    music_prompt = db.Column(
        db.Text,
        nullable=True,
    )

    music_url = db.Column(
        db.Text,
        nullable=True,
    )

    mubert_track_id = db.Column(
        db.String(255),
        nullable=True,
    )

    creatomate_render_id = db.Column(
        db.String(255),
        nullable=True,
        index=True,
    )

    video_url = db.Column(
        db.Text,
        nullable=True,
    )

    error_message = db.Column(
        db.Text,
        nullable=True,
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=db.text("now()"),
    )

    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        server_default=db.text("now()"),
    )

    def __repr__(self):
        return (
            f"<MemoryVideo "
            f"video_id={self.video_id} "
            f"story_id={self.story_id} "
            f"status={self.status!r}>"
        )
