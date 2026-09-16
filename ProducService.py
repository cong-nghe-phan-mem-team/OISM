from typing import Any, Dict, List, Optional
from prisma import Prisma

# Khởi tạo Prisma Client
db = Prisma()


class ProductService:
    @staticmethod
    async def create_product(tenant_id: str, data: Dict[str, Any]):
        async with db.tx() as tx:
            # Tạo sản phẩm chính
            product = await tx.product.create(
                data={
                    "tenantId": tenant_id,[cite: 6]
                    "title": data["title"],[cite: 6]
                    "categoryId": data.get("categoryId"),[cite: 6]
                    "brandId": data.get("brandId"),[cite: 6]
                }
            )

            # Chuẩn bị dữ liệu danh sách biến thể (variants)
            variants_data = [
                {
                    "tenantId": tenant_id,[cite: 6]
                    "productId": product.id,[cite: 6]
                    "sku": v["sku"],[cite: 6]
                    "barcode": v.get("barcode"),[cite: 6]
                    "retailPrice": v["retailPrice"],[cite: 6]
                    "wholesalePrice": v.get("wholesalePrice", 0),[cite: 6]
                    "attributes": v.get("attributes", {}),[cite: 6]
                }
                for v in data.get("variants", [])[cite: 6]
            ]

            # Tạo nhiều biến thể cùng lúc
            await tx.productvariant.create_many(data=variants_data)[cite: 6]

            # Trả về thông tin sản phẩm kèm các quan hệ liên quan
            return await tx.product.find_unique(
                where={"id": product.id},[cite: 6]
                include={"variants": True, "category": True, "brand": True},[cite: 6]
            )

    @staticmethod
    async def get_products(tenant_id: str):
        return await db.product.find_many(
            where={"tenantId": tenant_id},[cite: 6]
            include={"variants": True, "category": True, "brand": True},[cite: 6]
        )