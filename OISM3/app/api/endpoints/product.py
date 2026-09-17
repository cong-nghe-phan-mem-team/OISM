from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.product import ProductCreateRequest
from app.services.product_service import ProductService
from app.security import get_current_tenant_id

router = APIRouter(prefix="/products", tags=["Product Catalog"])


@router.post("")
def create_new_product(request: ProductCreateRequest, db: Session = Depends(get_db), tenant_id: int = Depends(get_current_tenant_id)):
    try:
        return {"success": True, "message": "Product created successfully", "data": ProductService.create_product(db, tenant_id, request)}
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception:
        raise HTTPException(500, "Cannot create product")


@router.get("")
def list_products(db: Session = Depends(get_db), tenant_id: int = Depends(get_current_tenant_id)):
    try:
        return {"success": True, "data": ProductService.get_products(db, tenant_id)}
    except Exception:
        raise HTTPException(500, "Cannot load products")
