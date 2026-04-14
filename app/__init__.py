import os
from flask import Flask
from dotenv import load_dotenv
from flask_jwt_extended import JWTManager

from app.extensions.db import db
from app.extensions.migrate import migrate
from app.api.routes import register_blueprints
from app import models

load_dotenv()


def create_app():
    app = Flask(__name__)

    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret")

    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "jwt-dev-secret")

    db.init_app(app)
    migrate.init_app(app, db)

    JWTManager(app)

    register_blueprints(app)

    return app