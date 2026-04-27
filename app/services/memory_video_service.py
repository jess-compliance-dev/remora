import os
from pathlib import Path
from types import SimpleNamespace

from flask import current_app

from app.database.memory_video_database import MemoryVideoDatabase
from app.models.life_story import LifeStory
from app.models.story_media import StoryMedia
from app.services.creatomate_service import CreatomateService
from app.services.mubert_service import MubertService
from app.services.profile_service import ProfileService
from app.services.storyboard_ai_service import StoryboardAIService


class MemoryVideoService:
    """
    Orchestrates memory video generation.

    Current MVP flow:
    LifeStory + uploaded photos
        -> StoryboardAIService
        -> CreatomateService with template background music
        -> MemoryVideo

    Media sources:
    1. StoryMedia rows linked to the story/profile
    2. Local files in app/static/uploads/memories/photo

    Only photos/images are allowed.
    Videos and voice/audio files are intentionally ignored.
    """

    ACTIVE_OR_DONE_STATUSES = {
        "pending",
        "generating_storyboard",
        "generating_music",
        "rendering",
        "completed",
    }

    ALLOWED_MEDIA_TYPES = {
        "photo",
        "image",
        "memory_photo",
    }

    PHOTO_EXTENSIONS = {
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
        ".gif",
    }

    BLOCKED_EXTENSIONS = {
        ".mp4",
        ".mov",
        ".m4v",
        ".webm",
        ".mp3",
        ".wav",
        ".m4a",
        ".ogg",
    }

    def __init__(self):
        self.video_db = MemoryVideoDatabase()
        self.profile_service = ProfileService()
        self.storyboard_ai = StoryboardAIService()
        self.creatomate = CreatomateService()

        self.use_mubert = (
            os.getenv("USE_MUBERT_FOR_MEMORY_VIDEOS", "false").lower() == "true"
        )

        self.mubert = MubertService() if self.use_mubert else None

    def get_video_by_id(self, video_id, user_id):
        video = self.video_db.get_by_id(video_id)

        if not video:
            return None, "Memory video not found"

        profile = self.profile_service.get_profile_by_id(video.profile_id)

        if not profile:
            return None, "Profile not found"

        if str(profile.owner_id) != str(user_id):
            return None, "Forbidden"

        return video, None

    def get_videos_by_story_id(self, story_id, user_id):
        story = LifeStory.query.get(story_id)

        if not story:
            return None, "Life story not found"

        profile = self.profile_service.get_profile_by_id(story.profile_id)

        if not profile:
            return None, "Profile not found"

        if str(profile.owner_id) != str(user_id):
            return None, "Forbidden"

        return self.video_db.get_by_story_id(story_id), None

    def _get_existing_video_for_story(self, story_id):
        existing_videos = self.video_db.get_by_story_id(story_id) or []

        for existing_video in existing_videos:
            if existing_video.status in self.ACTIVE_OR_DONE_STATUSES:
                return existing_video

        return None

    def _is_photo_file_url(self, file_url):
        if not file_url:
            return False

        lowered_url = str(file_url).strip().lower()

        if not lowered_url:
            return False

        if "/voice/" in lowered_url:
            return False

        if "/video/" in lowered_url:
            return False

        if lowered_url.endswith(tuple(self.BLOCKED_EXTENSIONS)):
            return False

        return lowered_url.endswith(tuple(self.PHOTO_EXTENSIONS))

    def _is_allowed_story_media(self, media):
        media_type = (getattr(media, "media_type", "") or "").lower().strip()
        file_url = (getattr(media, "file_url", "") or "").strip()

        if media_type not in self.ALLOWED_MEDIA_TYPES:
            return False

        return self._is_photo_file_url(file_url)

    def _get_story_media_for_story_and_profile(self, story):
        """
        Load photo StoryMedia rows attached to this story and other stories
        under the same memorial profile.
        """

        if not story:
            return []

        direct_media = (
            StoryMedia.query
            .filter_by(story_id=story.story_id)
            .order_by(StoryMedia.created_at.asc())
            .all()
        )

        profile_media = (
            StoryMedia.query
            .join(LifeStory, StoryMedia.story_id == LifeStory.story_id)
            .filter(LifeStory.profile_id == story.profile_id)
            .order_by(StoryMedia.created_at.asc())
            .all()
        )

        combined_media = []
        seen_urls = set()

        for media in direct_media + profile_media:
            if not self._is_allowed_story_media(media):
                continue

            file_url = str(getattr(media, "file_url", "")).strip()

            if file_url in seen_urls:
                continue

            seen_urls.add(file_url)
            combined_media.append(media)

        return combined_media

    def _get_upload_folder(self):
        upload_folder = current_app.config.get("UPLOAD_FOLDER")

        if upload_folder:
            return Path(upload_folder).resolve()

        return Path(current_app.root_path).parent.joinpath(
            "static",
            "uploads",
        ).resolve()

    def _build_local_media_item(self, file_path, media_type, index):
        """
        Create a small object that behaves like StoryMedia for CreatomateService.

        file_url is stored as an upload-relative path:
        uploads/memories/photo/file.jpg

        CreatomateService will convert it to:
        PUBLIC_BASE_URL/static/uploads/memories/photo/file.jpg
        """

        upload_folder = self._get_upload_folder()
        relative_path = file_path.resolve().relative_to(upload_folder)
        file_url = f"uploads/{relative_path.as_posix()}"

        return SimpleNamespace(
            media_id=f"local_{media_type}_{index}",
            media_type=media_type,
            file_url=file_url,
            caption=None,
            created_at=None,
        )

    def _scan_local_upload_media(self):
        """
        Load uploaded photos directly from:
        app/static/uploads/memories/photo

        Intentionally ignores:
        app/static/uploads/memories/video
        app/static/uploads/memories/voice
        """

        upload_folder = self._get_upload_folder()
        memories_folder = upload_folder / "memories"
        photo_folder = memories_folder / "photo"

        media_items = []
        index = 0

        if not photo_folder.exists():
            return media_items

        for file_path in sorted(photo_folder.iterdir()):
            if not file_path.is_file():
                continue

            if file_path.suffix.lower() not in self.PHOTO_EXTENSIONS:
                continue

            index += 1
            media_items.append(
                self._build_local_media_item(
                    file_path=file_path,
                    media_type="photo",
                    index=index,
                )
            )

        return media_items

    def _get_media_for_story_and_profile(self, story):
        """
        Main media loader for Life Story Video.

        Priority:
        1. Photo StoryMedia from database
        2. Local photos from app/static/uploads/memories/photo

        Videos and voice/audio are ignored.
        """

        story_media = self._get_story_media_for_story_and_profile(story)
        local_media = self._scan_local_upload_media()

        combined_media = []
        seen_urls = set()

        for media in story_media + local_media:
            file_url = str(getattr(media, "file_url", "") or "").strip()

            if not self._is_photo_file_url(file_url):
                continue

            if file_url in seen_urls:
                continue

            seen_urls.add(file_url)
            combined_media.append(media)

        return combined_media

    def _generate_optional_music(self, storyboard):
        if not self.use_mubert or not self.mubert:
            return None, None

        music_result = self.mubert.generate_track(
            prompt=storyboard.get("music_prompt"),
            duration_seconds=storyboard.get("duration_seconds", 30),
        )

        return (
            music_result.get("music_url"),
            music_result.get("mubert_track_id"),
        )

    def create_video_from_story(self, story_id, user_id):
        story = LifeStory.query.get(story_id)

        if not story:
            return None, "Life story not found"

        profile = self.profile_service.get_profile_by_id(story.profile_id)

        if not profile:
            return None, "Profile not found"

        if str(profile.owner_id) != str(user_id):
            return None, "Forbidden"

        existing_video = self._get_existing_video_for_story(story_id)

        if existing_video:
            return existing_video, None

        media_items = self._get_media_for_story_and_profile(story)

        if not media_items:
            return None, (
                "No uploaded photos found for this profile. "
                "Please upload photos before creating a Life Story Video."
            )

        memory_video = self.video_db.create(
            {
                "profile_id": story.profile_id,
                "story_id": story.story_id,
                "created_by": int(user_id) if user_id is not None else None,
                "title": story.title,
                "status": "generating_storyboard",
            }
        )

        if not memory_video:
            return None, "Unable to create memory video record"

        try:
            storyboard = self.storyboard_ai.generate_storyboard(
                story=story,
                media_items=media_items,
            )

            if not storyboard:
                raise RuntimeError("Unable to generate storyboard")

            self.video_db.update(
                memory_video,
                {
                    "storyboard_json": storyboard,
                    "music_prompt": storyboard.get("music_prompt"),
                    "status": "rendering",
                },
            )

            music_url = None
            mubert_track_id = None

            if self.use_mubert:
                self.video_db.update(
                    memory_video,
                    {
                        "status": "generating_music",
                    },
                )

                try:
                    music_url, mubert_track_id = self._generate_optional_music(
                        storyboard=storyboard,
                    )
                except Exception as music_error:
                    print("MUBERT GENERATION ERROR:", repr(music_error))
                    music_url = None
                    mubert_track_id = None

                self.video_db.update(
                    memory_video,
                    {
                        "music_url": music_url,
                        "mubert_track_id": mubert_track_id,
                        "status": "rendering",
                    },
                )

            render_result = self.creatomate.create_render(
                storyboard=storyboard,
                media_items=media_items,
                music_url=music_url,
                metadata=str(memory_video.video_id),
            )

            render_video_url = render_result.get("video_url")
            render_status = render_result.get("status")

            next_status = "rendering"

            if render_video_url and render_status in {"succeeded", "finished", "completed"}:
                next_status = "completed"

            updated_video = self.video_db.update(
                memory_video,
                {
                    "creatomate_render_id": render_result.get("render_id"),
                    "video_url": render_video_url,
                    "status": next_status,
                },
            )

            return updated_video, None

        except Exception as error:
            updated_video = self.video_db.update(
                memory_video,
                {
                    "status": "failed",
                    "error_message": str(error),
                },
            )
            return updated_video, str(error)

    def refresh_render_status(self, video_id, user_id):
        video, error = self.get_video_by_id(video_id, user_id)

        if error:
            return None, error

        if not video.creatomate_render_id:
            return video, "Memory video has no Creatomate render id"

        try:
            render = self.creatomate.get_render(video.creatomate_render_id)

            video_url = render.get("url") or video.video_url
            next_status = self.creatomate.normalize_render_status(render)

            updated_video = self.video_db.update(
                video,
                {
                    "status": next_status,
                    "video_url": video_url,
                    "error_message": render.get("error_message") or video.error_message,
                },
            )

            return updated_video, None

        except Exception as error:
            updated_video = self.video_db.update(
                video,
                {
                    "error_message": str(error),
                },
            )
            return updated_video, str(error)
