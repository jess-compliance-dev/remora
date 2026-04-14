from app.controllers.profile_controller import profile_bp
from app.controllers.story_controller import story_bp


def register_blueprints(app):
    app.register_blueprint(profile_bp, url_prefix="/profiles")
    app.register_blueprint(story_bp, url_prefix="/stories")