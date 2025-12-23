from abc import ABC, abstractmethod
from datetime import datetime
from typing import Sequence, Type, Mapping, Any
from uuid import UUID

from sqlalchemy import Row, delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database import Base
from utils import Pagination


class IRepository(ABC):
    @abstractmethod
    async def get(
        self, /, returns: Sequence[str] | None = None, **data: str | int | UUID
    ) -> Base:
        raise NotImplementedError

    @abstractmethod
    async def add(self, **insert_data) -> Base:
        raise NotImplementedError

    @abstractmethod
    async def isearch_count(self, **data: str | int) -> int:
        raise NotImplementedError

    @abstractmethod
    async def get_paginated_all(
        self,
        /,
        pagination: Pagination,
        returns: Sequence[str] | None = None,
        **data: str | int,
    ) -> Sequence[Row]:
        raise NotImplementedError

    @abstractmethod
    async def get_all(
        self, /, returns: Sequence[str] | None = None, **data: str | int | UUID
    ) -> Sequence[Row]:
        raise NotImplementedError

    @abstractmethod
    async def get_last(
        self, /, returns: Sequence[str] | None = None, **data: str | int | UUID
    ) -> Row[tuple]:
        raise NotImplementedError

    @abstractmethod
    async def get_last_or_create(
        self, /, returns: Sequence[str] | None = None, **data: str | int | UUID
    ) -> Row[tuple]:
        raise NotImplementedError

    @abstractmethod
    async def remove(self, **data: str | int | UUID) -> None:
        raise NotImplementedError

    @abstractmethod
    async def bulk_add(self, inserts: list[dict[str, str | int | UUID | None]]) -> None:
        raise NotImplementedError


class SQLAlchemyRepository(IRepository):
    model: Type[Base]

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get(
        self, /, returns: Sequence[str] | None = None, **data: str | int | UUID
    ) -> Row[tuple]:
        if returns is None:
            returns = [c.name for c in self.model.__table__.columns]
        query = select(*[getattr(self.model, c) for c in returns]).filter_by(**data)
        res = await self._session.execute(query)
        return res.first()

    async def add(self, **insert_data) -> Base:
        new_model_object = self.model(**insert_data)
        self._session.add(new_model_object)
        await self._session.flush()
        return new_model_object

    async def isearch_count(self, **data: str | int) -> int:
        """
        Search for the count of rows that match the given data.

        Case-insensitive search.
        """
        query = select(func.count())
        for key, value in data.items():
            column = getattr(self.model, key)
            query = query.filter(column.ilike(f"%{value}%"))
        result = await self._session.execute(query)
        return result.scalar()

    async def get_paginated_all(
        self,
        /,
        pagination: Pagination,
        returns: Sequence[str] | None = None,
        **data: str | int,
    ) -> Sequence[Row]:
        if returns is None:
            returns = [c.name for c in self.model.__table__.columns]
        query = select(*[getattr(self.model, c) for c in returns])
        for key, value in data.items():
            column = getattr(self.model, key)
            query = query.filter(column.ilike(f"%{value}%"))
        query = query.offset(pagination.get_offset()).limit(pagination.limit)
        result = await self._session.execute(query)
        return result.fetchall()

    async def get_all(
        self, /, returns: Sequence[str] | None = None, **data: str | int | UUID
    ) -> Sequence[Mapping[str, Any]]:
        if returns is None:
            returns = [c.name for c in self.model.__table__.columns]
        query = select(*[getattr(self.model, c) for c in returns]).filter_by(**data)
        res = await self._session.execute(query)
        return res.mappings().all()

    async def count(self, /, **data: str | int | UUID) -> int:
        query = select(func.count()).filter_by(**data)
        res = await self._session.execute(query)
        return res.scalar()

    async def update(
        self,
        /,
        what_to_update: dict[str, str | int | UUID],
        **data: str | int | UUID | datetime,
    ) -> None:
        stmt = update(self.model).filter_by(**what_to_update).values(**data)
        await self._session.execute(stmt)

    async def get_last(
        self, /, returns: Sequence[str] | None = None, **data: str | int | UUID
    ) -> Row[tuple]:
        if returns is None:
            returns = [c.name for c in self.model.__table__.columns]
        query = (
            select(*[getattr(self.model, c) for c in returns])
            .filter_by(**data)
            .order_by(self.model.id.desc())
        )
        res = await self._session.execute(query)
        return res.first()

    async def get_last_or_create(
        self, /, returns: Sequence[str] | None = None, **data: str | int | UUID
    ) -> Row[tuple]:
        obj = await self.get_last(returns=returns, **data)
        if obj is None:
            obj = await self.add(**data)
        return obj

    async def remove(self, **data: str | int | UUID) -> None:
        stmt = delete(self.model).filter_by(**data)
        await self._session.execute(stmt)

    async def bulk_add(self, inserts: list[dict[str, str | int | UUID | None]]) -> None:
        await self._session.execute(self.model.__table__.insert(), inserts)
