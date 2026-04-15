import os

from flask import Flask
from dotenv import load_dotenv
from flask_jwt_extended import JWTManager

from app.extensions.db import db
from app.extensions.migrate import migrate
from app.extensions.mail import mail

from app.api.routes import register_blueprints
from app.ui.routes import ui_bp

from app import models
from datetime import timedelta


load_dotenv()


def create_app():
    """
    Application factory for the Remora Flask app.
    """

    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static"
    )


    # DATABASE
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


    # SECURITY
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret")
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "jwt-dev-secret")
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=2)


    # EMAIL CONFIG
    app.config["MAIL_SERVER"] = "smtp.gmail.com"
    app.config["MAIL_PORT"] = 587
    app.config["MAIL_USE_TLS"] = True
    app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
    app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")


    # INIT EXTENSIONS
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    JWTManager(app)


    # REGISTER ROUTES
    register_blueprints(app)
    app.register_blueprint(ui_bp)

    return app
