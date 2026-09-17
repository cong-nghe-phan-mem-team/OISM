from decimal import Decimal
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.repositories.rse_repo import RSERepository
from app.repositories.auth_repo import AuthRepository


class OrderRepository:
    @staticmethod
    def _variant(db: Session, tenant_id: int, sku):
        value = str(sku).strip()
        numeric_id = int(value) if value.isdigit() else -1
        return db.execute(
            text('''SELECT * FROM "ProductVariant"
                    WHERE "tenantId"=:tenant_id
                      AND ("id"=:id OR lower("sku")=lower(:sku))
                    LIMIT 1'''),
            {"tenant_id": tenant_id, "id": numeric_id, "sku": value},
        ).mappings().first()

    @staticmethod
    def insert_order(db: Session, tenant_id: int, order_data: dict, items_data: list):
        if not items_data:
            raise ValueError("Order must contain at least one item")
        branch_id = int(order_data["branchId"])
        if not AuthRepository.validate_branch(db, tenant_id, branch_id):
            raise ValueError("Branch not found or inactive")

        try:
            resolved = []
            total = Decimal("0")
            for item in items_data:
                qty = int(item["quantity"])
                if qty <= 0:
                    raise ValueError("Invalid order item quantity")
                variant = OrderRepository._variant(db, tenant_id, item["skuId"])
                if not variant:
                    raise ValueError(f'SKU not found: {item["skuId"]}')

                # The database retail price is authoritative. The optional
                # client unit_price is retained only for backward compatibility.
                price = Decimal(str(variant["retailPrice"] or 0))
                available = RSERepository.get_available_stock(
                    db, tenant_id, variant["id"], branch_id
                )
                if available < qty:
                    raise ValueError(f'Insufficient available stock for SKU {item["skuId"]}')
                subtotal = price * qty
                total += subtotal
                resolved.append((variant, qty, price, subtotal))

            order_id = db.execute(
                text('''INSERT INTO "Order"
                        ("tenantId","branchId","salesChannel","type","status",
                         "totalAmount","discount","finalAmount","createdAt")
                        VALUES (:tenant_id,:branch_id,:sales_channel,'ONLINE','PENDING',
                                :total,0,:total,NOW())
                        RETURNING "orderId"'''),
                {
                    "tenant_id": tenant_id,
                    "branch_id": branch_id,
                    "sales_channel": order_data["salesChannel"],
                    "total": float(total),
                },
            ).scalar_one()

            for variant, qty, price, subtotal in resolved:
                db.execute(
                    text('''INSERT INTO "OrderItem"
                            ("orderId","tenantId","skuId","quantity","unitPrice","subTotal")
                            VALUES (:order_id,:tenant_id,:sku_id,:quantity,:unit_price,:subtotal)'''),
                    {
                        "order_id": order_id,
                        "tenant_id": tenant_id,
                        "sku_id": variant["id"],
                        "quantity": qty,
                        "unit_price": float(price),
                        "subtotal": float(subtotal),
                    },
                )
            db.commit()
            return order_id
        except Exception:
            db.rollback()
            raise

    @staticmethod
    def get_order(db: Session, tenant_id: int, order_id: int):
        row = db.execute(
            text('''SELECT * FROM "Order"
                    WHERE "orderId"=:order_id AND "tenantId"=:tenant_id'''),
            {"order_id": order_id, "tenant_id": tenant_id},
        ).mappings().first()
        if not row:
            raise ValueError("Order not found")
        items = db.execute(
            text('''SELECT oi.*,pv."sku"
                    FROM "OrderItem" oi
                    JOIN "ProductVariant" pv
                      ON pv."id"=oi."skuId" AND pv."tenantId"=oi."tenantId"
                    WHERE oi."orderId"=:order_id AND oi."tenantId"=:tenant_id
                    ORDER BY oi."id"'''),
            {"order_id": order_id, "tenant_id": tenant_id},
        ).mappings().all()
        return dict(row), [dict(i) for i in items]

    @staticmethod
    def list_orders(db: Session, tenant_id: int, limit: int = 100):
        limit = max(1, min(int(limit), 200))
        rows = db.execute(
            text('''SELECT o.*,
                           COUNT(oi."id") AS "itemCount"
                    FROM "Order" o
                    LEFT JOIN "OrderItem" oi ON oi."orderId"=o."orderId" AND oi."tenantId"=o."tenantId"
                    WHERE o."tenantId"=:tenant_id
                    GROUP BY o."orderId"
                    ORDER BY o."createdAt" DESC, o."orderId" DESC
                    LIMIT :limit'''),
            {"tenant_id": tenant_id, "limit": limit},
        ).mappings().all()
        return [dict(r) for r in rows]

    @staticmethod
    def update_order_status(db: Session, tenant_id: int, order_id: int, action: str):
        order, items = OrderRepository.get_order(db, tenant_id, order_id)
        current = order["status"]
        transitions = {
            "reserve": {"PENDING": "RESERVED"},
            "confirm": {"RESERVED": "CONFIRMED"},
            "cancel": {"PENDING": "CANCELLED", "RESERVED": "CANCELLED", "CONFIRMED": "CANCELLED"},
            "pos_checkout": {"PENDING": "COMPLETED", "RESERVED": "COMPLETED", "CONFIRMED": "COMPLETED"},
        }
        new_status = transitions.get(action, {}).get(current)
        if not new_status:
            raise ValueError(f"Invalid transition: {current} -> {action}")

        try:
            if action == "reserve":
                for item in items:
                    RSERepository.reserve(
                        db, tenant_id, item["skuId"], order["branchId"], int(item["quantity"]), f"ORDER-{order_id}"
                    )
            elif action == "cancel" and current in {"RESERVED", "CONFIRMED"}:
                for item in items:
                    RSERepository.release_reservation(
                        db, tenant_id, item["skuId"], order["branchId"], int(item["quantity"]), f"ORDER-{order_id}"
                    )
            elif action == "pos_checkout":
                for item in items:
                    qty = int(item["quantity"])
                    release_qty = qty if current in {"RESERVED", "CONFIRMED"} else 0
                    updated = db.execute(
                        text('''UPDATE "ProductVariant"
                                SET "onHand"=COALESCE("onHand",0)-:qty,
                                    "reserved"=CASE
                                      WHEN :release_qty>0 THEN GREATEST(0,COALESCE("reserved",0)-:release_qty)
                                      ELSE COALESCE("reserved",0)
                                    END
                                WHERE "id"=:sku_id AND "tenantId"=:tenant_id
                                  AND COALESCE("onHand",0)-CASE WHEN :release_qty>0 THEN 0 ELSE COALESCE("reserved",0) END>=:qty'''),
                        {
                            "qty": qty,
                            "release_qty": release_qty,
                            "sku_id": item["skuId"],
                            "tenant_id": tenant_id,
                        },
                    )
                    if updated.rowcount != 1:
                        raise ValueError(f'Insufficient stock for SKU {item.get("sku", item["skuId"])}')
                    balance = db.execute(
                        text('''SELECT "onHand" FROM "ProductVariant"
                                WHERE "id"=:sku_id AND "tenantId"=:tenant_id'''),
                        {"sku_id": item["skuId"], "tenant_id": tenant_id},
                    ).scalar_one()
                    db.execute(
                        text('''INSERT INTO "InventoryTransaction"
                                ("tenantId","branchId","skuId","type","quantity","balanceAfter","referenceId","createdAt")
                                VALUES (:tenant_id,:branch_id,:sku_id,'SALE',:quantity,:balance_after,:reference_id,NOW())'''),
                        {
                            "tenant_id": tenant_id,
                            "branch_id": order["branchId"],
                            "sku_id": item["skuId"],
                            "quantity": -qty,
                            "balance_after": int(balance or 0),
                            "reference_id": f"ORDER-{order_id}",
                        },
                    )

            db.execute(
                text('''UPDATE "Order" SET "status"=:status
                        WHERE "orderId"=:order_id AND "tenantId"=:tenant_id'''),
                {"status": new_status, "order_id": order_id, "tenant_id": tenant_id},
            )
            db.commit()
            return {"orderId": order_id, "status": new_status}
        except Exception:
            db.rollback()
            raise
