from sqlalchemy.orm import Session
from app.repositories.rse_repo import RSERepository


class RSEService:
    @staticmethod
    def check_available_stock(db: Session, sku_id, tenant_id: int, branch_id: int):
        return RSERepository.get_available_stock(db, tenant_id, sku_id, branch_id)

    @staticmethod
    def reserve(db: Session, sku_id, tenant_id: int, branch_id: int, requested_qty: int, reference_id: str = "API-RESERVE"):
        result = RSERepository.reserve(db, tenant_id, sku_id, branch_id, requested_qty, reference_id)
        db.commit()
        return result
