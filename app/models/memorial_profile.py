from datetime import datetime, UTC

from app.extensions.db import db


class MemorialProfile(db.Model):
    """
    Database model for memorial profiles.
    """

    __tablename__ = "memorial_profiles"

    profile_id = db.Column(db.Integer, primary_key=True)

    owner_id = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False
    )

    full_name = db.Column(db.String(255), nullable=False)
    relationship = db.Column(db.String(100), nullable=True)

    birth_date = db.Column(db.Date, nullable=True)
    death_date = db.Column(db.Date, nullable=True)

    status = db.Column(
        db.String(50),
        nullable=True,
    )

    short_description = db.Column(db.Text, nullable=True)
    profile_image_url = db.Column(db.Text, nullable=True)

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