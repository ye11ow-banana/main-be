from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from models import DateRangeDTO


class TrendTypeEnum(StrEnum):
    WEIGHT = "weight"
    CALORIE = "calorie"


class TrendFilterDTO(DateRangeDTO):
    type: TrendTypeEnum

    def to_date_range(self) -> DateRangeDTO:
        return DateRangeDTO(start_date=self.start_date, end_date=self.end_date)


class TrendItem(BaseModel):
    date: date
    value: Decimal


class DayInDBDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID | None = None
    body_weight: Decimal | None = None
    body_fat: Decimal | None = None
    trend: Decimal | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    user_id: UUID | None = None
