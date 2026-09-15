from sqlalchemy.orm import Session
from app.repositories.webhook_repo import WebhookRepository
from app.schemas.webhook import WebhookEventRequest


class WebhookService:
    @staticmethod
    def process_webhook(db: Session, tenant_id: int, data: WebhookEventRequest):
        try:
            log = WebhookRepository.save_webhook_log(db, tenant_id, data.platform, data.event_type, data.payload)
            notification = WebhookRepository.create_notification(
                db, tenant_id, f"Đã nhận webhook {data.event_type} từ {data.platform}"
            )
            db.commit()
            return {
                "webhook_id": log["id"],
                "status": log["status"],
                "notification_id": notification["id"],
                "background_job": {
                    "queued": False,
                    "reason": "Legacy schema không có bảng background job tương ứng; webhook đã được ghi nhận thành công.",
                },
            }
        except Exception:
            db.rollback()
            raise

    @staticmethod
    def fetch_notifications(db: Session, tenant_id: int):
        return WebhookRepository.get_notifications(db, tenant_id)
