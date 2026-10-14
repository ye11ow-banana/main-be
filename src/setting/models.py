from pydantic import BaseModel, ConfigDict


class CalorieSettingDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    add_day_notes: bool
    ai_creates_products: bool
    goal_calories_per_day: int | None = None
    goal_proteins_per_day: int | None = None
    goal_fats_per_day: int | None = None
    goal_carbs_per_day: int | None = None


class AllSettingsResponseDTO(BaseModel):
    calorie_setting: CalorieSettingDTO


class UpdateCalorieSettingDTO(BaseModel):
    add_day_notes: bool | None = None
    ai_creates_products: bool | None = None
    goal_calories_per_day: int | None = None
    goal_proteins_per_day: int | None = None
    goal_fats_per_day: int | None = None
    goal_carbs_per_day: int | None = None


class UpdateSettingsRequestDTO(BaseModel):
    calorie_setting: UpdateCalorieSettingDTO | None = None
