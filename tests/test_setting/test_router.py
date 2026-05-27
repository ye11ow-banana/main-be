async def test_get_all_settings(client, authenticated_user, calorie_setting):
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
