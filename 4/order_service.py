from sqlalchemy.orm import Session
from app.schemas.order import CreateOrderRequest
from app.repositories.order_repo import OrderRepository


class OrderService:
    @staticmethod
    def create_new_order(db: Session, tenant_id: int, payload: CreateOrderRequest):
        return OrderRepository.insert_order(
            db,
            tenant_id,
            {
                "branchId": int(payload.branch_id),
                "salesChannel": payload.sales_channel,
            },
            [
                {
                    "skuId": i.sku_id,
                    "quantity": i.quantity,
                    "unitPrice": i.unit_price,
                }
                for i in payload.items
            ],
        )

    @staticmethod
    def get_order(db: Session, tenant_id: int, order_id: int):
        order, items = OrderRepository.get_order(db, tenant_id, order_id)
        return {"order": order, "items": items}

    @staticmethod
    def list_orders(db: Session, tenant_id: int, limit: int = 100):
        return OrderRepository.list_orders(db, tenant_id, limit)

    @staticmethod
    def execute_order_action(db: Session, tenant_id: int, action: str, order_id: int):
        return OrderRepository.update_order_status(db, tenant_id, order_id, action)
