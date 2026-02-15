from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from models import DateRangeDTO


class TrendTypeEnum(StrEnum):
    WEIGHT = "weight"
    CALORIE = "calorie"


class TrendFilterDTO(DateRangeDTO):
    type: TrendTypeEnum

    def to_date_range(self) -> DateRangeDTO:
        return DateRangeDTO(start_date=self.start_date, end_date=self.end_date)


class TrendItemDTO(BaseModel):
    date: date
    value: Decimal


class DayInDBDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID | None = None
    body_weight: Decimal | None = None
    body_fat: Decimal | None = None
    trend: Decimal | None = None
    total_proteins: Decimal = Decimal("0.0")
    total_fats: Decimal = Decimal("0.0")
    total_carbs: Decimal = Decimal("0.0")
    total_calories: Decimal = Decimal("0.0")
    additional_calories: Decimal = Decimal("0.0")
    created_at: datetime | None = None
    updated_at: datetime | None = None
    user_id: UUID | None = None


class DaysFilterSortByEnum(StrEnum):
    MOST_RECENT = "most_recent"
    OLDEST = "oldest"
    MOST_CALORIES = "most_calories"
    LOWEST_WEIGHT = "lowest_weight"


class DaysFilterDTO(DateRangeDTO):
    sort_by: DaysFilterSortByEnum
    page: int = 1

    def to_date_range(self) -> DateRangeDTO:
        return DateRangeDTO(start_date=self.start_date, end_date=self.end_date)


class DayProductDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    weight: int
    proteins: Decimal
    fats: Decimal
    carbs: Decimal
    calories: Decimal

    @model_validator(mode="before")
    @classmethod
    def _from_day_product(cls, obj):
        if hasattr(obj, "product") and hasattr(obj, "weight"):
            p = getattr(obj, "product", None)
            if p is None:
                raise ValueError("DayProduct.product is None (not loaded or missing)")
            return {
                "id": p.id,
                "name": p.name,
                "weight": obj.weight,
                "proteins": p.proteins * obj.weight / 100,
                "fats": p.fats * obj.weight / 100,
                "carbs": p.carbs * obj.weight / 100,
                "calories": p.calories * obj.weight / 100,
            }
        return obj


class DayMeasurementUpdateDTO(BaseModel):
    body_weight: Decimal | None = None
    body_fat: Decimal | None = None

    @field_validator("body_weight", "body_fat")
    @classmethod
    def bigger_than_zero(cls, v: Decimal | None):
        if v is None:
            return v
        if v <= 0:
            raise ValueError("must be bigger than zero")
        return v


class DayFullInfoDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    body_weight: Decimal | None = None
    body_fat: Decimal | None = None
    trend: Decimal | None = None
    created_at: datetime
    total_proteins: Decimal = Decimal("0.0")
    total_fats: Decimal = Decimal("0.0")
    total_carbs: Decimal = Decimal("0.0")
    total_calories: Decimal = Decimal("0.0")
    additional_calories: Decimal = Decimal("0.0")
    products: list[DayProductDTO] = Field(validation_alias="day_products")


class OpenAIProductDTO(BaseModel):
    user: str
    raw_name: str
    weight: str  # can be 123 or 123+49

    @field_validator("raw_name", mode="before")
    @classmethod
    def capitalize_raw_name(cls, v):
        if isinstance(v, str):
            return v.capitalize()
        return v


class OpenAIProductListResponseDTO(BaseModel):
    items: list[OpenAIProductDTO]
    warnings: list[str]
    unparsed: list[str]


class OpenAIProductMatchDTO(BaseModel):
    user: str
    product_id: UUID
    name: str
    weight: str
    matched_score: Decimal


class OpenAIPer100gDTO(BaseModel):
    proteins: Decimal
    fats: Decimal
    carbs: Decimal
    calories: Decimal


class OpenAIProductCreationDTO(BaseModel):
    raw_name: str
    name_ua: str
    per_100g: OpenAIPer100gDTO
    confidence: Decimal
    assumptions: str

    @field_validator("name_ua", mode="before")
    @classmethod
    def capitalize_name_ua(cls, v):
        if isinstance(v, str):
            return v.capitalize()
        return v


class OpenAIProductCreationListResponseDTO(BaseModel):
    products: list[OpenAIProductCreationDTO]


class IngestResponseDTO(BaseModel):
    products: list[OpenAIProductMatchDTO]
    warnings: list[str]
    unparsed: list[str]


class ProductCreationDTO(BaseModel):
    name: str
    proteins: Decimal
    fats: Decimal
    carbs: Decimal
    calories: Decimal


class ProductDTO(ProductCreationDTO):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime


class UserDayProductCreationDTO(BaseModel):
    user_id: UUID
    product_id: UUID
    weight: int

    @field_validator("weight", mode="before")
    @classmethod
    def convert_weight_to_int(cls, v) -> int:
        if isinstance(v, str):
            numbers = v.split("+")
            try:
                return sum(list(map(int, numbers)))
            except ValueError:
                raise ValueError("Weight must be a number or a sum of numbers")
        raise ValueError("Weight must be a string")


class DayCreationDTO(BaseModel):
    date: date
    user_additional_calories: dict[UUID, Decimal]  # user_id -> additional_calories
    products: list[UserDayProductCreationDTO]


class DayProductCreationDTO(BaseModel):
    day_id: UUID | None
    product_id: UUID
    weight: int
