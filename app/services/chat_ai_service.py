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

    # Set up the OpenAI client and model settings
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None

    # Clean and normalize the message list
    def _format_messages(self, messages):
        formatted = []
        for message in messages or []:
            role = message.get("role", "user")
            content = str(message.get("content") or "").strip()
            if not content:
                continue
            if role not in {"user", "assistant"}:
                role = "user"
            formatted.append({"role": role, "content": content})
        return formatted

    # Get the most recent user message
    def _get_last_user_message(self, messages):
        for message in reversed(messages or []):
            if message.get("role") == "user":
                return str(message.get("content") or "").strip()
        return ""

    # Check if the user wants to move to the next topic
    def _is_next(self, text):
        return text and text.lower().strip() in {"next", "skip", "continue", "weiter"}

    # Detect whether the user explicitly mentioned a topic
    def _detect_explicit_topic(self, text):
        if not text:
            return None
        lowered = text.lower().strip()
        for topic, keywords in self.TOPICS.items():
            if lowered == topic or lowered == topic.replace("_", " "):
                return topic
            for keyword in keywords:
                if keyword in lowered:
                    return topic
        return None

    # Convert a topic into a valid normalized topic key
    def _normalize_topic(self, topic):
        if not topic:
            return None
        topic = str(topic).strip().lower()
        return topic if topic in self.TOPICS else None

    # Clean a topic list and remove duplicates or invalid entries
    def _normalize_topics(self, topics, current_topic=None):
        normalized = []
        seen = set()
        for topic in topics or []:
            topic_key = self._normalize_topic(topic)
            if not topic_key or topic_key == current_topic or topic_key in seen:
                continue
            normalized.append(topic_key)
            seen.add(topic_key)
            if len(normalized) >= 4:
                break
        return normalized

    # Return default topic suggestions
    def _fallback_suggested_topics(self, current_topic=None):
        defaults = list(self.TOPICS.keys())
        return [t for t in defaults if t != current_topic][:4]

    # Build the prompt for the visible chat reply
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

If the user says "next", gently move on.
If the user names a topic, guide them into it naturally. When guiding to a new topic make sure that the topic is connected with the person being remembered. 
""".strip()

    # Build the prompt for structured conversation analysis
    def build_analysis_prompt(self, profile=None):
        topics = ", ".join(self.TOPICS.keys())
        name = getattr(profile, "full_name", None) or "this person"

        return f"""
Analyze a memorial conversation about {name}.

Available topics:
{topics}

Return ONLY JSON:
{{
  "show_topic_choices": true,
  "suggested_topics": ["childhood", "values"],
  "current_topic": "daily_life",
  "topic_complete": false
}}
""".strip()

    # Parse JSON from the model response text
    def _parse_response_json(self, text):
        text = (text or "").strip()
        if not text:
            return None
        try:
            return json.loads(text)
        except:
            start, end = text.find("{"), text.rfind("}")
            if start != -1 and end != -1:
                try:
                    return json.loads(text[start:end + 1])
                except:
                    return None
        return None

    # Return a simple reply when the AI is unavailable
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

    # Generate the visible assistant reply
    def generate_chat_reply(self, messages, profile=None):
        messages = self._format_messages(messages)

        if not self.client:
            return self._fallback_chat_reply(messages, profile)

        if not messages:
            messages = [{"role": "user", "content": "Help me start remembering this person."}]

        last = self._get_last_user_message(messages)
        topic = self._detect_explicit_topic(last)
        is_next = self._is_next(last)

        instructions = self.build_chat_prompt(profile)

        if is_next:
            instructions += "\nThe user wants to move on."
        elif topic:
            instructions += f"\nThe user chose the topic '{topic}'."

        try:
            response = self.client.responses.create(
                model=self.model,
                instructions=instructions,
                input=messages,
            )
            return (response.output_text or "").strip() or self._fallback_chat_reply(messages, profile)
        except:
            return self._fallback_chat_reply(messages, profile)

    # Return a simple analysis result when the AI is unavailable
    def _fallback_analysis_result(self, messages):
        last = self._get_last_user_message(messages)
        topic = self._detect_explicit_topic(last)

        if self._is_next(last):
            return {
                "show_topic_choices": True,
                "suggested_topics": self._fallback_suggested_topics(),
                "current_topic": None,
                "topic_complete": True,
            }

        if topic:
            return {
                "show_topic_choices": False,
                "suggested_topics": [],
                "current_topic": topic,
                "topic_complete": False,
            }

        return {
            "show_topic_choices": False,
            "suggested_topics": [],
            "current_topic": None,
            "topic_complete": False,
        }

    # Validate and clean the structured analysis result
    def _validate_analysis_result(self, result, messages):
        if not isinstance(result, dict):
            return self._fallback_analysis_result(messages)

        current = self._normalize_topic(result.get("current_topic"))
        show = bool(result.get("show_topic_choices"))
        complete = bool(result.get("topic_complete"))

        topics = self._normalize_topics(result.get("suggested_topics"), current)

        if show and not topics:
            topics = self._fallback_suggested_topics(current)
        if not show:
            topics = []

        return {
            "show_topic_choices": show,
            "suggested_topics": topics,
            "current_topic": current,
            "topic_complete": complete,
        }

    # Analyze the conversation and return structured state data
    def analyze_conversation_state(self, messages, profile=None):
        messages = self._format_messages(messages)

        if not self.client:
            return self._fallback_analysis_result(messages)

        try:
            response = self.client.responses.create(
                model=self.model,
                instructions=self.build_analysis_prompt(profile),
                input=messages,
            )
            parsed = self._parse_response_json(response.output_text)
            return self._validate_analysis_result(parsed, messages)
        except:
            return self._fallback_analysis_result(messages)

    # Generate the final combined reply and analysis result
    def generate_reply(self, messages, profile=None):
        messages = self._format_messages(messages)

        reply = self.generate_chat_reply(messages, profile)
        analysis = self.analyze_conversation_state(messages, profile)

        return {
            "reply": reply,
            "show_topic_choices": analysis["show_topic_choices"],
            "suggested_topics": analysis["suggested_topics"],
            "current_topic": analysis["current_topic"],
            "topic_complete": analysis["topic_complete"],
        }