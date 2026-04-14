from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.services.profile_service import ProfileService

profile_bp = Blueprint("profiles", __name__)
profile_service = ProfileService()


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
def get_profiles():
    """
    Retrieve all memorial profiles.
    """
    profiles = profile_service.get_profiles()
    return jsonify([serialize_profile(profile) for profile in profiles]), 200


@profile_bp.route("/<int:profile_id>", methods=["GET"])
def get_profile(profile_id):
    """
    Retrieve a single memorial profile by ID.
    """
    profile = profile_service.get_profile_by_id(profile_id)

    if not profile:
        return jsonify({"error": "Profile not found"}), 404

    return jsonify(serialize_profile(profile)), 200


@profile_bp.route("", methods=["POST"])
@jwt_required()
def create_profile():
    """
    Create a new memorial profile for the currently authenticated user.
    """
    data = request.get_json()
    user_id = get_jwt_identity()

    data["owner_id"] = user_id

    profile = profile_service.create_profile(data)
    return jsonify(serialize_profile(profile)), 201


@profile_bp.route("/<int:profile_id>", methods=["PUT"])
@jwt_required()
def update_profile(profile_id):
    """
    Update an existing memorial profile.
    """
    data = request.get_json()
    profile = profile_service.update_profile(profile_id, data)

    if not profile:
        return jsonify({"error": "Profile not found"}), 404

    return jsonify(serialize_profile(profile)), 200


@profile_bp.route("/<int:profile_id>", methods=["DELETE"])
@jwt_required()
def delete_profile(profile_id):
    """
    Delete a memorial profile.
    """
    deleted = profile_service.delete_profile(profile_id)

    if not deleted:
        return jsonify({"error": "Profile not found"}), 404

    return jsonify({"message": "Profile deleted successfully"}), 200
