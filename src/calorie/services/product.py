from calorie.models import ProductDTO
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
