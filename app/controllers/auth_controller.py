from flask import Blueprint, request, jsonify, url_for, redirect
from flask_jwt_extended import create_access_token

from app.services.auth_service import AuthService
from app.utils.token import generate_confirmation_token, confirm_token
from app.utils.email import send_confirmation_email
from app.extensions.db import db

auth_bp = Blueprint("auth", __name__)
auth_service = AuthService()


def serialize_user(user):
    """
    Convert a User object into a JSON-serializable dictionary.
    """
    if user is None:
        return None

    return {
        "user_id": user.user_id,
        "username": user.username,
        "email": user.email,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "updated_at": user.updated_at.isoformat() if user.updated_at else None,
    }


@auth_bp.route("/register", methods=["POST"])
def register():
    """
    Register a new user and send an email confirmation link.
    """
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    user, error = auth_service.register_user(data)

    if error:
        return jsonify({"error": error}), 400

    token = generate_confirmation_token(user.email)
    confirm_url = url_for("auth.confirm_email", token=token, _external=True)
    send_confirmation_email(user.email, confirm_url)

    return jsonify({
        "message": "User created. Please check your email to confirm your account."
    }), 201


@auth_bp.route("/confirm/<token>", methods=["GET"])
def confirm_email(token):
    """
    Confirm a user's email address using the confirmation token.
    """
    email = confirm_token(token)

    if not email:
        return jsonify({"error": "Invalid or expired token"}), 400

    user = auth_service.get_user_by_email(email)

    if not user:
        return jsonify({"error": "User not found"}), 404

    if not user.is_active:
        user.is_active = True
        db.session.commit()

    return redirect("/ui/email-confirmed")


@auth_bp.route("/login", methods=["POST"])
def login():
    """
    Log in a user and return a JWT access token.
    """
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    user, error = auth_service.login_user(data)

    if error:
        return jsonify({"error": error}), 401

    access_token = create_access_token(identity=str(user.user_id))

    return jsonify({
        "message": "Login successful",
        "access_token": access_token,
        "user": serialize_user(user),
    }), 200
