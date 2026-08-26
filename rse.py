from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.rse_service import RSEService
from app.security import get_current_tenant_id

router = APIRouter(prefix="/rse", tags=["Anti-Oversell"])


@router.get("/available-stock")
def get_available_stock(sku_id: str, branch_id: int,
                       db: Session = Depends(get_db), tenant_id: int = Depends(get_current_tenant_id)):
    try:
        available = RSEService.check_available_stock(db, sku_id, tenant_id, branch_id)
        return {"success": True, "sku_id": sku_id, "branch_id": branch_id, "available_stock": available}
    except ValueError as e:
        raise HTTPException(404, str(e))
    except Exception:
        raise HTTPException(500, "Cannot calculate available stock")
