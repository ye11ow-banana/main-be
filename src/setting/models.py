from pydantic import BaseModel, ConfigDict


class CalorieSettingDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    add_day_notes: bool
    ai_creates_products: bool


class AllSettingsResponseDTO(BaseModel):
    calorie_setting: CalorieSettingDTO


class UpdateCalorieSettingDTO(BaseModel):
    add_day_notes: bool | None = None
    ai_creates_products: bool | None = None


class UpdateSettingsRequestDTO(BaseModel):
    calorie_setting: UpdateCalorieSettingDTO | None = None
