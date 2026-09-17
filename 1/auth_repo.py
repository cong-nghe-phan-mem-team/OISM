from types import SimpleNamespace
from typing import Optional, Dict, Any
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


def _obj(row):
    return SimpleNamespace(**dict(row)) if row else None


class AuthRepository:
    """Repository for the INTEGER/camelCase schema that is actually present.

    The UUID/snake_case tables in the same Supabase project are a separate,
    incomplete schema: their auth_tenant_id() function expects users.auth_user_id
    and users.tenant_id, while the real users table has userId/tenantId and no
    auth_user_id. This application therefore deliberately targets the existing
    legacy OISM tables and does not alter the Supabase schema.
    """

    @staticmethod
    def get_user_by_email(db: Session, email: str):
        row = db.execute(
            text('SELECT * FROM users WHERE lower(email)=lower(:email) LIMIT 1'),
            {"email": email.strip()},
        ).mappings().first()
        return _obj(row)

    @staticmethod
    def get_user_by_id(db: Session, user_id: int):
        row = db.execute(
            text('SELECT * FROM users WHERE "userId"=:user_id LIMIT 1'),
            {"user_id": user_id},
        ).mappings().first()
        return _obj(row)

    @staticmethod
    def get_tenant(db: Session, tenant_id: int):
        row = db.execute(
            text('SELECT * FROM tenants WHERE "tenantId"=:tenant_id LIMIT 1'),
            {"tenant_id": tenant_id},
        ).mappings().first()
        return _obj(row)

    @staticmethod
    def get_default_branch(db: Session, tenant_id: int, preferred_branch_id: Optional[int] = None):
        if preferred_branch_id is not None:
            row = db.execute(
                text('''SELECT * FROM branches
                        WHERE "tenantId"=:tenant_id
                          AND "branchId"=:branch_id
                          AND "isActive"=TRUE
                        LIMIT 1'''),
                {"tenant_id": tenant_id, "branch_id": preferred_branch_id},
            ).mappings().first()
            if row:
                return _obj(row)

        row = db.execute(
            text('''SELECT * FROM branches
                    WHERE "tenantId"=:tenant_id AND "isActive"=TRUE
                    ORDER BY "branchId" ASC LIMIT 1'''),
            {"tenant_id": tenant_id},
        ).mappings().first()
        return _obj(row)

    @staticmethod
    def validate_branch(db: Session, tenant_id: int, branch_id: int):
        row = db.execute(
            text('''SELECT * FROM branches
                    WHERE "tenantId"=:tenant_id
                      AND "branchId"=:branch_id
                      AND "isActive"=TRUE
                    LIMIT 1'''),
            {"tenant_id": tenant_id, "branch_id": branch_id},
        ).mappings().first()
        return _obj(row)

    @staticmethod
    def create_tenant_and_owner(
        db: Session,
        tenant_name: str,
        owner_email: str,
        hashed_password: str,
        full_name: str,
        phone: Optional[str] = None,
    ) -> Dict[str, Any]:
        try:
            tenant = db.execute(
                text('''INSERT INTO tenants (name,status)
                        VALUES (:name,'ACTIVE') RETURNING *'''),
                {"name": tenant_name.strip()},
            ).mappings().first()
            if not tenant:
                raise ValueError("Cannot create tenant")

            role = db.execute(
                text('''SELECT * FROM roles WHERE lower("roleName")='owner' LIMIT 1''')
            ).mappings().first()
            if not role:
                role = db.execute(
                    text('''INSERT INTO roles ("roleName",permissions)
                            VALUES ('OWNER','ALL') RETURNING *''')
                ).mappings().first()

            branch = db.execute(
                text('''INSERT INTO branches
                        ("branchName",address,"isActive","tenantId")
                        VALUES ('Kho/Chi nhánh chính',NULL,TRUE,:tenant_id)
                        RETURNING *'''),
                {"tenant_id": tenant["tenantId"]},
            ).mappings().first()

            owner = db.execute(
                text('''INSERT INTO users
                        (email,phone,"passwordHash","fullName","tenantId","roleId")
                        VALUES (:email,:phone,:password_hash,:full_name,:tenant_id,:role_id)
                        RETURNING *'''),
                {
                    "email": owner_email.lower().strip(),
                    "phone": phone,
                    "password_hash": hashed_password,
                    "full_name": full_name.strip(),
                    "tenant_id": tenant["tenantId"],
                    "role_id": role["roleId"] if role else None,
                },
            ).mappings().first()
            if not owner:
                raise ValueError("Cannot create owner")

            db.commit()
            return {"tenant": _obj(tenant), "owner": _obj(owner), "defaultBranch": _obj(branch)}
        except IntegrityError as exc:
            db.rollback()
            raise ValueError("Email already exists or a unique constraint was violated") from exc
        except Exception:
            db.rollback()
            raise
