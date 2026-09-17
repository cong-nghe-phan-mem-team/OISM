from sqlalchemy import Column, Integer, String, ForeignKey
from app.database import Base


class User(Base):
    __tablename__ = "users"

    userId = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    phone = Column(String, nullable=True)
    passwordHash = Column(String, nullable=False)
    fullName = Column(String, nullable=True)
    tenantId = Column(Integer, ForeignKey("tenants.tenantId"), nullable=False)
    roleId = Column(Integer, ForeignKey("roles.roleId"), nullable=True)
