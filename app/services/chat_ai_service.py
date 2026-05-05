import json
import os
from openai import OpenAI


class ChatAIService:
    TOPICS = {
        "childhood": [
            "childhood", "kid", "early life", "youth", "school", "growing up"
        ],
        "daily_life": [
            "daily", "routine", "everyday", "habit", "morning", "evening"
        ],
        "personality": [
            "personality", "character", "kind", "strict", "gentle", "quiet", "loud"
        ],
        "values": [
            "values", "beliefs", "principles", "faith", "lesson", "advice"
        ],
        "humor": [
            "humor", "funny", "laugh", "joke", "playful"
        ],
        "friendship": [
            "friends", "friendship", "relationship", "relationships",
            "neighbor", "community"
        ],
        "family": [
            "family", "house", "home", "mother", "father", "grandmother",
            "grandfather", "sibling", "parent", "child", "family-bond",
        ],
        "hobbies": [
            "hobbies", "interests", "music", "sports", "garden", "cooking",
            "reading", "travel"
        ],
        "achievements": [
            "achievement", "proud", "success", "career", "work", "award",
            "accomplishment"
        ],
        "loss": [
            "loss", "last", "goodbye", "grief", "farewell", "miss"
        ],
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

    NEXT_WORDS = {
        "next",
        "skip",
        "continue",
        "another topic",
        "new topic",
        "move on",
    }

    CRISIS_KEYWORDS = {
        "suicide",
        "suicidal",
        "self harm",
        "self-harm",
        "kill myself",
        "killing myself",
        "i want to die",
        "want to die",
        "i wanna die",
        "i don't want to live",
        "i dont want to live",
        "don't want to live",
        "dont want to live",
        "i do not want to live",
        "end my life",
        "ending my life",
        "take my life",
        "taking my life",
        "hurt myself",
        "harming myself",
        "harm myself",
        "i can't go on",
        "i cant go on",
        "can't go on",
        "cant go on",
        "i cannot go on",
        "no reason to live",
        "no point in living",
        "life is not worth living",
        "rather be dead",
        "better off dead",
        "wish i was dead",
        "wish i were dead",
        "overdose",
        "hang myself",
        "jump off",
        "cut myself",
    }

    CRISIS_SUPPORT_MESSAGE_DE = (
        "I’m very sorry that you’re feeling this way right now. "
        "If you are thinking about hurting yourself or you are not sure you can stay safe, "
        "please contact emergency services at 112 immediately or reach out to someone near you.\n\n"
        "You can also contact Telefon-Seelsorge in Germany for free and anonymously:\n"
        "0800 1110111\n"
        "0800 1110222\n"
        "116 123\n\n"
        "You do not have to go through this alone."
    )

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None

    # Message formatting
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
        if not text:
            return False

        normalized = text.strip().lower()
        return normalized in self.NEXT_WORDS

    def _detect_crisis_risk(self, text):
        if not text:
            return False

        normalized = str(text).strip().lower()
        return any(keyword in normalized for keyword in self.CRISIS_KEYWORDS)

    def _crisis_support_message(self):
        return self.CRISIS_SUPPORT_MESSAGE_DE

    # Topic helpers

    def _normalize_topic(self, topic):
        topic = str(topic or "").strip().lower()

        if topic == "unknown":
            return None

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

            if not topic:
                continue

            if topic == current_topic:
                continue

            if topic in seen:
                continue

            cleaned.append(topic)
            seen.add(topic)

            if len(cleaned) == 4:
                break

        return cleaned

    def _fallback_suggested_topics(self, current_topic=None):
        result = []

        for topic in self.TOPICS.keys():
            if topic != current_topic:
                result.append(topic)

            if len(result) == 4:
                break

        return result

    # Fallbacks
    def _fallback_chat_reply(self, messages, profile=None):
        name = getattr(profile, "full_name", None) or "this person"

        return (
            f"I can help you reflect on memories of {name}. "
            "I’m an AI memory companion, so I may be incomplete or inaccurate. "
            "What is one small detail from that memory that still feels vivid to you?"
        )

    def _fallback_analysis_result(self, messages):
        last_user_message = self._get_last_user_message(messages)
        current_topic = self._detect_explicit_topic(last_user_message)

        return {
            "show_topic_choices": False,
            "suggested_topics": [],
            "current_topic": current_topic,
            "topic_complete": False,
            "topic_summary": "",
            "facts_count": 0,
        }

    # Prompts
    def build_chat_prompt(self, profile=None):
        name = getattr(profile, "full_name", None) or "this person"
        relationship = getattr(profile, "relationship", None) or "someone important"
        description = getattr(profile, "short_description", None) or ""

        return f"""
        You are Remora, a calm and emotionally sensitive AI memory companion.

        You are helping a user remember {name}, who is {relationship} to them.
        Context about {name}: {description}

        Safety and identity rules:
        - You are an AI memory companion, not {name}.
        - Never claim to be {name}.
        - Never speak as if you are {name}.
        - Never imply that {name} is actually responding.
        - Do not invent facts, memories, feelings, quotes, events, preferences, or biographical details.
        - If something is unknown, say so gently or ask the user to share more.
        - Avoid making definitive claims about what {name} thought, felt, wanted, believed or would say unless the user clearly provided that information.
        - If the user mentions self-harm, suicide, wanting to die, or not being able to stay safe, stop the memory-companion style and respond with immediate crisis support.
        - Mention Telefon-Seelsorge: 0800 1110111, 0800 1110222 and 116 123.

        Your job:
        - Write a warm, natural chat reply.
        - Help the user remember concrete moments, habits, places, feelings, quotes and relationships.
        - Ask only one follow-up question.
        - Stay grounded in what the user actually said.
        - Do not sound like a therapist.
        - Keep the reply concise, usually 2 to 4 sentences.
        - If the user wants to move to another topic, gently guide them to a new memory topic.
        - If the user chooses a topic, connect that topic to {name}.
        - Do not write a comma before 'and' or 'or'.
        """.strip()

    def build_analysis_instructions(self, profile=None):
        name = getattr(profile, "full_name", None) or "this person"
        relationship = getattr(profile, "relationship", None) or "someone important"
        topics = ", ".join(self.TOPICS.keys())

        return f"""
        Analyze the current Remora memory conversation.

        Person being remembered:
        - Name: {name}
        - Relationship: {relationship}

        Available topics:
        {topics}

        Your job:
        - Analyze the chat state in the background.
        - Detect the current topic.
        - Count meaningful facts for the current topic.
        - Decide whether the topic has enough material for a future life story.
        - Write a short factual summary of the current topic.
        - Suggest 2 to 4 next topics when moving on makes sense.

        Important rules:
        - Do not invent facts.
        - A meaningful fact can be a concrete memory, action, habit, place, feeling, relationship detail, quote, tradition, repeated behavior, event, or life detail.
        - facts_count should be a small integer.
        - topic_summary must be factual and short.
        - If no topic is clear, use "unknown" as current_topic.
        - If not enough was shared, use an empty string for topic_summary.
        - If the user says "next", "skip", "continue", "another topic", or asks to change topic, suggest next topics.
        - Do not write a normal assistant reply in this analysis step.
        - Use the function tool to return the structured analysis.
        """.strip()

    # Function Calling Tool
    def _chat_state_analysis_tool(self):
        topic_values = list(self.TOPICS.keys())

        return {
            "type": "function",
            "name": "analyze_chat_state",
            "description": (
                "Analyze the Remora chat state. This tool returns structured "
                "background data for topic tracking, suggested topics, fact counting, "
                "and future life story preparation."
            ),
            "strict": True,
            "parameters": {
                "type": "object",
                "properties": {
                    "show_topic_choices": {
                        "type": "boolean",
                        "description": "Whether the UI should show topic choice buttons.",
                    },
                    "suggested_topics": {
                        "type": "array",
                        "description": "Two to three next topics that would make sense if the user moves on.",
                        "items": {
                            "type": "string",
                            "enum": topic_values,
                        },
                    },
                    "current_topic": {
                        "type": "string",
                        "description": "The current conversation topic. Use 'unknown' if unclear.",
                        "enum": topic_values + ["unknown"],
                    },
                    "topic_complete": {
                        "type": "boolean",
                        "description": "Whether enough material has been gathered for the current topic.",
                    },
                    "topic_summary": {
                        "type": "string",
                        "description": "Short factual summary of what has been shared for the current topic.",
                    },
                    "facts_count": {
                        "type": "integer",
                        "description": "Number of meaningful facts or details gathered for the current topic.",
                    },
                },
                "required": [
                    "show_topic_choices",
                    "suggested_topics",
                    "current_topic",
                    "topic_complete",
                    "topic_summary",
                    "facts_count",
                ],
                "additionalProperties": False,
            },
        }

    # Validation
    def _validate_analysis_result(self, result, messages):
        if not isinstance(result, dict):
            return self._fallback_analysis_result(messages)

        current_topic = self._normalize_topic(result.get("current_topic"))

        try:
            facts_count = int(result.get("facts_count", 0) or 0)
        except (TypeError, ValueError):
            facts_count = 0

        if facts_count < 0:
            facts_count = 0

        topic_summary = str(result.get("topic_summary") or "").strip()
        topic_complete = bool(result.get("topic_complete"))

        suggested_topics = self._normalize_topics(
            result.get("suggested_topics"),
            current_topic=current_topic,
        )

        requested_show_choices = bool(result.get("show_topic_choices"))
        last_user_message = self._get_last_user_message(messages)

        show_topic_choices = False

        if facts_count >= 2:
            show_topic_choices = True

        if requested_show_choices and self._is_next(last_user_message):
            show_topic_choices = True

        if self._is_next(last_user_message):
            show_topic_choices = True

        if show_topic_choices and not suggested_topics:
            suggested_topics = self._fallback_suggested_topics(current_topic)

        if not show_topic_choices:
            suggested_topics = []

        if facts_count >= 2:
            topic_complete = True

        if not current_topic and not self._is_next(last_user_message):
            detected_topic = self._detect_explicit_topic(last_user_message)

            if detected_topic:
                current_topic = detected_topic

        if facts_count < 1:
            topic_summary = ""

        return {
            "show_topic_choices": show_topic_choices,
            "suggested_topics": suggested_topics,
            "current_topic": current_topic,
            "topic_complete": topic_complete,
            "topic_summary": topic_summary,
            "facts_count": facts_count,
        }

    # OpenAI calls
    def _call_text_model(self, instructions, messages):
        if not self.client:
            return None

        try:
            response = self.client.responses.create(
                model=self.model,
                instructions=instructions,
                input=messages,
            )

            return (response.output_text or "").strip()

        except Exception as error:
            print("OPENAI CHAT TEXT ERROR:", repr(error))
            return None

    def _call_analysis_function(self, messages, profile=None):
        if not self.client:
            return None

        try:
            response = self.client.responses.create(
                model=self.model,
                instructions=self.build_analysis_instructions(profile),
                input=messages,
                tools=[
                    self._chat_state_analysis_tool()
                ],
                tool_choice={
                    "type": "function",
                    "name": "analyze_chat_state",
                },
                parallel_tool_calls=False,
            )

            for item in response.output:
                if getattr(item, "type", None) != "function_call":
                    continue

                if getattr(item, "name", None) != "analyze_chat_state":
                    continue

                raw_arguments = getattr(item, "arguments", "{}") or "{}"

                return json.loads(raw_arguments)

            return None

        except Exception as error:
            print("OPENAI CHAT ANALYSIS FUNCTION ERROR:", repr(error))
            return None

    # -------------------------------------------------------------------------
    # Public methods
    # -------------------------------------------------------------------------

    def generate_chat_reply(self, messages, profile=None):
        messages = self._format_messages(messages)

        if not messages:
            messages = [
                {
                    "role": "user",
                    "content": "Help me start remembering this person.",
                }
            ]

        last_user_message = self._get_last_user_message(messages)
        instructions = self.build_chat_prompt(profile)

        if self._is_next(last_user_message):
            instructions += "\nThe user wants to move to another topic."
        else:
            explicit_topic = self._detect_explicit_topic(last_user_message)

            if explicit_topic:
                instructions += f"\nThe user chose the topic '{explicit_topic}'."

        reply = self._call_text_model(instructions, messages)

        return reply or self._fallback_chat_reply(messages, profile)

    def analyze_conversation_state(self, messages, profile=None):
        messages = self._format_messages(messages)

        if not messages:
            return self._fallback_analysis_result(messages)

        result = self._call_analysis_function(messages, profile)

        return self._validate_analysis_result(result, messages)

    def generate_reply(self, messages, profile=None):
        messages = self._format_messages(messages)

        analysis = self.analyze_conversation_state(messages, profile)
        reply = self.generate_chat_reply(messages, profile)

        last_user_message = self._get_last_user_message(messages)
        crisis_detected = self._detect_crisis_risk(last_user_message)

        if (
            analysis["facts_count"] >= 2
            and not self._is_next(last_user_message)
            and analysis["show_topic_choices"]
            and not crisis_detected
        ):
            reply = (
                f"{reply} "
                "We can stay with this a little longer, or gently move to another topic if you’d like."
            ).strip()

        if crisis_detected:
            reply = self._crisis_support_message()

        return {
            "reply": reply,
            "show_topic_choices": False if crisis_detected else analysis["show_topic_choices"],
            "suggested_topics": [] if crisis_detected else analysis["suggested_topics"],
            "current_topic": analysis["current_topic"],
            "topic_complete": analysis["topic_complete"],
            "topic_summary": analysis["topic_summary"],
            "facts_count": analysis["facts_count"],
        }