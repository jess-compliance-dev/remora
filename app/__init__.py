import os
from pathlib import Path
from datetime import timedelta

from flask import Flask
from dotenv import load_dotenv
from flask_jwt_extended import JWTManager

from app.extensions.db import db
from app.extensions.migrate import migrate
from app.extensions.mail import mail

from app.api.routes import register_blueprints
from app.ui.routes import ui_bp

from app import models


# Load .env safely
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


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
    app.config["SQLALCHEMY_DATABASE_URI"] = require_env("DATABASE_URL")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # SECURITY
    app.config["SECRET_KEY"] = require_env("SECRET_KEY")
    app.config["JWT_SECRET_KEY"] = require_env("JWT_SECRET_KEY")
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=72)

    # EMAIL CONFIG
    app.config["MAIL_SERVER"] = "smtp.gmail.com"
    app.config["MAIL_PORT"] = 587
    app.config["MAIL_USE_TLS"] = True
    app.config["MAIL_USERNAME"] = require_env("MAIL_USERNAME")
    app.config["MAIL_PASSWORD"] = require_env("MAIL_PASSWORD")

    # INIT EXTENSIONS
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)

    jwt = JWTManager()
    jwt.init_app(app)

    # REGISTER ROUTES
    register_blueprints(app)
    app.register_blueprint(ui_bp)

    return app
