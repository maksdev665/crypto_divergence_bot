from sqlalchemy import Column, Integer, String, Boolean
from app.database.base import BaseModel

class Admin(BaseModel):
    __tablename__ = 'admins'

    user_id = Column(Integer, unique=True, nullable=False)
    username = Column(String, nullable=True)
    is_superadmin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    def __repr__(self):
        return f"<Admin(user_id={self.user_id}, username={self.username})>"