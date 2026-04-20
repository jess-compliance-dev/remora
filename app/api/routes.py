from flask import Blueprint

from app.controllers.auth_controller import auth_bp
from app.controllers.profile_controller import profile_bp
from app.controllers.story_controller import story_bp
from app.controllers.story_media_controller import story_media_bp
from app.controllers.chatbot_prompt_controller import chatbot_prompt_bp
from app.controllers.chat_session_controller import chat_session_bp
from app.controllers.chat_message_controller import chat_message_bp
from app.controllers.chat_ai_controller import chat_ai_bp
from app.controllers.memory_controller import memory_bp

def register_blueprints(app):
    api_bp = Blueprint("api", __name__)

    api_bp.register_blueprint(auth_bp, url_prefix="/auth")
    api_bp.register_blueprint(profile_bp, url_prefix="/profiles")
    api_bp.register_blueprint(story_bp, url_prefix="/stories")
    api_bp.register_blueprint(story_media_bp, url_prefix="/story-media")
    api_bp.register_blueprint(chatbot_prompt_bp, url_prefix="/prompts")
    api_bp.register_blueprint(chat_session_bp, url_prefix="/chat/sessions")
    api_bp.register_blueprint(chat_message_bp, url_prefix="/chat/messages")
    api_bp.register_blueprint(chat_ai_bp, url_prefix="/chat")
    app.register_blueprint(memory_bp, url_prefix="/memories")

    app.register_blueprint(api_bp, url_prefix="/api")