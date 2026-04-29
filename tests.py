from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token

from app.services.auth_service import AuthService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_test_app():
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["JWT_SECRET_KEY"] = "test-jwt-secret"

    JWTManager(app)

    return app


def make_auth_header(app, user_id):
    with app.app_context():
        token = create_access_token(identity=str(user_id))

    return {"Authorization": f"Bearer {token}"}


def make_story(
    story_id=1,
    profile_id=1,
    created_by=1,
    title="Test Story",
    story_text="Test story text",
):
    now = datetime.now(UTC)

    return SimpleNamespace(
        story_id=story_id,
        profile_id=profile_id,
        created_by=created_by,
        source_session_id=None,
        title=title,
        prompt_question="What happened?",
        story_text=story_text,
        source_type="manual",
        audio_url=None,
        summary=None,
        summary_json=None,
        theme=None,
        emotion_tag=None,
        life_period=None,
        location=None,
        happened_at=None,
        is_featured=False,
        created_at=now,
        updated_at=now,
    )


def make_session(
    session_id=1,
    profile_id=1,
    user_id=1,
    category="memory_chat",
    status="active",
):
    now = datetime.now(UTC)

    return SimpleNamespace(
        session_id=session_id,
        profile_id=profile_id,
        user_id=user_id,
        category=category,
        status=status,
        started_at=now,
        ended_at=None,
        created_at=now,
        updated_at=now,
    )


def make_profile(profile_id=1, owner_id=1):
    return SimpleNamespace(
        profile_id=profile_id,
        owner_id=owner_id,
    )


# ---------------------------------------------------------------------------
# AuthService tests
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Story controller tests
# ---------------------------------------------------------------------------

@pytest.fixture
def story_app():
    from app.controllers.story_controller import story_bp

    app = make_test_app()
    app.register_blueprint(story_bp, url_prefix="/stories")

    return app


def test_get_stories_only_returns_current_users_stories(story_app, monkeypatch):
    from app.controllers import story_controller

    class FakeStoryService:
        def get_stories(self):
            return [
                make_story(story_id=1, created_by=1),
                make_story(story_id=2, created_by=2),
                make_story(story_id=3, created_by=1),
            ]

    monkeypatch.setattr(
        story_controller,
        "story_service",
        FakeStoryService(),
    )

    client = story_app.test_client()
    response = client.get(
        "/stories",
        headers=make_auth_header(story_app, user_id=1),
    )

    assert response.status_code == 200

    data = response.get_json()
    assert len(data) == 2
    assert {story["story_id"] for story in data} == {1, 3}
    assert all(str(story["created_by"]) == "1" for story in data)


def test_get_story_returns_404_for_other_users_story(story_app, monkeypatch):
    from app.controllers import story_controller

    class FakeStoryService:
        def get_story_by_id(self, story_id):
            return make_story(story_id=story_id, created_by=2)

    monkeypatch.setattr(
        story_controller,
        "story_service",
        FakeStoryService(),
    )

    client = story_app.test_client()
    response = client.get(
        "/stories/1",
        headers=make_auth_header(story_app, user_id=1),
    )

    assert response.status_code == 404
    assert response.get_json() == {"error": "Story not found"}


def test_get_story_returns_own_story(story_app, monkeypatch):
    from app.controllers import story_controller

    class FakeStoryService:
        def get_story_by_id(self, story_id):
            return make_story(story_id=story_id, created_by=1)

    monkeypatch.setattr(
        story_controller,
        "story_service",
        FakeStoryService(),
    )

    client = story_app.test_client()
    response = client.get(
        "/stories/1",
        headers=make_auth_header(story_app, user_id=1),
    )

    assert response.status_code == 200

    data = response.get_json()
    assert data["story_id"] == 1
    assert data["created_by"] == 1


def test_get_stories_by_profile_filters_to_current_user(story_app, monkeypatch):
    from app.controllers import story_controller

    class FakeProfileService:
        def get_profile_by_id(self, profile_id):
            return make_profile(profile_id=profile_id, owner_id=1)

    class FakeStoryService:
        def get_stories_by_profile_id(self, profile_id):
            return [
                make_story(story_id=1, profile_id=profile_id, created_by=1),
                make_story(story_id=2, profile_id=profile_id, created_by=2),
            ]

    monkeypatch.setattr(
        story_controller,
        "profile_service",
        FakeProfileService(),
    )
    monkeypatch.setattr(
        story_controller,
        "story_service",
        FakeStoryService(),
    )

    client = story_app.test_client()
    response = client.get(
        "/stories/profile/10",
        headers=make_auth_header(story_app, user_id=1),
    )

    assert response.status_code == 200

    data = response.get_json()
    assert len(data) == 1
    assert data[0]["story_id"] == 1
    assert data[0]["created_by"] == 1


