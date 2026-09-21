from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.services.stock_service import StockService
from app.schemas.stock import StockResponse, StockPriceResponse

router = APIRouter()

@router.post("/{ticker}/sync")
def sync_stock_data(ticker: str, period: str = "1y", db: Session = Depends(get_db)):
    """Fetch live & historical market data for a ticker from Yahoo Finance and store in DB."""
    try:
        added_count = StockService.sync_historical_prices(db, ticker, period=period)
        return {
            "status": "success",
            "ticker": ticker.upper(),
            "period": period,
            "candles_added": added_count,
            "message": f"Successfully synchronized market data for {ticker.upper()}"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to sync stock data: {str(e)}")

@router.get("/{ticker}", response_model=StockResponse)
def get_stock_info(ticker: str, db: Session = Depends(get_db)):
    """Get metadata for a specific stock ticker."""
    stock = StockService.get_or_create_stock(db, ticker)
    if not stock:
        raise HTTPException(status_code=444, detail=f"Stock ticker {ticker} not found.")
    return stock

@router.get("/{ticker}/prices", response_model=List[StockPriceResponse])
def get_stock_prices(ticker: str, limit: int = 100, db: Session = Depends(get_db)):
    """Get historical stock price candles from database."""
    prices = StockService.get_stock_prices(db, ticker, limit=limit)
    return prices
