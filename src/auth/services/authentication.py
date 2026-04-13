from abc import ABC, abstractmethod
from datetime import UTC, datetime, timedelta
from typing import cast

from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from jose import JWTError, jwt
from passlib.context import CryptContext
from passlib.exc import UnknownHashError
from sqlalchemy.orm.exc import NoResultFound

from auth.exceptions import AuthenticationException
from auth.models import (
    GoogleTokenPayload,
    TokenDTO,
    UserInDBDTO,
    UserInfoDTO,
    UserInLoginDTO,
)
from config import settings
from unitofwork import IUnitOfWork


class IAuthenticationService(ABC):
    def __init__(self, uow: IUnitOfWork):
        self._uow: IUnitOfWork = uow
        self._pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

    @abstractmethod
    async def authenticate_user(self, data: UserInLoginDTO):
        raise NotImplementedError

    @abstractmethod
    async def get_current_user(self, token: str) -> UserInfoDTO:
        raise NotImplementedError

    async def _verify_password(self, plain_password: str, hashed_password: str) -> None:
        try:
            is_password_verified = self._pwd_context.verify(
                plain_password, hashed_password
            )
        except UnknownHashError:
            raise ValueError("Incorrect password")
        if not is_password_verified:
            raise ValueError("Incorrect password")

    async def _get_db_user_by_username_or_email(self, username: str) -> UserInDBDTO:
        return await self._uow.users.get_by_username_or_email(username)


class JWTAuthenticationService(IAuthenticationService):
    async def authenticate_user(self, user: UserInLoginDTO) -> TokenDTO:
        try:
            async with self._uow:
                db_user = await self._get_db_user_by_username_or_email(user.username)

            if not db_user:
                raise AuthenticationException("Incorrect username or password")

            await self._verify_password(user.password, db_user.hashed_password)

        except (NoResultFound, ValueError):
            raise AuthenticationException("Incorrect username or password")

        return await self._issue_tokens(user.username)

    async def authenticate_google_user(self, google_token: str) -> TokenDTO:
        payload = await self._verify_google_token(google_token)

        email = payload["email"]

        async with self._uow:
            user = await self._get_db_user_by_username_or_email(email)

        if not user:
            raise AuthenticationException("User not found")

        if not user.is_verified:
            raise AuthenticationException("User is not verified")

        return await self._issue_tokens(user.email)

    @staticmethod
    async def _verify_google_token(id_token_str: str) -> GoogleTokenPayload:
        try:
            request = google_requests.Request()

            payload = cast(
                GoogleTokenPayload,
                google_id_token.verify_oauth2_token(
                    id_token_str,
                    request,
                    audience=settings.google.client_id,
                ),
            )

        except ValueError:
            raise AuthenticationException("Invalid Google token")

        if payload.get("iss") not in (
            "accounts.google.com",
            "https://accounts.google.com",
        ):
            raise AuthenticationException("Invalid token issuer")

        if not payload.get("email_verified"):
            raise AuthenticationException("Google email not verified")

        return payload

    async def get_current_user(self, token: str) -> UserInfoDTO:
        try:
            async with self._uow:
                db_user = await self._get_db_user_by_jwt(token)
        except JWTError:
            raise AuthenticationException("Could not validate credentials")
        return db_user.to_user_info()

    @staticmethod
    async def create_access_token(
        data: dict, expires_delta: timedelta | None = None
    ) -> str:
        if expires_delta is None:
            expires_delta = timedelta(minutes=15)
        expire = datetime.now(UTC) + expires_delta
        data.update({"exp": expire})
        encoded_jwt = jwt.encode(
            data, settings.secret_key, algorithm=settings.jwt.algorithm
        )
        return str(encoded_jwt)

    async def refresh_access_token(self, refresh_token: str) -> TokenDTO:
        try:
            username = self._decore_jwt(refresh_token, is_refresh=True)
        except JWTError:
            raise AuthenticationException("Could not validate credentials")
        access_token_expires = timedelta(
            minutes=settings.jwt.access_token_expire_minutes
        )
        access_token = await self.create_access_token(
            data={"sub": username}, expires_delta=access_token_expires
        )
        return TokenDTO(
            access_token=access_token, refresh_token=refresh_token, token_type="bearer"
        )

    async def _issue_tokens(self, subject: str) -> TokenDTO:
        access_token_expires = timedelta(
            minutes=settings.jwt.access_token_expire_minutes
        )
        access_token = await self.create_access_token(
            data={"sub": subject},
            expires_delta=access_token_expires,
        )

        refresh_token_expires = timedelta(days=settings.jwt.refresh_token_expire_days)
        refresh_token = await self.create_access_token(
            data={"sub": subject, "token_type": "refresh"},
            expires_delta=refresh_token_expires,
        )

        return TokenDTO(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
        )

    async def _get_db_user_by_jwt(self, token: str) -> UserInDBDTO:
        username = self._decore_jwt(token, is_refresh=False)
        try:
            db_user = await self._get_db_user_by_username_or_email(username)
        except NoResultFound:
            raise JWTError
        return db_user

    @staticmethod
    def _decore_jwt(token: str, is_refresh: bool) -> str:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.jwt.algorithm]
        )
        username: str = payload.get("sub")
        token_type: str = payload.get("token_type")
        if username is None or (token_type == "refresh") is not is_refresh:
            raise JWTError
        return username
