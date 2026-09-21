from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.models.user import User, PortfolioItem
from app.api.v1.endpoints.auth import get_current_user
from app.services.stock_service import StockService

router = APIRouter()

# --- Pydantic Schemas ---
class BuyStockRequest(BaseModel):
    ticker: str
    shares: float
    buy_price: float

class PortfolioItemResponse(BaseModel):
    id: int
    ticker: str
    company_name: Optional[str]
    shares_owned: float
    buy_price: float
    current_price: Optional[float] = None
    total_invested: Optional[float] = None
    current_value: Optional[float] = None
    profit_loss: Optional[float] = None
    profit_loss_pct: Optional[float] = None
    added_at: datetime

    class Config:
        from_attributes = True

# --- Endpoints ---
@router.get("/", response_model=List[PortfolioItemResponse])
def get_my_portfolio(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Fetch the authenticated user's stock portfolio with live P&L calculations."""
    items = db.query(PortfolioItem).filter(PortfolioItem.user_id == current_user.id).all()
    result = []
    
    for item in items:
        # Fetch latest stock price from DB for live P&L calculation
        prices = StockService.get_stock_prices(db, item.ticker, limit=1000)
        current_price = float(prices[-1].close_price) if prices else item.buy_price
        total_invested = round(item.shares_owned * item.buy_price, 2)
        current_value = round(item.shares_owned * current_price, 2)
        profit_loss = round(current_value - total_invested, 2)
        profit_loss_pct = round(((current_price - item.buy_price) / item.buy_price) * 100, 2)

        result.append(PortfolioItemResponse(
            id=item.id,
            ticker=item.ticker,
            company_name=item.company_name,
            shares_owned=item.shares_owned,
            buy_price=item.buy_price,
            current_price=current_price,
            total_invested=total_invested,
            current_value=current_value,
            profit_loss=profit_loss,
            profit_loss_pct=profit_loss_pct,
            added_at=item.added_at
        ))

    return result

@router.post("/buy")
def buy_stock(request: BuyStockRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Add a stock position to user's portfolio."""
    stock = StockService.get_or_create_stock(db, request.ticker)
    
    portfolio_item = PortfolioItem(
        user_id=current_user.id,
        ticker=stock.ticker,
        company_name=stock.name,
        shares_owned=request.shares,
        buy_price=request.buy_price
    )
    db.add(portfolio_item)
    db.commit()
    db.refresh(portfolio_item)
    
    return {
        "status": "success",
        "message": f"Added {request.shares} shares of {stock.ticker} at ${request.buy_price:.2f} to portfolio",
        "portfolio_item_id": portfolio_item.id
    }

@router.delete("/{item_id}")
def remove_stock(item_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Remove a stock position from user's portfolio."""
    item = db.query(PortfolioItem).filter(
        PortfolioItem.id == item_id,
        PortfolioItem.user_id == current_user.id
    ).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="Portfolio item not found.")
    
    db.delete(item)
    db.commit()
    return {"status": "success", "message": f"Removed {item.ticker} from portfolio"}
