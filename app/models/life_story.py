from datetime import datetime

from app.extensions.db import db


class LifeStory(db.Model):
    """
    Database model for life stories connected to a memorial profile.
    """

    __tablename__ = "life_stories"

    story_id = db.Column(db.Integer, primary_key=True)

    profile_id = db.Column(
        db.Integer,
        db.ForeignKey("memorial_profiles.profile_id", ondelete="CASCADE"),
        nullable=False
    )

    created_by = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=True
    )

    title = db.Column(db.String(255), nullable=True)
    prompt_question = db.Column(db.Text, nullable=True)
    story_text = db.Column(db.Text, nullable=True)

    source_type = db.Column(db.String(50), nullable=True)
    audio_url = db.Column(db.Text, nullable=True)

    summary = db.Column(db.Text, nullable=True)
    theme = db.Column(db.String(100), nullable=True)
    emotion_tag = db.Column(db.String(100), nullable=True)
    life_period = db.Column(db.String(100), nullable=True)

    location = db.Column(db.String(255), nullable=True)
    happened_at = db.Column(db.Date, nullable=True)

    is_featured = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )