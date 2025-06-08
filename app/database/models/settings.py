from sqlalchemy import Column, String, Integer, Boolean, Float, JSON
from app.database.base import BaseModel

class BotSettings(BaseModel):
    __tablename__ = 'bot_settings'

    key = Column(String, unique=True, nullable=False)
    value = Column(String, nullable=True)
    value_int = Column(Integer, nullable=True)
    value_bool = Column(Boolean, nullable=True)
    value_float = Column(Float, nullable=True)
    value_json = Column(JSON, nullable=True)
    description = Column(String, nullable=True)
    
    def __repr__(self):
        return f"<BotSettings(key={self.key})>"