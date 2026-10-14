import pytest
from sqlalchemy import select

from setting.orm import CalorieSetting

GOALS = {
    "goal_calories_per_day": 2200,
    "goal_proteins_per_day": 150,
    "goal_fats_per_day": 70,
    "goal_carbs_per_day": 240,
}


class TestGetAllSettings:
    @pytest.mark.parametrize("goals", [dict.fromkeys(GOALS), GOALS])
    async def test_success(
        self, client, authenticated_user, calorie_setting, db, goals
    ):
        if any(value is not None for value in goals.values()):
            async with db() as session:
                setting = await session.get(CalorieSetting, calorie_setting.user_id)
                for field, value in goals.items():
                    setattr(setting, field, value)
                await session.commit()

        response = await client.get("/settings")

        assert response.status_code == 200
        assert response.json() == {
            "data": {
                "calorie_setting": {
                    "add_day_notes": True,
                    "ai_creates_products": True,
                    **goals,
                }
            }
        }


class TestUpdateSettings:
    async def test_success(self, client, authenticated_user, calorie_setting, db):
        request_data = {"calorie_setting": {"add_day_notes": False, **GOALS}}
        response = await client.patch("/settings", json=request_data)

        assert response.status_code == 200
        assert response.json() == {"data": {"success": True}}
        async with db() as session:
            query = select(CalorieSetting).where(
                CalorieSetting.user_id == authenticated_user.id
            )
            row = await session.execute(query)
            setting = row.scalar_one()
            assert setting.add_day_notes is False
            assert setting.ai_creates_products is True
            for field, value in GOALS.items():
                assert getattr(setting, field) == value

        response = await client.get("/settings")
        assert response.status_code == 200
        assert response.json() == {
            "data": {
                "calorie_setting": {
                    "add_day_notes": False,
                    "ai_creates_products": True,
                    **GOALS,
                }
            }
        }

    @pytest.mark.parametrize("field", GOALS)
    @pytest.mark.parametrize("value", [180, None])
    async def test_partial_goal_update(
        self, client, authenticated_user, calorie_setting, db, field, value
    ):
        async with db() as session:
            setting = await session.get(CalorieSetting, calorie_setting.user_id)
            for goal, initial_value in GOALS.items():
                setattr(setting, goal, initial_value)
            await session.commit()

        response = await client.patch(
            "/settings", json={"calorie_setting": {field: value}}
        )

        assert response.status_code == 200
        assert response.json() == {"data": {"success": True}}
        async with db() as session:
            setting = await session.get(CalorieSetting, authenticated_user.id)
            assert setting.add_day_notes is True
            assert setting.ai_creates_products is True
            for goal, expected in (GOALS | {field: value}).items():
                assert getattr(setting, goal) == expected

    async def test_empty_request_data(self, client, authenticated_user, db):
        response = await client.patch("/settings", json={})

        assert response.status_code == 200
        assert response.json() == {"data": {"success": True}}
        async with db() as session:
            query = select(CalorieSetting).where(
                CalorieSetting.user_id == authenticated_user.id
            )
            row = await session.execute(query)
            assert row.scalar_one_or_none() is None
