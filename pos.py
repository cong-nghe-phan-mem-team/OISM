from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.pos import POSCheckoutRequest
from app.services.pos_service import POSService
from app.security import get_current_tenant_id, get_current_branch_id

router = APIRouter(prefix="/pos", tags=["Point of Sale"])


@router.post("/checkout")
def checkout(payload: POSCheckoutRequest, db: Session = Depends(get_db),
             tenant_id: int = Depends(get_current_tenant_id), branch_id: int = Depends(get_current_branch_id)):
    try:
        return POSService.process_checkout(db, tenant_id, branch_id, payload)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception:
        raise HTTPException(500, "POS checkout failed")
