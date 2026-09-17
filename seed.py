from decimal import Decimal
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.security import get_current_tenant_id
from app.repositories.auth_repo import AuthRepository


router = APIRouter(prefix="/seed", tags=["Demo Seed"])


@router.post("/demo")
def seed_demo_data(
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_current_tenant_id)
):
    """
    Create demo data for the current tenant.

    Creates:
    - 20 Products
    - 20 Product Variants
    - 20 Inventory transactions
    - 20 Orders
    - 20 POS orders

    The operation is idempotent:
    if demo products already exist, no duplicate data is created.
    """

    try:
        # ============================================================
        # 1. CHECK WHETHER DEMO DATA ALREADY EXISTS
        # ============================================================

        existing = db.execute(
            text("""
                SELECT COUNT(*)
                FROM "ProductVariant"
                WHERE "tenantId" = :tenant_id
                  AND "sku" LIKE 'DEMO-SKU-%'
            """),
            {"tenant_id": tenant_id}
        ).scalar()

        if existing and int(existing) > 0:
            return {
                "success": True,
                "message": "Demo data already exists for this tenant.",
                "created": False
            }

        # ============================================================
        # 2. FIND ACTIVE BRANCH
        # ============================================================

        branch = AuthRepository.get_default_branch(
            db,
            tenant_id
        )

        if not branch:
            raise ValueError(
                "No active branch found. Please create a branch first."
            )

        branch_id = int(branch.branchId)

        # ============================================================
        # 3. CREATE 20 PRODUCTS + 20 VARIANTS
        # ============================================================

        variants = []

        product_names = [
            "Áo thun Basic",
            "Áo polo Classic",
            "Áo sơ mi Oxford",
            "Quần jean Slim",
            "Quần kaki Regular",
            "Quần short Casual",
            "Váy chữ A",
            "Váy công sở",
            "Áo khoác Bomber",
            "Áo hoodie Basic",
            "Giày sneaker Classic",
            "Giày thể thao Runner",
            "Dép quai ngang",
            "Túi tote Canvas",
            "Balo thời trang",
            "Mũ lưỡi trai",
            "Thắt lưng da",
            "Ví da mini",
            "Áo len cổ tròn",
            "Quần jogger"
        ]

        for i, name in enumerate(product_names, start=1):

            product = db.execute(
                text("""
                    INSERT INTO "Product"
                        ("tenantId", "title", "categoryId", "brandId")
                    VALUES
                        (:tenant_id, :title, NULL, NULL)
                    RETURNING "id"
                """),
                {
                    "tenant_id": tenant_id,
                    "title": name
                }
            ).mappings().first()

            if not product:
                raise ValueError(
                    f"Cannot create demo product #{i}"
                )

            product_id = int(product["id"])

            sku = f"DEMO-SKU-{i:03d}"
            barcode = f"893000000{i:04d}"

            retail_price = Decimal("100000") + (
                Decimal(i) * Decimal("5000")
            )

            wholesale_price = Decimal("80000") + (
                Decimal(i) * Decimal("4000")
            )

            variant = db.execute(
                text("""
                    INSERT INTO "ProductVariant"
                        (
                            "tenantId",
                            "productId",
                            "sku",
                            "barcode",
                            "retailPrice",
                            "wholesalePrice",
                            "attributes",
                            "cogs",
                            "onHand",
                            "reserved"
                        )
                    VALUES
                        (
                            :tenant_id,
                            :product_id,
                            :sku,
                            :barcode,
                            :retail_price,
                            :wholesale_price,
                            '{}',
                            :cogs,
                            0,
                            0
                        )
                    RETURNING "id", "sku", "retailPrice"
                """),
                {
                    "tenant_id": tenant_id,
                    "product_id": product_id,
                    "sku": sku,
                    "barcode": barcode,
                    "retail_price": float(retail_price),
                    "wholesale_price": float(wholesale_price),
                    "cogs": float(wholesale_price)
                }
            ).mappings().first()

            if not variant:
                raise ValueError(
                    f"Cannot create demo variant #{i}"
                )

            variants.append(dict(variant))

        # ============================================================
        # 4. CREATE 20 INVENTORY IMPORT TRANSACTIONS
        # ============================================================

        for i, variant in enumerate(variants, start=1):

            quantity = 100

            import_price = (
                Decimal("50000") +
                Decimal(i * 2000)
            )

            sku_id = int(variant["id"])

            # Update stock + COGS
            db.execute(
                text("""
                    UPDATE "ProductVariant"
                    SET
                        "onHand" = COALESCE("onHand", 0) + :quantity,
                        "cogs" = :cogs
                    WHERE
                        "id" = :sku_id
                        AND "tenantId" = :tenant_id
                """),
                {
                    "quantity": quantity,
                    "cogs": float(import_price),
                    "sku_id": sku_id,
                    "tenant_id": tenant_id
                }
            )

            # Append-only inventory ledger
            db.execute(
                text("""
                    INSERT INTO "InventoryTransaction"
                        (
                            "tenantId",
                            "branchId",
                            "skuId",
                            "type",
                            "quantity",
                            "balanceAfter",
                            "referenceId",
                            "createdAt"
                        )
                    VALUES
                        (
                            :tenant_id,
                            :branch_id,
                            :sku_id,
                            'IMPORT',
                            :quantity,
                            :balance_after,
                            :reference_id,
                            NOW()
                        )
                """),
                {
                    "tenant_id": tenant_id,
                    "branch_id": branch_id,
                    "sku_id": sku_id,
                    "quantity": quantity,
                    "balance_after": quantity,
                    "reference_id": f"DEMO-IMPORT-{i:03d}"
                }
            )

        # ============================================================
        # 5. CREATE 20 ONLINE ORDERS
        # ============================================================

        for i, variant in enumerate(variants, start=1):

            sku_id = int(variant["id"])
            quantity = 2
            unit_price = Decimal(str(variant["retailPrice"]))
            total = unit_price * quantity

            order = db.execute(
                text("""
                    INSERT INTO "Order"
                        (
                            "tenantId",
                            "branchId",
                            "salesChannel",
                            "type",
                            "status",
                            "totalAmount",
                            "discount",
                            "finalAmount",
                            "createdAt"
                        )
                    VALUES
                        (
                            :tenant_id,
                            :branch_id,
                            'Website',
                            'ONLINE',
                            'PENDING',
                            :total,
                            0,
                            :total,
                            NOW()
                        )
                    RETURNING "orderId"
                """),
                {
                    "tenant_id": tenant_id,
                    "branch_id": branch_id,
                    "total": float(total)
                }
            ).mappings().first()

            order_id = int(order["orderId"])

            db.execute(
                text("""
                    INSERT INTO "OrderItem"
                        (
                            "orderId",
                            "tenantId",
                            "skuId",
                            "quantity",
                            "unitPrice",
                            "subTotal"
                        )
                    VALUES
                        (
                            :order_id,
                            :tenant_id,
                            :sku_id,
                            :quantity,
                            :unit_price,
                            :subtotal
                        )
                """),
                {
                    "order_id": order_id,
                    "tenant_id": tenant_id,
                    "sku_id": sku_id,
                    "quantity": quantity,
                    "unit_price": float(unit_price),
                    "subtotal": float(total)
                }
            )

        # ============================================================
        # 6. CREATE 20 POS SALES
        # ============================================================

        for i, variant in enumerate(variants, start=1):

            sku_id = int(variant["id"])
            quantity = 1
            unit_price = Decimal(str(variant["retailPrice"]))

            pos_order = db.execute(
                text("""
                    INSERT INTO "Order"
                        (
                            "tenantId",
                            "branchId",
                            "type",
                            "status",
                            "totalAmount",
                            "discount",
                            "finalAmount",
                            "paymentMethod",
                            "createdAt"
                        )
                    VALUES
                        (
                            :tenant_id,
                            :branch_id,
                            'POS',
                            'COMPLETED',
                            :total,
                            0,
                            :total,
                            :payment_method,
                            NOW()
                        )
                    RETURNING "orderId"
                """),
                {
                    "tenant_id": tenant_id,
                    "branch_id": branch_id,
                    "total": float(unit_price),
                    "payment_method": (
                        "Cash"
                        if i % 3 == 1
                        else "Card"
                        if i % 3 == 2
                        else "QR"
                    )
                }
            ).mappings().first()

            order_id = int(pos_order["orderId"])

            # Reduce stock
            updated = db.execute(
                text("""
                    UPDATE "ProductVariant"
                    SET "onHand" = COALESCE("onHand", 0) - :quantity
                    WHERE
                        "id" = :sku_id
                        AND "tenantId" = :tenant_id
                        AND COALESCE("onHand", 0)
                            - COALESCE("reserved", 0) >= :quantity
                """),
                {
                    "quantity": quantity,
                    "sku_id": sku_id,
                    "tenant_id": tenant_id
                }
            )

            if updated.rowcount != 1:
                raise ValueError(
                    f"Insufficient stock for demo POS SKU {sku_id}"
                )

            db.execute(
                text("""
                    INSERT INTO "OrderItem"
                        (
                            "orderId",
                            "skuId",
                            "tenantId",
                            "quantity",
                            "unitPrice",
                            "subTotal"
                        )
                    VALUES
                        (
                            :order_id,
                            :sku_id,
                            :tenant_id,
                            :quantity,
                            :unit_price,
                            :subtotal
                        )
                """),
                {
                    "order_id": order_id,
                    "sku_id": sku_id,
                    "tenant_id": tenant_id,
                    "quantity": quantity,
                    "unit_price": float(unit_price),
                    "subtotal": float(unit_price)
                }
            )

            # Current balance after POS sale
            balance = db.execute(
                text("""
                    SELECT "onHand"
                    FROM "ProductVariant"
                    WHERE
                        "id" = :sku_id
                        AND "tenantId" = :tenant_id
                """),
                {
                    "sku_id": sku_id,
                    "tenant_id": tenant_id
                }
            ).scalar_one()

            # Append-only SALE ledger
            db.execute(
                text("""
                    INSERT INTO "InventoryTransaction"
                        (
                            "tenantId",
                            "branchId",
                            "skuId",
                            "type",
                            "quantity",
                            "balanceAfter",
                            "referenceId",
                            "createdAt"
                        )
                    VALUES
                        (
                            :tenant_id,
                            :branch_id,
                            :sku_id,
                            'SALE',
                            :quantity,
                            :balance_after,
                            :reference_id,
                            NOW()
                        )
                """),
                {
                    "tenant_id": tenant_id,
                    "branch_id": branch_id,
                    "sku_id": sku_id,
                    "quantity": -quantity,
                    "balance_after": int(balance or 0),
                    "reference_id": f"DEMO-POS-{i:03d}"
                }
            )

        # ============================================================
        # 7. COMMIT EVERYTHING
        # ============================================================

        db.commit()

        return {
            "success": True,
            "message": "Demo data created successfully.",
            "created": True,
            "data": {
                "products": 20,
                "variants": 20,
                "inventory_transactions": 40,
                "orders": 20,
                "pos_orders": 20
            }
        }

    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )

    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create demo data: {str(exc)}"
        )