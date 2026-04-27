import os
from urllib.parse import quote


def is_public_url(value):
    if not value:
        return False

    value = str(value).strip()

    return value.startswith("http://") or value.startswith("https://")


def normalize_upload_path(file_url):
    """
    Converts stored upload paths into upload-relative paths.

    Examples:
    app/static/uploads/memories/photo/a.jpg -> memories/photo/a.jpg
    static/uploads/memories/photo/a.jpg -> memories/photo/a.jpg
    uploads/memories/photo/a.jpg -> memories/photo/a.jpg
    memories/photo/a.jpg -> memories/photo/a.jpg
    """

    if not file_url:
        return None

    path = str(file_url).strip().replace("\\", "/")

    if path.startswith("http://") or path.startswith("https://"):
        return path

    if path.startswith("/"):
        path = path[1:]

    prefixes = [
        "app/static/uploads/",
        "static/uploads/",
        "uploads/",
    ]

    for prefix in prefixes:
        if path.startswith(prefix):
            path = path[len(prefix):]
            break

    return path.strip("/")


def build_public_media_url(file_url):
    """
    Returns a Creatomate-accessible public URL.

    Current Remora upload location:
    app/static/uploads/memories/photo/...
    app/static/uploads/memories/video/...

    Public URL:
    PUBLIC_BASE_URL/static/uploads/memories/photo/...
    """

    if not file_url:
        return None

    if is_public_url(file_url):
        return str(file_url).strip()

    public_base_url = os.getenv("PUBLIC_BASE_URL", "").strip().rstrip("/")

    if not public_base_url:
        return None

    upload_path = normalize_upload_path(file_url)

    if not upload_path:
        return None

    encoded_path = quote(upload_path, safe="/")

    return f"{public_base_url}/static/uploads/{encoded_path}"