from datetime import UTC, datetime

from app.extensions.db import db


class LifeStory(db.Model):
    """
    Database model for life stories connected to a memorial profile.
    """

    __tablename__ = "life_stories"

    story_id = db.Column(
        db.Integer,
        primary_key=True,
    )

    profile_id = db.Column(
        db.Integer,
        db.ForeignKey("memorial_profiles.profile_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    created_by = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    source_session_id = db.Column(
        db.Integer,
        db.ForeignKey("chat_sessions.session_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    title = db.Column(
        db.String(255),
        nullable=False,
    )

    prompt_question = db.Column(
        db.Text,
        nullable=True,
    )

    story_text = db.Column(
        db.Text,
        nullable=False,
    )

    source_type = db.Column(
        db.String(50),
        nullable=False,
        default="chat",
        server_default="chat",
    )

    audio_url = db.Column(
        db.Text,
        nullable=True,
    )

    summary = db.Column(
        db.Text,
        nullable=True,
    )

    summary_json = db.Column(
        db.JSON,
        nullable=True,
    )

    theme = db.Column(
        db.String(100),
        nullable=True,
    )

    emotion_tag = db.Column(
        db.String(100),
        nullable=True,
    )

    is_featured = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
        server_default=db.text("false"),
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
        return f"<LifeStory story_id={self.story_id} profile_id={self.profile_id}>"
