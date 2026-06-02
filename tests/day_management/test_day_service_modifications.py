import asyncio
from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

from calorie.models import DayFullInfoDTO
from calorie.services.day import DayService


class FakeProduct:
    def __init__(
        self,
        proteins=10,
        fats=5,
        carbs=20,
        calories=200,
        product_id=None,
        name="Test product",
    ):
        self.id = product_id or uuid4()
        self.name = name

        self.proteins = Decimal(proteins)
        self.fats = Decimal(fats)
        self.carbs = Decimal(carbs)
        self.calories = Decimal(calories)


class FakeDayProduct:
    def __init__(self, product, weight):
        self.product = product
        self.weight = weight


class FakeDay:
    def __init__(self, day_id=None):
        self.id = day_id or uuid4()

        self.created_at = datetime.now()

        self.body_weight = None
        self.additional_calories = Decimal("100")
        self.total_proteins = Decimal("0")
        self.total_fats = Decimal("0")
        self.total_carbs = Decimal("0")
        self.total_calories = Decimal("200")

        self.day_products = [FakeDayProduct(FakeProduct(), 100)]


class FakeDaysRepo:
    def __init__(self, day):
        self.day = day
        self.updated = None
        self.updated_args = None

    async def get_day_with_products(self, user_id, target_date):
        return self.day

    async def get_by_id(self, day_id):
        return self.day

    async def update(self, where, **data):
        self.updated = where
        self.updated_args = data

        for k, v in data.items():
            setattr(self.day, k, v)

    async def get_trend_adjacent_days(self, *args, **kwargs):
        return None, self.day, None


class FakeDayProductsRepo:
    def __init__(self):
        self.updated_weight = None
        self.deleted = None

    async def update_weight(self, day_id, product_id, weight):
        self.updated_weight = (day_id, product_id, weight)

    async def delete_product(self, day_id, product_id):
        self.deleted = (day_id, product_id)


class FakeUnitOfWork:
    def __init__(self, day):
        self.days = FakeDaysRepo(day)
        self.day_products = FakeDayProductsRepo()
        self.committed = False

    async def __aenter__(self):
        pass

    async def __aexit__(self, *args):
        pass

    async def commit(self):
        self.committed = True


def test_get_day_details_returns_dto():
    day = FakeDay(uuid4())
    uow = FakeUnitOfWork(day)

    service = DayService(uow, calorie_openai_client=None)

    result = asyncio.run(service.get_day_details(uuid4(), date.today()))

    assert isinstance(result, DayFullInfoDTO)
    assert result.total_calories == day.total_calories


def test_update_additional_calories_triggers_recalc():
    day = FakeDay(uuid4())
    uow = FakeUnitOfWork(day)

    service = DayService(uow, calorie_openai_client=None)

    asyncio.run(
        service.update_additional_calories(
            user_id=uuid4(),
            day_id=day.id,
            value=Decimal("250"),
        )
    )

    assert uow.days.updated is not None
    assert uow.committed is True
    assert uow.days.updated_args["additional_calories"] == Decimal("250")


def test_update_day_product_weight():
    day = FakeDay(uuid4())
    uow = FakeUnitOfWork(day)

    service = DayService(uow, calorie_openai_client=None)

    pid = uuid4()

    asyncio.run(
        service.update_day_product_weight(
            user_id=uuid4(),
            day_id=day.id,
            product_id=pid,
            weight=150,
        )
    )

    assert uow.day_products.updated_weight == (day.id, pid, 150)
    assert uow.committed is True


def test_delete_day_product():
    day = FakeDay(uuid4())
    uow = FakeUnitOfWork(day)

    service = DayService(uow, calorie_openai_client=None)

    pid = uuid4()

    asyncio.run(
        service.delete_day_product(
            user_id=uuid4(),
            day_id=day.id,
            product_id=pid,
        )
    )

    assert uow.day_products.deleted == (day.id, pid)
    assert uow.committed is True


def test_recalculate_day_totals():
    product = FakeProduct(proteins=10, fats=5, carbs=20, calories=200)

    day = FakeDay(uuid4())
    day.additional_calories = Decimal("50")
    day.day_products = [FakeDayProduct(product, 100)]

    uow = FakeUnitOfWork(day)
    service = DayService(uow, calorie_openai_client=None)

    asyncio.run(service._recalculate_day(day.id))

    updated = uow.days.updated_args

    assert updated["total_proteins"] == Decimal("10")
    assert updated["total_fats"] == Decimal("5")
    assert updated["total_carbs"] == Decimal("20")
    assert updated["total_calories"] == Decimal("250")
