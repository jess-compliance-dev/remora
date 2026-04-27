import json
import os
import re
from datetime import datetime

from openai import OpenAI


class StoryAIService:
    """
    AI service for creating structured life stories from chat conversations.
    """

    GENERIC_TITLE_PHRASES = [
        "a life of love and resilience",
        "a life remembered",
        "love and resilience",
        "legacy of love",
        "a legacy of love",
        "a story of love",
        "a journey of love",
        "a journey of resilience",
    ]

    GENERIC_TEXT_REPLACEMENTS = {
        "legacy lives on": "is remembered",
        "cherished memories": "memories",
        "love and joy": "warmth",
        "values she instilled": "things she shared",
        "values he instilled": "things he shared",
        "great challenges": "difficult moments",
        "resilience": "strength",
        "unforgettable": "important",
        "inspiring journey": "life",
        "beautiful journey": "life",
        "heartwarming": "warm",
        "profound": "deep",
        "treasured": "important",
    }

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None

    def _life_story_tool(self):
        return {
            "type": "function",
            "function": {
                "name": "create_life_story",
                "description": "Create a structured Remora life story from memory conversations.",
                "strict": True,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": (
                                "A simple title. Avoid poetic or generic titles like "
                                "'A Life of Love and Resilience', 'A Life Remembered' "
                                "or 'A Legacy of Love'."
                            ),
                        },
                        "prompt_question": {
                            "type": "string",
                            "description": "The main question or topic that led to this story.",
                        },
                        "story_text": {
                            "type": "string",
                            "description": (
                                "A factual life story based only on the user messages. "
                                "Use simple everyday English, short sentences and concrete details. "
                                "Avoid poetic, dramatic or flowery language."
                            ),
                        },
                        "summary": {
                            "type": "string",
                            "description": (
                                "A simple person summary in maximum 5 complete sentences. "
                                "Use concrete details from the user messages. "
                                "Avoid clichés, marketing language and generic memorial phrases. "
                                "Do not use a comma before 'and' or 'or'."
                            ),
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
                            "description": "Life period, for example childhood, adulthood, later_life, mixed, unknown.",
                        },
                        "location": {
                            "type": "string",
                            "description": "Location if known, otherwise empty string.",
                        },
                        "happened_at": {
                            "type": "string",
                            "description": "Date in YYYY-MM-DD format if known, otherwise empty string.",
                        },
                        "summary_json": {
                            "type": "object",
                            "description": "Structured summary for video/storyboard generation.",
                            "properties": {
                                "short_summary": {
                                    "type": "string",
                                },
                                "key_moments": {
                                    "type": "array",
                                    "items": {
                                        "type": "string",
                                    },
                                },
                                "important_people": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "name": {
                                                "type": "string",
                                            },
                                            "role": {
                                                "type": "string",
                                            },
                                            "relationship": {
                                                "type": "string",
                                            },
                                        },
                                        "required": [
                                            "name",
                                            "role",
                                            "relationship",
                                        ],
                                        "additionalProperties": False,
                                    },
                                },
                                "emotional_arc": {
                                    "type": "array",
                                    "items": {
                                        "type": "string",
                                    },
                                },
                                "visual_suggestions": {
                                    "type": "array",
                                    "items": {
                                        "type": "string",
                                    },
                                },
                                "suggested_music_mood": {
                                    "type": "string",
                                },
                                "sensitive_content_flags": {
                                    "type": "array",
                                    "items": {
                                        "type": "string",
                                    },
                                },
                            },
                            "required": [
                                "short_summary",
                                "key_moments",
                                "important_people",
                                "emotional_arc",
                                "visual_suggestions",
                                "suggested_music_mood",
                                "sensitive_content_flags",
                            ],
                            "additionalProperties": False,
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
                        "summary_json",
                    ],
                    "additionalProperties": False,
                },
            },
        }

    def _parse_date(self, value):
        value = (value or "").strip()

        if not value:
            return None

        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            return None

    def _limit_to_five_sentences(self, text):
        text = (text or "").strip()

        if not text:
            return text

        sentences = re.split(r"(?<=[.!?])\s+", text)

        sentences = [
            sentence.strip()
            for sentence in sentences
            if sentence.strip()
        ]

        if len(sentences) <= 5:
            return " ".join(sentences).strip()

        return " ".join(sentences[:5]).strip()

    def _remove_oxford_commas(self, text):
        """
        Remove commas directly before 'and' or 'or'.

        Example:
        gardening, cooking, and humor
        -> gardening, cooking and humor
        """

        if not text:
            return text

        cleaned = str(text)

        cleaned = re.sub(
            r",\s+and\s+",
            " and ",
            cleaned,
            flags=re.IGNORECASE,
        )

        cleaned = re.sub(
            r",\s+or\s+",
            " or ",
            cleaned,
            flags=re.IGNORECASE,
        )

        return cleaned.strip()

    def _replace_generic_language(self, text):
        if not text:
            return text

        cleaned = str(text).strip()

        for old, new in self.GENERIC_TEXT_REPLACEMENTS.items():
            cleaned = re.sub(
                old,
                new,
                cleaned,
                flags=re.IGNORECASE,
            )

        return cleaned.strip()

    def _clean_text(self, text):
        if not text:
            return text

        cleaned = str(text).strip()
        cleaned = self._replace_generic_language(cleaned)
        cleaned = self._remove_oxford_commas(cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()

        return cleaned

    def _clean_summary(self, summary):
        summary = self._limit_to_five_sentences(summary)
        return self._clean_text(summary)

    def _clean_story_text(self, story_text):
        return self._clean_text(story_text)

    def _clean_title(self, title, profile):
        title = (title or "").strip()
        name = getattr(profile, "full_name", None) or "Life Story"

        if not title:
            return f"{name}'s Story"

        normalized = title.lower().strip()

        for phrase in self.GENERIC_TITLE_PHRASES:
            if phrase in normalized:
                return f"{name}'s Story"

        if len(title) > 90:
            return f"{name}'s Story"

        title = self._remove_oxford_commas(title)
        title = re.sub(r"\s+", " ", title).strip()

        return title

    def _fallback_summary_json(self, combined_text):
        short_summary = self._clean_summary(combined_text[:700])

        return {
            "short_summary": short_summary,
            "key_moments": [],
            "important_people": [],
            "emotional_arc": ["reflective"],
            "visual_suggestions": [
                "family photos",
                "home memories",
                "quiet personal moments",
            ],
            "suggested_music_mood": "warm, calm, gentle",
            "sensitive_content_flags": [],
        }

    def _fallback_story_data(self, chat_messages, profile, combined=False):
        user_texts = []

        for message in chat_messages:
            if getattr(message, "role", None) == "user":
                text = getattr(message, "message_text", "") or ""

                if text.strip():
                    user_texts.append(text.strip())

        combined_text = "\n\n".join(user_texts).strip()

        if not combined_text:
            combined_text = "The user shared memories during the conversation."

        name = getattr(profile, "full_name", None) or "this person"
        title = f"{name}'s Story" if combined else f"A Memory of {name}"

        summary = self._clean_summary(combined_text[:700])
        story_text = self._clean_story_text(combined_text)

        return {
            "title": title,
            "prompt_question": "Combined memories" if combined else "What is one memory that comes to mind?",
            "story_text": story_text,
            "summary": summary,
            "summary_json": self._fallback_summary_json(combined_text),
            "theme": "memory",
            "emotion_tag": "reflective",
            "life_period": "mixed" if combined else "unknown",
            "location": None,
            "happened_at": None,
        }

    def _extract_tool_story_data(self, response, profile):
        assistant_message = response.choices[0].message
        tool_calls = assistant_message.tool_calls or []

        for tool_call in tool_calls:
            if tool_call.function.name != "create_life_story":
                continue

            data = json.loads(tool_call.function.arguments)

            title = self._clean_title(data.get("title"), profile)
            story_text = self._clean_story_text(data.get("story_text"))
            summary = self._clean_summary(data.get("summary"))

            summary_json = data.get("summary_json") or {}

            if isinstance(summary_json, dict):
                short_summary = self._clean_summary(
                    summary_json.get("short_summary") or summary
                )
                summary_json["short_summary"] = short_summary

                key_moments = summary_json.get("key_moments") or []
                if isinstance(key_moments, list):
                    summary_json["key_moments"] = [
                        self._clean_text(item)
                        for item in key_moments
                        if item
                    ]

                visual_suggestions = summary_json.get("visual_suggestions") or []
                if isinstance(visual_suggestions, list):
                    summary_json["visual_suggestions"] = [
                        self._clean_text(item)
                        for item in visual_suggestions
                        if item
                    ]

            return {
                "title": title,
                "prompt_question": data.get("prompt_question"),
                "story_text": story_text,
                "summary": summary,
                "summary_json": summary_json,
                "theme": data.get("theme"),
                "emotion_tag": data.get("emotion_tag"),
                "life_period": data.get("life_period"),
                "location": data.get("location") or None,
                "happened_at": self._parse_date(data.get("happened_at")),
            }

        return None

    def _build_single_session_messages(self, chat_messages, profile):
        name = getattr(profile, "full_name", None) or "this person"
        relationship = getattr(profile, "relationship", None) or "someone important"
        description = getattr(profile, "short_description", None) or ""

        system_prompt = f"""
You are Remora, a memory-preservation assistant.

Create one meaningful life story from this conversation.

Person being remembered:
Name: {name}
Relationship: {relationship}
Description: {description}

Style rules:
- Use simple everyday English.
- Use short sentences.
- Do not use poetic or flowery language.
- Do not use dramatic words unless the user clearly said them.
- Do not use a comma before "and" or "or".
- Avoid Oxford commas.
- Avoid clichés such as "legacy lives on", "cherished memories", "love and resilience", "values she instilled" and "inspiring journey".
- Avoid marketing-style language.
- Avoid making the person sound perfect unless the user said that.

Content rules:
- Use only concrete facts from the user messages.
- Do not invent names, dates, places, relationships, challenges or events.
- If information is limited, write a modest summary instead of exaggerating.
- The summary must be maximum 5 complete sentences.
- The summary should describe who the person was, what they enjoyed, how they related to others and how the family remembers them.
- Also create summary_json for later video generation.
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

            if role != "user":
                continue

            if not text.strip():
                continue

            messages.append(
                {
                    "role": "user",
                    "content": text.strip(),
                }
            )

        return messages

    def generate_life_story_from_chat(self, chat_messages, profile):
        if not chat_messages:
            return None

        if not self.client:
            return self._fallback_story_data(
                chat_messages=chat_messages,
                profile=profile,
                combined=False,
            )

        messages = self._build_single_session_messages(
            chat_messages=chat_messages,
            profile=profile,
        )

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

            data = self._extract_tool_story_data(
                response=response,
                profile=profile,
            )

            if data:
                return data

            return self._fallback_story_data(
                chat_messages=chat_messages,
                profile=profile,
                combined=False,
            )

        except Exception as error:
            print("GENERATE LIFE STORY AI ERROR:", repr(error))
            return self._fallback_story_data(
                chat_messages=chat_messages,
                profile=profile,
                combined=False,
            )

    def generate_combined_life_story_from_messages(self, chat_messages, profile):
        """
        Create ONE coherent connected life story from all user memory messages
        connected to a memorial profile.
        """

        if not chat_messages:
            return None

        if not self.client:
            return self._fallback_story_data(
                chat_messages=chat_messages,
                profile=profile,
                combined=True,
            )

        name = getattr(profile, "full_name", None) or "this person"
        relationship = getattr(profile, "relationship", None) or "someone important"
        description = getattr(profile, "short_description", None) or ""

        conversation_items = []

        for message in chat_messages:
            role = getattr(message, "role", "")
            text = getattr(message, "message_text", "") or ""

            if role != "user":
                continue

            if not text.strip():
                continue

            conversation_items.append(
                {
                    "content": text.strip(),
                    "session_id": getattr(message, "session_id", None),
                    "message_order": getattr(message, "message_order", None),
                    "created_at": (
                        message.created_at.isoformat()
                        if getattr(message, "created_at", None)
                        else None
                    ),
                }
            )

        if not conversation_items:
            return None

        system_prompt = f"""
You are Remora, a memory-preservation assistant.

Create ONE connected life story about {name} from all user messages.

Person being remembered:
Name: {name}
Relationship: {relationship}
Description: {description}

Main goal:
The result should feel calm, simple and personal. It should not sound like marketing text or a poem.

Style rules:
- Use simple everyday English.
- Use short sentences.
- Do not use poetic or flowery language.
- Do not use dramatic words unless the user clearly said them.
- Do not use a comma before "and" or "or".
- Avoid Oxford commas.
- Avoid clichés such as "legacy lives on", "cherished memories", "resilience", "love and joy", "values she instilled", "unforgettable" and "inspiring journey".
- Avoid making the person sound perfect unless the user said that.
- Prefer plain words like kind, funny, warm, strong, quiet, caring or practical when supported by the messages.

Content rules:
- Use only concrete facts from the user messages.
- Do not invent events, dates, personality traits, challenges or relationships.
- If the user mentioned concrete things like gardening, cooking, humor, family traditions, places, habits, sayings or small everyday details, include those details.
- If the information is limited, write a modest and simple summary instead of exaggerating.
- The result must be one connected life story, not separate stories per chat session.
- Remove repetition.
- Preserve factual details.
- If the timeline is unclear, organize the story by theme.
- Do not mention chat sessions or that the story came from chat messages.
- The summary must be maximum 5 complete sentences.
- The summary should describe who the person was, what they enjoyed, how they related to others and how the family remembers them.
- The story_text can be longer, but it must still avoid invented details.
- Do not end the summary with an unfinished sentence.
- Also create summary_json for video generation.
- visual_suggestions must be generic visual ideas and not invented facts.
        """.strip()

        user_prompt = json.dumps(
            {
                "instruction": "Create one connected life story from these user memories only.",
                "messages": conversation_items,
            },
            ensure_ascii=False,
            indent=2,
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": user_prompt,
                    },
                ],
                tools=[self._life_story_tool()],
                tool_choice={
                    "type": "function",
                    "function": {
                        "name": "create_life_story",
                    },
                },
                parallel_tool_calls=False,
            )

            data = self._extract_tool_story_data(
                response=response,
                profile=profile,
            )

            if data:
                data["prompt_question"] = data.get("prompt_question") or "Combined memories"
                data["life_period"] = data.get("life_period") or "mixed"
                return data

            return self._fallback_story_data(
                chat_messages=chat_messages,
                profile=profile,
                combined=True,
            )

        except Exception as error:
            print("GENERATE COMBINED LIFE STORY AI ERROR:", repr(error))
            return self._fallback_story_data(
                chat_messages=chat_messages,
                profile=profile,
                combined=True,
            )
