import json
import os
from openai import OpenAI


class ChatAIService:
    """
    Remora hybrid AI chat service.

    Separation of concerns:
    - generate_chat_reply(): natural, empathetic visible assistant reply
    - analyze_conversation_state(): structured background analysis
    - generate_reply(): combines both into one result for the controller

    Returned structure:
    {
        "reply": str,
        "show_topic_choices": bool,
        "suggested_topics": list[str],
        "current_topic": str | None,
        "topic_complete": bool
    }
    """

    TOPICS = {
        "childhood": ["childhood", "kid", "early life"],
        "daily_life": ["daily", "routine", "everyday"],
        "personality": ["personality", "character"],
        "values": ["values", "beliefs"],
        "humor": ["humor", "funny", "laugh"],
        "relationships": ["friends", "relationship"],
        "family": ["family", "house", "home"],
        "hobbies": ["hobbies", "interests"],
        "achievements": ["achievement", "proud"],
        "loss": ["loss", "last", "goodbye"],
    }

    TOPIC_LABELS = {
        "childhood": "Childhood",
        "daily_life": "Daily Life",
        "personality": "Personality",
        "values": "Values",
        "humor": "Humor",
        "relationships": "Relationships",
        "family": "Family",
        "hobbies": "Hobbies",
        "achievements": "Achievements",
        "loss": "Loss",
    }

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None

        if not self.api_key:
            print("⚠️ OPENAI_API_KEY missing – AI disabled")

    # -----------------------------
    # shared helpers
    # -----------------------------
    def _format_messages(self, messages: list[dict]) -> list[dict]:
        formatted = []

        for message in messages or []:
            role = message.get("role", "user")
            content = str(message.get("content") or "").strip()

            if not content:
                continue

            if role not in {"user", "assistant"}:
                role = "user"

            formatted.append(
                {
                    "role": role,
                    "content": content,
                }
            )

        return formatted

    def _get_last_user_message(self, messages: list[dict]) -> str:
        for message in reversed(messages or []):
            if message.get("role") == "user":
                return str(message.get("content") or "").strip()
        return ""

    def _is_next(self, text: str) -> bool:
        if not text:
            return False

        return text.lower().strip() in {
            "next",
            "skip",
            "continue",
            "weiter",
        }

    def _detect_explicit_topic(self, text: str):
        if not text:
            return None

        lowered = text.lower().strip()

        for topic, keywords in self.TOPICS.items():
            if lowered == topic:
                return topic

            if lowered == topic.replace("_", " "):
                return topic

            for keyword in keywords:
                if keyword in lowered:
                    return topic

        return None

    def _normalize_topic(self, topic):
        if not topic:
            return None

        topic = str(topic).strip().lower()
        return topic if topic in self.TOPICS else None

    def _normalize_topics(self, topics, current_topic=None):
        normalized = []
        seen = set()

        for topic in topics or []:
            topic_key = self._normalize_topic(topic)
            if not topic_key:
                continue
            if topic_key == current_topic:
                continue
            if topic_key in seen:
                continue

            normalized.append(topic_key)
            seen.add(topic_key)

            if len(normalized) >= 4:
                break

        return normalized

    def _fallback_suggested_topics(self, current_topic=None):
        defaults = [
            "childhood",
            "daily_life",
            "personality",
            "values",
            "humor",
            "relationships",
            "family",
            "hobbies",
            "achievements",
            "loss",
        ]

        suggestions = [topic for topic in defaults if topic != current_topic]
        return suggestions[:4]

    # -----------------------------
    # prompts
    # -----------------------------
    def build_chat_prompt(self, profile=None) -> str:
        name = getattr(profile, "full_name", None) or "this person"
        relationship = getattr(profile, "relationship", None) or "someone important"
        description = getattr(profile, "short_description", None) or ""

        return f"""
You are Remora, a calm, warm, emotionally sensitive memory companion.

You are helping a user remember {name}, who is {relationship} to them.
Context: {description}

Your role:
- respond with warmth, gentleness, and emotional intelligence
- sound natural, never robotic
- keep replies concise, usually 2 to 4 sentences
- ask only one follow-up question at a time
- stay grounded in the user's most recent message
- do not invent places, objects, scenes, or facts the user did not mention
- if details are missing, ask a neutral follow-up question instead of guessing
- help the user preserve meaningful memories, habits, feelings, relationships and moments
- do not sound like a therapist
- do not lecture, summarize too early or force structure into the conversation

Important:
- your visible reply should feel human and emotionally attuned
- if the user says only "next", gently suggest moving on in a natural way
- if the user names a topic, guide them gently into that topic without sounding scripted
""".strip()

    def build_analysis_prompt(self, profile=None) -> str:
        available_topics = ", ".join(self.TOPICS.keys())
        name = getattr(profile, "full_name", None) or "this person"

        return f"""
You analyze a memorial conversation about {name}.

Your task is NOT to write the visible assistant reply.
Your task is ONLY to return structured conversation state as JSON.

Available topics:
{available_topics}

You must decide:
- which topic is currently being discussed
- whether the current topic already has enough detail for a future story section
- whether topic choices should be shown now
- which 3 to 4 next topics make sense

Rules:
- if the user explicitly says "next", set show_topic_choices to true
- if the user explicitly names a topic, usually set current_topic to that topic
- only set topic_complete to true when there is enough meaningful detail for that topic
- only set show_topic_choices to true when moving on would feel natural
- suggested_topics must contain only valid topics from the list above
- avoid suggesting the same current topic again
- return ONLY JSON

Return exactly this shape:
{{
  "show_topic_choices": true,
  "suggested_topics": ["childhood", "values", "humor"],
  "current_topic": "daily_life",
  "topic_complete": false
}}
""".strip()

    # -----------------------------
    # parsing
    # -----------------------------
    def _parse_response_json(self, raw_text: str):
        text = (raw_text or "").strip()

        if not text:
            return None

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            start = text.find("{")
            end = text.rfind("}")

            if start != -1 and end != -1 and end > start:
                try:
                    return json.loads(text[start:end + 1])
                except json.JSONDecodeError:
                    return None

        return None

    # -----------------------------
    # visible chat reply
    # -----------------------------
    def _fallback_chat_reply(self, messages: list[dict], profile=None) -> str:
        last_user = self._get_last_user_message(messages)
        explicit_topic = self._detect_explicit_topic(last_user)

        if self._is_next(last_user):
            return "We can gently move to another part of their life. What would you like to talk about next?"

        if explicit_topic:
            label = self.TOPIC_LABELS.get(explicit_topic, explicit_topic.replace("_", " ").title())
            return f"Let's stay with {label.lower()} for a moment. What comes to your mind first?"

        name = getattr(profile, "full_name", None) or "this person"
        return f"What is one moment with {name} that comes to your mind first?"

    def generate_chat_reply(self, messages: list[dict], profile=None) -> str:
        formatted_messages = self._format_messages(messages)

        if not self.client:
            return self._fallback_chat_reply(formatted_messages, profile)

        if not formatted_messages:
            formatted_messages = [
                {
                    "role": "user",
                    "content": "Help me start remembering this person.",
                }
            ]

        last_user = self._get_last_user_message(formatted_messages)
        explicit_topic = self._detect_explicit_topic(last_user)
        user_requested_next = self._is_next(last_user)

        grounding_instruction = f"""
The user's latest message is:
"{last_user}"

Stay grounded in that latest message.
Do not introduce unrelated details.
Ask only one natural follow-up question directly related to what the user actually said.
""".strip()

        extra_instruction = ""

        if user_requested_next:
            extra_instruction = """
The user wants to move on.
Respond naturally and gently invite them to choose another part of this person's life.
Do not output a list format unless it feels natural.
""".strip()
        elif explicit_topic:
            extra_instruction = f"""
The user explicitly chose the topic "{explicit_topic}".
Guide them gently into that topic.
Ask one warm, natural opening question for that topic.
Do not sound scripted.
""".strip()

        instructions = self.build_chat_prompt(profile)
        instructions = f"{instructions}\n\n{grounding_instruction}"

        if extra_instruction:
            instructions = f"{instructions}\n\n{extra_instruction}"

        try:
            response = self.client.responses.create(
                model=self.model,
                instructions=instructions,
                input=formatted_messages,
            )

            reply = (response.output_text or "").strip()
            return reply or self._fallback_chat_reply(formatted_messages, profile)

        except Exception as error:
            print("❌ OpenAI chat reply error:", str(error))
            return self._fallback_chat_reply(formatted_messages, profile)

    # -----------------------------
    # structured analysis
    # -----------------------------
    def _fallback_analysis_result(self, messages: list[dict], profile=None) -> dict:
        last_user = self._get_last_user_message(messages)
        explicit_topic = self._detect_explicit_topic(last_user)

        if self._is_next(last_user):
            return {
                "show_topic_choices": True,
                "suggested_topics": self._fallback_suggested_topics(),
                "current_topic": None,
                "topic_complete": True,
            }

        if explicit_topic:
            return {
                "show_topic_choices": False,
                "suggested_topics": [],
                "current_topic": explicit_topic,
                "topic_complete": False,
            }

        return {
            "show_topic_choices": False,
            "suggested_topics": [],
            "current_topic": None,
            "topic_complete": False,
        }

    def _validate_analysis_result(self, result: dict, messages: list[dict], profile=None):
        if not isinstance(result, dict):
            return self._fallback_analysis_result(messages, profile)

        current_topic = self._normalize_topic(result.get("current_topic"))
        topic_complete = bool(result.get("topic_complete"))
        show_topic_choices = bool(result.get("show_topic_choices"))

        suggested_topics = self._normalize_topics(
            result.get("suggested_topics") or [],
            current_topic=current_topic,
        )

        if show_topic_choices and not suggested_topics:
            suggested_topics = self._fallback_suggested_topics(current_topic=current_topic)

        if not show_topic_choices:
            suggested_topics = []

        return {
            "show_topic_choices": show_topic_choices,
            "suggested_topics": suggested_topics,
            "current_topic": current_topic,
            "topic_complete": topic_complete,
        }

    def analyze_conversation_state(self, messages: list[dict], profile=None) -> dict:
        formatted_messages = self._format_messages(messages)

        if not self.client:
            return self._fallback_analysis_result(formatted_messages, profile)

        if not formatted_messages:
            return self._fallback_analysis_result(formatted_messages, profile)

        last_user = self._get_last_user_message(formatted_messages)
        explicit_topic = self._detect_explicit_topic(last_user)
        user_requested_next = self._is_next(last_user)

        extra_instruction = ""

        if user_requested_next:
            extra_instruction = """
The user explicitly said "next".
Set show_topic_choices to true.
Suggest 3 to 4 meaningful next topics.
""".strip()
        elif explicit_topic:
            extra_instruction = f"""
The user explicitly chose the topic "{explicit_topic}".
Usually set current_topic to "{explicit_topic}".
Do not force show_topic_choices too early.
""".strip()

        instructions = self.build_analysis_prompt(profile)
        if extra_instruction:
            instructions = f"{instructions}\n\n{extra_instruction}"

        try:
            response = self.client.responses.create(
                model=self.model,
                instructions=instructions,
                input=formatted_messages,
            )

            parsed = self._parse_response_json(response.output_text or "")
            return self._validate_analysis_result(parsed, formatted_messages, profile)

        except Exception as error:
            print("❌ OpenAI analysis error:", str(error))
            return self._fallback_analysis_result(formatted_messages, profile)

    # -----------------------------
    # combined public method
    # -----------------------------
    def generate_reply(self, messages: list[dict], profile=None) -> dict:
        formatted_messages = self._format_messages(messages)

        reply = self.generate_chat_reply(formatted_messages, profile)
        analysis = self.analyze_conversation_state(formatted_messages, profile)

        return {
            "reply": reply,
            "show_topic_choices": bool(analysis.get("show_topic_choices")),
            "suggested_topics": analysis.get("suggested_topics") or [],
            "current_topic": analysis.get("current_topic"),
            "topic_complete": bool(analysis.get("topic_complete")),
        }