from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.cost_service import CostService
from app.security import get_current_tenant_id

router = APIRouter(prefix="/cost", tags=["Cost Management"])


@router.post("/receipts/{receipt_id}/confirm")
def confirm_purchase_receipt(receipt_id: int, db: Session = Depends(get_db), tenant_id: int = Depends(get_current_tenant_id)):
    try:
        return {"message": "Receipt confirmation checked.", "data": CostService.confirm_purchase(db, receipt_id, tenant_id)}
    except ValueError as e:
        raise HTTPException(404, str(e))
    except Exception:
        raise HTTPException(500, "Cannot confirm receipt")