def test_get_stories_by_profile_rejects_other_users_profile(story_app, monkeypatch):
    from app.controllers import story_controller

    get_stories_called = False

    class FakeProfileService:
        def get_profile_by_id(self, profile_id):
            return make_profile(profile_id=profile_id, owner_id=2)

    class FakeStoryService:
        def get_stories_by_profile_id(self, profile_id):
            nonlocal get_stories_called
            get_stories_called = True
            return []

    monkeypatch.setattr(
        story_controller,
        "profile_service",
        FakeProfileService(),
    )
    monkeypatch.setattr(
        story_controller,
        "story_service",
        FakeStoryService(),
    )

    client = story_app.test_client()
    response = client.get(
        "/stories/profile/10",
        headers=make_auth_header(story_app, user_id=1),
    )

    assert response.status_code == 404
    assert response.get_json() == {"error": "Profile not found"}
    assert get_stories_called is False


def test_create_story_sets_created_by_to_current_user(story_app, monkeypatch):
    from app.controllers import story_controller

    captured_payload = {}

    class FakeProfileService:
        def get_profile_by_id(self, profile_id):
            return make_profile(profile_id=profile_id, owner_id=1)

    class FakeStoryService:
        def create_story(self, data):
            captured_payload.update(data)

            return make_story(
                story_id=1,
                profile_id=data["profile_id"],
                created_by=data["created_by"],
                title=data.get("title", "Created Story"),
            )

    monkeypatch.setattr(
        story_controller,
        "profile_service",
        FakeProfileService(),
    )
    monkeypatch.setattr(
        story_controller,
        "story_service",
        FakeStoryService(),
    )

    client = story_app.test_client()
    response = client.post(
        "/stories",
        json={
            "profile_id": 10,
            "created_by": 999,
            "title": "Created Story",
            "story_text": "Hello",
        },
        headers=make_auth_header(story_app, user_id=1),
    )

    assert response.status_code == 201
    assert captured_payload["profile_id"] == 10
    assert captured_payload["created_by"] == 1

    data = response.get_json()
    assert data["profile_id"] == 10
    assert data["created_by"] == 1


def test_create_story_rejects_other_users_profile(story_app, monkeypatch):
    from app.controllers import story_controller

    create_called = False

    class FakeProfileService:
        def get_profile_by_id(self, profile_id):
            return make_profile(profile_id=profile_id, owner_id=2)

    class FakeStoryService:
        def create_story(self, data):
            nonlocal create_called
            create_called = True

            return make_story(
                story_id=1,
                profile_id=data["profile_id"],
                created_by=data["created_by"],
            )

    monkeypatch.setattr(
        story_controller,
        "profile_service",
        FakeProfileService(),
    )
    monkeypatch.setattr(
        story_controller,
        "story_service",
        FakeStoryService(),
    )

    client = story_app.test_client()
    response = client.post(
        "/stories",
        json={
            "profile_id": 10,
            "title": "Should not create",
            "story_text": "Hello",
        },
        headers=make_auth_header(story_app, user_id=1),
    )

    assert response.status_code == 404
    assert response.get_json() == {"error": "Profile not found"}
    assert create_called is False


def test_create_story_requires_profile_id(story_app):
    client = story_app.test_client()

    response = client.post(
        "/stories",
        json={
            "title": "Missing profile",
            "story_text": "Hello",
        },
        headers=make_auth_header(story_app, user_id=1),
    )

    assert response.status_code == 400
    assert response.get_json() == {"error": "profile_id is required"}


