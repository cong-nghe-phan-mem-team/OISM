from app.repositories.cost_repo import CostRepository
from sqlalchemy.orm import Session
class CostService:
    @staticmethod
    def confirm_purchase(db:Session,receipt_id:int,tenant_id:int):
        return CostRepository.confirm_receipt(db,receipt_id,tenant_id)
