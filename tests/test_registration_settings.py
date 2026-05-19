import asyncio
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy.dialects import postgresql

from auth.models import UserInCreateDTO, UserInfoDTO
from auth.services.registration import RegistrationService
from setting.repositories import SettingRepository


class FakeUsers:
    def __init__(self, user: UserInfoDTO, events: list[str]):
        self._user = user
        self._events = events

    async def add(self, **insert_data) -> UserInfoDTO:
        self._events.append("users.add")
        return self._user


class FakeSettings:
    def __init__(self, events: list[str], error: Exception | None = None):
        self._events = events
        self._error = error
        self.created_for_user_id: UUID | None = None

    async def create_for_active_apps(self, user_id: UUID) -> None:
        self._events.append("settings.create_for_active_apps")
        self.created_for_user_id = user_id
        if self._error is not None:
            raise self._error


class FakeUnitOfWork:
    def __init__(self, user: UserInfoDTO, settings_error: Exception | None = None):
        self.events: list[str] = []
        self.users = FakeUsers(user, self.events)
        self.settings = FakeSettings(self.events, settings_error)
        self.committed = False

    async def __aenter__(self):
        self.events.append("enter")

    async def __aexit__(self, *args):
        self.events.append("exit")

    async def commit(self) -> None:
        self.events.append("commit")
        self.committed = True

    async def rollback(self) -> None:
        self.events.append("rollback")


class CapturingSession:
    def __init__(self):
        self.statement = None

    async def execute(self, statement):
        self.statement = statement


def make_user() -> UserInfoDTO:
    return UserInfoDTO(
        id=uuid4(),
        username="settings_user",
        email="settings-user@example.com",
        is_verified=False,
        avatar_url=None,
        created_at=datetime.now(timezone.utc),
    )


def make_user_input() -> UserInCreateDTO:
    return UserInCreateDTO(
        username="settings_user",
        email="settings-user@example.com",
        password="password",
        repeat_password="password",
    )


def test_register_user_creates_settings_for_active_apps(monkeypatch) -> None:
    user = make_user()
    uow = FakeUnitOfWork(user)
    service = RegistrationService(uow)

    async def fake_hash_password(plain_password: str) -> str:
        return f"hashed:{plain_password}"

    monkeypatch.setattr(service, "_hash_password", fake_hash_password)

    new_user = asyncio.run(service.register_user(make_user_input()))

    assert new_user == user
    assert uow.settings.created_for_user_id == user.id
    assert uow.events == [
        "enter",
        "users.add",
        "settings.create_for_active_apps",
        "commit",
        "exit",
    ]


def test_register_user_does_not_commit_when_settings_creation_fails(
    monkeypatch,
) -> None:
    user = make_user()
    uow = FakeUnitOfWork(user, settings_error=RuntimeError("settings failed"))
    service = RegistrationService(uow)

    async def fake_hash_password(plain_password: str) -> str:
        return f"hashed:{plain_password}"

    monkeypatch.setattr(service, "_hash_password", fake_hash_password)

    try:
        asyncio.run(service.register_user(make_user_input()))
    except RuntimeError as exc:
        assert str(exc) == "settings failed"
    else:
        raise AssertionError("Expected settings creation failure")

    assert uow.committed is False
    assert uow.events == [
        "enter",
        "users.add",
        "settings.create_for_active_apps",
        "exit",
    ]


def test_setting_repository_creates_defaults_only_for_active_apps() -> None:
    session = CapturingSession()
    repository = SettingRepository(session)

    asyncio.run(repository.create_for_active_apps(uuid4()))

    compiled = str(
        session.statement.compile(
            dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
        )
    )

    assert "INSERT INTO settings (app_id, user_id)" in compiled
    assert "SELECT apps.id" in compiled
    assert "FROM apps" in compiled
    assert "WHERE apps.is_active IS true" in compiled
