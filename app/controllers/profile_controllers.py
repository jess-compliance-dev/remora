from flask import Blueprint, request, jsonify

# Definition of profile blueprint
profile_bp = Blueprint("profiles", __name__)


@profile_bp.route("", methods=["GET"])
def get_profiles():
    """
    Retrieve all memorial profiles.
    Returns:
        JSON: List of memorial profiles.
        HTTP 200: Success.
    """
    return jsonify([]), 200


@profile_bp.route("/<int:profile_id>", methods=["GET"])
def get_profile(profile_id):
    """
    Retrieve a single memorial profile by ID.
    Returns:
        JSON: Memorial profile object.
        HTTP 200: Success.
        HTTP 404: Profile not found.
    """
    return jsonify({"profile_id": profile_id}), 200


@profile_bp.route("", methods=["POST"])
def create_profile():
    """
    Create a new memorial profile.
    Request Body:
        owner_id (int): ID of the user who owns the profile.
        full_name (str): Full name of the person.
        relationship (str): Relationship to the user.
        birth_date (str): Birth date in YYYY-MM-DD format.
        death_date (str): Death date in YYYY-MM-DD format.
        status (str): Current status, e.g. living, dying, deceased.
        short_description (str): Short description of the person.
        profile_image_url (str): URL or path to profile image.
    Returns:
        JSON: Created memorial profile.
        HTTP 201: Created.
    """
    data = request.get_json()
    return jsonify(data), 201


@profile_bp.route("/<int:profile_id>", methods=["PUT"])
def update_profile(profile_id):
    """
    Update an existing memorial profile.
    Request Body:
        Any updatable memorial profile fields.
    Returns:
        JSON: Updated memorial profile data.
        HTTP 200: Success.
        HTTP 404: Profile not found.
    """
    data = request.get_json()
    return jsonify({"profile_id": profile_id, "updated_data": data}), 200


@profile_bp.route("/<int:profile_id>", methods=["DELETE"])
def delete_profile(profile_id):
    """
    Delete a memorial profile.
    Returns:
        JSON: Confirmation message.
        HTTP 200: Success.
        HTTP 404: Profile not found.
    """
    return jsonify({"message": f"Profile {profile_id} deleted successfully."}), 200