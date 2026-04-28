ALLOWED_IMAGE_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif",
}

ALLOWED_VIDEO_MIME_TYPES = {
    "video/mp4",
    "video/webm",
    "video/quicktime",
}

ALLOWED_AUDIO_MIME_TYPES = {
    "audio/mpeg",
    "audio/wav",
    "audio/webm",
    "audio/mp4",
    "audio/x-m4a",
}


def is_allowed_mime(mime_type, category):
    if category == "image":
        return mime_type in ALLOWED_IMAGE_MIME_TYPES

    if category == "video":
        return mime_type in ALLOWED_VIDEO_MIME_TYPES

    if category == "audio":
        return mime_type in ALLOWED_AUDIO_MIME_TYPES

    return False


def detect_mime_from_file_storage(file_storage):
    """
    Best-effort MIME detection.

    Uses python-magic when available.
    Falls back to the browser-provided MIME type.
    """
    try:
        import magic

        head = file_storage.stream.read(2048)
        file_storage.stream.seek(0)

        return magic.from_buffer(head, mime=True)

    except Exception:
        file_storage.stream.seek(0)
        return file_storage.mimetype
