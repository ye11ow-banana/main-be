from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import select

from auth.orm import User
from calorie.orm import Day, DayProduct, Product


class TestUpdateAdditionalCalories:
    async def test_success(
        self,
        client,
        authenticated_user,
        db,
    ):
        async with db() as session:
            day = Day(
                user_id=authenticated_user.id,
                created_at=datetime(2026, 6, 1),
                additional_calories=Decimal("100"),
                total_calories=Decimal("500"),
            )

            session.add(day)
            await session.commit()

            day_id = day.id

        response = await client.patch(
            f"/calorie/days/{day_id}/additional-calories",
            params={"value": "250"},
        )

        assert response.status_code == 200
        assert response.json() == {"data": {"success": True}}

        async with db() as session:
            result = await session.execute(select(Day).where(Day.id == day_id))

            day = result.scalar_one()

            assert day.additional_calories == Decimal("250")

    async def test_foreign_day_returns_forbidden(
        self,
        client,
        authenticated_user,
        db,
    ):
        async with db() as session:
            foreign_user = User(
                username="foreign-user",
                email="foreign-user@example.com",
                hashed_password="not-used",
                is_verified=True,
            )
            session.add(foreign_user)
            await session.flush()

            day = Day(
                user_id=foreign_user.id,
                created_at=datetime(2026, 6, 1),
                additional_calories=Decimal("100"),
                total_calories=Decimal("500"),
            )

            session.add(day)
            await session.commit()

            day_id = day.id

        response = await client.patch(
            f"/calorie/days/{day_id}/additional-calories",
            params={"value": "250"},
        )

        assert response.status_code == 403


class TestUpdateDayProductWeight:
    async def test_success(
        self,
        client,
        authenticated_user,
        db,
    ):
        async with db() as session:
            product = Product(
                name="Rice",
                proteins=Decimal("10"),
                fats=Decimal("2"),
                carbs=Decimal("80"),
                calories=Decimal("400"),
            )
            session.add(product)
            await session.flush()

            day = Day(
                user_id=authenticated_user.id,
                created_at=datetime(2026, 6, 1),
                additional_calories=Decimal("0"),
            )
            session.add(day)
            await session.flush()

            session.add(
                DayProduct(
                    day_id=day.id,
                    product_id=product.id,
                    weight=100,
                )
            )

            await session.commit()

            day_id = day.id
            product_id = product.id

        response = await client.patch(
            f"/calorie/days/{day_id}/products/{product_id}",
            params={"weight": 200},
        )

        assert response.status_code == 200

        async with db() as session:
            row = await session.execute(
                select(DayProduct).where(
                    DayProduct.day_id == day_id,
                    DayProduct.product_id == product_id,
                )
            )
            day_product = row.scalar_one()

            assert day_product.weight == 200

            row = await session.execute(select(Day).where(Day.id == day_id))
            day = row.scalar_one()

            assert day.total_proteins == Decimal("20")
            assert day.total_fats == Decimal("4")
            assert day.total_carbs == Decimal("160")
            assert day.total_calories == Decimal("800")

    async def test_missing_day_product_returns_not_found(
        self,
        client,
        authenticated_user,
        db,
    ):
        async with db() as session:
            day = Day(
                user_id=authenticated_user.id,
                created_at=datetime(2026, 6, 1),
            )
            session.add(day)
            await session.commit()

            day_id = day.id

        response = await client.patch(
            f"/calorie/days/{day_id}/products/{uuid4()}",
            params={"weight": 200},
        )

        assert response.status_code == 404

    async def test_rejects_non_positive_weight(
        self,
        client,
        authenticated_user,
        db,
    ):
        async with db() as session:
            day = Day(
                user_id=authenticated_user.id,
                created_at=datetime(2026, 6, 1),
            )
            session.add(day)
            await session.commit()

            day_id = day.id

        response = await client.patch(
            f"/calorie/days/{day_id}/products/{uuid4()}",
            params={"weight": 0},
        )

        assert response.status_code == 422


class TestDeleteDayProduct:
    async def test_success(
        self,
        client,
        authenticated_user,
        db,
    ):
        async with db() as session:
            product = Product(
                name="Rice",
                proteins=Decimal("10"),
                fats=Decimal("2"),
                carbs=Decimal("80"),
                calories=Decimal("400"),
            )
            session.add(product)
            await session.flush()

            day = Day(
                user_id=authenticated_user.id,
                created_at=datetime(2026, 6, 1),
                total_proteins=Decimal("10"),
                total_fats=Decimal("2"),
                total_carbs=Decimal("80"),
                total_calories=Decimal("400"),
            )
            session.add(day)
            await session.flush()

            session.add(
                DayProduct(
                    day_id=day.id,
                    product_id=product.id,
                    weight=100,
                )
            )

            await session.commit()

            day_id = day.id
            product_id = product.id

        response = await client.delete(f"/calorie/days/{day_id}/products/{product_id}")

        assert response.status_code == 200

        async with db() as session:
            row = await session.execute(
                select(DayProduct).where(
                    DayProduct.day_id == day_id,
                    DayProduct.product_id == product_id,
                )
            )

            assert row.scalar_one_or_none() is None

            row = await session.execute(select(Day).where(Day.id == day_id))

            day = row.scalar_one()

            assert day.total_proteins == Decimal("0")
            assert day.total_fats == Decimal("0")
            assert day.total_carbs == Decimal("0")
            assert day.total_calories == Decimal("0")

    async def test_missing_day_product_returns_not_found(
        self,
        client,
        authenticated_user,
        db,
    ):
        async with db() as session:
            day = Day(
                user_id=authenticated_user.id,
                created_at=datetime(2026, 6, 1),
            )
            session.add(day)
            await session.commit()

            day_id = day.id

        response = await client.delete(f"/calorie/days/{day_id}/products/{uuid4()}")

        assert response.status_code == 404


class TestDeleteDay:
    async def test_success(
        self,
        client,
        authenticated_user,
        db,
    ):
        async with db() as session:
            day = Day(
                user_id=authenticated_user.id,
                created_at=datetime(2026, 6, 1),
            )
            session.add(day)
            await session.commit()

            day_id = day.id

        response = await client.delete(f"/calorie/days/{day_id}")

        assert response.status_code == 200

        async with db() as session:
            row = await session.execute(select(Day).where(Day.id == day_id))

            assert row.scalar_one_or_none() is None
