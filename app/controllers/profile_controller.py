import os
import uuid
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename

from app.services.profile_service import ProfileService

profile_bp = Blueprint("profiles", __name__)
profile_service = ProfileService()

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def serialize_profile(profile):
    """
    Convert a MemorialProfile object into a JSON-serializable dictionary.
    """
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
        "created_at": profile.created_at.isoformat(),
        "updated_at": profile.updated_at.isoformat(),
    }


@profile_bp.route("", methods=["GET"])
@jwt_required()
def get_profiles():
    """
    Retrieve all memorial profiles for the currently authenticated user.
    """
    user_id = get_jwt_identity()
    profiles = profile_service.get_profiles_by_owner_id(user_id)

    return jsonify([serialize_profile(profile) for profile in profiles]), 200


@profile_bp.route("/<int:profile_id>", methods=["GET"])
@jwt_required()
def get_profile(profile_id):
    """
    Retrieve a single memorial profile by ID for the currently authenticated user.
    """
    user_id = get_jwt_identity()
    profile = profile_service.get_profile_by_id(profile_id)

    if not profile:
        return jsonify({"error": "Profile not found"}), 404

    if str(profile.owner_id) != str(user_id):
        return jsonify({"error": "Access denied"}), 403

    return jsonify(serialize_profile(profile)), 200


@profile_bp.route("", methods=["POST"])
@jwt_required()
def create_profile():
    """
    Create a new memorial profile for the currently authenticated user.
    """
    data = request.get_json()
    user_id = get_jwt_identity()

    data["owner_id"] = int(user_id)
    data.setdefault("status", None)

    profile = profile_service.create_profile(data)
    return jsonify(serialize_profile(profile)), 201


@profile_bp.route("/upload-image", methods=["POST"])
@jwt_required()
def upload_profile_image():
    """
    Upload a profile image and return the saved file URL.
    """
    if "image" not in request.files:
        return jsonify({"error": "No image file provided"}), 400

    file = request.files["image"]

    if file.filename == "":
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
    """
    Update an existing memorial profile.
    """
    user_id = get_jwt_identity()
    profile = profile_service.get_profile_by_id(profile_id)

    if not profile:
        return jsonify({"error": "Profile not found"}), 404

    if str(profile.owner_id) != str(user_id):
        return jsonify({"error": "Access denied"}), 403

    data = request.get_json()
    updated_profile = profile_service.update_profile(profile_id, data)

    return jsonify(serialize_profile(updated_profile)), 200


@profile_bp.route("/<int:profile_id>", methods=["DELETE"])
@jwt_required()
def delete_profile(profile_id):
    """
    Delete a memorial profile.
    """
    user_id = get_jwt_identity()
    profile = profile_service.get_profile_by_id(profile_id)

    if not profile:
        return jsonify({"error": "Profile not found"}), 404

    if str(profile.owner_id) != str(user_id):
        return jsonify({"error": "Access denied"}), 403

    deleted = profile_service.delete_profile(profile_id)

    if not deleted:
        return jsonify({"error": "Profile not found"}), 404

    return jsonify({"message": "Profile deleted successfully"}), 200
