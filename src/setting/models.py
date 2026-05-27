from pydantic import BaseModel, ConfigDict


class CalorieSettingDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    add_day_notes: bool
    ai_creates_products: bool


class AllSettingsResponseDTO(BaseModel):
    calorie_setting: CalorieSettingDTO
