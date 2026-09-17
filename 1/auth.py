from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.auth import RegisterTenantRequest, LoginRequest
from app.services.auth_service import AuthService
from app.repositories.auth_repo import AuthRepository
from app.security import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register")
def register(
    request: RegisterTenantRequest,
    db: Session = Depends(get_db)
):
    try:
        return {
            "message": "Register successfully",
            "data": AuthService.register_tenant(db, request.model_dump())
        }

    except ValueError as e:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception as e:
        db.rollback()
        print("REGISTER ERROR:", repr(e))
        raise HTTPException(
            status_code=500,
            detail=f"Registration failed: {str(e)}"
        )


@router.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    try:
        return AuthService.login(db, request.email, request.password)
    except ValueError as e:
        raise HTTPException(401, str(e))
    except Exception as e:
        db.rollback()
        print("LOGIN ERROR:", repr(e))
        raise HTTPException(500, "Login failed")


@router.get("/me")
def me(user=Depends(get_current_user), db: Session = Depends(get_db)):
    branch = AuthRepository.get_default_branch(db, user.tenantId)
    return {
        "userId": user.userId,
        "email": user.email,
        "fullName": user.fullName,
        "tenantId": user.tenantId,
        "roleId": user.roleId,
        "branchId": branch.branchId if branch else None,
    }
