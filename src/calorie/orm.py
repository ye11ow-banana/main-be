from __future__ import annotations

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import UUID, ForeignKey
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base, created_at, updated_at, uuidpk

if TYPE_CHECKING:
    from auth.orm import User


class Day(Base):
    __tablename__ = "days"

    id: Mapped[uuidpk]
    body_weight: Mapped[Decimal] = mapped_column(nullable=True)
    body_fat: Mapped[Decimal] = mapped_column(nullable=True)
    trend: Mapped[Decimal] = mapped_column(nullable=True)  # weight trend
    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")
    )

    user: Mapped["User"] = relationship("User", back_populates="days")
    day_products: Mapped[list["DayProduct"]] = relationship(
        "DayProduct",
        back_populates="day",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    products = association_proxy("day_products", "product")


class Product(Base):
    __tablename__ = "products"

    id: Mapped[uuidpk]
    name: Mapped[str] = mapped_column(nullable=False, unique=True)
    proteins: Mapped[Decimal] = mapped_column(nullable=False)
    fats: Mapped[Decimal] = mapped_column(nullable=False)
    carbs: Mapped[Decimal] = mapped_column(nullable=False)
    calories: Mapped[Decimal] = mapped_column(nullable=False)
    created_at: Mapped[created_at]

    day_products: Mapped[list["DayProduct"]] = relationship(
        "DayProduct",
        back_populates="product",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    days = association_proxy("day_products", "day")


class DayProduct(Base):
    __tablename__ = "day_products"

    day_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("days.id", ondelete="CASCADE"),
        primary_key=True,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        primary_key=True,
    )

    weight: Mapped[int] = mapped_column(nullable=False)

    day: Mapped["Day"] = relationship("Day", back_populates="day_products")
    product: Mapped["Product"] = relationship("Product", back_populates="day_products")
