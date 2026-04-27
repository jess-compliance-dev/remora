import json
import os

from openai import OpenAI


class StoryboardAIService:
    """
    Creates a video storyboard from a LifeStory and its StoryMedia.
    """

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None

    def _storyboard_tool(self):
        return {
            "type": "function",
            "function": {
                "name": "create_memory_video_storyboard",
                "description": "Create a short vertical video storyboard from a Remora life story.",
                "strict": True,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "format": {
                            "type": "string",
                            "enum": ["vertical_9_16"],
                        },
                        "duration_seconds": {
                            "type": "integer",
                            "minimum": 15,
                            "maximum": 60,
                        },
                        "tone": {"type": "string"},
                        "music_prompt": {"type": "string"},
                        "scenes": {
                            "type": "array",
                            "minItems": 3,
                            "maxItems": 8,
                            "items": {
                                "type": "object",
                                "properties": {
                                    "scene_number": {"type": "integer"},
                                    "duration": {
                                        "type": "integer",
                                        "minimum": 3,
                                        "maximum": 10,
                                    },
                                    "media_id": {
                                        "type": ["integer", "null"],
                                    },
                                    "text": {
                                        "type": "string",
                                        "description": "Short overlay text. Max 14 words.",
                                    },
                                    "purpose": {
                                        "type": "string",
                                        "enum": [
                                            "opening",
                                            "memory",
                                            "transition",
                                            "growth",
                                            "climax",
                                            "closing",
                                        ],
                                    },
                                },
                                "required": [
                                    "scene_number",
                                    "duration",
                                    "media_id",
                                    "text",
                                    "purpose",
                                ],
                                "additionalProperties": False,
                            },
                        },
                    },
                    "required": [
                        "title",
                        "format",
                        "duration_seconds",
                        "tone",
                        "music_prompt",
                        "scenes",
                    ],
                    "additionalProperties": False,
                },
            },
        }

    def _build_media_context(self, media_items):
        return [
            {
                "media_id": media.media_id,
                "media_type": media.media_type,
                "file_url": media.file_url,
                "caption": media.caption,
            }
            for media in media_items
        ]

    def _fallback_storyboard(self, story, media_items):
        media_ids = [media.media_id for media in media_items]
        title = getattr(story, "title", None) or "Memory Story"

        scene_templates = [
            ("opening", "Every memory begins with a moment worth keeping."),
            ("memory", "A story, a feeling, a piece of a life."),
            ("growth", "Small details become something meaningful over time."),
            ("closing", "Some memories stay with us forever."),
        ]

        scenes = []

        for index, item in enumerate(scene_templates, start=1):
            purpose, text = item
            media_id = media_ids[index - 1] if index - 1 < len(media_ids) else None

            scenes.append(
                {
                    "scene_number": index,
                    "duration": 5,
                    "media_id": media_id,
                    "text": text,
                    "purpose": purpose,
                }
            )

        return {
            "title": title,
            "format": "vertical_9_16",
            "duration_seconds": 20,
            "tone": "warm, respectful, reflective",
            "music_prompt": "warm gentle emotional cinematic background music",
            "scenes": scenes,
        }

    def generate_storyboard(self, story, media_items):
        if not story:
            return None

        if not self.client:
            return self._fallback_storyboard(story, media_items)

        media_context = self._build_media_context(media_items)

        story_payload = {
            "title": story.title,
            "story_text": story.story_text,
            "summary": story.summary,
            "summary_json": story.summary_json,
            "theme": story.theme,
            "emotion_tag": story.emotion_tag,
            "life_period": story.life_period,
            "location": story.location,
            "happened_at": story.happened_at.isoformat() if story.happened_at else None,
        }

        system_prompt = """
You are Remora's memory video director.

Create a short vertical 9:16 storyboard from a LifeStory and available media.

Rules:
- Use only facts from the story and summary.
- Do not invent events, names, places, dates, or relationships.
- Keep overlay text short, warm, and respectful.
- Do not mention that the story came from chat messages.
- Prefer media_id values from the available media list.
- If there are fewer media items than scenes, media_id can be null.
- The video should feel like a personal memory story, not an advertisement.
        """.strip()

        user_prompt = f"""
LifeStory:
{json.dumps(story_payload, ensure_ascii=False, indent=2)}

Available media:
{json.dumps(media_context, ensure_ascii=False, indent=2)}
        """.strip()

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
                tools=[self._storyboard_tool()],
                tool_choice={
                    "type": "function",
                    "function": {
                        "name": "create_memory_video_storyboard",
                    },
                },
                parallel_tool_calls=False,
            )

            assistant_message = response.choices[0].message
            tool_calls = assistant_message.tool_calls or []

            for tool_call in tool_calls:
                if tool_call.function.name != "create_memory_video_storyboard":
                    continue

                return json.loads(tool_call.function.arguments)

            return self._fallback_storyboard(story, media_items)

        except Exception as error:
            print("GENERATE STORYBOARD AI ERROR:", repr(error))
            return self._fallback_storyboard(story, media_items)
        