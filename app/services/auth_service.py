from app.database.user_database import UserDatabase
from app.utils.security import hash_password, verify_password, is_strong_password


class AuthService:
    """
    Service layer for authentication logic.
    """

    def __init__(self):
        self.user_db = UserDatabase()

    def register_user(self, data: dict):
        """
        Register a new user.
        """

        username = data.get("username")
        email = data.get("email")
        password = data.get("password")

        if not username or not email or not password:
            return None, "Username, email and password are required."

        # check if user already exists
        existing_user = self.user_db.get_by_email(email)
        if existing_user:
            return None, "User with this email already exists."

        # validate password strength
        is_valid, message = is_strong_password(password)
        if not is_valid:
            return None, message

        # hash password
        password_hash = hash_password(password)

        # create user
        user = self.user_db.create({
            "username": username,
            "email": email,
            "password_hash": password_hash
        })

        return user, None

    def login_user(self, data: dict):
        """
        Login a user.
        """

        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return None, "Email and password are required."

        user = self.user_db.get_by_email(email)

        if not user:
            return None, "Invalid email or password."

        # verify password
        if not verify_password(password, user.password_hash):
            return None, "Invalid email or password."

        return user, None