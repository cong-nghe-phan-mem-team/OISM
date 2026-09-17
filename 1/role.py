from sqlalchemy import Column, Integer, String
from app.database import Base

class Role(Base):
    __tablename__ = "roles"
    roleId = Column(Integer, primary_key=True)
    roleName = Column(String, unique=True, nullable=False)
    permissions = Column(String, nullable=True)
