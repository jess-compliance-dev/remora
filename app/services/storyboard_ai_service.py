import json
import os
import re

from openai import OpenAI


class StoryboardAIService:
    """
    Creates a video storyboard from a LifeStory and its StoryMedia.

    The storyboard is based primarily on the curated LifeStory summary
    and summary_json. Raw chat messages should not be used or referenced.
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
                "description": (
                    "Create an emotional memory video storyboard from the life story "
                    "of a person being remembered."
                ),
                "strict": True,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": (
                                "A short, meaningful title inspired by the LifeStory. "
                                "The title should feel specific to the story, not generic. "
                                "Do not use the title as the person's display name. "
                                "Do not include dates. Maximum 45 characters."
                            ),
                        },
                        "memorial_name": {
                            "type": "string",
                            "description": (
                                "Full name of the person being remembered. "
                                "Use memorial_profile.full_name exactly when available. "
                                "Do not invent a name."
                            ),
                        },
                        "format": {
                            "type": "string",
                            "enum": ["vertical_9_16"],
                        },
                        "duration_seconds": {
                            "type": "integer",
                            "minimum": 20,
                            "maximum": 60,
                        },
                        "tone": {
                            "type": "string",
                            "description": "Overall tone of the memory video.",
                        },
                        "music_prompt": {
                            "type": "string",
                            "description": "Prompt for warm emotional background music.",
                        },
                        "intro_text": {
                            "type": "string",
                            "description": (
                                "Opening memorial label. Must be exactly 'In loving memory of'. "
                                "Do not include the person's name here because the template displays "
                                "the name separately."
                            ),
                        },
                        "caption_text": {
                            "type": "string",
                            "description": (
                                "Main emotional story text for the 1PC-Caption.text template field. "
                                "Must be 2 to 3 complete natural English sentences. "
                                "Keep it concise enough for a vertical video screen. "
                                "Do not copy fragments from summary_json directly. "
                                "Rewrite facts into coherent sentences. "
                                "Do not use a comma before 'and' or 'or'. "
                                "Maximum 220 characters."
                            ),
                        },
                        "final_message": {
                            "type": "string",
                            "description": (
                                "Closing message for the FM-Text.text template field. "
                                "Must be 1 to 2 complete natural English sentences. "
                                "Keep it concise enough for a vertical video screen. "
                                "Do not use sentence fragments, isolated phrases, labels, or keyword lists. "
                                "Do not use a comma before 'and' or 'or'. "
                                "Maximum 180 characters."
                            ),
                        },
                        "short_name": {
                            "type": "string",
                            "description": (
                                "Short display name for the FT-Name.text template field. "
                                "Use the remembered person's first name when memorial_name is available."
                            ),
                        },
                        "date_text": {
                            "type": "string",
                            "description": (
                                "Optional date, year, period or location text for the ID-Date.text template field. "
                                "Use an empty string if unknown. "
                                "Do not use generic values like mixed or unknown. "
                                "Maximum 35 characters."
                            ),
                        },
                        "scenes": {
                            "type": "array",
                            "minItems": 4,
                            "maxItems": 6,
                            "items": {
                                "type": "object",
                                "properties": {
                                    "scene_number": {
                                        "type": "integer",
                                    },
                                    "duration": {
                                        "type": "integer",
                                        "minimum": 4,
                                        "maximum": 8,
                                    },
                                    "media_id": {
                                        "type": ["integer", "string", "null"],
                                    },
                                    "text": {
                                        "type": "string",
                                        "description": (
                                            "Warm overlay text for this scene. "
                                            "Must be one complete natural English sentence. "
                                            "Use 8 to 16 words only so the text fits on screen. "
                                            "Do not use fragments, labels, keyword lists, or bullet points. "
                                            "Do not use a comma before 'and' or 'or'."
                                        ),
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
                        "memorial_name",
                        "format",
                        "duration_seconds",
                        "tone",
                        "music_prompt",
                        "intro_text",
                        "caption_text",
                        "final_message",
                        "short_name",
                        "date_text",
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

    def _safe_text(self, value, fallback=""):
        if value is None:
            return fallback

        return str(value).strip() or fallback

    def _remove_oxford_commas(self, text):
        text = self._safe_text(text)

        if not text:
            return text

        text = re.sub(r",\s+and\s+", " and ", text, flags=re.IGNORECASE)
        text = re.sub(r",\s+or\s+", " or ", text, flags=re.IGNORECASE)

        return text.strip()

    def _limit_text(self, value, max_length, fallback=""):
        text = self._safe_text(value, fallback)
        text = self._remove_oxford_commas(text)

        if len(text) <= max_length:
            return text

        return text[: max_length - 1].rstrip() + "…"

    def _ensure_sentence_punctuation(self, text):
        text = self._safe_text(text)
        text = self._remove_oxford_commas(text)

        if not text:
            return text

        if text.endswith((".", "!", "?")):
            return text

        return f"{text}."

    def _looks_like_fragment(self, text):
        text = self._safe_text(text)

        if not text:
            return True

        words = text.split()

        if len(words) < 5:
            return True

        if not text.endswith((".", "!", "?")):
            return True

        fragment_separators = [
            " / ",
            " | ",
            ";",
            ":",
        ]

        if any(separator in text for separator in fragment_separators):
            return True

        if len(words) <= 7 and "," in text:
            return True

        weak_fragment_starts = {
            "family",
            "childhood",
            "home",
            "warmth",
            "humor",
            "garden",
            "cooking",
            "memories",
            "love",
            "kindness",
            "strength",
            "traditions",
            "laughter",
            "friendship",
            "companionship",
            "support",
            "presence",
            "connection",
        }

        first_word = words[0].lower().strip(".,:;!?") if words else ""

        if first_word in weak_fragment_starts and len(words) <= 7:
            return True

        return False

    def _ensure_complete_sentence(self, text, fallback):
        text = self._ensure_sentence_punctuation(text)
        fallback = self._ensure_sentence_punctuation(fallback)

        if self._looks_like_fragment(text):
            return fallback

        return text

    def _limit_sentence_words(self, text, max_words, fallback):
        text = self._ensure_complete_sentence(text, fallback)
        words = text.split()

        if len(words) <= max_words:
            return text

        shortened = " ".join(words[:max_words]).rstrip(".,;:!?")
        return self._ensure_sentence_punctuation(shortened)

    def _build_memorial_name(self, profile=None):
        return self._safe_text(getattr(profile, "full_name", None), "")

    def _build_intro_text(self):
        return "In loving memory of"

    def _build_short_name(self, profile=None, memorial_name="", title=""):
        name = self._safe_text(memorial_name) or self._build_memorial_name(profile)

        if name:
            return name.split()[0]

        title = self._safe_text(title, "Memory")
        return title.split()[0] if title else "Memory"

    def _fallback_title_from_story(self, story, memorial_name=""):
        theme = self._safe_text(getattr(story, "theme", None))
        title = self._safe_text(getattr(story, "title", None))

        if title:
            return self._limit_text(title, 45, f"Remembering {memorial_name or 'This Life'}")

        if theme and memorial_name:
            return self._limit_text(
                f"{memorial_name} and {theme.title()}",
                45,
                f"Remembering {memorial_name}",
            )

        if memorial_name:
            return f"Remembering {memorial_name}"

        return "A Memory to Keep"

    def _clean_title(self, title, story=None, profile=None, memorial_name=""):
        title = self._safe_text(title)
        memorial_name = self._safe_text(memorial_name) or self._build_memorial_name(profile)

        if not title:
            return self._fallback_title_from_story(story, memorial_name)

        title = self._remove_oxford_commas(title)
        title = re.sub(r"\s+", " ", title).strip()

        if len(title) > 45:
            return self._fallback_title_from_story(story, memorial_name)

        return title

    def _build_date_text(self, story):
        life_period = self._safe_text(getattr(story, "life_period", None))
        location = self._safe_text(getattr(story, "location", None))
        happened_at = getattr(story, "happened_at", None)

        ignored_values = {
            "mixed",
            "unknown",
            "none",
            "n/a",
            "na",
            "null",
        }

        parts = []

        if life_period and life_period.lower() not in ignored_values:
            parts.append(life_period)

        if location and location.lower() not in ignored_values:
            parts.append(location)

        if happened_at:
            parts.append(happened_at.isoformat())

        date_text = " · ".join(parts)

        return self._limit_text(date_text, 35, "")

    def _fallback_storyboard(self, story, media_items, profile=None):
        media_ids = [media.media_id for media in media_items]

        memorial_name = self._build_memorial_name(profile)
        fallback_name = memorial_name or "this person"

        title = self._fallback_title_from_story(story, memorial_name)

        summary = self._safe_text(getattr(story, "summary", None))
        story_text = self._safe_text(getattr(story, "story_text", None))
        theme = self._safe_text(getattr(story, "theme", None))
        emotion_tag = self._safe_text(getattr(story, "emotion_tag", None))

        base_text = (
            summary
            or story_text
            or f"This memory keeps {fallback_name} close in a quiet and meaningful way."
        )

        date_text = self._build_date_text(story)

        caption_text = self._limit_text(
            base_text,
            220,
            f"This story remembers {fallback_name} through the details shared with care.",
        )
        caption_text = self._ensure_sentence_punctuation(caption_text)

        final_message = (
            f"{fallback_name} is remembered through the moments that still feel close. "
            "This memory remains a gentle place to return to."
        )

        if theme or emotion_tag:
            final_message = (
                f"This memory carries a {theme or emotion_tag} feeling. "
                f"It keeps {fallback_name} close in a gentle way."
            )

        final_message = self._limit_text(final_message, 180, final_message)
        final_message = self._ensure_sentence_punctuation(final_message)

        scene_templates = [
            (
                "opening",
                f"This story begins with a memory of {fallback_name}.",
            ),
            (
                "memory",
                self._limit_sentence_words(
                    base_text,
                    16,
                    f"A small memory can hold the feeling of {fallback_name}.",
                ),
            ),
            (
                "growth",
                "The details shared here help this memory feel personal and close.",
            ),
            (
                "closing",
                f"This memory keeps {fallback_name} present in a quiet way.",
            ),
        ]

        scenes = []

        for index, item in enumerate(scene_templates, start=1):
            purpose, text = item
            media_id = media_ids[index - 1] if index - 1 < len(media_ids) else None

            scenes.append(
                {
                    "scene_number": index,
                    "duration": 6,
                    "media_id": media_id,
                    "text": self._limit_sentence_words(
                        text,
                        16,
                        f"This memory keeps {fallback_name} close.",
                    ),
                    "purpose": purpose,
                }
            )

        return {
            "title": title,
            "memorial_name": memorial_name,
            "format": "vertical_9_16",
            "duration_seconds": 26,
            "tone": "warm, respectful, reflective",
            "music_prompt": "warm gentle emotional cinematic background music",
            "intro_text": self._build_intro_text(),
            "caption_text": caption_text,
            "final_message": final_message,
            "short_name": self._build_short_name(
                profile=profile,
                memorial_name=memorial_name,
                title=title,
            ),
            "date_text": date_text,
            "scenes": scenes,
        }

    def _normalize_storyboard_text(self, storyboard, story, media_items, profile=None):
        if not isinstance(storyboard, dict):
            return self._fallback_storyboard(story, media_items, profile)

        fallback = self._fallback_storyboard(story, media_items, profile)

        memorial_name = self._build_memorial_name(profile)

        storyboard["memorial_name"] = memorial_name

        storyboard["title"] = self._clean_title(
            storyboard.get("title"),
            story=story,
            profile=profile,
            memorial_name=memorial_name,
        )

        storyboard["intro_text"] = self._build_intro_text()

        storyboard["caption_text"] = self._limit_text(
            self._ensure_complete_sentence(
                storyboard.get("caption_text"),
                fallback.get("caption_text"),
            ),
            220,
            fallback.get("caption_text"),
        )

        storyboard["final_message"] = self._limit_text(
            self._ensure_complete_sentence(
                storyboard.get("final_message"),
                fallback.get("final_message"),
            ),
            180,
            fallback.get("final_message"),
        )

        storyboard["short_name"] = self._build_short_name(
            profile=profile,
            memorial_name=memorial_name,
            title=storyboard.get("title"),
        )

        storyboard["date_text"] = self._limit_text(
            storyboard.get("date_text") or fallback.get("date_text"),
            35,
            "",
        )

        ignored_date_values = {
            "mixed",
            "unknown",
            "none",
            "n/a",
            "na",
            "null",
        }

        if storyboard["date_text"].lower() in ignored_date_values:
            storyboard["date_text"] = ""

        scenes = storyboard.get("scenes") or []
        fallback_scenes = fallback.get("scenes") or []

        normalized_scenes = []

        for index, scene in enumerate(scenes):
            if not isinstance(scene, dict):
                continue

            fallback_scene = fallback_scenes[
                min(index, len(fallback_scenes) - 1)
            ]

            scene["text"] = self._limit_sentence_words(
                scene.get("text"),
                16,
                fallback_scene.get("text"),
            )

            normalized_scenes.append(scene)

        if len(normalized_scenes) < 4:
            normalized_scenes = fallback_scenes

        storyboard["scenes"] = normalized_scenes[:6]

        return storyboard

    def generate_storyboard(self, story, media_items, profile=None):
        if not story:
            return None

        if not self.client:
            return self._fallback_storyboard(story, media_items, profile)

        media_context = self._build_media_context(media_items)
        memorial_name = self._build_memorial_name(profile)

        story_payload = {
            "title": story.title,
            "memorial_profile": {
                "full_name": memorial_name,
            },
            "summary_json": story.summary_json,
            "summary": story.summary,
            "story_text": story.story_text,
            "theme": story.theme,
            "emotion_tag": story.emotion_tag,
            "life_period": story.life_period,
            "location": story.location,
            "happened_at": story.happened_at.isoformat() if story.happened_at else None,
        }

        system_prompt = """
