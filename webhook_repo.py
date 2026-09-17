import json
from sqlalchemy import text
from sqlalchemy.orm import Session


class WebhookRepository:
    @staticmethod
    def save_webhook_log(db: Session, tenant_id: int, platform: str, event_type: str, payload: dict):
        result = db.execute(
            text('''INSERT INTO "WebhookLog"
                    ("tenantId","platform","eventType","payload","status")
                    VALUES (:tenant_id,:platform,:event_type,:payload,'Processed')
                    RETURNING *'''),
            {
                "tenant_id": tenant_id,
                "platform": platform.strip(),
                "event_type": event_type.strip(),
                "payload": json.dumps(payload, ensure_ascii=False),
            },
        )
        return dict(result.mappings().first())

    @staticmethod
    def create_notification(db: Session, tenant_id: int, message: str):
        result = db.execute(
            text('''INSERT INTO "Notification"
                    ("tenantId","message","status","createdAt")
                    VALUES (:tenant_id,:message,'Unread',NOW())
                    RETURNING *'''),
            {"tenant_id": tenant_id, "message": message},
        )
        return dict(result.mappings().first())

    @staticmethod
    def get_notifications(db: Session, tenant_id: int):
        return [dict(row) for row in db.execute(
            text('''SELECT * FROM "Notification"
                    WHERE "tenantId"=:tenant_id
                    ORDER BY "createdAt" DESC,"id" DESC'''),
            {"tenant_id": tenant_id},
        ).mappings().all()]
