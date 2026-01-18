from uuid import UUID

from sqlalchemy.exc import IntegrityError

from calorie.models import ProductCreationDTO, ProductDTO
from models import PaginationDTO
from unitofwork import IUnitOfWork
from utils import Pagination


class ProductService:
    def __init__(self, uow: IUnitOfWork):
        self._uow = uow

    async def search_products(
        self, q: str, pagination: Pagination
    ) -> PaginationDTO[ProductDTO]:
        async with self._uow:
            products = await self._uow.products.search_by_name(q, pagination)
            count = await self._uow.products.count_by_name(q)

        return PaginationDTO(
            page_count=pagination.get_page_count(count),
            total_count=count,
            data=products,
        )

    async def update_product(self, product_id: UUID, data: ProductCreationDTO) -> None:
        async with self._uow:
            try:
                await self._uow.products.update(
                    what_to_update={"id": product_id}, **data.model_dump()
                )
            except IntegrityError:
                raise ValueError("Error while product update")
        await self._uow.commit()

    async def create_product(self, data: ProductCreationDTO) -> UUID:
        async with self._uow:
            try:
                product = await self._uow.products.add(**data.model_dump())
            except IntegrityError:
                raise ValueError("Error while product creation")
            await self._uow.commit()
            return product.id
