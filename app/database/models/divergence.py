from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Text, Integer, Boolean
from sqlalchemy.orm import relationship 
from app.database.base import BaseModel
from datetime import datetime, timezone

def utcnow():
    return datetime.now(timezone.utc)

class Divergence(BaseModel):
    __tablename__ = 'divergences'

    pair1_id = Column(Integer, ForeignKey('currency_pairs.id'))
    pair2_id = Column(Integer, ForeignKey('currency_pairs.id'))
    pair1_symbol = Column(String, nullable=False)
    pair2_symbol = Column(String, nullable=False)
    pair1_price = Column(Float, nullable=False)
    pair2_price = Column(Float, nullable=False)
    divergence_percent = Column(Float, nullable=False)
    detected_at = Column(DateTime(timezone=True), default=utcnow)
    notification_sent = Column(Boolean, default=False)
    description = Column(Text, nullable=True)

    pair1 = relationship('CurrencyPair', foreign_keys=[pair1_id])
    pair2 = relationship('CurrencyPair', foreign_keys=[pair2_id])

    def __repr__(self):
        return f"<Divergence(pair1={self.pair1_symbol}, pair2={self.pair2_symbol}, percent={self.divergence_percent})>"