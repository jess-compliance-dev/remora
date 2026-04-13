from app.controllers.profile_controller import profile_bp


def register_blueprints(app):
    app.register_blueprint(profile_bp, url_prefix="/profiles")