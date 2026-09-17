from datetime import datetime, timedelta, timezone
from typing import Any, Optional
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from app.config import settings
from app.database import get_db
from app.repositories.auth_repo import AuthRepository

bearer = HTTPBearer(auto_error=False)


def create_access_token(user: Any, branch_id: Optional[int] = None) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user.userId),
        "userId": int(user.userId),
        "tenantId": int(user.tenantId),
        "roleId": getattr(user, "roleId", None),
        "branchId": int(branch_id) if branch_id is not None else None,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=settings.JWT_EXPIRE_HOURS)).timestamp()),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")


def get_current_claims(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)):
    if not credentials:
        raise HTTPException(status_code=401, detail="Authentication required")
    try:
        return jwt.decode(credentials.credentials, settings.JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_current_user(claims: dict = Depends(get_current_claims), db: Session = Depends(get_db)):
    try:
        user_id = int(claims["userId"])
        tenant_id = int(claims["tenantId"])
    except (KeyError, TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid authentication claims")

    user = AuthRepository.get_user_by_id(db, user_id)
    if not user or int(user.tenantId) != tenant_id:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def get_current_tenant_id(claims: dict = Depends(get_current_claims)) -> int:
    try:
        return int(claims["tenantId"])
    except (KeyError, TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Tenant context missing")


def get_current_branch_id(claims: dict = Depends(get_current_claims), db: Session = Depends(get_db)) -> int:
    branch_id = claims.get("branchId")
    tenant_id = claims.get("tenantId")
    try:
        tenant_id = int(tenant_id)
    except (TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Tenant context missing")

    branch = AuthRepository.get_default_branch(
        db, tenant_id, int(branch_id) if branch_id is not None else None
    )
    if not branch:
        raise HTTPException(status_code=400, detail="No active branch found for this tenant")
    return int(branch.branchId)
