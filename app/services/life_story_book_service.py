import json
import os

from openai import OpenAI

from app.services.chat_ai_service import ChatAIService


class LifeStoryBookService:
    TOPICS = ChatAIService.TOPICS
    TOPIC_LABELS = ChatAIService.TOPIC_LABELS

    PLACEHOLDER_TEXT = (
        "This chapter is still being shaped. Add more memories or conversations "
        "to enrich it."
    )

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None

    def build_chapters(self, profile=None, story=None, memories=None):
        memories = memories or []

        if not story:
            return self._empty_chapters()

        ai_chapters = self._generate_ai_chapters(
            profile=profile,
            story=story,
            memories=memories,
        )

        if ai_chapters:
            return ai_chapters

        return self._fallback_chapters(
            story=story,
            memories=memories,
        )

    def _empty_chapters(self):
        return [
            {
                "id": topic,
                "title": self.TOPIC_LABELS.get(topic, topic.replace("_", " ").title()),
                "subtitle": self._subtitle_for_topic(topic),
                "text": self.PLACEHOLDER_TEXT,
                "memory_ids": [],
            }
            for topic in self.TOPICS.keys()
        ]

    def _fallback_chapters(self, story, memories):
        story_text = str(getattr(story, "story_text", "") or "").strip()
        summary = str(getattr(story, "summary", "") or "").strip()

        paragraphs = self._split_paragraphs(story_text)

        if not paragraphs and summary:
            paragraphs = [summary]

        if not paragraphs:
            paragraphs = [self.PLACEHOLDER_TEXT]

        chapters = self._empty_chapters()

        for index, paragraph in enumerate(paragraphs):
            topic_index = min(index, len(chapters) - 1)

            if chapters[topic_index]["text"] == self.PLACEHOLDER_TEXT:
                chapters[topic_index]["text"] = paragraph
            else:
                chapters[topic_index]["text"] += f"\n\n{paragraph}"

        for memory in memories:
            topic = self._fallback_topic_for_memory(memory)
            chapter = self._find_chapter(chapters, topic)

            if chapter and getattr(memory, "memory_id", None) is not None:
                chapter["memory_ids"].append(memory.memory_id)

        return chapters

    def _generate_ai_chapters(self, profile=None, story=None, memories=None):
        if not self.client:
            return None

        payload = {
            "profile": self._profile_payload(profile),
            "story": self._story_payload(story),
            "memories": [
                self._memory_payload(memory)
                for memory in memories or []
            ],
            "required_topics": list(self.TOPICS.keys()),
            "topic_labels": self.TOPIC_LABELS,
        }

        try:
            response = self.client.responses.create(
                model=self.model,
                instructions=self._build_ai_instructions(),
                input=[
                    {
                        "role": "user",
                        "content": json.dumps(payload, ensure_ascii=False),
                    }
                ],
                tools=[
                    self._life_story_book_tool()
                ],
                tool_choice={
                    "type": "function",
                    "name": "create_life_story_book_chapters",
                },
                parallel_tool_calls=False,
            )

            for item in response.output:
                if getattr(item, "type", None) != "function_call":
                    continue

                if getattr(item, "name", None) != "create_life_story_book_chapters":
                    continue

                raw_arguments = getattr(item, "arguments", "{}") or "{}"
                result = json.loads(raw_arguments)

                return self._validate_ai_chapters(
                    result=result,
                    memories=memories or [],
                )

            return None

        except Exception as error:
            print("OPENAI LIFE STORY BOOK ERROR:", repr(error))
            return None

    def _build_ai_instructions(self):
        topics = ", ".join(self.TOPICS.keys())

        return f"""
        You are creating a respectful Remora Life Story Book.

        Use exactly these topic chapters:
        {topics}

        Rules:
        - Return all 10 chapters.
        - Use the exact topic ids provided.
        - Do not invent facts, events, quotes, dates, relationships or emotions.
        - Stay grounded in the supplied story text, summary, profile and memory metadata.
        - Birth date and death date are profile context only.
        - Do not output birth_date or death_date as story fields.
        - If a chapter has little information, write a gentle placeholder sentence.
        - Write in a warm memorial storytelling style.
        - Never claim to speak as the remembered person.
        - Never write as if the remembered person is speaking.
        - Assign each memory_id to the best fitting chapter.
        - If a memory has a topic field and it matches one of the required topics, assign it to that topic.
        - Use each memory_id at most once.
        - If a memory does not clearly fit and has no topic, place it in daily_life.
        - Memory assignment can use title, memory_date, topic, memory_type and created_at.
        - Do not rely on original_filename for visible text.
        - Return structured data only through the function tool.
        """.strip()

    def _life_story_book_tool(self):
        topic_values = list(self.TOPICS.keys())

        return {
            "type": "function",
            "name": "create_life_story_book_chapters",
            "description": "Create the 10 Remora Life Story Book chapters and assign memories to chapters.",
            "strict": True,
            "parameters": {
                "type": "object",
                "properties": {
                    "chapters": {
                        "type": "array",
                        "description": "Exactly 10 life story chapters matching the required topic ids.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {
                                    "type": "string",
                                    "enum": topic_values,
                                },
                                "title": {
                                    "type": "string",
                                },
                                "subtitle": {
                                    "type": "string",
                                },
                                "text": {
                                    "type": "string",
                                },
                                "memory_ids": {
                                    "type": "array",
                                    "items": {
                                        "type": "integer",
                                    },
                                },
                            },
                            "required": [
                                "id",
                                "title",
                                "subtitle",
                                "text",
                                "memory_ids",
                            ],
                            "additionalProperties": False,
                        },
                    },
                },
                "required": [
                    "chapters",
                ],
                "additionalProperties": False,
            },
        }

    def _validate_ai_chapters(self, result, memories):
        if not isinstance(result, dict):
            return None

        raw_chapters = result.get("chapters")

        if not isinstance(raw_chapters, list):
            return None

        allowed_topics = list(self.TOPICS.keys())
        valid_memory_ids = {
            int(memory.memory_id)
            for memory in memories
            if getattr(memory, "memory_id", None) is not None
        }

        used_topics = set()
        used_memory_ids = set()
        chapters_by_id = {}

        for raw_chapter in raw_chapters:
            if not isinstance(raw_chapter, dict):
                continue

            topic_id = str(raw_chapter.get("id") or "").strip()

            if topic_id not in allowed_topics:
                continue

            if topic_id in used_topics:
                continue

            memory_ids = []

            for memory_id in raw_chapter.get("memory_ids") or []:
                try:
                    parsed_memory_id = int(memory_id)
                except (TypeError, ValueError):
                    continue

                if parsed_memory_id not in valid_memory_ids:
                    continue

                if parsed_memory_id in used_memory_ids:
                    continue

                memory_ids.append(parsed_memory_id)
                used_memory_ids.add(parsed_memory_id)

            text = str(raw_chapter.get("text") or "").strip()
            if not text:
                text = self.PLACEHOLDER_TEXT

            chapters_by_id[topic_id] = {
                "id": topic_id,
                "title": self.TOPIC_LABELS.get(topic_id, topic_id.replace("_", " ").title()),
                "subtitle": str(raw_chapter.get("subtitle") or self._subtitle_for_topic(topic_id)).strip(),
                "text": text,
                "memory_ids": memory_ids,
            }

            used_topics.add(topic_id)

        chapters = []

        for topic_id in allowed_topics:
            if topic_id in chapters_by_id:
                chapters.append(chapters_by_id[topic_id])
            else:
                chapters.append(
                    {
                        "id": topic_id,
                        "title": self.TOPIC_LABELS.get(topic_id, topic_id.replace("_", " ").title()),
                        "subtitle": self._subtitle_for_topic(topic_id),
                        "text": self.PLACEHOLDER_TEXT,
                        "memory_ids": [],
                    }
                )

        self._assign_unassigned_memories(
            chapters=chapters,
            memories=memories,
            used_memory_ids=used_memory_ids,
        )

        return chapters

    def _assign_unassigned_memories(self, chapters, memories, used_memory_ids):
        for memory in memories:
            memory_id = getattr(memory, "memory_id", None)

            if memory_id is None:
                continue

            parsed_memory_id = int(memory_id)

            if parsed_memory_id in used_memory_ids:
                continue

            topic = self._fallback_topic_for_memory(memory)
            chapter = self._find_chapter(chapters, topic)

            if not chapter:
                chapter = self._find_chapter(chapters, "daily_life")

            if chapter:
                chapter["memory_ids"].append(parsed_memory_id)
                used_memory_ids.add(parsed_memory_id)

    def _profile_payload(self, profile):
        if not profile:
            return {}

        return {
            "profile_id": getattr(profile, "profile_id", None),
            "full_name": getattr(profile, "full_name", None),
            "relationship": getattr(profile, "relationship", None),
            "short_description": getattr(profile, "short_description", None),
            "birth_date": profile.birth_date.isoformat()
            if getattr(profile, "birth_date", None)
            else None,
            "death_date": profile.death_date.isoformat()
            if getattr(profile, "death_date", None)
            else None,
        }

    def _story_payload(self, story):
        if not story:
            return {}

        return {
            "story_id": getattr(story, "story_id", None),
            "title": getattr(story, "title", None),
            "summary": getattr(story, "summary", None),
            "story_text": getattr(story, "story_text", None),
            "theme": getattr(story, "theme", None),
            "emotion_tag": getattr(story, "emotion_tag", None),
        }

    def _memory_payload(self, memory):
        return {
            "memory_id": getattr(memory, "memory_id", None),
            "memory_type": getattr(memory, "memory_type", None),
            "title": getattr(memory, "title", None),
            "memory_date": memory.memory_date.isoformat()
            if getattr(memory, "memory_date", None)
            else None,
            "topic": getattr(memory, "topic", None),
            "created_at": memory.created_at.isoformat()
            if getattr(memory, "created_at", None)
            else None,
        }

    def _split_paragraphs(self, text):
        if not text:
            return []

        normalized = text.replace("\r\n", "\n").replace("\r", "\n")

        paragraphs = [
            paragraph.strip()
            for paragraph in normalized.split("\n")
            if paragraph.strip()
        ]

        return paragraphs or [text.strip()]

    def _fallback_topic_for_memory(self, memory):
        explicit_topic = str(getattr(memory, "topic", "") or "").strip()

        if explicit_topic in self.TOPICS:
            return explicit_topic

        title = str(getattr(memory, "title", "") or "").lower()

        for topic, keywords in self.TOPICS.items():
            for keyword in keywords:
                if keyword.lower() in title:
                    return topic

        memory_type = str(getattr(memory, "memory_type", "") or "").lower()

        if memory_type == "voice":
            return "personality"

        if memory_type == "video":
            return "daily_life"

        return "daily_life"

    def _find_chapter(self, chapters, topic_id):
        for chapter in chapters:
            if chapter.get("id") == topic_id:
                return chapter

        return None

    def _subtitle_for_topic(self, topic):
        subtitles = {
            "childhood": "Early life, school years and growing up.",
            "daily_life": "Routines, habits and everyday moments.",
            "personality": "Character, presence and the way they moved through life.",
            "values": "Beliefs, principles, advice and lessons.",
            "humor": "Laughter, jokes and playful memories.",
            "friendship": "Friends, relationships, neighbors and community.",
            "family": "Home, family bonds and the people closest to them.",
            "hobbies": "Interests, passions and the things that brought joy.",
            "achievements": "Work, success, proud moments and accomplishments.",
            "loss": "Goodbyes, grief and what is deeply missed.",
        }

        return subtitles.get(topic, "")
