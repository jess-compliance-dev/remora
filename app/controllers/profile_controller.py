import os
import uuid

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename

from app.services.profile_service import ProfileService

profile_bp = Blueprint("profiles", __name__)
profile_service = ProfileService()

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def serialize_profile(profile):
    if profile is None:
        return None

    return {
        "profile_id": profile.profile_id,
        "owner_id": profile.owner_id,
        "full_name": profile.full_name,
        "relationship": profile.relationship,
        "birth_date": profile.birth_date.isoformat() if profile.birth_date else None,
        "death_date": profile.death_date.isoformat() if profile.death_date else None,
        "status": profile.status,
        "short_description": profile.short_description,
        "profile_image_url": profile.profile_image_url,
        "created_at": profile.created_at.isoformat() if getattr(profile, "created_at", None) else None,
        "updated_at": profile.updated_at.isoformat() if getattr(profile, "updated_at", None) else None,
    }


@profile_bp.route("", methods=["GET"])
@jwt_required()
def get_profiles():
    user_id = int(get_jwt_identity())
    profiles = profile_service.get_profiles_by_owner_id(user_id)
    return jsonify([serialize_profile(profile) for profile in profiles]), 200


@profile_bp.route("/<int:profile_id>", methods=["GET"])
@jwt_required()
def get_profile(profile_id):
    user_id = int(get_jwt_identity())
    profile = profile_service.get_profile_by_id(profile_id)

    if not profile:
        return jsonify({"error": "Profile not found"}), 404

    if profile.owner_id != user_id:
        return jsonify({"error": "Forbidden"}), 404

    return jsonify(serialize_profile(profile)), 200


@profile_bp.route("", methods=["POST"])
@jwt_required()
def create_profile():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    full_name = (data.get("full_name") or "").strip()
    relationship = (data.get("relationship") or "").strip() or None
    birth_date = data.get("birth_date") or None
    death_date = data.get("death_date") or None
    short_description = (data.get("short_description") or "").strip() or None
    profile_image_url = data.get("profile_image_url") or None
    status = (data.get("status") or "").strip() or None

    if not full_name:
        return jsonify({"error": "full_name is required"}), 400

    user_id = int(get_jwt_identity())

    payload = {
        "owner_id": user_id,
        "full_name": full_name,
        "relationship": relationship,
        "birth_date": birth_date,
        "death_date": death_date,
        "status": status,
        "short_description": short_description,
        "profile_image_url": profile_image_url,
    }

    profile = profile_service.create_profile(payload)

    if not profile:
        return jsonify({"error": "Unable to create profile"}), 400

    return jsonify(serialize_profile(profile)), 201


@profile_bp.route("/upload-image", methods=["POST"])
@jwt_required()
def upload_profile_image():
    if "image" not in request.files:
        return jsonify({"error": "No image file provided"}), 400

    file = request.files["image"]

    if not file or file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Invalid file type"}), 400

    filename = secure_filename(file.filename)
    ext = filename.rsplit(".", 1)[1].lower()
    unique_name = f"{uuid.uuid4().hex}.{ext}"

    upload_folder = os.path.join(current_app.static_folder, "uploads", "profiles")
    os.makedirs(upload_folder, exist_ok=True)

    save_path = os.path.join(upload_folder, unique_name)
    file.save(save_path)

    file_url = f"/static/uploads/profiles/{unique_name}"

    return jsonify({
        "message": "Image uploaded successfully",
        "profile_image_url": file_url
    }), 201


@profile_bp.route("/<int:profile_id>", methods=["PUT"])
@jwt_required()
def update_profile(profile_id):
    user_id = int(get_jwt_identity())
    existing_profile = profile_service.get_profile_by_id(profile_id)

    if not existing_profile:
        return jsonify({"error": "Profile not found"}), 404

    if existing_profile.owner_id != user_id:
        return jsonify({"error": "Forbidden"}), 403

    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    updatable_fields = {
        "full_name": (data.get("full_name") or "").strip() if data.get("full_name") is not None else existing_profile.full_name,
        "relationship": (data.get("relationship") or "").strip() if data.get("relationship") is not None else existing_profile.relationship,
        "birth_date": data.get("birth_date") if "birth_date" in data else existing_profile.birth_date,
        "death_date": data.get("death_date") if "death_date" in data else existing_profile.death_date,
        "status": (data.get("status") or "").strip() if data.get("status") is not None else existing_profile.status,
        "short_description": (data.get("short_description") or "").strip() if data.get("short_description") is not None else existing_profile.short_description,
        "profile_image_url": data.get("profile_image_url") if "profile_image_url" in data else existing_profile.profile_image_url,
    }

    if not updatable_fields["full_name"]:
        return jsonify({"error": "full_name cannot be empty"}), 400

    updated_profile = profile_service.update_profile(profile_id, updatable_fields)

    if not updated_profile:
        return jsonify({"error": "Unable to update profile"}), 400

    return jsonify(serialize_profile(updated_profile)), 200


@profile_bp.route("/<int:profile_id>", methods=["DELETE"])
@jwt_required()
def delete_profile(profile_id):
    user_id = int(get_jwt_identity())
    existing_profile = profile_service.get_profile_by_id(profile_id)

    if not existing_profile:
        return jsonify({"error": "Profile not found"}), 404

    if existing_profile.owner_id != user_id:
        return jsonify({"error": "Forbidden"}), 403

    deleted = profile_service.delete_profile(profile_id)

    if not deleted:
        return jsonify({"error": "Unable to delete profile"}), 400

    return jsonify({"message": "Profile deleted successfully"}), 200

