from datetime import datetime, UTC

from app.extensions.db import db


class User(db.Model):
    """
    Database model for application users.
    """

    __tablename__ = "users"

    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), nullable=True)
    email = db.Column(db.String(255), unique=True, nullable=True)
    password_hash = db.Column(db.Text, nullable=True)

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