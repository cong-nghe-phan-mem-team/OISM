from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.inventory import PurchaseReceiptRequest
from app.services.inventory_service import InventoryService
from app.security import get_current_tenant_id

router = APIRouter(prefix="/inventory", tags=["Inventory & Ledger"])


@router.post("/receipts")
def create_receipt(request: PurchaseReceiptRequest, db: Session = Depends(get_db), tenant_id: int = Depends(get_current_tenant_id)):
    try:
        return {"success": True, "data": InventoryService.create_purchase_receipt(db, tenant_id, request)}
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception:
        raise HTTPException(500, "Cannot process inventory receipt")


@router.get("/ledger")
def get_ledger(sku_id: Optional[str] = None, branch_id: Optional[int] = None,
              db: Session = Depends(get_db), tenant_id: int = Depends(get_current_tenant_id)):
    try:
        return {"success": True, "data": InventoryService.get_ledger_history(db, tenant_id, sku_id, branch_id)}
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception:
        raise HTTPException(500, "Cannot load inventory ledger")
