from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from app.database import Base

class Branch(Base):
    __tablename__ = "branches"
    branchId = Column(Integer, primary_key=True)
    branchName = Column(String, nullable=False)
    address = Column(String, nullable=True)
    isActive = Column(Boolean, nullable=False, default=True)
    tenantId = Column(Integer, ForeignKey('tenants.tenantId'), nullable=False)
