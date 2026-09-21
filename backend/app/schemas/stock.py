from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class StockPriceResponse(BaseModel):
    date: datetime
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: int

    class Config:
        from_attributes = True


class StockResponse(BaseModel):
    id: int
    ticker: str
    name: str
    sector: Optional[str] = None
    industry: Optional[str] = None
    currency: str
    created_at: datetime

    class Config:
        from_attributes = True


class StockDetailResponse(StockResponse):
    prices: List[StockPriceResponse] = []
