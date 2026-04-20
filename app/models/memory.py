from datetime import datetime, UTC

from app.extensions.db import db


class Memory(db.Model):
    """
    Database model for uploaded memories.
    """

    __tablename__ = "memories"

    memory_id = db.Column(db.Integer, primary_key=True)

    owner_id = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False
    )

    profile_id = db.Column(
        db.Integer,
        db.ForeignKey("memorial_profiles.profile_id", ondelete="CASCADE"),
        nullable=True
    )

    memory_type = db.Column(
        db.String(20),
        nullable=False
    )  # photo, video, voice

    file_url = db.Column(
        db.Text,
        nullable=False
    )

    original_filename = db.Column(
        db.String(255),
        nullable=True
    )

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
