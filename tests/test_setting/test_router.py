from sqlalchemy import select

from setting.orm import CalorieSetting


class TestGetAllSettings:
    async def test_success(self, client, authenticated_user, calorie_setting):
        response = await client.get("/settings")

        assert response.status_code == 200
        assert response.json() == {
            "data": {
                "calorie_setting": {
                    "add_day_notes": True,
                    "ai_creates_products": True,
                }
            }
        }


class TestUpdateSettings:
    async def test_success(self, client, authenticated_user, calorie_setting, db):
        request_data = {"calorie_setting": {"add_day_notes": False}}
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
