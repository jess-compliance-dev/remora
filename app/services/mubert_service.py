import os

import requests


class MubertService:
    """
    Service for generating music with Mubert.

    Required environment variables:
    - MUBERT_CUSTOMER_ID
    - MUBERT_ACCESS_TOKEN

    Optional:
    - MUBERT_API_URL
    - MUBERT_PLAYLIST_INDEX
    - MUBERT_AUDIO_FORMAT
    - MUBERT_AUDIO_BITRATE
    """

    def __init__(self):
        self.customer_id = os.getenv("MUBERT_CUSTOMER_ID")
        self.access_token = os.getenv("MUBERT_ACCESS_TOKEN")
        self.api_url = os.getenv(
            "MUBERT_API_URL",
            "https://music-api.mubert.com/api/v3/public/tracks",
        )
        self.playlist_index = os.getenv("MUBERT_PLAYLIST_INDEX", "1.0.0")
        self.audio_format = os.getenv("MUBERT_AUDIO_FORMAT", "mp3")
        self.audio_bitrate = int(os.getenv("MUBERT_AUDIO_BITRATE", "320"))

    def is_configured(self):
        return bool(self.customer_id and self.access_token)

    def _extract_audio_url(self, data):
        if not isinstance(data, dict):
            return None

        direct_keys = [
            "url",
            "track_url",
            "download_url",
            "audio_url",
            "file_url",
            "render_url",
        ]

        for key in direct_keys:
            value = data.get(key)
            if isinstance(value, str) and value.startswith("http"):
                return value

        nested_candidates = [
            data.get("data"),
            data.get("result"),
            data.get("track"),
            data.get("payload"),
        ]

        for candidate in nested_candidates:
            if isinstance(candidate, dict):
                nested_url = self._extract_audio_url(candidate)
                if nested_url:
                    return nested_url

            if isinstance(candidate, list):
                for item in candidate:
                    nested_url = self._extract_audio_url(item)
                    if nested_url:
                        return nested_url

        return None

    def _extract_track_id(self, data):
        if not isinstance(data, dict):
            return None

        for key in ["id", "track_id", "uuid"]:
            value = data.get(key)
            if value:
                return str(value)

        for key in ["data", "result", "track", "payload"]:
            value = data.get(key)

            if isinstance(value, dict):
                nested_id = self._extract_track_id(value)
                if nested_id:
                    return nested_id

            if isinstance(value, list):
                for item in value:
                    nested_id = self._extract_track_id(item)
                    if nested_id:
                        return nested_id

        return None

    def generate_track(self, prompt: str, duration_seconds: int = 30):
        """
        Generate a music track.

        Returns:
            {
                "music_url": str | None,
                "mubert_track_id": str | None,
                "raw_response": dict
            }
        """

        if not self.is_configured():
            raise RuntimeError("Mubert is not configured. Missing MUBERT_CUSTOMER_ID or MUBERT_ACCESS_TOKEN.")

        safe_duration = max(15, min(int(duration_seconds or 30), 300))

        payload = {
            "playlist_index": self.playlist_index,
            "duration": safe_duration,
            "bitrate": self.audio_bitrate,
            "format": self.audio_format,
            "intensity": "medium",
            "mode": "track",
            "prompt": prompt or "warm emotional cinematic background music",
        }

        response = requests.post(
            self.api_url,
            headers={
                "customer-id": self.customer_id,
                "access-token": self.access_token,
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=90,
        )

        response.raise_for_status()
        data = response.json()

        return {
            "music_url": self._extract_audio_url(data),
            "mubert_track_id": self._extract_track_id(data),
            "raw_response": data,
        }
    