def test_update_story_returns_404_for_other_users_story(story_app, monkeypatch):
    from app.controllers import story_controller

    update_called = False

    class FakeStoryService:
        def get_story_by_id(self, story_id):
            return make_story(story_id=story_id, created_by=2)

        def update_story(self, story_id, data):
            nonlocal update_called
            update_called = True
            return make_story(story_id=story_id, created_by=2)

    monkeypatch.setattr(
        story_controller,
        "story_service",
        FakeStoryService(),
    )

    client = story_app.test_client()
    response = client.put(
        "/stories/1",
        json={"title": "Should not update"},
        headers=make_auth_header(story_app, user_id=1),
    )

    assert response.status_code == 404
    assert response.get_json() == {"error": "Story not found"}
    assert update_called is False


def test_update_story_removes_protected_fields(story_app, monkeypatch):
    from app.controllers import story_controller

    captured_payload = {}

    class FakeStoryService:
        def get_story_by_id(self, story_id):
            return make_story(story_id=story_id, profile_id=10, created_by=1)

        def update_story(self, story_id, data):
            captured_payload.update(data)

            return make_story(
                story_id=story_id,
                profile_id=10,
                created_by=1,
                title=data.get("title", "Updated"),
            )

    monkeypatch.setattr(
        story_controller,
        "story_service",
        FakeStoryService(),
    )

    client = story_app.test_client()
    response = client.put(
        "/stories/1",
        json={
            "story_id": 999,
            "profile_id": 999,
            "created_by": 999,
            "created_at": "fake",
            "updated_at": "fake",
            "title": "Updated title",
        },
        headers=make_auth_header(story_app, user_id=1),
    )

    assert response.status_code == 200
    assert captured_payload == {"title": "Updated title"}


def test_delete_story_returns_404_for_other_users_story(story_app, monkeypatch):
    from app.controllers import story_controller

    delete_called = False

    class FakeStoryService:
        def get_story_by_id(self, story_id):
            return make_story(story_id=story_id, created_by=2)

        def delete_story(self, story_id):
            nonlocal delete_called
            delete_called = True
            return True

    monkeypatch.setattr(
        story_controller,
        "story_service",
        FakeStoryService(),
    )

    client = story_app.test_client()
    response = client.delete(
        "/stories/1",
        headers=make_auth_header(story_app, user_id=1),
    )

    assert response.status_code == 404
    assert response.get_json() == {"error": "Story not found"}
    assert delete_called is False


def test_delete_story_deletes_own_story(story_app, monkeypatch):
    from app.controllers import story_controller

    delete_called = False

    class FakeStoryService:
        def get_story_by_id(self, story_id):
            return make_story(story_id=story_id, created_by=1)

        def delete_story(self, story_id):
            nonlocal delete_called
            delete_called = True
            return True

    monkeypatch.setattr(
        story_controller,
        "story_service",
        FakeStoryService(),
    )

    client = story_app.test_client()
    response = client.delete(
        "/stories/1",
        headers=make_auth_header(story_app, user_id=1),
    )

    assert response.status_code == 200
    assert response.get_json() == {"message": "Story deleted successfully"}
    assert delete_called is True


# ---------------------------------------------------------------------------
# Chat session controller tests
# ---------------------------------------------------------------------------

@pytest.fixture
def chat_session_app():
    from app.controllers.chat_session_controller import chat_session_bp

    app = make_test_app()
    app.register_blueprint(chat_session_bp, url_prefix="/chat-sessions")

    return app


def test_get_sessions_only_returns_current_users_sessions(chat_session_app, monkeypatch):
    from app.controllers import chat_session_controller

    class FakeChatSessionService:
        def get_sessions(self):
            return [
                make_session(session_id=1, user_id=1),
                make_session(session_id=2, user_id=2),
                make_session(session_id=3, user_id=1),
            ]

    monkeypatch.setattr(
        chat_session_controller,
        "chat_session_service",
        FakeChatSessionService(),
    )

    client = chat_session_app.test_client()
    response = client.get(
        "/chat-sessions",
        headers=make_auth_header(chat_session_app, user_id=1),
    )

    assert response.status_code == 200

    data = response.get_json()
    assert len(data) == 2
    assert {session["session_id"] for session in data} == {1, 3}
    assert all(str(session["user_id"]) == "1" for session in data)


