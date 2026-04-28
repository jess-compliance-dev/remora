from app.services.auth_service import AuthService


def test_auth_service_register_creates_inactive_user(monkeypatch):
    created_payload = {}

    class FakeUserDatabase:
        def get_by_email(self, email):
            return None

        def create(self, payload):
            created_payload.update(payload)

            class User:
                user_id = 1
                username = payload["username"]
                email = payload["email"]
                is_active = payload["is_active"]
                created_at = None
                updated_at = None

            return User()

    service = AuthService()
    service.user_db = FakeUserDatabase()

    user, error = service.register_user({
        "username": "testuser",
        "email": "test@example.com",
        "password": "StrongPass123!",
    })

    assert error is None
    assert user is not None
    assert created_payload["is_active"] is False


def test_auth_service_rejects_inactive_login(monkeypatch):
    class FakeUser:
        email = "test@example.com"
        password_hash = "hashed-password"
        is_active = False

    class FakeUserDatabase:
        def get_by_email(self, email):
            return FakeUser()

    service = AuthService()
    service.user_db = FakeUserDatabase()

    monkeypatch.setattr(
        "app.services.auth_service.verify_password",
        lambda password, password_hash: True,
    )

    user, error = service.login_user({
        "email": "test@example.com",
        "password": "StrongPass123!",
    })

    assert user is None
    assert error == "Please confirm your email before logging in."
