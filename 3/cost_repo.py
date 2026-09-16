from sqlalchemy import text
from sqlalchemy.orm import Session


class CostRepository:
    @staticmethod
    def confirm_receipt(db: Session, receipt_id: int, tenant_id: int):
        row = db.execute(
            text('''SELECT it.*,pv."sku",pv."cogs"
                    FROM "InventoryTransaction" it
                    JOIN "ProductVariant" pv
                      ON pv."id"=it."skuId" AND pv."tenantId"=it."tenantId"
                    WHERE it."id"=:receipt_id
                      AND it."tenantId"=:tenant_id
                      AND it."type"='IMPORT'
                    LIMIT 1'''),
            {"receipt_id": receipt_id, "tenant_id": tenant_id},
        ).mappings().first()
        if not row:
            raise ValueError("Import inventory transaction not found")
        # Legacy InventoryTransaction has no import price or receipt status.
        # WAC is calculated when the IMPORT transaction is created; this endpoint
        # therefore returns a confirmation view without mutating the ledger.
        return {
            "receiptId": receipt_id,
            "status": "CONFIRMED",
            "sku": row["sku"],
            "updatedCogs": float(row["cogs"] or 0),
            "quantity": row["quantity"],
        }
