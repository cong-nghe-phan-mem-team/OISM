from fastapi import APIRouter
from app.api.endpoints import (
    auth, cost, inventory, order, pos, product, report, rse, webhook, seed
)

# Khởi tạo Router tổng
api_router = APIRouter()

# Nhúng các Router con vào Router tổng.
# Mỗi router con đã tự khai báo prefix riêng (vd: auth.router có prefix="/auth"),
# nên KHÔNG truyền lại prefix ở đây nữa — tránh bị lặp path kiểu /auth/auth/....
api_router.include_router(auth.router, tags=["Authentication"])
api_router.include_router(product.router, tags=["Product Catalog"])
api_router.include_router(inventory.router, tags=["Inventory & Ledger"])
api_router.include_router(cost.router, tags=["Cost Management"])
api_router.include_router(rse.router, tags=["Anti-Oversell"])
api_router.include_router(order.router, tags=["Order Hub"])
api_router.include_router(pos.router, tags=["Point of Sale"])
api_router.include_router(report.router, tags=["Analytics & Reports"])
api_router.include_router(webhook.router, tags=["Integration & Notifications"])
api_router.include_router(seed.router, tags=["Demo Seed"])