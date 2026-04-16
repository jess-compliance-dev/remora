import os

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


class ChatAIService:
    """
    Service for guided life story conversation.
    """

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=self.api_key) if self.api_key and OpenAI else None

    def build_system_prompt(self):
        return (
            "You are a warm, thoughtful memory interviewer for a memorial storytelling app. "
            "Your role is to help the user preserve meaningful life stories, memories, moments, "
            "habits, values, relationships, and personal details about someone. "
            "Ask one clear follow-up question at a time. "
            "Be empathetic, concise, and natural. "
            "Focus on helping the user tell a rich, biographical story."
        )

    def generate_reply(self, messages: list[dict]) -> str:
        """
        Generate an assistant reply from chat history.
        """

        if self.client:
            completion = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": self.build_system_prompt()},
                    *messages
                ],
                temperature=0.7
            )
            return completion.choices[0].message.content.strip()

        # Fallback, wenn kein API-Key gesetzt ist
        if not messages:
            return "Tell me about a moment from this person's life that still feels especially vivid to you."

        last_user_message = ""
        for msg in reversed(messages):
            if msg["role"] == "user":
                last_user_message = msg["content"]
                break

        if not last_user_message:
            return "What is one memory that immediately comes to mind when you think of this person?"

        fallback_questions = [
            "Can you describe that moment in a little more detail?",
            "Who else was there, and what do you remember most clearly?",
            "How did that moment make you feel?",
            "Why do you think this memory stayed with you?",
            "What does this memory say about who this person was?"
        ]

        index = min(len(messages) // 2, len(fallback_questions) - 1)
        return fallback_questions[index]
    