import re
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from pydantic_core.core_schema import ValidationInfo


class TokenDTO(BaseModel):
    access_token: str
    token_type: str


class UserInLoginDTO(BaseModel):
    username: str
    password: str


class UserInfoDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    username: str
    email: str
    created_at: datetime


class UserInDBDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID | None = None
    username: str | None = None
    email: str | None = None
    created_at: datetime | None = None
    hashed_password: str | None = None

    def to_user_info(self) -> UserInfoDTO:
        return UserInfoDTO(**self.model_dump())


class UserInCreateDTO(BaseModel):
    username: str = Field(min_length=3, max_length=30)
    email: EmailStr
    password: str = Field(min_length=6)
    repeat_password: str

    @field_validator("username")
    def username_has_no_invalid_symbols(cls, username: str) -> str:
        match = re.search(r"^[a-zA-Z0-9_-]+$", username)
        if match is None:
            raise ValueError("Username has invalid symbols")
        return username

    @field_validator("repeat_password")
    def check_passwords_match(cls, repeat_password: str, info: ValidationInfo) -> str:
        if repeat_password != info.data.get("password", ""):
            raise ValueError("Passwords do not match")
        return repeat_password


class UserIdDTO(BaseModel):
    id: UUID
