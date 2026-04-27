import json
import os
from datetime import datetime

from openai import OpenAI


class StoryAIService:
    """
    AI service for creating structured life stories from chat conversations.
    """

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")

        # Important:
        # Do not use a model here that your OpenAI project cannot access.
        # If OPENAI_MODEL is not set, this safe default is used.
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

        self.client = OpenAI(api_key=self.api_key) if self.api_key else None

    def _life_story_tool(self):
        return {
            "type": "function",
            "function": {
                "name": "create_life_story",
                "description": "Create a structured Remora life story from a memory conversation.",
                "strict": True,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "A short, warm title for the life story.",
                        },
                        "prompt_question": {
                            "type": "string",
                            "description": "The main question or topic that led to this story.",
                        },
                        "story_text": {
                            "type": "string",
                            "description": "A polished but factual life story based only on the conversation.",
                        },
                        "summary": {
                            "type": "string",
                            "description": "A short factual summary of the story.",
                        },
                        "theme": {
                            "type": "string",
                            "description": "Main theme, for example family, childhood, humor, values, daily_life.",
                        },
                        "emotion_tag": {
                            "type": "string",
                            "description": "Main emotional tone, for example warm, joyful, reflective, nostalgic.",
                        },
                        "life_period": {
                            "type": "string",
                            "description": "Life period, for example childhood, adulthood, later_life, unknown.",
                        },
                        "location": {
                            "type": "string",
                            "description": "Location if known, otherwise empty string.",
                        },
                        "happened_at": {
                            "type": "string",
                            "description": "Date in YYYY-MM-DD format if known, otherwise empty string.",
                        },
                    },
                    "required": [
                        "title",
                        "prompt_question",
                        "story_text",
                        "summary",
                        "theme",
                        "emotion_tag",
                        "life_period",
                        "location",
                        "happened_at",
                    ],
                    "additionalProperties": False,
                },
            },
        }

    def _build_messages(self, chat_messages, profile):
        name = getattr(profile, "full_name", None) or "this person"
        relationship = getattr(profile, "relationship", None) or "someone important"
        description = getattr(profile, "short_description", None) or ""

        system_prompt = f"""
You are Remora, a memory-preservation assistant.

Your task:
Create one meaningful life story from the chat conversation.

Person being remembered:
Name: {name}
Relationship: {relationship}
Description: {description}

Rules:
- Use only facts from the conversation.
- Do not invent names, dates, places, or events.
- If a date or place is unknown, return an empty string for that field.
- The story should feel warm and human, but still factual.
- Do not make the story too long.
- Write in clear, simple English.
""".strip()

        messages = [
            {
                "role": "system",
                "content": system_prompt,
            }
        ]

        for message in chat_messages:
            role = getattr(message, "role", "user")
            text = getattr(message, "message_text", "") or ""

            if role not in {"user", "assistant"}:
                continue

            if not text.strip():
                continue

            messages.append(
                {
                    "role": role,
                    "content": text.strip(),
                }
            )

        return messages

    def _parse_date(self, value):
        value = (value or "").strip()

        if not value:
            return None

        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            return None

    def _fallback_story_data(self, chat_messages, profile):
        user_texts = []

        for message in chat_messages:
            if getattr(message, "role", None) == "user":
                text = getattr(message, "message_text", "") or ""

                if text.strip():
                    user_texts.append(text.strip())

        combined_text = "\n\n".join(user_texts).strip()

        if not combined_text:
            combined_text = "The user shared a memory during the conversation."

        name = getattr(profile, "full_name", None) or "this person"

        return {
            "title": f"A Memory of {name}",
            "prompt_question": "What is one memory that comes to mind?",
            "story_text": combined_text,
            "summary": combined_text[:220],
            "theme": "memory",
            "emotion_tag": "reflective",
            "life_period": "unknown",
            "location": None,
            "happened_at": None,
        }

    def _clean_story_data(self, data):
        """
        Make sure the data can safely be saved to PostgreSQL.
        Especially important for date fields.
        """

        if not data:
            return None

        return {
            "title": data.get("title") or "Untitled Life Story",
            "prompt_question": data.get("prompt_question") or "",
            "story_text": data.get("story_text") or "",
            "summary": data.get("summary") or "",
            "theme": data.get("theme") or "memory",
            "emotion_tag": data.get("emotion_tag") or "reflective",
            "life_period": data.get("life_period") or "unknown",
            "location": data.get("location") or None,
            "happened_at": self._parse_date(data.get("happened_at")),
        }

    def generate_life_story_from_chat(self, chat_messages, profile):
        """
        Generate structured story data from chat messages.
        Returns a dict that can be saved into LifeStory.
        """

        if not chat_messages:
            return None

        if not self.client:
            return self._fallback_story_data(chat_messages, profile)

        messages = self._build_messages(chat_messages, profile)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=[self._life_story_tool()],
                tool_choice={
                    "type": "function",
                    "function": {
                        "name": "create_life_story",
                    },
                },
                parallel_tool_calls=False,
            )

            assistant_message = response.choices[0].message
            tool_calls = assistant_message.tool_calls or []

            for tool_call in tool_calls:
                if tool_call.function.name != "create_life_story":
                    continue

                raw_data = json.loads(tool_call.function.arguments)
                return self._clean_story_data(raw_data)

            return self._fallback_story_data(chat_messages, profile)

        except Exception as error:
            print("GENERATE LIFE STORY AI ERROR:", repr(error))
            return self._fallback_story_data(chat_messages, profile)