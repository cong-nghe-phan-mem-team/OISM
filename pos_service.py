from decimal import Decimal
from sqlalchemy.orm import Session
from app.schemas.pos import POSCheckoutRequest
from app.repositories.pos_repo import POSRepository


class POSService:
    @staticmethod
    def process_checkout(db: Session, tenant_id: int, branch_id: int, payload: POSCheckoutRequest):
        if not payload.items:
            raise ValueError("Giỏ hàng trống!")
        # Total/price is intentionally calculated in the repository from the
        # ProductVariant.retailPrice, not from client-provided prices.
        items = [i.model_dump() for i in payload.items]
        saved = POSRepository.save_pos_receipt(
            db, tenant_id, branch_id, Decimal("0"), payload.discount, Decimal("0"), payload.payment_method, items
        )
        return {"message": "Thanh toán thành công!", "receipt": saved}
