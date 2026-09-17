from sqlalchemy.orm import Session
from app.repositories.report_repo import ReportRepository


class ReportService:
    @staticmethod
    def generate_revenue_report(db: Session, tenant_id: int):
        rows = ReportRepository.get_sales_data(db, tenant_id)
        revenue = sum(float(r["finalAmount"] or 0) for r in rows)
        cogs = sum(float(r["estimatedCogs"] or 0) for r in rows)
        return {
            "total_revenue": round(revenue, 2),
            "total_cogs": round(cogs, 2),
            "gross_profit": round(revenue - cogs, 2),
            "note": "COGS là ước tính theo COGS hiện tại của SKU vì OrderItem không có cột CostPrice trong schema Supabase hiện tại.",
        }

    @staticmethod
    def generate_inventory_report(db: Session, tenant_id: int):
        report = []
        for item in ReportRepository.get_inventory_data(db, tenant_id):
            qty = float(item["onHand"] or 0)
            reserved = float(item["reserved"] or 0)
            reorder = int(item["reorderLevel"] or 5)
            available = max(0, qty - reserved)
            report.append({
                "sku": item["sku"],
                "quantity": int(qty) if qty.is_integer() else qty,
                "reserved": int(reserved) if reserved.is_integer() else reserved,
                "available": int(available) if available.is_integer() else available,
                "total_value": round(qty * float(item["cogs"] or 0), 2),
                "status": "SẮP HẾT" if available <= reorder else "BÌNH THƯỜNG",
            })
        return report

    @staticmethod
    def get_low_stock_alerts(db: Session, tenant_id: int):
        result = []
        for item in ReportRepository.get_inventory_data(db, tenant_id):
            available = max(0, float(item["onHand"] or 0) - float(item["reserved"] or 0))
            reorder = int(item["reorderLevel"] or 5)
            if available <= reorder:
                result.append({
                    "sku": item["sku"],
                    "quantity": int(available) if available.is_integer() else available,
                    "reorder_level": reorder,
                })
        return result