You are Remora's memory video director.

Create an emotional memory video storyboard from the life story of a person being remembered.

Source priority:
1. Use summary_json as the primary source of truth when available.
2. Use summary as the next most important source of truth.
3. Use story_text only as secondary supporting context.
4. Use theme, emotion_tag, life_period, location and happened_at only when they are present.
5. Do not use or refer to raw chat messages.

Template mapping:
- intro_text maps to IT-Text.text and must be exactly "In loving memory of".
- memorial_name maps to ID-Name.text and must use memorial_profile.full_name when available.
- date_text maps to ID-Date.text.
- caption_text maps to 1PC-Caption.text.
- final_message maps to FM-Text.text.
- short_name maps to FT-Name.text.
- The template displays intro_text and memorial_name separately.

Title rules:
- Create a short title that fits the specific LifeStory.
- The title should be meaningful, natural and connected to the story details.
- Do not make the title sound like a marketing slogan.
- Do not use the title as the person's display name.
- Do not include date_text in the title.
- Keep the title under 45 characters.

Opening text rule:
- intro_text must be exactly "In loving memory of".
- Do not include the person's name in intro_text because the template displays the name separately.

Rules:
- Use only facts from summary_json, summary and the provided LifeStory fields.
- Do not invent events, names, places, dates, relationships, emotions, preferences, quotes or biographical details.
- Do not imply certainty about feelings or intentions unless the LifeStory clearly provides them.
- The video text should feel personal, warm, reflective and emotionally meaningful.
- The video should contain enough text to tell a small story, not just short captions.
- Write natural text for a memorial or memory video.
- Do not mention that the story came from chat messages.
- Prefer media_id values from the available media list.
- If there are fewer media items than scenes, media_id can be null.
- The video should feel like a personal memory story, not an advertisement.