def test_get_session_returns_404_for_other_users_session(chat_session_app, monkeypatch):
    from app.controllers import chat_session_controller

    class FakeChatSessionService:
        def get_session_by_id(self, session_id):
            return make_session(session_id=session_id, user_id=2)

    monkeypatch.setattr(
        chat_session_controller,
        "chat_session_service",
        FakeChatSessionService(),
    )

    client = chat_session_app.test_client()
    response = client.get(
        "/chat-sessions/1",
        headers=make_auth_header(chat_session_app, user_id=1),
    )

    assert response.status_code == 404
    assert response.get_json() == {"error": "Session not found"}


def test_create_session_rejects_other_users_profile(chat_session_app, monkeypatch):
    from app.controllers import chat_session_controller

    create_called = False

    class FakeProfileService:
        def get_profile_by_id(self, profile_id):
            return make_profile(profile_id=profile_id, owner_id=2)

    class FakeChatSessionService:
        def create_session(self, payload):
            nonlocal create_called
            create_called = True
            return make_session(
                session_id=1,
                profile_id=payload["profile_id"],
                user_id=payload["user_id"],
            )

    monkeypatch.setattr(
        chat_session_controller,
        "profile_service",
        FakeProfileService(),
    )
    monkeypatch.setattr(
        chat_session_controller,
        "chat_session_service",
        FakeChatSessionService(),
    )

    client = chat_session_app.test_client()
    response = client.post(
        "/chat-sessions",
        json={"profile_id": 20, "category": "memory_chat"},
        headers=make_auth_header(chat_session_app, user_id=1),
    )

    assert response.status_code == 404
    assert response.get_json() == {"error": "Profile not found"}
    assert create_called is False


def test_create_session_accepts_own_profile(chat_session_app, monkeypatch):
    from app.controllers import chat_session_controller

    captured_payload = {}

    class FakeProfileService:
        def get_profile_by_id(self, profile_id):
            return make_profile(profile_id=profile_id, owner_id=1)

    class FakeChatSessionService:
        def create_session(self, payload):
            captured_payload.update(payload)

            return make_session(
                session_id=1,
                profile_id=payload["profile_id"],
                user_id=payload["user_id"],
                category=payload["category"],
                status=payload["status"],
            )

    monkeypatch.setattr(
        chat_session_controller,
        "profile_service",
        FakeProfileService(),
    )
    monkeypatch.setattr(
        chat_session_controller,
        "chat_session_service",
        FakeChatSessionService(),
    )

    client = chat_session_app.test_client()
    response = client.post(
        "/chat-sessions",
        json={"profile_id": 10, "category": "memory_chat"},
        headers=make_auth_header(chat_session_app, user_id=1),
    )

    assert response.status_code == 201

    data = response.get_json()
    assert data["profile_id"] == 10
    assert data["user_id"] == 1
    assert data["status"] == "active"

    assert captured_payload == {
        "profile_id": 10,
        "category": "memory_chat",
        "status": "active",
        "user_id": 1,
    }


def test_get_sessions_by_profile_rejects_other_users_profile(chat_session_app, monkeypatch):
    from app.controllers import chat_session_controller

    get_sessions_called = False

    class FakeProfileService:
        def get_profile_by_id(self, profile_id):
            return make_profile(profile_id=profile_id, owner_id=2)

    class FakeChatSessionService:
        def get_sessions_by_profile_id(self, profile_id):
            nonlocal get_sessions_called
            get_sessions_called = True
            return []

    monkeypatch.setattr(
        chat_session_controller,
        "profile_service",
        FakeProfileService(),
    )
    monkeypatch.setattr(
        chat_session_controller,
        "chat_session_service",
        FakeChatSessionService(),
    )

    client = chat_session_app.test_client()
    response = client.get(
        "/chat-sessions/profile/20",
        headers=make_auth_header(chat_session_app, user_id=1),
    )

    assert response.status_code == 404
    assert response.get_json() == {"error": "Profile not found"}
    assert get_sessions_called is False


def test_get_sessions_by_profile_returns_own_profile_sessions(chat_session_app, monkeypatch):
    from app.controllers import chat_session_controller

    class FakeProfileService:
        def get_profile_by_id(self, profile_id):
            return make_profile(profile_id=profile_id, owner_id=1)

    class FakeChatSessionService:
        def get_sessions_by_profile_id(self, profile_id):
            return [
                make_session(session_id=1, profile_id=profile_id, user_id=1),
                make_session(session_id=2, profile_id=profile_id, user_id=2),
            ]

    monkeypatch.setattr(
        chat_session_controller,
        "profile_service",
        FakeProfileService(),
    )
    monkeypatch.setattr(
        chat_session_controller,
        "chat_session_service",
        FakeChatSessionService(),
    )

    client = chat_session_app.test_client()
    response = client.get(
        "/chat-sessions/profile/10",
        headers=make_auth_header(chat_session_app, user_id=1),
    )

    assert response.status_code == 200

    data = response.get_json()
    assert len(data) == 1
    assert data[0]["session_id"] == 1
    assert data[0]["user_id"] == 1


