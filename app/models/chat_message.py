from datetime import datetime
from app.extensions.db import db


class ChatMessage(db.Model):
    __tablename__ = "chat_messages"

    message_id = db.Column(db.Integer, primary_key=True)

    session_id = db.Column(
        db.Integer,
        db.ForeignKey("chat_sessions.session_id", ondelete="CASCADE"),
        nullable=False,
    )

    profile_id = db.Column(
        db.Integer,
        db.ForeignKey("memorial_profiles.profile_id", ondelete="CASCADE"),
        nullable=False,
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=True,
    )

    role = db.Column(db.String(20), nullable=False)  # "user" or "assistant"

    message_text = db.Column(db.Text, nullable=False)

    audio_url = db.Column(db.String(500), nullable=True)

    related_story_id = db.Column(
        db.Integer,
        db.ForeignKey("life_stories.story_id", ondelete="SET NULL"),
        nullable=True,
    )

    message_order = db.Column(db.Integer, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Optional relationships
    session = db.relationship("ChatSession", backref="messages", lazy=True)
    profile = db.relationship("MemorialProfile", backref="messages", lazy=True)
    user = db.relationship("User", backref="messages", lazy=True)

    def __repr__(self):
        return f"<ChatMessage {self.message_id} ({self.role})>"
