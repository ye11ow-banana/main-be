from datetime import date
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel

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
