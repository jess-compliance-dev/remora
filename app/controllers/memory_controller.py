import os
import uuid

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename

from app.extensions.db import db
from app.models.memory import Memory
from app.services.profile_service import ProfileService
from app.utils.uploads import detect_mime_from_file_storage, is_allowed_mime

memory_bp = Blueprint("memories", __name__)
profile_service = ProfileService()

ALLOWED_MEMORY_EXTENSIONS = {
    "photo": {"png", "jpg", "jpeg", "webp"},
    "video": {"mp4", "mov", "webm", "m4v"},
    "voice": {"mp3", "wav", "m4a", "ogg", "webm"},
}


def allowed_memory_file(filename, memory_type):
    if "." not in filename:
        return False

    extension = filename.rsplit(".", 1)[1].lower()
    return extension in ALLOWED_MEMORY_EXTENSIONS.get(memory_type, set())


def memory_type_to_mime_category(memory_type):
    if memory_type == "photo":
        return "image"

    if memory_type == "video":
        return "video"

    if memory_type == "voice":
        return "audio"

    return None


def serialize_memory(memory):
    if memory is None:
        return None

    return {
        "memory_id": memory.memory_id,
        "owner_id": memory.owner_id,
        "profile_id": memory.profile_id,
        "memory_type": memory.memory_type,
        "file_url": memory.file_url,
        "original_filename": memory.original_filename,
        "created_at": memory.created_at.isoformat() if getattr(memory, "created_at", None) else None,
        "updated_at": memory.updated_at.isoformat() if getattr(memory, "updated_at", None) else None,
    }


@memory_bp.route("", methods=["GET"])
@jwt_required()
def get_memories():
    user_id = int(get_jwt_identity())
    profile_id = request.args.get("profile_id", type=int)

    query = Memory.query.filter_by(owner_id=user_id)

    if profile_id is not None:
        profile = profile_service.get_profile_by_id(profile_id)

        if not profile:
            return jsonify({"error": "Profile not found"}), 404

        if profile.owner_id != user_id:
            return jsonify({"error": "Forbidden"}), 403

        query = query.filter_by(profile_id=profile_id)

    memories = query.order_by(Memory.created_at.desc()).all()
    return jsonify([serialize_memory(memory) for memory in memories]), 200


@memory_bp.route("/<int:memory_id>", methods=["GET"])
@jwt_required()
def get_memory(memory_id):
    user_id = int(get_jwt_identity())

    memory = Memory.query.filter_by(
        memory_id=memory_id,
        owner_id=user_id
    ).first()

    if not memory:
        return jsonify({"error": "Memory not found"}), 404

    return jsonify(serialize_memory(memory)), 200


@memory_bp.route("/upload", methods=["POST"])
@jwt_required()
def upload_memory():
    user_id = int(get_jwt_identity())

    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    memory_type = (request.form.get("memory_type") or "").strip().lower()
    profile_id = request.form.get("profile_id")

    if not file or file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    if memory_type not in {"photo", "video", "voice"}:
        return jsonify({"error": "Invalid memory_type"}), 400

    if not allowed_memory_file(file.filename, memory_type):
        return jsonify({"error": "Invalid file type for memory_type"}), 400

    mime_category = memory_type_to_mime_category(memory_type)
    mime_type = detect_mime_from_file_storage(file)

    if not is_allowed_mime(mime_type, mime_category):
        return jsonify({"error": "Invalid file MIME type for memory_type"}), 400

    profile = None
    parsed_profile_id = None

    if profile_id:
        try:
            parsed_profile_id = int(profile_id)
        except ValueError:
            return jsonify({"error": "profile_id must be an integer"}), 400

        profile = profile_service.get_profile_by_id(parsed_profile_id)

        if not profile:
            return jsonify({"error": "Profile not found"}), 404

        if profile.owner_id != user_id:
            return jsonify({"error": "Forbidden"}), 403

    filename = secure_filename(file.filename)
    extension = filename.rsplit(".", 1)[1].lower()
    unique_name = f"{uuid.uuid4().hex}.{extension}"

    upload_folder = os.path.join(
        current_app.static_folder,
        "uploads",
        "memories",
        memory_type
    )
    os.makedirs(upload_folder, exist_ok=True)

    save_path = os.path.join(upload_folder, unique_name)
    file.save(save_path)

    file_url = f"/static/uploads/memories/{memory_type}/{unique_name}"

    memory = Memory(
        owner_id=user_id,
        profile_id=parsed_profile_id,
        memory_type=memory_type,
        file_url=file_url,
        original_filename=filename,
    )

    db.session.add(memory)
    db.session.commit()

    return jsonify({
        "message": "Memory uploaded successfully",
        "memory": serialize_memory(memory)
    }), 201


@memory_bp.route("/<int:memory_id>", methods=["DELETE"])
@jwt_required()
def delete_memory(memory_id):
    user_id = int(get_jwt_identity())

    memory = Memory.query.filter_by(
        memory_id=memory_id,
        owner_id=user_id
    ).first()

    if not memory:
        return jsonify({"error": "Memory not found"}), 404

    if memory.file_url:
        relative_path = memory.file_url.replace("/static/", "", 1)
        file_path = os.path.join(current_app.static_folder, relative_path)

        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                pass

    db.session.delete(memory)
    db.session.commit()

    return jsonify({"message": "Memory deleted successfully"}), 200
