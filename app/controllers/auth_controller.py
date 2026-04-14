from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token

from app.services.auth_service import AuthService

auth_bp = Blueprint("auth", __name__)
auth_service = AuthService()


def serialize_user(user):
    """
    Convert a User object into JSON.
    """
    return {
        "user_id": user.user_id,
        "username": user.username,
        "email": user.email,
        "created_at": user.created_at.isoformat(),
        "updated_at": user.updated_at.isoformat(),
    }


@auth_bp.route("/register", methods=["POST"])
def register():
    """
    Register a new user.
    """
    data = request.get_json()

    user, error = auth_service.register_user(data)

    if error:
        return jsonify({"error": error}), 400

    return jsonify({
        "message": "User registered successfully",
        "user": serialize_user(user)
    }), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    """
    Login user and return JWT token.
    """
    data = request.get_json()

    user, error = auth_service.login_user(data)

    if error:
        return jsonify({"error": error}), 401

    access_token = create_access_token(identity=user.user_id)

    return jsonify({
        "message": "Login successful",
        "access_token": access_token,
        "user": serialize_user(user)
    }), 200
