from datetime import UTC, datetime

from app.extensions.db import db


class Memory(db.Model):
    __tablename__ = "memories"

    memory_id = db.Column(
        db.Integer,
        primary_key=True,
    )

    owner_id = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    profile_id = db.Column(
        db.Integer,
        db.ForeignKey("memorial_profiles.profile_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    memory_type = db.Column(
        db.String(30),
        nullable=False,
    )

    file_url = db.Column(
        db.Text,
        nullable=False,
    )

    original_filename = db.Column(
        db.String(255),
        nullable=True,
    )

    title = db.Column(
        db.String(255),
        nullable=True,
    )

    memory_date = db.Column(
        db.Date,
        nullable=True,
    )

    topic = db.Column(
        db.String(50),
        nullable=True,
        index=True,
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
        return f"<Memory memory_id={self.memory_id} owner_id={self.owner_id}>"
