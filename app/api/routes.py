from flask import Blueprint

from app.controllers.auth_controller import auth_bp
from app.controllers.chat_ai_controller import chat_ai_bp
from app.controllers.chat_session_controller import chat_session_bp
from app.controllers.memory_controller import memory_bp
from app.controllers.memory_video_controller import memory_video_bp
from app.controllers.profile_controller import profile_bp
from app.controllers.story_controller import story_bp
from app.controllers.upload_controller import upload_bp


def register_blueprints(app):
    api_bp = Blueprint("api", __name__)

    api_bp.register_blueprint(auth_bp, url_prefix="/auth")
    api_bp.register_blueprint(profile_bp, url_prefix="/profiles")
    api_bp.register_blueprint(chat_session_bp, url_prefix="/chat/sessions")
    api_bp.register_blueprint(chat_ai_bp, url_prefix="/chat")
    api_bp.register_blueprint(memory_bp, url_prefix="/memories")
    api_bp.register_blueprint(story_bp, url_prefix="/stories")
    api_bp.register_blueprint(memory_video_bp, url_prefix="/memory-videos")
    app.register_blueprint(upload_bp, url_prefix="/uploads")

    app.register_blueprint(api_bp, url_prefix="/api")


