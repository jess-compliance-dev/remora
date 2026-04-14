from app.controllers.profile_controller import profile_bp
from app.controllers.story_controller import story_bp
from app.controllers.story_media_controller import story_media_bp
from app.controllers.chatbot_prompt_controller import chatbot_prompt_bp


def register_blueprints(app):
    app.register_blueprint(profile_bp, url_prefix="/profiles")
    app.register_blueprint(story_bp, url_prefix="/stories")
    app.register_blueprint(story_media_bp, url_prefix="/story-media")
    app.register_blueprint(chatbot_prompt_bp, url_prefix="/prompts")