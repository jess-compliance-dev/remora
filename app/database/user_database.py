from app.extensions.db import db
from app.models.user import User


class UserDatabase:
    """
    Database layer for user operations.
    """

    def get_by_id(self, user_id: int):
        return User.query.get(user_id)

    def get_by_email(self, email: str):
        return User.query.filter_by(email=email).first()

    def create(self, data: dict):
        user = User(**data)
        db.session.add(user)
        db.session.commit()
        return user
