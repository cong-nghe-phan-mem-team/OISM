from decimal import Decimal
from typing import Optional
import time
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.repositories.auth_repo import AuthRepository


class InventoryRepository:
    @staticmethod
    def resolve_variant(db: Session, tenant_id: int, sku, for_update: bool = False):
        value = str(sku).strip()
        numeric_id = int(value) if value.isdigit() else -1
        lock_clause = " FOR UPDATE" if (
            for_update
            and getattr(getattr(db, "bind", None), "dialect", None)
            and db.bind.dialect.name == "postgresql"
        ) else ""
        sql = ('SELECT * FROM "ProductVariant" '
               'WHERE "tenantId"=:tenant_id '
               'AND ("sku"=:sku OR "id"=:sku_id) '
               'LIMIT 1' + lock_clause)
        return db.execute(
            text(sql),
            {"tenant_id": tenant_id, "sku": value, "sku_id": numeric_id},
        ).mappings().first()

    @staticmethod
    def validate_branch(db: Session, tenant_id: int, branch_id: int):
        if not AuthRepository.validate_branch(db, tenant_id, branch_id):
            raise ValueError("Branch not found or inactive")

    @staticmethod
    def process_purchase_receipt_tx(
        db: Session,
        tenant_id: int,
        branch_id: int,
        sku_id,
        import_qty: int,
        import_price: Decimal,
        ref_id: Optional[str],
    ):
        InventoryRepository.validate_branch(db, tenant_id, branch_id)
        # Lock the SKU row on PostgreSQL before calculating WAC. SQLite/local
        # mocks use the normal SELECT because they do not support FOR UPDATE.
        variant = InventoryRepository.resolve_variant(db, tenant_id, sku_id, for_update=True)
        if not variant:
            raise ValueError(f"Product SKU not found: {sku_id}")

        current_stock = int(variant["onHand"] or 0)
        current_cogs = Decimal(str(variant["cogs"] or 0))
        import_price = Decimal(str(import_price))
        new_stock = current_stock + int(import_qty)
        new_cogs = (
            ((Decimal(current_stock) * current_cogs) + (Decimal(import_qty) * import_price))
            / Decimal(new_stock)
            if new_stock else Decimal("0")
        ).quantize(Decimal("0.01"))

        try:
            db.execute(
                text('''UPDATE "ProductVariant"
                        SET "onHand"=:stock,"cogs"=:cogs
                        WHERE "id"=:sku_id AND "tenantId"=:tenant_id'''),
                {
                    "stock": new_stock,
                    "cogs": float(new_cogs),
                    "sku_id": variant["id"],
                    "tenant_id": tenant_id,
                },
            )

            reference_id = ref_id or f"IMPORT-{int(time.time()*1000)}"
            entry = db.execute(
                text('''INSERT INTO "InventoryTransaction"
                        ("tenantId","branchId","skuId","type","quantity","balanceAfter","referenceId","createdAt")
                        VALUES (:tenant_id,:branch_id,:sku_id,'IMPORT',:quantity,:balance_after,:reference_id,NOW())
                        RETURNING *'''),
                {
                    "tenant_id": tenant_id,
                    "branch_id": branch_id,
                    "sku_id": variant["id"],
                    "quantity": int(import_qty),
                    "balance_after": new_stock,
                    "reference_id": reference_id,
                },
            ).mappings().first()
            db.commit()
            return {
                "ledgerEntry": dict(entry),
                "updatedCogs": float(new_cogs),
                "currentStock": new_stock,
                "skuId": variant["id"],
            }
        except Exception:
            db.rollback()
            raise

    @staticmethod
    def get_ledger(db: Session, tenant_id: int, sku_id=None, branch_id=None):
        sql = '''SELECT it.*,pv."sku"
                 FROM "InventoryTransaction" it
                 JOIN "ProductVariant" pv
                   ON pv."id"=it."skuId" AND pv."tenantId"=it."tenantId"
                 WHERE it."tenantId"=:tenant_id'''
        params = {"tenant_id": tenant_id}
        if sku_id is not None:
            value = str(sku_id).strip()
            sql += ' AND (it."skuId"=:sku_id OR pv."sku"=:sku)'
            params.update({"sku_id": int(value) if value.isdigit() else -1, "sku": value})
        if branch_id is not None:
            sql += ' AND it."branchId"=:branch_id'
            params["branch_id"] = int(branch_id)
        sql += ' ORDER BY it."createdAt" DESC,it."id" DESC'
        return [dict(r) for r in db.execute(text(sql), params).mappings().all()]
