from sqlalchemy import text
from sqlalchemy.orm import Session
from app.repositories.auth_repo import AuthRepository


class RSERepository:
    """Anti-oversell against the legacy ProductVariant stock counters.

    The real legacy schema stores onHand/reserved on ProductVariant and keeps a
    branch-aware append-only InventoryTransaction ledger. It does not have a
    branch-aware reservation table, so reserved is intentionally treated as a
    SKU-level counter. Every mutation is tenant-scoped and the reservation
    update is an atomic conditional UPDATE for concurrency safety.
    """

    @staticmethod
    def _variant(db: Session, tenant_id: int, sku_id):
        value = str(sku_id).strip()
        numeric_id = int(value) if value.isdigit() else -1
        return db.execute(
            text('''SELECT "id","sku","onHand","reserved"
                    FROM "ProductVariant"
                    WHERE "tenantId"=:tenant_id
                      AND ("id"=:id OR lower("sku")=lower(:sku))
                    LIMIT 1'''),
            {"tenant_id": tenant_id, "id": numeric_id, "sku": value},
        ).mappings().first()

    @staticmethod
    def _validate_branch(db: Session, tenant_id: int, branch_id: int):
        if not AuthRepository.validate_branch(db, tenant_id, branch_id):
            raise ValueError("Branch not found or inactive")

    @staticmethod
    def get_available_stock(db: Session, tenant_id: int, sku_id, branch_id: int):
        RSERepository._validate_branch(db, tenant_id, int(branch_id))
        variant = RSERepository._variant(db, tenant_id, sku_id)
        if not variant:
            raise ValueError(f"Product SKU not found: {sku_id}")
        return max(0, int(variant["onHand"] or 0) - int(variant["reserved"] or 0))

    @staticmethod
    def reserve(db: Session, tenant_id: int, sku_id, branch_id: int, qty: int, reference_id: str):
        if qty <= 0:
            raise ValueError("Requested quantity must be greater than 0")
        RSERepository._validate_branch(db, tenant_id, int(branch_id))
        variant = RSERepository._variant(db, tenant_id, sku_id)
        if not variant:
            raise ValueError(f"Product SKU not found: {sku_id}")

        try:
            result = db.execute(
                text('''UPDATE "ProductVariant"
                        SET "reserved"=COALESCE("reserved",0)+:qty
                        WHERE "id"=:id AND "tenantId"=:tenant_id
                          AND COALESCE("onHand",0)-COALESCE("reserved",0)>=:qty'''),
                {"qty": qty, "id": variant["id"], "tenant_id": tenant_id},
            )
            if result.rowcount != 1:
                raise ValueError("Sản phẩm không đủ tồn kho khả dụng (Anti-Oversell)")

            updated = db.execute(
                text('''SELECT "onHand","reserved" FROM "ProductVariant"
                        WHERE "id"=:id AND "tenantId"=:tenant_id'''),
                {"id": variant["id"], "tenant_id": tenant_id},
            ).mappings().one()

            db.execute(
                text('''INSERT INTO "InventoryTransaction"
                        ("tenantId","branchId","skuId","type","quantity","balanceAfter","referenceId","createdAt")
                        VALUES (:tenant_id,:branch_id,:sku_id,'RESERVE',0,:balance_after,:reference_id,NOW())'''),
                {
                    "tenant_id": tenant_id,
                    "branch_id": int(branch_id),
                    "sku_id": variant["id"],
                    "balance_after": int(updated["onHand"] or 0),
                    "reference_id": reference_id,
                },
            )
            return {
                "skuId": variant["id"],
                "reservedQuantity": qty,
                "availableAfter": max(0, int(updated["onHand"] or 0) - int(updated["reserved"] or 0)),
            }
        except Exception:
            db.rollback()
            raise

    @staticmethod
    def release_reservation(db: Session, tenant_id: int, sku_id, branch_id: int, qty: int, reference_id: str):
        if qty <= 0:
            raise ValueError("Release quantity must be greater than 0")
        RSERepository._validate_branch(db, tenant_id, int(branch_id))
        variant = RSERepository._variant(db, tenant_id, sku_id)
        if not variant:
            raise ValueError("SKU not found")

        result = db.execute(
            text('''UPDATE "ProductVariant"
                    SET "reserved"=COALESCE("reserved",0)-:qty
                    WHERE "id"=:sku_id AND "tenantId"=:tenant_id
                      AND COALESCE("reserved",0)>=:qty'''),
            {"qty": qty, "sku_id": variant["id"], "tenant_id": tenant_id},
        )
        if result.rowcount != 1:
            raise ValueError("Cannot release reservation: reserved quantity is insufficient")

        current = db.execute(
            text('''SELECT "onHand" FROM "ProductVariant"
                    WHERE "id"=:sku_id AND "tenantId"=:tenant_id'''),
            {"sku_id": variant["id"], "tenant_id": tenant_id},
        ).scalar_one()
        db.execute(
            text('''INSERT INTO "InventoryTransaction"
                    ("tenantId","branchId","skuId","type","quantity","balanceAfter","referenceId","createdAt")
                    VALUES (:tenant_id,:branch_id,:sku_id,'RELEASE',0,:balance_after,:reference_id,NOW())'''),
            {
                "tenant_id": tenant_id,
                "branch_id": int(branch_id),
                "sku_id": variant["id"],
                "balance_after": int(current or 0),
                "reference_id": reference_id,
            },
        )

    # Compatibility helper used by older tests/integrations.
    @staticmethod
    def process_flash_sale_reservation(db: Session, tenant_id: int, sku_id, requested_qty: int):
        variant = RSERepository._variant(db, tenant_id, sku_id)
        if not variant:
            raise ValueError("Product SKU not found")
        available = int(variant["onHand"] or 0) - int(variant["reserved"] or 0)
        if requested_qty <= 0:
            raise ValueError("Requested quantity must be greater than 0")
        if available < requested_qty:
            raise ValueError("Sản phẩm không đủ tồn kho khả dụng (Anti-Oversell)")
        result = db.execute(
            text('''UPDATE "ProductVariant"
                    SET "reserved"=COALESCE("reserved",0)+:qty
                    WHERE "id"=:id AND "tenantId"=:tenant_id
                      AND COALESCE("onHand",0)-COALESCE("reserved",0)>=:qty'''),
            {"qty": requested_qty, "id": variant["id"], "tenant_id": tenant_id},
        )
        if result.rowcount != 1:
            raise ValueError("Sản phẩm không đủ tồn kho khả dụng (Anti-Oversell)")
        return {
            "message": "Giữ chỗ thành công",
            "reserved_quantity": requested_qty,
            "available_after": available - requested_qty,
        }
