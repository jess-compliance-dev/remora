from datetime import datetime, UTC
from app.extensions.db import db


class ChatMessage(db.Model):
    """
    Database model for chatbot interview messages.
    """

    __tablename__ = "chat_messages"

    message_id = db.Column(db.Integer, primary_key=True)

    session_id = db.Column(
        db.Integer,
        db.ForeignKey("chat_sessions.session_id", ondelete="CASCADE"),
        nullable=False
    )

    profile_id = db.Column(
        db.Integer,
        db.ForeignKey("memorial_profiles.profile_id", ondelete="CASCADE"),
        nullable=False
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=True
    )

    role = db.Column(db.String(50), nullable=False)
    message_text = db.Column(db.Text, nullable=True)
    audio_url = db.Column(db.Text, nullable=True)

    related_prompt_id = db.Column(
        db.Integer,
        db.ForeignKey("chatbot_prompts.prompt_id", ondelete="SET NULL"),
        nullable=True
    )

    related_story_id = db.Column(
        db.Integer,
        db.ForeignKey("life_stories.story_id", ondelete="SET NULL"),
        nullable=True
    )

    message_order = db.Column(db.Integer, nullable=True)

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(UTC)
    )
