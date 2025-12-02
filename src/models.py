from typing import Generic, Literal, TypeVar

from pydantic import BaseModel

S = TypeVar("S", bound=BaseModel)


class ResponseDTO(BaseModel, Generic[S]):
    data: S | list[S]


class ErrorResponseDTO(BaseModel, Generic[S]):
    error: S


class PydanticErrorResponseDTO(BaseModel):
    field: str
    message: str


class MessageErrorResponseDTO(BaseModel):
    message: str


class PaginationDTO(BaseModel, Generic[S]):
    page_count: int
    total_count: int
    data: list[S]


class ErrorEventDTO(BaseModel):
    event: Literal["error"]
    data: dict[str, str]
