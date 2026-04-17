import os

from openai import OpenAI


class ChatAIService:
    """
    Service for Remora's memorial conversation chat.
    Uses the OpenAI Responses API.
    """

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_MODEL", "gpt-5")
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None

    def build_system_prompt(self, profile=None) -> str:
        profile_name = getattr(profile, "full_name", None) or "the memorialized person"
        relationship = getattr(profile, "relationship", None) or "someone meaningful to the user"
        short_description = getattr(profile, "short_description", None) or ""

        return (
            "You are Remora, a warm and thoughtful memorial conversation guide. "
            "Your task is to help the user preserve meaningful memories, stories, "
            "habits, values, relationships, and small personal details.\n\n"
            f"The person being remembered is {profile_name}. "
            f"Their relationship to the user is {relationship}. "
            f"{short_description}\n\n"
            "Guidelines:\n"
            "- Be empathetic, calm, and natural.\n"
            "- Keep replies concise.\n"
            "- Ask at most one clear follow-up question at a time.\n"
            "- Encourage specific sensory details, people, places, and emotions.\n"
            "- Never invent facts.\n"
            "- If the user shares something painful, respond gently and supportively.\n"
            "- Focus on preserving memory, not therapy or diagnosis."
        )

    def _normalize_role(self, role: str) -> str:
        if role in ("user", "assistant", "system", "developer"):
            return role
        return "user"

    def _to_responses_input(self, messages: list[dict]) -> list[dict]:
        response_items = []

        for message in messages or []:
            role = self._normalize_role(message.get("role", "user"))
            text = str(message.get("content") or "").strip()

            if not text:
                continue

            response_items.append(
                {
                    "role": role,
                    "content": text,
                }
            )

        return response_items

    def generate_reply(self, messages: list[dict], profile=None) -> str:
        if self.client:
            response_input = self._to_responses_input(messages)

            if not response_input:
                response_input = [
                    {
                        "role": "user",
                        "content": "Help the user begin sharing a meaningful memory.",
                    }
                ]

            response = self.client.responses.create(
                model=self.model,
                instructions=self.build_system_prompt(profile),
                input=response_input,
            )

            return (response.output_text or "").strip()

        if not messages:
            return "What is one memory of this person that comes to your mind immediately?"

        last_user_message = ""
        for msg in reversed(messages):
            if msg.get("role") == "user" and msg.get("content"):
                last_user_message = str(msg["content"]).strip()
                break

        if not last_user_message:
            return "What is one small detail about this person that you never want to forget?"

        fallback_questions = [
            "Can you tell me a little more about that moment?",
            "What do you remember most clearly about it?",
            "Who else was there, and how did it feel?",
            "What did that moment reveal about who this person was?",
            "Is there a small detail from that memory that still stays with you?",
        ]
        index = min(len(messages) // 2, len(fallback_questions) - 1)
        return fallback_questions[index]