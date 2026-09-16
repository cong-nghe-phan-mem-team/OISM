import os
import time
from typing import Any, Dict
from prisma import Prisma
import passlib.hash as passlib_hash
import jwt

# Khởi tạo Prisma Client
db = Prisma()


class AuthService:
    @staticmethod
    async def register_tenant(data: Dict[str, Any]) -> Dict[str, Any]:
        # Kiểm tra email đã tồn tại chưa
        existing_user = await db.user.find_unique(where={"email": data["ownerEmail"]})[cite: 5]
        if existing_user:
            raise ValueError("Email already exists")[cite: 5]

        # Mã hóa mật khẩu với bcrypt
        hashed_password = passlib_hash.bcrypt.hash(data["password"])[cite: 5]

        # Thực thi transaction
        async with db.tx() as tx:
            tenant = await tx.tenant.create(
                data={"name": data["tenantName"]}[cite: 5]
            )

            owner = await tx.user.create(
                data={
                    "tenantId": tenant.id,[cite: 5]
                    "email": data["ownerEmail"],[cite: 5]
                    "passwordHash": hashed_password,[cite: 5]
                    "fullName": data["fullName"],[cite: 5]
                    "phone": data.get("phone"),[cite: 5]
                    "role": "OWNER"[cite: 5]
                }
            )

            default_branch = await tx.branch.create(
                data={
                    "tenantId": tenant.id,[cite: 5]
                    "name": "Kho/Chi nhánh chính",[cite: 5]
                    "code": "MAIN"[cite: 5]
                }
            )

            return {
                "tenant": tenant,
                "owner": owner,
                "defaultBranch": default_branch
            }[cite: 5]

    @staticmethod
    async def login(email: str, password: str) -> Dict[str, Any]:
        # Tìm người dùng theo email
        user = await db.user.find_unique(where={"email": email})[cite: 5]
        if not user:
            raise ValueError("Invalid email or password")[cite: 5]

        # Kiểm tra mật khẩu
        is_match = passlib_hash.bcrypt.verify(password, user.passwordHash)[cite: 5]
        if not is_match:
            raise ValueError("Invalid email or password")[cite: 5]

        # Tạo JWT token
        jwt_secret = os.getenv("JWT_SECRET", "secret")[cite: 5]
        payload = {
            "userId": user.id,[cite: 5]
            "tenantId": user.tenantId,[cite: 5]
            "role": user.role,[cite: 5]
            "exp": int(time.time()) + (24 * 3600)  # Hạn dùng 1 ngày[cite: 5]
        }
        token = jwt.encode(payload, jwt_secret, algorithm="HS256")

        return {
            "token": token,
            "user": {
                "id": user.id,[cite: 5]
                "email": user.email,[cite: 5]
                "fullName": user.fullName,[cite: 5]
                "role": user.role,[cite: 5]
                "tenantId": user.tenantId[cite: 5]
            }
        }[cite: 5]