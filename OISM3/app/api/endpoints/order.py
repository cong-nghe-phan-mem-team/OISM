from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.order import CreateOrderRequest
from app.services.order_service import OrderService
from app.security import get_current_tenant_id

router = APIRouter(prefix="/orders", tags=["Order Hub"])


@router.get("")
def list_orders(limit: int = 100, db: Session = Depends(get_db), tenant_id: int = Depends(get_current_tenant_id)):
    return {"success": True, "data": OrderService.list_orders(db, tenant_id, limit)}


@router.post("")
def create_order(payload: CreateOrderRequest, db: Session = Depends(get_db), tenant_id: int = Depends(get_current_tenant_id)):
    try:
        order_id = OrderService.create_new_order(db, tenant_id, payload)
        return {"success": True, "order_id": order_id, "status": "PENDING"}
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception:
        raise HTTPException(500, "Cannot create order")


@router.get("/{order_id}")
def get_order(order_id: int, db: Session = Depends(get_db), tenant_id: int = Depends(get_current_tenant_id)):
    try:
        return {"success": True, "data": OrderService.get_order(db, tenant_id, order_id)}
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.post("/{order_id}/{action}")
def process_order_action(order_id: int, action: str, db: Session = Depends(get_db), tenant_id: int = Depends(get_current_tenant_id)):
    if action not in {"reserve", "confirm", "cancel", "pos_checkout"}:
        raise HTTPException(404, "Action not found")
    try:
        return {
            "success": True,
            "message": f"Action '{action}' executed for order {order_id}.",
            "data": OrderService.execute_order_action(db, tenant_id, action, order_id),
        }
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception:
        raise HTTPException(500, "Order action failed")
