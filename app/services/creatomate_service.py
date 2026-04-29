import os

import requests

from app.utils.media_url import build_public_media_url, is_public_url


class CreatomateService:
    """
    Service for creating and checking Creatomate renders.

    This service maps Remora uploaded media into Creatomate template fields.

    Important:
    Creatomate cannot read local files.

    Your current local upload location is:
    app/static/uploads/memories/photo/...
    app/static/uploads/memories/video/...

    Local paths like:
    uploads/memories/photo/a.jpg

    are converted by app.utils.media_url.build_public_media_url() to:
    PUBLIC_BASE_URL/static/uploads/memories/photo/a.jpg
    """

    MEDIA_FIELDS = [
        "1PC-Photo.source",
        "MPP-Photo-Background.source",
        "MPP-Photo-1.source",
        "MPP-Photo-2.source",
        "MPP-Photo-3.source",
        "MPP-Photo-4.source",
        "MPP-Photo-5.source",
        "MPP-Photo-6.source",
        "MPP-Photo-7.source",
        "MPP-Photo-8.source",
        "MPP-Photo-9.source",
        "MPP-Photo-10.source",
        "SPB-Photo.source",
        "3P-Photo-1.source",
        "3P-Photo-2.source",
        "3P-Photo-3.source",
        "2P-Photo-Background.source",
        "2P-Photo-1.source",
        "2P-Photo-2.source",
        "1PF-Photo.source",
        "1PA-Photo.source",
    ]

    SUCCESS_STATUSES = {
        "succeeded",
        "finished",
        "completed",
    }

    FAILED_STATUSES = {
        "failed",
        "error",
    }

    def __init__(self):
        self.api_key = os.getenv("CREATOMATE_API_KEY")
        self.template_id = os.getenv("CREATOMATE_TEMPLATE_ID")
        self.webhook_url = os.getenv("CREATOMATE_WEBHOOK_URL")
        self.base_url = os.getenv(
            "CREATOMATE_API_BASE_URL",
            "https://api.creatomate.com/v2",
        ).rstrip("/")

    def is_configured(self):
        return bool(self.api_key and self.template_id)

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _limit_text(self, value, max_length, fallback=""):
        text = (value or fallback or "").strip()

        if len(text) <= max_length:
            return text

        return text[: max_length - 1].rstrip() + "…"

    def _safe_string(self, value, fallback=""):
        if value is None:
            return fallback

        return str(value).strip() or fallback

    def _get_media_urls(self, media_items):
        """
        Extract Creatomate-accessible media URLs.

        Supports:
        - already public URLs
        - local upload paths converted through PUBLIC_BASE_URL

        Expected result:
        https://your-ngrok-url.ngrok-free.dev/static/uploads/memories/photo/file.jpg
        """

        urls = []
        seen_urls = set()

        for media in media_items or []:
            file_url = getattr(media, "file_url", None)

            if not file_url:
                continue

            public_url = build_public_media_url(file_url)

            if not public_url:
                continue

            if not is_public_url(public_url):
                continue

            if public_url in seen_urls:
                continue

            print("CREATOMATE MEDIA URL:", public_url)

            seen_urls.add(public_url)
            urls.append(public_url)

        return urls

    def _get_scene_texts(self, storyboard):
        scenes = (storyboard or {}).get("scenes") or []
        texts = []

        for scene in scenes:
            text = (scene.get("text") or "").strip()

            if text:
                texts.append(text)

        return texts

    def _join_texts(self, texts, start=0, end=None, fallback=""):
        selected = texts[start:end]
        result = " ".join(selected).strip()

        return result or fallback

    def _get_date_text(self, storyboard):
        storyboard = storyboard or {}

        date_text = (
            storyboard.get("date_text")
            or storyboard.get("date")
            or storyboard.get("date_range")
            or ""
        )

        date_text = str(date_text).strip()

        if date_text.lower() in {"mixed", "unknown", "none", "n/a"}:
            return ""

        return date_text

    def _build_text_modifications(self, storyboard):
        storyboard = storyboard or {}

        title = self._safe_string(
            storyboard.get("title"),
            "Memory Story",
        )

        memorial_name = self._safe_string(
            storyboard.get("memorial_name"),
            title,
        )

        scene_texts = self._get_scene_texts(storyboard)

        intro_text = self._safe_string(
            storyboard.get("intro_text"),
            "in loving memory of",
        )

        date_text = self._get_date_text(storyboard)

        caption_text = (
            storyboard.get("caption_text")
            or self._join_texts(
                texts=scene_texts,
                start=0,
                end=3,
                fallback=storyboard.get("tone") or "A life remembered with love.",
            )
        )

        final_message = (
            storyboard.get("final_message")
            or self._join_texts(
                texts=scene_texts,
                start=3,
                end=None,
                fallback=self._join_texts(
                    texts=scene_texts,
                    start=0,
                    end=None,
                    fallback="A memory to keep close forever.",
                ),
            )
        )

        short_name = self._safe_string(
            storyboard.get("short_name"),
            memorial_name.split(" ")[0] if memorial_name else "Memory",
        )

        return {
            "IT-Text.text": self._limit_text(
                intro_text,
                40,
                "in loving memory of",
            ),
            "ID-Date.text": self._limit_text(
                date_text,
                40,
                "",
            ),
            "ID-Name.text": self._limit_text(
                memorial_name,
                80,
                "Memory Story",
            ),
            "1PC-Caption.text": self._limit_text(
                caption_text,
                360,
                "A life remembered with love.",
            ),
            "FM-Text.text": self._limit_text(
                final_message,
                420,
                "A memory to keep close forever.",
            ),
            "FT-Name.text": self._limit_text(
                short_name,
                40,
                title,
            ),
        }

    def _build_media_modifications(self, media_items):
        media_urls = self._get_media_urls(media_items)

        if not media_urls:
            raise RuntimeError(
                "No public uploaded media URLs were found. "
                "Creatomate cannot access local files. "
                "Set PUBLIC_BASE_URL and make /static/uploads publicly reachable."
            )

        modifications = {}

        for index, field_name in enumerate(self.MEDIA_FIELDS):
            modifications[field_name] = media_urls[index % len(media_urls)]

        return modifications

    def _build_music_modification(self, music_url):
        if not music_url:
            return {}

        music_url = build_public_media_url(music_url)

        if not is_public_url(music_url):
            return {}

        return {
            "Music.source": music_url,
        }

    def build_modifications(self, storyboard, media_items, music_url=None):
        modifications = {}

        modifications.update(
            self._build_text_modifications(storyboard)
        )

        modifications.update(
            self._build_media_modifications(media_items)
        )

        modifications.update(
            self._build_music_modification(music_url)
        )

        return modifications

    def create_render(
        self,
        storyboard,
        media_items,
        music_url=None,
        metadata=None,
    ):
        if not self.is_configured():
            raise RuntimeError(
                "Creatomate is not configured. "
                "Missing CREATOMATE_API_KEY or CREATOMATE_TEMPLATE_ID."
            )

        modifications = self.build_modifications(
            storyboard=storyboard,
            media_items=media_items,
            music_url=music_url,
        )

        payload = {
            "template_id": self.template_id,
            "modifications": modifications,
            "max_width": 1080,
            "max_height": 1920,
        }

        if self.webhook_url:
            payload["webhook_url"] = self.webhook_url

        if metadata is not None:
            payload["metadata"] = str(metadata)

        print("CREATOMATE TEMPLATE ID:", self.template_id)
        print("CREATOMATE MODIFICATION KEYS:", list(modifications.keys()))

        try:
            response = requests.post(
                f"{self.base_url}/renders",
                headers=self._headers(),
                json=payload,
                timeout=90,
            )

            response.raise_for_status()

        except requests.exceptions.HTTPError as error:
            response_text = getattr(error.response, "text", "")
            raise RuntimeError(
                f"Creatomate render request failed: {response_text}"
            ) from error

        except requests.exceptions.RequestException as error:
            raise RuntimeError(
                f"Creatomate render request failed: {repr(error)}"
            ) from error

        data = response.json()
        render = self._extract_render_object(data)

        render_id = render.get("id")
        video_url = render.get("url")
        status = render.get("status")

        if not render_id:
            raise RuntimeError(
                f"Creatomate response did not include a render id: {data}"
            )

        return {
            "render_id": render_id,
            "video_url": video_url,
            "status": status,
            "raw_response": data,
        }

    def _extract_render_object(self, data):
        if isinstance(data, list) and data:
            return data[0]

        if isinstance(data, dict):
            return data

        raise RuntimeError(
            f"Creatomate returned an unexpected render response: {data}"
        )

    def get_render(self, render_id):
        if not self.api_key:
            raise RuntimeError(
                "Creatomate is not configured. Missing CREATOMATE_API_KEY."
            )

        if not render_id:
            raise RuntimeError("render_id is required.")

        try:
            response = requests.get(
                f"{self.base_url}/renders/{render_id}",
                headers=self._headers(),
                timeout=60,
            )

            response.raise_for_status()

        except requests.exceptions.HTTPError as error:
            response_text = getattr(error.response, "text", "")
            raise RuntimeError(
                f"Creatomate get render request failed: {response_text}"
            ) from error

        except requests.exceptions.RequestException as error:
            raise RuntimeError(
                f"Creatomate get render request failed: {repr(error)}"
            ) from error

        return response.json()

    def normalize_render_status(self, render):
        status = (render or {}).get("status")

        if status in self.SUCCESS_STATUSES:
            return "completed"

        if status in self.FAILED_STATUSES:
            return "failed"

        return "rendering"
