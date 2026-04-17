from flask import Blueprint, request, jsonify, url_for, redirect
from flask_jwt_extended import create_access_token

from app.services.auth_service import AuthService
from app.utils.token import generate_confirmation_token, confirm_token
from app.utils.email import send_confirmation_email
from app.extensions.db import db

auth_bp = Blueprint("auth", __name__)
auth_service = AuthService()


def serialize_user(user):
    if user is None:
        return None

    return {
        "user_id": user.user_id,
        "username": user.username,
        "email": user.email,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat() if getattr(user, "created_at", None) else None,
        "updated_at": user.updated_at.isoformat() if getattr(user, "updated_at", None) else None,
    }


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not username:
        return jsonify({"error": "username is required"}), 400

    if not email:
        return jsonify({"error": "email is required"}), 400

    if not password:
        return jsonify({"error": "password is required"}), 400

    user, error = auth_service.register_user({
        "username": username,
        "email": email,
        "password": password
    })

    if error:
        return jsonify({"error": error}), 400

    user.is_active = True
    db.session.commit()

    return jsonify({
        "message": "User created successfully.",
        "user": serialize_user(user)
    }), 201


@auth_bp.route("/confirm/<token>", methods=["GET"])
def confirm_email(token):
    """
    Confirm a user's email address using the token from the email.
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

    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "email and password are required"}), 400

    user, error = auth_service.login_user({
        "email": email,
        "password": password
    })

    if error:
        return jsonify({"error": error}), 401

    access_token = create_access_token(identity=str(user.user_id))

    return jsonify({
        "message": "Login successful",
        "access_token": access_token,
        "user": serialize_user(user),
    }), 200
