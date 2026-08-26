import json
from sqlalchemy import text
from sqlalchemy.orm import Session


class ProductRepository:
    @staticmethod
    def _find_variant(db: Session, tenant_id: int, sku):
        value = str(sku).strip()
        numeric_id = int(value) if value.isdigit() else -1
        return db.execute(
            text('''SELECT * FROM "ProductVariant"
                    WHERE "tenantId"=:tenant_id
                      AND ("id"=:sku_id OR lower("sku")=lower(:sku))
                    LIMIT 1'''),
            {"tenant_id": tenant_id, "sku_id": numeric_id, "sku": value},
        ).mappings().first()

    @staticmethod
    def create_product_with_variants(db: Session, tenant_id: int, data: dict):
        variants = data.get("variants") or []
        if not variants:
            raise ValueError("At least one variant is required")

        seen = set()
        for v in variants:
            sku = v["sku"].strip()
            key = sku.lower()
            if not sku or key in seen:
                raise ValueError("SKU must be non-empty and unique in the request")
            if ProductRepository._find_variant(db, tenant_id, sku):
                raise ValueError(f"SKU already exists: {sku}")
            seen.add(key)

        try:
            product = db.execute(
                text('''INSERT INTO "Product"
                        ("tenantId","title","categoryId","brandId")
                        VALUES (:tenant_id,:title,:category_id,:brand_id)
                        RETURNING *'''),
                {
                    "tenant_id": tenant_id,
                    "title": data["title"].strip(),
                    "category_id": data.get("categoryId"),
                    "brand_id": data.get("brandId"),
                },
            ).mappings().first()
            if not product:
                raise ValueError("Cannot create product")

            for v in variants:
                db.execute(
                    text('''INSERT INTO "ProductVariant"
                            ("tenantId","productId","sku","barcode",
                             "retailPrice","wholesalePrice","attributes","cogs","onHand","reserved")
                            VALUES (:tenant_id,:product_id,:sku,:barcode,
                                    :retail_price,:wholesale_price,:attributes,0,0,0)'''),
                    {
                        "tenant_id": tenant_id,
                        "product_id": product["id"],
                        "sku": v["sku"].strip(),
                        "barcode": v.get("barcode"),
                        "retail_price": float(v.get("retailPrice", 0)),
                        "wholesale_price": float(v.get("wholesalePrice", 0)),
                        "attributes": json.dumps(v.get("attributes", {}), ensure_ascii=False),
                    },
                )

            rows = db.execute(
                text('''SELECT * FROM "ProductVariant"
                        WHERE "tenantId"=:tenant_id AND "productId"=:product_id
                        ORDER BY "id"'''),
                {"tenant_id": tenant_id, "product_id": product["id"]},
            ).mappings().all()
            db.commit()
            return {"product": dict(product), "variants": [dict(r) for r in rows]}
        except Exception:
            db.rollback()
            raise

    @staticmethod
    def get_products_by_tenant(db: Session, tenant_id: int):
        rows = db.execute(
            text('''SELECT p.*,COUNT(pv."id") AS "variantCount"
                    FROM "Product" p
                    LEFT JOIN "ProductVariant" pv
                      ON pv."productId"=p."id" AND pv."tenantId"=p."tenantId"
                    WHERE p."tenantId"=:tenant_id
                    GROUP BY p."id"
                    ORDER BY p."id" DESC'''),
            {"tenant_id": tenant_id},
        ).mappings().all()
        result = []
        for row in rows:
            item = dict(row)
            item["variants"] = [
                dict(v) for v in db.execute(
                    text('''SELECT * FROM "ProductVariant"
                            WHERE "tenantId"=:tenant_id AND "productId"=:product_id
                            ORDER BY "id"'''),
                    {"tenant_id": tenant_id, "product_id": row["id"]},
                ).mappings().all()
            ]
            result.append(item)
        return result
