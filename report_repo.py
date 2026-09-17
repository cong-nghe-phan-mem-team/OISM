from sqlalchemy import text
from sqlalchemy.orm import Session


class ReportRepository:
    @staticmethod
    def get_inventory_data(db: Session, tenant_id: int):
        return [dict(r) for r in db.execute(
            text('''SELECT pv."id",pv."sku",
                         COALESCE(pv."onHand",0) AS "onHand",
                         COALESCE(pv."reserved",0) AS "reserved",
                         COALESCE(pv."cogs",0) AS "cogs",
                         COALESCE(pv."reorderLevel",5) AS "reorderLevel",
                         p."title"
                  FROM "ProductVariant" pv
                  LEFT JOIN "Product" p
                    ON p."id"=pv."productId" AND p."tenantId"=pv."tenantId"
                  WHERE pv."tenantId"=:tenant_id
                  ORDER BY pv."id"'''),
            {"tenant_id": tenant_id},
        ).mappings().all()]

    @staticmethod
    def get_sales_data(db: Session, tenant_id: int):
        return [dict(r) for r in db.execute(
            text('''SELECT o."orderId",o."finalAmount",o."discount",o."createdAt",
                         SUM(oi."subTotal") AS "itemSubtotal",
                         SUM(oi."quantity" * COALESCE(pv."cogs",0)) AS "estimatedCogs"
                  FROM "Order" o
                  JOIN "OrderItem" oi
                    ON oi."orderId"=o."orderId" AND oi."tenantId"=o."tenantId"
                  LEFT JOIN "ProductVariant" pv
                    ON pv."id"=oi."skuId" AND pv."tenantId"=oi."tenantId"
                  WHERE o."tenantId"=:tenant_id AND o."status"='COMPLETED'
                  GROUP BY o."orderId",o."finalAmount",o."discount",o."createdAt"
                  ORDER BY o."createdAt" DESC'''),
            {"tenant_id": tenant_id},
        ).mappings().all()]
