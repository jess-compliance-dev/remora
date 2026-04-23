import json
import os
from openai import OpenAI


class ChatAIService:
    TOPICS = {
        "childhood": ["childhood", "kid", "early life"],
        "daily_life": ["daily", "routine", "everyday"],
        "personality": ["personality", "character"],
        "values": ["values", "beliefs"],
        "humor": ["humor", "funny", "laugh"],
        "friendship": ["friends", "relationship"],
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
        "friendship": "Friendship",
        "family": "Family",
        "hobbies": "Hobbies",
        "achievements": "Achievements",
        "loss": "Loss",
    }

    NEXT_WORDS = {"next", "skip", "continue", "weiter"}

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None

    def _format_messages(self, messages):
        result = []

        for msg in messages or []:
            content = str(msg.get("content") or "").strip()
            if not content:
                continue

            role = msg.get("role", "user")
            if role not in {"user", "assistant"}:
                role = "user"

            result.append(
                {
                    "role": role,
                    "content": content,
                }
            )

        return result

    def _get_last_user_message(self, messages):
        for msg in reversed(messages or []):
            if msg.get("role") == "user":
                return str(msg.get("content") or "").strip()
        return ""

    def _is_next(self, text):
        return text.strip().lower() in self.NEXT_WORDS if text else False

    def _normalize_topic(self, topic):
        topic = str(topic or "").strip().lower()
        return topic if topic in self.TOPICS else None

    def _detect_explicit_topic(self, text):
        text = str(text or "").strip().lower()
        if not text:
            return None

        for topic, keywords in self.TOPICS.items():
            if text in {topic, topic.replace("_", " ")}:
                return topic
            if any(keyword in text for keyword in keywords):
                return topic

        return None

    def _normalize_topics(self, topics, current_topic=None):
        cleaned = []
        seen = set()

        for topic in topics or []:
            topic = self._normalize_topic(topic)
            if not topic or topic == current_topic or topic in seen:
                continue

            cleaned.append(topic)
            seen.add(topic)

            if len(cleaned) == 4:
                break

        return cleaned

    def _fallback_suggested_topics(self, current_topic=None):
        return [topic for topic in self.TOPICS if topic != current_topic][:4]

    def build_chat_prompt(self, profile=None):
        name = getattr(profile, "full_name", None) or "this person"
        relationship = getattr(profile, "relationship", None) or "someone important"
        description = getattr(profile, "short_description", None) or ""

        return f"""
You are Remora, a calm and emotionally sensitive memory companion who collects information about a person being remembered.

You are helping a user remember {name}, who is {relationship} to them.
Context: {description}

- Be warm, natural and concise (2–4 sentences)
- Ask only one follow-up question
- Stay grounded in the latest user message
- Do not invent details
- Collect meaningful memories and details
- Do not sound like a therapist
- If enough detail has already been gathered for the current topic, gently mention that you can also move to another topic if the user wants

If the user says "next", gently move on.
If the user names a topic, guide them into it naturally.
When guiding to a new topic, make sure that the topic is connected with the person being remembered.
""".strip()

    def build_analysis_prompt(self, profile=None):
        name = getattr(profile, "full_name", None) or "this person"
        topics = ", ".join(self.TOPICS.keys())

        return f"""
Analyze a memorial conversation about {name}.

Available topics:
{topics}

Your task:
- detect the current topic
- decide whether the topic already contains enough material for a future story
- count how many meaningful facts or details have already been mentioned for the current topic
- write a short summary of what has been shared in the current topic
- suggest 2 to 4 next topics if moving on would make sense

Rules:
- a meaningful fact is a concrete detail, action, memory, feeling, habit, or relationship detail
- facts_count should be a small integer
- topic_summary should be short, clear, and factual
- if no current topic is clear, use null for current_topic
- if not enough has been shared, use an empty summary
- if the user explicitly says "next", still return possible next topics
- return ONLY valid JSON

Return ONLY JSON in exactly this shape:
{{
  "show_topic_choices": false,
  "suggested_topics": ["childhood", "values"],
  "current_topic": "daily_life",
  "topic_complete": false,
  "topic_summary": "The user described a joyful birthday celebration and the surprise party.",
  "facts_count": 2
}}
""".strip()

    def _parse_response_json(self, text):
        text = (text or "").strip()
        if not text:
            return None

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1:
                try:
                    return json.loads(text[start:end + 1])
                except json.JSONDecodeError:
                    pass
        return None

    def _fallback_chat_reply(self, messages, profile=None):
        last = self._get_last_user_message(messages)
        topic = self._detect_explicit_topic(last)

        if self._is_next(last):
            return "We can move to another part of their life. What would you like to talk about next?"

        if topic:
            label = self.TOPIC_LABELS.get(topic, topic)
            return f"Let’s stay with {label.lower()} for a moment. What comes to your mind first?"

        name = getattr(profile, "full_name", None) or "this person"
        return f"What is one moment with {name} that comes to your mind first?"

    def _fallback_analysis_result(self, messages):
        last = self._get_last_user_message(messages)
        topic = self._detect_explicit_topic(last)

        if self._is_next(last):
            return {
                "show_topic_choices": True,
                "suggested_topics": self._fallback_suggested_topics(),
                "current_topic": None,
                "topic_complete": True,
                "topic_summary": "",
                "facts_count": 0,
            }

        if topic:
            return {
                "show_topic_choices": False,
                "suggested_topics": [],
                "current_topic": topic,
                "topic_complete": False,
                "topic_summary": last if last else "",
                "facts_count": 1 if last else 0,
            }

        return {
            "show_topic_choices": False,
            "suggested_topics": [],
            "current_topic": None,
            "topic_complete": False,
            "topic_summary": "",
            "facts_count": 0,
        }

    def _validate_analysis_result(self, result, messages):
        if not isinstance(result, dict):
            return self._fallback_analysis_result(messages)

        current_topic = self._normalize_topic(result.get("current_topic"))
        topic_complete = bool(result.get("topic_complete"))

        topic_summary = str(result.get("topic_summary") or "").strip()

        try:
            facts_count = int(result.get("facts_count", 0) or 0)
        except (TypeError, ValueError):
            facts_count = 0

        if facts_count < 0:
            facts_count = 0

        suggested_topics = self._normalize_topics(
            result.get("suggested_topics"),
            current_topic=current_topic,
        )

        requested_show_choices = bool(result.get("show_topic_choices"))
        last_user_message = self._get_last_user_message(messages)

        show_topic_choices = False

        if facts_count >= 2:
            show_topic_choices = True
        elif requested_show_choices and self._is_next(last_user_message):
            show_topic_choices = True

        if show_topic_choices and not suggested_topics:
            suggested_topics = self._fallback_suggested_topics(current_topic)
        elif not show_topic_choices:
            suggested_topics = []

        if facts_count >= 2:
            topic_complete = True

        return {
            "show_topic_choices": show_topic_choices,
            "suggested_topics": suggested_topics,
            "current_topic": current_topic,
            "topic_complete": topic_complete,
            "topic_summary": topic_summary,
            "facts_count": facts_count,
        }

    def _call_model(self, instructions, messages):
        if not self.client:
            return None

        try:
            response = self.client.responses.create(
                model=self.model,
                instructions=instructions,
                input=messages,
            )
            return (response.output_text or "").strip()
        except Exception:
            return None

    def generate_chat_reply(self, messages, profile=None):
        messages = self._format_messages(messages)
        if not messages:
            messages = [{"role": "user", "content": "Help me start remembering this person."}]

        last = self._get_last_user_message(messages)
        instructions = self.build_chat_prompt(profile)

        if self._is_next(last):
            instructions += "\nThe user wants to move on."
        else:
            topic = self._detect_explicit_topic(last)
            if topic:
                instructions += f"\nThe user chose the topic '{topic}'."

        reply = self._call_model(instructions, messages)
        return reply or self._fallback_chat_reply(messages, profile)

    def analyze_conversation_state(self, messages, profile=None):
        messages = self._format_messages(messages)

        output = self._call_model(self.build_analysis_prompt(profile), messages)
        parsed = self._parse_response_json(output)
        return self._validate_analysis_result(parsed, messages)

    def generate_reply(self, messages, profile=None):
        messages = self._format_messages(messages)
        analysis = self.analyze_conversation_state(messages, profile)

        reply = self.generate_chat_reply(messages, profile)

        if analysis["facts_count"] >= 2 and not self._is_next(self._get_last_user_message(messages)):
            reply = (
                f"{reply} "
                "We can stay with this a little longer, or gently move to another topic if you’d like."
            ).strip()

        return {
            "reply": reply,
            "show_topic_choices": analysis["show_topic_choices"],
            "suggested_topics": analysis["suggested_topics"],
            "current_topic": analysis["current_topic"],
            "topic_complete": analysis["topic_complete"],
            "topic_summary": analysis["topic_summary"],
            "facts_count": analysis["facts_count"],
        }