Screen fit rules:
- Text must fit on a vertical 9:16 video screen.
- Keep scene text between 8 and 16 words.
- Keep caption_text concise and under 220 characters.
- Keep final_message concise and under 180 characters.
- Avoid long lines and overly broad text.

Grammar rules:
- Do not use a comma before "and" or "or".
- Every visible text field must be written as complete, natural English.
- Every scene text must be one complete sentence.
- Do not copy keyword fragments or short phrases directly from summary_json.
- Do not output isolated nouns, labels, bullet points, or sentence fragments.
- Rewrite available facts into coherent sentences with a subject and a verb.
- If summary_json contains fragments, combine them into readable sentences.
- Avoid text like "Family, garden, warmth" or "Childhood home and laughter".
- Prefer text like "Her family remembers the warmth she brought into everyday moments."

Text requirements:
- intro_text: exactly "In loving memory of".
- memorial_name: memorial_profile.full_name when available.
- caption_text: 2 to 3 warm complete sentences based mainly on summary_json and summary.
- final_message: 1 to 2 warm complete closing sentences.
- scene text: 8 to 16 words per scene, written as one complete sentence.
- Use concrete details from the LifeStory when available.
- If the LifeStory has little detail, keep the text honest and reflective instead of inventing facts.
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

                storyboard = json.loads(tool_call.function.arguments)

                return self._normalize_storyboard_text(
                    storyboard=storyboard,
                    story=story,
                    media_items=media_items,
                    profile=profile,
                )

            return self._fallback_storyboard(story, media_items, profile)

        except Exception as error:
            print("GENERATE STORYBOARD AI ERROR:", repr(error))
            return self._fallback_storyboard(story, media_items, profile)