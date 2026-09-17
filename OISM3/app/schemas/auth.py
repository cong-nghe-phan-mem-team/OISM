from pydantic import BaseModel, EmailStr

class RegisterTenantRequest(BaseModel):
    tenantName: str
    ownerEmail: EmailStr
    password: str
    fullName: str
    phone: str | None = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str