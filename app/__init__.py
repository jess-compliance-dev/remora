import os
from pathlib import Path
from datetime import timedelta

from flask import Flask, redirect
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
        static_folder="static",
    )

    project_root = Path(__file__).resolve().parent.parent

    # DATABASE
    app.config["SQLALCHEMY_DATABASE_URI"] = require_env("DATABASE_URL")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # SECURITY
    app.config["SECRET_KEY"] = require_env("SECRET_KEY")
    app.config["JWT_SECRET_KEY"] = require_env("JWT_SECRET_KEY")
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=72)

    # UPLOADS
    # Local upload directory:
    # remora/app/static/uploads/memories/photo/...
    # remora/app/static/uploads/memories/video/...
    # remora/app/static/uploads/memories/voice/...
    #
    # Flask serves these files publicly under:
    # /static/uploads/memories/photo/...
    # /static/uploads/memories/video/...
    #
    # Example local URL:
    # http://127.0.0.1:5000/static/uploads/memories/photo/example.jpg
    #
    # Example public/ngrok URL for Creatomate:
    # https://your-ngrok-url.ngrok-free.app/static/uploads/memories/photo/example.jpg
    upload_folder_env = os.getenv("UPLOAD_FOLDER")

    if upload_folder_env:
        upload_folder_path = Path(upload_folder_env)

        if not upload_folder_path.is_absolute():
            upload_folder_path = project_root / upload_folder_path
    else:
        upload_folder_path = project_root / "app" / "static" / "uploads"

    app.config["UPLOAD_FOLDER"] = str(upload_folder_path.resolve())

    # EMAIL CONFIG
    app.config["MAIL_SERVER"] = "smtp.gmail.com"
    app.config["MAIL_PORT"] = 587
    app.config["MAIL_USE_TLS"] = True
    app.config["MAIL_USERNAME"] = require_env("MAIL_USERNAME")
    app.config["MAIL_PASSWORD"] = require_env("MAIL_PASSWORD")
    app.config["MAIL_SUPPRESS_SEND"] = os.getenv("MAIL_SUPPRESS_SEND", "false").lower() == "true"

    # INIT EXTENSIONS
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)

    jwt = JWTManager()
    jwt.init_app(app)

    # REGISTER ROUTES
    register_blueprints(app)
    app.register_blueprint(ui_bp)

    @app.route("/")
    def index():
        return redirect("/ui/login")

    return app