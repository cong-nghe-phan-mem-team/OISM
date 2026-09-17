from pydantic import BaseModel
from typing import List

class RevenueReportResponse(BaseModel):
    total_revenue: float
    total_cogs: float
    gross_profit: float

class InventoryValueItem(BaseModel):
    sku: str
    quantity: int
    total_value: float
    status: str

class LowStockAlertItem(BaseModel):
    sku: str
    quantity: int
    reorder_level: int