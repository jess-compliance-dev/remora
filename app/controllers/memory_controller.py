import os
import uuid
from datetime import datetime

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from werkzeug.utils import secure_filename

from app.extensions.db import db
from app.models.memory import Memory
from app.services.chat_ai_service import ChatAIService
from app.services.profile_service import ProfileService
from app.utils.uploads import detect_mime_from_file_storage, is_allowed_mime

memory_bp = Blueprint("memories", __name__)
profile_service = ProfileService()

ALLOWED_MEMORY_EXTENSIONS = {
    "photo": {"png", "jpg", "jpeg", "webp"},
    "video": {"mp4", "mov", "webm", "m4v"},
    "voice": {"mp3", "wav", "m4a", "ogg", "webm"},
}

ALLOWED_TOPICS = set(ChatAIService.TOPICS.keys())

TOPIC_LABELS = ChatAIService.TOPIC_LABELS


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


def parse_optional_date(value):
    value = (value or "").strip()

    if not value:
        return None

    # HTML date input format: YYYY-MM-DD
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        pass

    # German display input fallback: DD.MM.YYYY
    try:
        return datetime.strptime(value, "%d.%m.%Y").date()
    except ValueError:
        return None


def normalize_optional_topic(value):
    value = (value or "").strip()

    if not value:
        return None

    if value not in ALLOWED_TOPICS:
        return None

    return value


def serialize_memory(memory):
    if memory is None:
        return None

    topic = getattr(memory, "topic", None)

    return {
        "memory_id": memory.memory_id,
        "owner_id": memory.owner_id,
        "profile_id": memory.profile_id,
        "memory_type": memory.memory_type,
        "file_url": memory.file_url,
        "original_filename": memory.original_filename,
        "title": getattr(memory, "title", None),
        "memory_date": memory.memory_date.isoformat()
        if getattr(memory, "memory_date", None)
        else None,
        "topic": topic,
        "topic_label": TOPIC_LABELS.get(topic) if topic else None,
        "created_at": memory.created_at.isoformat()
        if getattr(memory, "created_at", None)
        else None,
        "updated_at": memory.updated_at.isoformat()
        if getattr(memory, "updated_at", None)
        else None,
    }


def json_error(message, status_code=400):
    return jsonify({"error": message}), status_code


def current_user_id():
    return int(get_jwt_identity())


def get_owned_memory_or_404(memory_id, user_id):
    return Memory.query.filter_by(
        memory_id=memory_id,
        owner_id=user_id,
    ).first()


@memory_bp.route("", methods=["GET"])
@jwt_required()
def get_memories():
    user_id = current_user_id()
    profile_id = request.args.get("profile_id", type=int)

    query = Memory.query.filter_by(owner_id=user_id)

    if profile_id is not None:
        profile = profile_service.get_profile_by_id(profile_id)

        if not profile:
            return json_error("Profile not found", 404)

        if int(profile.owner_id) != user_id:
            return json_error("Forbidden", 403)

        query = query.filter_by(profile_id=profile_id)

    memories = query.order_by(Memory.created_at.desc()).all()
    return jsonify([serialize_memory(memory) for memory in memories]), 200


@memory_bp.route("/topics", methods=["GET"])
@jwt_required()
def get_memory_topics():
    return jsonify(
        [
            {
                "id": topic,
                "label": TOPIC_LABELS.get(topic, topic.replace("_", " ").title()),
            }
            for topic in ChatAIService.TOPICS.keys()
        ]
    ), 200


@memory_bp.route("/<int:memory_id>", methods=["GET"])
@jwt_required()
def get_memory(memory_id):
    user_id = current_user_id()

    memory = get_owned_memory_or_404(memory_id, user_id)

    if not memory:
        return json_error("Memory not found", 404)

    return jsonify(serialize_memory(memory)), 200


@memory_bp.route("/upload", methods=["POST"])
@jwt_required()
def upload_memory():
    user_id = current_user_id()

    if "file" not in request.files:
        return json_error("No file provided", 400)

    file = request.files["file"]
    memory_type = (request.form.get("memory_type") or "").strip().lower()
    profile_id = request.form.get("profile_id")

    title = (request.form.get("title") or "").strip() or None
    memory_date = parse_optional_date(request.form.get("memory_date"))
    topic = normalize_optional_topic(request.form.get("topic"))

    if not file or file.filename == "":
        return json_error("No selected file", 400)

    if memory_type not in {"photo", "video", "voice"}:
        return json_error("Invalid memory_type", 400)

    if not allowed_memory_file(file.filename, memory_type):
        return json_error("Invalid file type for memory_type", 400)

    mime_category = memory_type_to_mime_category(memory_type)
    mime_type = detect_mime_from_file_storage(file)

    if not is_allowed_mime(mime_type, mime_category):
        return json_error("Invalid file MIME type for memory_type", 400)

    parsed_profile_id = None

    if profile_id:
        try:
            parsed_profile_id = int(profile_id)
        except ValueError:
            return json_error("profile_id must be an integer", 400)

        profile = profile_service.get_profile_by_id(parsed_profile_id)

        if not profile:
            return json_error("Profile not found", 404)

        if int(profile.owner_id) != user_id:
            return json_error("Forbidden", 403)

    if request.form.get("topic") and topic is None:
        return json_error("Invalid topic", 400)

    if request.form.get("memory_date") and memory_date is None:
        return json_error("memory_date must be YYYY-MM-DD or DD.MM.YYYY", 400)

    filename = secure_filename(file.filename)
    extension = filename.rsplit(".", 1)[1].lower()
    unique_name = f"{uuid.uuid4().hex}.{extension}"

    upload_folder = os.path.join(
        current_app.static_folder,
        "uploads",
        "memories",
        memory_type,
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
        title=title,
        memory_date=memory_date,
        topic=topic,
    )

    db.session.add(memory)
    db.session.commit()

    return jsonify(
        {
            "message": "Memory uploaded successfully",
            "memory": serialize_memory(memory),
        }
    ), 201


@memory_bp.route("/<int:memory_id>", methods=["PATCH", "PUT"])
@jwt_required()
def update_memory(memory_id):
    user_id = current_user_id()

    memory = get_owned_memory_or_404(memory_id, user_id)

    if not memory:
        return json_error("Memory not found", 404)

    data = request.get_json(silent=True)

    if data is None:
        return json_error("Request body must be valid JSON", 400)

    if "title" in data:
        memory.title = (str(data.get("title") or "").strip() or None)

    if "memory_date" in data:
        raw_date = data.get("memory_date")
        parsed_date = parse_optional_date(raw_date)

        if raw_date and not parsed_date:
            return json_error("memory_date must be YYYY-MM-DD or DD.MM.YYYY", 400)

        memory.memory_date = parsed_date

    if "topic" in data:
        raw_topic = data.get("topic")
        parsed_topic = normalize_optional_topic(raw_topic)

        if raw_topic and not parsed_topic:
            return json_error("Invalid topic", 400)

        memory.topic = parsed_topic

    db.session.commit()

    return jsonify(serialize_memory(memory)), 200


@memory_bp.route("/<int:memory_id>", methods=["DELETE"])
@jwt_required()
def delete_memory(memory_id):
    user_id = current_user_id()

    memory = get_owned_memory_or_404(memory_id, user_id)

    if not memory:
        return json_error("Memory not found", 404)

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
