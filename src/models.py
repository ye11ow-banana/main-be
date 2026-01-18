from datetime import date, datetime, time, timedelta
from typing import Generic, Literal, TypeVar
from uuid import UUID

from pydantic import BaseModel, model_validator

S = TypeVar("S", bound=BaseModel)


class SuccessDTO(BaseModel):
    success: bool = True


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


class DateRangeDTO(BaseModel):
    start_date: date
    end_date: date

    @model_validator(mode="after")
    def validate_date_order(self):
        if self.start_date > self.end_date:
            raise ValueError("start_date must be <= end_date")
        return self

    def format_to_exclusive_range(self) -> tuple[date, date]:
        start_dt = datetime.combine(self.start_date, time.min)
        end_dt_exclusive = datetime.combine(self.end_date + timedelta(days=1), time.min)
        return start_dt, end_dt_exclusive


class NameCodeDTO(BaseModel):
    name: str
    code: str


class SearchDTO(BaseModel):
    q: str = ""


class PaginatedSearchFilterDTO(SearchDTO):
    page: int = 1


class ObjectCreationDTO(BaseModel):
    id: UUID
