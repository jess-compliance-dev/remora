from app.database.chatbot_prompt_database import ChatbotPromptDatabase


class ChatbotPromptService:
    """
    Service layer for chatbot prompt business logic.
    """

    def __init__(self):
        self.prompt_db = ChatbotPromptDatabase()

    def get_prompts(self):
        """Get all chatbot prompts."""
        return self.prompt_db.get_all()

    def get_active_prompts(self):
        """Get all active chatbot prompts."""
        return self.prompt_db.get_active()

    def get_prompt_by_id(self, prompt_id: int):
        """Get a chatbot prompt by ID."""
        return self.prompt_db.get_by_id(prompt_id)

    def get_prompts_by_category(self, category: str):
        """Get prompts by category."""
        return self.prompt_db.get_by_category(category)

    def create_prompt(self, data: dict):
        """Create a new chatbot prompt."""
        return self.prompt_db.create(data)

    def update_prompt(self, prompt_id: int, data: dict):
        """Update a chatbot prompt."""
        prompt = self.prompt_db.get_by_id(prompt_id)

        if not prompt:
            return None

        return self.prompt_db.update(prompt, data)

    def delete_prompt(self, prompt_id: int):
        """Delete a chatbot prompt."""
        prompt = self.prompt_db.get_by_id(prompt_id)

        if not prompt:
            return False

        self.prompt_db.delete(prompt)
        return True
    