import time
from typing import Any, Dict, Optional
from prisma import Prisma
from prisma.enums import LedgerType

# Khởi tạo instance Prisma
db = Prisma()


class InventoryService:
    # FR-INV-01 & FR-INV-02: Record Inventory Ledger and calculate Weighted Average Cost (WAC)
    @staticmethod
    async def create_purchase_receipt(
        tenant_id: str, 
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        import_quantity = data.get("importQuantity", 0)[cite: 4]
        import_unit_price = data.get("importUnitPrice", 0)[cite: 4]
        branch_id = data.get("branchId")[cite: 4]
        sku_id = data.get("skuId")[cite: 4]
        reference_id = data.get("referenceId")[cite: 4]

        if import_quantity <= 0:
            raise ValueError("Quantity must be greater than 0")[cite: 4]

        # Thực thi Transaction trong Prisma Python
        async with db.tx() as tx:
            # Lấy thông tin SKU hiện tại
            variant = await tx.productvariant.find_first(
                where={"id": sku_id, "tenantId": tenant_id}[cite: 4]
            )
            if not variant:
                raise ValueError("Product SKU not found")[cite: 4]

            # Lấy giao dịch gần nhất của SKU tại chi nhánh này
            last_ledger = await tx.inventorytransaction.find_first(
                where={
                    "tenantId": tenant_id,
                    "branchId": branch_id,
                    "skuId": sku_id,
                },[cite: 4]
                order={"createdAt": "desc"},[cite: 4]
            )

            current_balance = last_ledger.balanceAfter if last_ledger else 0[cite: 4]
            new_balance = current_balance + import_quantity[cite: 4]

            # Tính Giá vốn bình quân gia quyền (WAC)
            current_cogs = variant.cogs if variant.cogs is not None else 0.0[cite: 4]
            new_cogs = (
                (current_balance * current_cogs)
                + (import_quantity * import_unit_price)
            ) / new_balance[cite: 4]

            # Cập nhật COGS mới cho Variant
            await tx.productvariant.update(
                where={"id": variant.id}, data={"cogs": new_cogs}[cite: 4]
            )

            # Ghi lịch sử kho (Append-Only Inventory Ledger)
            ref_id = reference_id or f"IMPORT-{int(time.time() * 1000)}"[cite: 4]
            ledger_entry = await tx.inventorytransaction.create(
                data={
                    "tenantId": tenant_id,[cite: 4]
                    "branchId": branch_id,[cite: 4]
                    "skuId": sku_id,[cite: 4]
                    "type": LedgerType.IMPORT,[cite: 4]
                    "quantity": import_quantity,[cite: 4]
                    "balanceAfter": new_balance,[cite: 4]
                    "referenceId": ref_id,[cite: 4]
                }
            )

            return {
                "ledgerEntry": ledger_entry,
                "updatedCogs": new_cogs,
                "currentStock": new_balance,
            }[cite: 4]

    @staticmethod
    async def get_ledger_history(tenant_id: str, sku_id: Optional[str] = None):
        where_clause = {"tenantId": tenant_id}[cite: 4]
        if sku_id:
            where_clause["skuId"] = sku_id[cite: 4]

        return await db.inventorytransaction.find_many(
            where=where_clause,[cite: 4]
            include={"variant": True, "branch": True},[cite: 4]
            order={"createdAt": "desc"},[cite: 4]
        )