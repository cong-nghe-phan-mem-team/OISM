from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.webhook import WebhookEventRequest
from app.services.webhook_service import WebhookService
from app.security import get_current_tenant_id

router = APIRouter(prefix="/system", tags=["Integration & Notifications"])


@router.post("/webhook/receive")
def receive_webhook(payload: WebhookEventRequest, db: Session = Depends(get_db), tenant_id: int = Depends(get_current_tenant_id)):
    try:
        return {"message": "Webhook đã được tiếp nhận", "data": WebhookService.process_webhook(db, tenant_id, payload)}
    except Exception:
        raise HTTPException(500, "Webhook processing failed")


@router.get("/notifications")
def get_notifications(db: Session = Depends(get_db), tenant_id: int = Depends(get_current_tenant_id)):
    try:
        return {"success": True, "data": WebhookService.fetch_notifications(db, tenant_id)}
    except Exception:
        raise HTTPException(500, "Cannot load notifications")
