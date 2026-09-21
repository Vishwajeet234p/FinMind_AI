import yfinance as yf
from sqlalchemy.orm import Session
from datetime import datetime
from app.models.stock import Stock, StockPrice

class StockService:
    @staticmethod
    def get_or_create_stock(db: Session, ticker: str) -> Stock:
        """Fetch stock metadata from DB or download from YFinance if missing."""
        ticker = ticker.upper().strip()
        stock = db.query(Stock).filter(Stock.ticker == ticker).first()
        
        if not stock:
            # Download stock info from Yahoo Finance API
            yf_ticker = yf.Ticker(ticker)
            info = yf_ticker.info
            
            stock = Stock(
                ticker=ticker,
                name=info.get("longName") or info.get("shortName") or ticker,
                sector=info.get("sector", "Unknown"),
                industry=info.get("industry", "Unknown"),
                currency=info.get("currency", "USD")
            )
            db.add(stock)
            db.commit()
            db.refresh(stock)
            
        return stock

    @staticmethod
    def sync_historical_prices(db: Session, ticker: str, period: str = "1y") -> int:
        """
        Download historical OHLCV stock price candles and save to database.
        period options: '1mo', '3mo', '6mo', '1y', '2y', '5y', 'max'
        """
        stock = StockService.get_or_create_stock(db, ticker)
        
        # Download historical daily data from Yahoo Finance
        yf_ticker = yf.Ticker(stock.ticker)
        df = yf_ticker.history(period=period)
        
        if df.empty:
            return 0

        added_count = 0
        for index, row in df.iterrows():
            candle_date = index.to_pydatetime()
            
            # Check if price candle already exists in database
            existing = db.query(StockPrice).filter(
                StockPrice.stock_id == stock.id,
                StockPrice.date == candle_date
            ).first()
            
            if not existing:
                price_record = StockPrice(
                    stock_id=stock.id,
                    date=candle_date,
                    open_price=float(row["Open"]),
                    high_price=float(row["High"]),
                    low_price=float(row["Low"]),
                    close_price=float(row["Close"]),
                    volume=int(row["Volume"])
                )
                db.add(price_record)
                added_count += 1
                
        db.commit()
        return added_count

    @staticmethod
    def get_stock_prices(db: Session, ticker: str, limit: int = 100):
        """Retrieve recent stock candles from database."""
        stock = db.query(Stock).filter(Stock.ticker == ticker.upper()).first()
        if not stock:
            return []
            
        return db.query(StockPrice).filter(
            StockPrice.stock_id == stock.id
        ).order_by(StockPrice.date.asc()).limit(limit).all()
