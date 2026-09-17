from sqlalchemy.orm import Session

from app.repositories.product_repo import ProductRepository
from app.schemas.product import ProductCreateRequest


class ProductService:

    @staticmethod
    def create_product(
        db: Session,
        tenant_id: int,
        payload: ProductCreateRequest
    ):
        return ProductRepository.create_product_with_variants(
            db=db,
            tenant_id=tenant_id,
            data=payload.model_dump()
        )

    @staticmethod
    def get_products(
        db: Session,
        tenant_id: int
    ):
        return ProductRepository.get_products_by_tenant(
            db=db,
            tenant_id=tenant_id
        )