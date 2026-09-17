from sqlalchemy import Column, Integer, String, DateTime
from app.database import Base

class Tenant(Base):
    __tablename__ = "tenants"
    tenantId = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    status = Column(String, nullable=False)
    createdAt = Column(DateTime(timezone=True), nullable=False)