def test_update_session_rejects_move_to_other_users_profile(chat_session_app, monkeypatch):
    from app.controllers import chat_session_controller

    update_called = False

    class FakeProfileService:
        def get_profile_by_id(self, profile_id):
            return make_profile(profile_id=profile_id, owner_id=2)

    class FakeChatSessionService:
        def get_session_by_id(self, session_id):
            return make_session(session_id=session_id, profile_id=10, user_id=1)

        def update_session(self, session_id, data):
            nonlocal update_called
            update_called = True
            return make_session(
                session_id=session_id,
                profile_id=data.get("profile_id", 10),
                user_id=1,
            )

    monkeypatch.setattr(
        chat_session_controller,
        "profile_service",
        FakeProfileService(),
    )
    monkeypatch.setattr(
        chat_session_controller,
        "chat_session_service",
        FakeChatSessionService(),
    )

    client = chat_session_app.test_client()
    response = client.put(
        "/chat-sessions/1",
        json={"profile_id": 20},
        headers=make_auth_header(chat_session_app, user_id=1),
    )

    assert response.status_code == 404
    assert response.get_json() == {"error": "Profile not found"}
    assert update_called is False


def test_update_session_removes_protected_fields(chat_session_app, monkeypatch):
    from app.controllers import chat_session_controller

    captured_payload = {}

    class FakeProfileService:
        def get_profile_by_id(self, profile_id):
            return make_profile(profile_id=profile_id, owner_id=1)

    class FakeChatSessionService:
        def get_session_by_id(self, session_id):
            return make_session(session_id=session_id, profile_id=10, user_id=1)

        def update_session(self, session_id, data):
            captured_payload.update(data)

            return make_session(
                session_id=session_id,
                profile_id=data.get("profile_id", 10),
                user_id=1,
                category=data.get("category", "memory_chat"),
                status=data.get("status", "active"),
            )

    monkeypatch.setattr(
        chat_session_controller,
        "profile_service",
        FakeProfileService(),
    )
    monkeypatch.setattr(
        chat_session_controller,
        "chat_session_service",
        FakeChatSessionService(),
    )

    client = chat_session_app.test_client()
    response = client.put(
        "/chat-sessions/1",
        json={
            "session_id": 999,
            "user_id": 999,
            "created_at": "fake",
            "updated_at": "fake",
            "started_at": "fake",
            "ended_at": "fake",
            "category": "interview",
            "status": "ended",
        },
        headers=make_auth_header(chat_session_app, user_id=1),
    )

    assert response.status_code == 200
    assert captured_payload == {
        "category": "interview",
        "status": "ended",
    }


def test_update_session_rejects_invalid_status(chat_session_app, monkeypatch):
    from app.controllers import chat_session_controller

    class FakeProfileService:
        def get_profile_by_id(self, profile_id):
            return make_profile(profile_id=profile_id, owner_id=1)

    class FakeChatSessionService:
        def get_session_by_id(self, session_id):
            return make_session(session_id=session_id, profile_id=10, user_id=1)

    monkeypatch.setattr(
        chat_session_controller,
        "profile_service",
        FakeProfileService(),
    )
    monkeypatch.setattr(
        chat_session_controller,
        "chat_session_service",
        FakeChatSessionService(),
    )

    client = chat_session_app.test_client()
    response = client.put(
        "/chat-sessions/1",
        json={"status": "deleted"},
        headers=make_auth_header(chat_session_app, user_id=1),
    )

    assert response.status_code == 400
    assert response.get_json() == {
        "error": "status must be 'active' or 'ended'"
    }


