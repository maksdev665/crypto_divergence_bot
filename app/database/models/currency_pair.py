from sqlalchemy import Column, String, Boolean, Float, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.database.base import BaseModel

class CurrencyPair(BaseModel):
    __tablename__ = 'currency_pairs'

    symbol = Column(String, unique=True, nullable=False)
    base_asset = Column(String, nullable=False)             # Например BTC
    quote_asset = Column(String, nullable=False)            # Например USDT
    is_active = Column(Boolean, default=True)
    devergence_threshold = Column(Float, default=5.0)       # Порог дивергенции в процентах

    def __repr__(self):
        return f"<CurrencyPair(symbol={self.symbol}, active={self.is_active})>"