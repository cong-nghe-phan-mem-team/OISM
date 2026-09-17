from decimal import Decimal
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.repositories.inventory_repo import InventoryRepository
from app.repositories.auth_repo import AuthRepository


class POSRepository:
    @staticmethod
    def save_pos_receipt(
        db: Session,
        tenant_id: int,
        branch_id: int,
        total_amount,
        discount,
        final_amount,
        payment_method: str,
        items: list,
    ):
        if not AuthRepository.validate_branch(db, tenant_id, branch_id):
            raise ValueError("Branch not found or inactive")

        try:
            # Resolve and lock every SKU before creating the order. The database
            # value of retailPrice is authoritative; client-supplied price is
            # ignored so a client cannot sell an item for an arbitrary price.
            resolved = []
            total = Decimal("0")
            for item in items:
                variant = InventoryRepository.resolve_variant(db, tenant_id, item["sku"])
                if not variant:
                    raise ValueError(f"SKU not found: {item['sku']}")

                lock_clause = " FOR UPDATE" if getattr(getattr(db, "bind", None), "dialect", None) and db.bind.dialect.name == "postgresql" else ""
                locked = db.execute(
                    text(f'''SELECT * FROM "ProductVariant"
                           WHERE "id"=:sku_id AND "tenantId"=:tenant_id{lock_clause}'''),
                    {"sku_id": variant["id"], "tenant_id": tenant_id},
                ).mappings().first()
                if not locked:
                    raise ValueError(f"SKU not found: {item['sku']}")

                qty = int(item["quantity"])
                if qty <= 0:
                    raise ValueError("Quantity must be greater than 0")

                available = int(locked["onHand"] or 0) - int(locked["reserved"] or 0)
                if available < qty:
                    raise ValueError(f"Insufficient stock for SKU {item['sku']}")

                unit_price = Decimal(str(locked["retailPrice"] or 0))
                subtotal = unit_price * qty
                total += subtotal
                resolved.append((locked, item, qty, unit_price, subtotal))

            discount = Decimal(str(discount))
            final_amount = total - discount
            if discount < 0 or discount > total:
                raise ValueError("Discount cannot be greater than total amount")

            order = db.execute(
                text('''INSERT INTO "Order"
                        ("tenantId","branchId","type","status","totalAmount","discount","finalAmount","paymentMethod","createdAt")
                        VALUES (:tenant_id,:branch_id,'POS','COMPLETED',:total,:discount,:final,:payment_method,NOW())
                        RETURNING *'''),
                {
                    "tenant_id": tenant_id,
                    "branch_id": branch_id,
                    "total": float(total),
                    "discount": float(discount),
                    "final": float(final_amount),
                    "payment_method": payment_method,
                },
            ).mappings().first()
            if not order:
                raise ValueError("Cannot create POS order")

            saved_items = []
            for variant, item, qty, unit_price, subtotal in resolved:
                updated = db.execute(
                    text('''UPDATE "ProductVariant"
                            SET "onHand"=COALESCE("onHand",0)-:qty
                            WHERE "id"=:sku_id AND "tenantId"=:tenant_id
                              AND COALESCE("onHand",0)-COALESCE("reserved",0)>=:qty'''),
                    {"qty": qty, "sku_id": variant["id"], "tenant_id": tenant_id},
                )
                if updated.rowcount != 1:
                    raise ValueError(f"Insufficient stock for SKU {item['sku']}")

                db.execute(
                    text('''INSERT INTO "OrderItem"
                            ("orderId","skuId","tenantId","quantity","unitPrice","subTotal")
                            VALUES (:order_id,:sku_id,:tenant_id,:quantity,:unit_price,:subtotal)'''),
                    {
                        "order_id": order["orderId"],
                        "sku_id": variant["id"],
                        "tenant_id": tenant_id,
                        "quantity": qty,
                        "unit_price": float(unit_price),
                        "subtotal": float(subtotal),
                    },
                )
                balance = db.execute(
                    text('''SELECT "onHand" FROM "ProductVariant"
                            WHERE "id"=:sku_id AND "tenantId"=:tenant_id'''),
                    {"sku_id": variant["id"], "tenant_id": tenant_id},
                ).scalar_one()
                db.execute(
                    text('''INSERT INTO "InventoryTransaction"
                            ("tenantId","branchId","skuId","type","quantity","balanceAfter","referenceId","createdAt")
                            VALUES (:tenant_id,:branch_id,:sku_id,'SALE',:quantity,:balance_after,:reference_id,NOW())'''),
                    {
                        "tenant_id": tenant_id,
                        "branch_id": branch_id,
                        "sku_id": variant["id"],
                        "quantity": -qty,
                        "balance_after": int(balance or 0),
                        "reference_id": f"POS-{order['orderId']}",
                    },
                )
                saved_items.append({
                    "sku": variant["sku"],
                    "quantity": qty,
                    "price": float(unit_price),
                    "subtotal": float(subtotal),
                })

            db.commit()
            return {"order": dict(order), "items": saved_items}
        except Exception:
            db.rollback()
            raise