def test_delete_session_returns_404_for_other_users_session(chat_session_app, monkeypatch):
    from app.controllers import chat_session_controller

    delete_called = False

    class FakeChatSessionService:
        def get_session_by_id(self, session_id):
            return make_session(session_id=session_id, user_id=2)

        def delete_session(self, session_id):
            nonlocal delete_called
            delete_called = True
            return True

    monkeypatch.setattr(
        chat_session_controller,
        "chat_session_service",
        FakeChatSessionService(),
    )

    client = chat_session_app.test_client()
    response = client.delete(
        "/chat-sessions/1",
        headers=make_auth_header(chat_session_app, user_id=1),
    )

    assert response.status_code == 404
    assert response.get_json() == {"error": "Session not found"}
    assert delete_called is False


def test_delete_session_deletes_own_session(chat_session_app, monkeypatch):
    from app.controllers import chat_session_controller

    delete_called = False

    class FakeChatSessionService:
        def get_session_by_id(self, session_id):
            return make_session(session_id=session_id, user_id=1)

        def delete_session(self, session_id):
            nonlocal delete_called
            delete_called = True
            return True

    monkeypatch.setattr(
        chat_session_controller,
        "chat_session_service",
        FakeChatSessionService(),
    )

    client = chat_session_app.test_client()
    response = client.delete(
        "/chat-sessions/1",
        headers=make_auth_header(chat_session_app, user_id=1),
    )

    assert response.status_code == 200
    assert response.get_json() == {"message": "Session deleted successfully"}
    assert delete_called is True


def test_generate_story_rejects_other_users_session(chat_session_app, monkeypatch):
    from app.controllers import chat_session_controller

    generate_called = False

    class FakeChatSessionService:
        def get_session_by_id(self, session_id):
            return make_session(session_id=session_id, profile_id=10, user_id=2)

        def generate_story_from_session(self, session_id):
            nonlocal generate_called
            generate_called = True
            return SimpleNamespace(story_id=1)

    monkeypatch.setattr(
        chat_session_controller,
        "chat_session_service",
        FakeChatSessionService(),
    )

    client = chat_session_app.test_client()
    response = client.post(
        "/chat-sessions/1/generate-story",
        headers=make_auth_header(chat_session_app, user_id=1),
    )

    assert response.status_code == 404
    assert response.get_json() == {"error": "Session not found"}
    assert generate_called is False


def test_generate_story_rejects_session_with_foreign_profile(chat_session_app, monkeypatch):
    from app.controllers import chat_session_controller

    generate_called = False

    class FakeProfileService:
        def get_profile_by_id(self, profile_id):
            return make_profile(profile_id=profile_id, owner_id=2)

    class FakeChatSessionService:
        def get_session_by_id(self, session_id):
            return make_session(session_id=session_id, profile_id=10, user_id=1)

        def generate_story_from_session(self, session_id):
            nonlocal generate_called
            generate_called = True
            return SimpleNamespace(story_id=1)

    monkeypatch.setattr(
        chat_session_controller,
        "profile_service",
        FakeProfileService(),
    )
    monkeypatch.setattr(
        chat_session_controller,
        "chat_session_service",
        FakeChatSessionService(),
    )

    client = chat_session_app.test_client()
    response = client.post(
        "/chat-sessions/1/generate-story",
        headers=make_auth_header(chat_session_app, user_id=1),
    )

    assert response.status_code == 404
    assert response.get_json() == {"error": "Session not found"}
    assert generate_called is False


def test_generate_story_from_own_session(chat_session_app, monkeypatch):
    from app.controllers import chat_session_controller

    class FakeProfileService:
        def get_profile_by_id(self, profile_id):
            return make_profile(profile_id=profile_id, owner_id=1)

    class FakeChatSessionService:
        def get_session_by_id(self, session_id):
            return make_session(session_id=session_id, profile_id=10, user_id=1)

        def generate_story_from_session(self, session_id):
            return SimpleNamespace(story_id=123)

    monkeypatch.setattr(
        chat_session_controller,
        "profile_service",
        FakeProfileService(),
    )
    monkeypatch.setattr(
        chat_session_controller,
        "chat_session_service",
        FakeChatSessionService(),
    )

    client = chat_session_app.test_client()
    response = client.post(
        "/chat-sessions/1/generate-story",
        headers=make_auth_header(chat_session_app, user_id=1),
    )

    assert response.status_code == 201
    assert response.get_json() == {
        "message": "Story generated successfully",
        "story_id": 123,
    }