from calorie import orm
from repository import SQLAlchemyRepository


class DayRepository(SQLAlchemyRepository):
    model = orm.Day


class ProductRepository(SQLAlchemyRepository):
    model = orm.Product
