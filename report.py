from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.report_service import ReportService
from app.security import get_current_tenant_id

router = APIRouter(prefix="/reports", tags=["Analytics & Reports"])


@router.get("/revenue")
def get_revenue_report(db: Session = Depends(get_db), tenant_id: int = Depends(get_current_tenant_id)):
    try:
        return {"success": True, "data": ReportService.generate_revenue_report(db, tenant_id)}
    except Exception:
        raise HTTPException(500, "Cannot generate revenue report")


@router.get("/inventory")
def get_inventory_report(db: Session = Depends(get_db), tenant_id: int = Depends(get_current_tenant_id)):
    try:
        return {"success": True, "data": ReportService.generate_inventory_report(db, tenant_id)}
    except Exception:
        raise HTTPException(500, "Cannot generate inventory report")


@router.get("/alerts")
def get_alerts(db: Session = Depends(get_db), tenant_id: int = Depends(get_current_tenant_id)):
    try:
        return {"success": True, "data": ReportService.get_low_stock_alerts(db, tenant_id)}
    except Exception:
        raise HTTPException(500, "Cannot load low-stock alerts")
