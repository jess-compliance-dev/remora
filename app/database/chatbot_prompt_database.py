from app.extensions.db import db
from app.models.chatbot_prompt import ChatbotPrompt


class ChatbotPromptDatabase:
    """
    Database layer for chatbot prompts.
    """

    def get_all(self):
        """Return all chatbot prompts."""
        return ChatbotPrompt.query.order_by(ChatbotPrompt.sort_order.asc()).all()

    def get_active(self):
        """Return all active chatbot prompts."""
        return (
            ChatbotPrompt.query
            .filter_by(is_active=True)
            .order_by(ChatbotPrompt.sort_order.asc())
            .all()
        )

    def get_by_id(self, prompt_id: int):
        """Return a chatbot prompt by ID."""
        return ChatbotPrompt.query.get(prompt_id)

    def get_by_category(self, category: str):
        """Return all prompts for a category."""
        return (
            ChatbotPrompt.query
            .filter_by(category=category)
            .order_by(ChatbotPrompt.sort_order.asc())
            .all()
        )

    def create(self, data: dict):
        """Create a new chatbot prompt."""
        prompt = ChatbotPrompt(**data)
        db.session.add(prompt)
        db.session.commit()
        return prompt

    def update(self, prompt, data: dict):
        """Update an existing chatbot prompt."""
        for key, value in data.items():
            setattr(prompt, key, value)

        db.session.commit()
        return prompt

    def delete(self, prompt):
        """Delete a chatbot prompt."""
        db.session.delete(prompt)
        db.session.commit()
        