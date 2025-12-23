from abc import ABC, abstractmethod

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from app.repositories import AppRepository
from auth.repositories import UserRepository
from notification.repositories import VerificationCodeRepository


class IUnitOfWork(ABC):
    users: UserRepository
    verification_codes: VerificationCodeRepository
    apps: AppRepository

    @abstractmethod
    def __init__(self):
        raise NotImplementedError

    @abstractmethod
    async def __aenter__(self):
        raise NotImplementedError

    @abstractmethod
    async def __aexit__(self, *args):
        raise NotImplementedError

    @abstractmethod
    async def commit(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def rollback(self) -> None:
        raise NotImplementedError


class UnitOfWork(IUnitOfWork):
    def __init__(self, async_session_maker: sessionmaker[AsyncSession]):
        self.session_factory = async_session_maker

    async def __aenter__(self):
        self._session = self.session_factory()
        self.users = UserRepository(self._session)
        self.verification_codes = VerificationCodeRepository(self._session)
        self.apps = AppRepository(self._session)

    async def __aexit__(self, *args):
        await self.rollback()
        await self._session.close()

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()
