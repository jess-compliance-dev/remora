import os

from flask import Blueprint, abort, current_app, send_from_directory

upload_bp = Blueprint("uploads", __name__)


@upload_bp.route("/<path:filename>", methods=["GET"])
def serve_uploaded_file(filename):
    """
    Serve uploaded files from the local uploads directory.

    Example:
    /uploads/memories/photo/image.jpg
    /uploads/memories/video/video.mp4

    Important:
    This only works for Creatomate if the Flask app is publicly reachable.
    For local development, use ngrok and set PUBLIC_BASE_URL.
    """

    upload_folder = current_app.config.get("UPLOAD_FOLDER")

    if not upload_folder:
        upload_folder = os.path.join(current_app.root_path, "..", "uploads")

    upload_folder = os.path.abspath(upload_folder)

    requested_path = os.path.abspath(
        os.path.join(upload_folder, filename)
    )

    if not requested_path.startswith(upload_folder):
        abort(403)

    if not os.path.exists(requested_path):
        abort(404)

    return send_from_directory(upload_folder, filename)
