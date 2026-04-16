from flask import Blueprint

from app.controllers.auth_controller import auth_bp
from app.controllers.profile_controller import profile_bp
from app.controllers.story_controller import story_bp
from app.controllers.story_media_controller import story_media_bp
from app.controllers.chat_session_controller import chat_session_bp
from app.controllers.chat_message_controller import chat_message_bp
from app.controllers.chat_ai_controller import chat_ai_bp
from app.controllers.chatbot_prompt_controller import chatbot_prompt_bp

api_bp = Blueprint("api", __name__)

# Auth
api_bp.register_blueprint(auth_bp, url_prefix="/auth")

# Profiles
api_bp.register_blueprint(profile_bp, url_prefix="/profiles")

# Stories
api_bp.register_blueprint(story_bp, url_prefix="/stories")

# Story Media
api_bp.register_blueprint(story_media_bp, url_prefix="/story-media")

# Chat Sessions
api_bp.register_blueprint(chat_session_bp, url_prefix="/chat/sessions")

# Chat Messages
api_bp.register_blueprint(chat_message_bp, url_prefix="/chat/messages")

# AI Chat
api_bp.register_blueprint(chat_ai_bp, url_prefix="/chat")

# Prompts
api_bp.register_blueprint(chatbot_prompt_bp, url_prefix="/chat/prompts")