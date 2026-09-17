import passlib.hash as passlib_hash
from sqlalchemy.orm import Session
from app.repositories.auth_repo import AuthRepository
from app.security import create_access_token


class AuthService:
    @staticmethod
    def register_tenant(db: Session, data: dict):
        tenant_name = data["tenantName"].strip()
        owner_email = str(data["ownerEmail"]).strip().lower()
        full_name = data["fullName"].strip()
        if not tenant_name:
            raise ValueError("Tenant name is required")
        if not full_name:
            raise ValueError("Full name is required")
        if AuthRepository.get_user_by_email(db, owner_email):
            raise ValueError("Email already exists")
        if len(data["password"]) < 6:
            raise ValueError("Password must contain at least 6 characters")

        result = AuthRepository.create_tenant_and_owner(
            db,
            tenant_name,
            owner_email,
            passlib_hash.bcrypt.hash(data["password"]),
            full_name,
            data.get("phone"),
        )
        tenant = result["tenant"]
        owner = result["owner"]
        branch = result.get("defaultBranch")
        return {
            "tenantId": tenant.tenantId,
            "userId": owner.userId,
            "branchId": branch.branchId if branch else None,
            "email": owner.email,
        }

    @staticmethod
    def login(db: Session, email: str, password: str):
        user = AuthRepository.get_user_by_email(db, email)
        if not user:
            raise ValueError("Invalid email or password")
        tenant = AuthRepository.get_tenant(db, user.tenantId)
        if not tenant or str(tenant.status).upper() != "ACTIVE":
            raise ValueError("Tenant is inactive")
        try:
            valid = passlib_hash.bcrypt.verify(password, user.passwordHash)
        except Exception:
            valid = False
        if not valid:
            raise ValueError("Invalid email or password")

        branch = AuthRepository.get_default_branch(db, user.tenantId)
        branch_id = branch.branchId if branch else None
        token = create_access_token(user, branch_id=branch_id)
        return {
            "access_token": token,
            "token": token,
            "token_type": "bearer",
            "user": {
                "userId": user.userId,
                "email": user.email,
                "fullName": user.fullName,
                "roleId": user.roleId,
                "tenantId": user.tenantId,
                "branchId": branch_id,
            },
        }
