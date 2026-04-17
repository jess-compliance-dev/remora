from datetime import datetime, UTC
from app.extensions.db import db


class ChatSession(db.Model):
    """
    Database model for guided chatbot interview with user.
    """

    __tablename__ = "chat_sessions"

    session_id = db.Column(db.Integer, primary_key=True)

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

    category = db.Column(db.String(100), nullable=True)

    # possible values: "active", "ended"
    status = db.Column(db.String(50), nullable=False, default="active")

    started_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(UTC)
    )

    ended_at = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(UTC)
    )

    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC)
    )

    def is_active(self):
        return self.status == "active"

    def end(self):
        self.status = "ended"
        self.ended_at = datetime.now(UTC)
