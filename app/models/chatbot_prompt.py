from datetime import datetime, UTC
from app.extensions.db import db


class ChatbotPrompt(db.Model):
    """
    Database model for chatbot prompts used to build stories.
    """

    __tablename__ = "chatbot_prompts"

    prompt_id = db.Column(db.Integer, primary_key=True)

    category = db.Column(db.String(100), nullable=True)
    question_text = db.Column(db.Text, nullable=False)
    life_period = db.Column(db.String(100), nullable=True)

    is_active = db.Column(db.Boolean, nullable=False, default=True)
    sort_order = db.Column(db.Integer, nullable=True)

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(UTC)
    )
