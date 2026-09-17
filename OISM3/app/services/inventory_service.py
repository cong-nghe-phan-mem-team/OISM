from sqlalchemy.orm import Session
from app.repositories.inventory_repo import InventoryRepository
from app.schemas.inventory import PurchaseReceiptRequest


class InventoryService:
    @staticmethod
    def create_purchase_receipt(db: Session, tenant_id: int, data: PurchaseReceiptRequest):
        return InventoryRepository.process_purchase_receipt_tx(
            db=db,
            tenant_id=tenant_id,
            branch_id=int(data.branchId),
            sku_id=data.skuId,
            import_qty=data.importQuantity,
            import_price=data.importUnitPrice,
            ref_id=data.referenceId,
        )

    @staticmethod
    def get_ledger_history(db: Session, tenant_id: int, sku_id=None, branch_id=None):
        if branch_id is not None:
            branch_id = int(branch_id)
        return InventoryRepository.get_ledger(db, tenant_id, sku_id, branch_id)
