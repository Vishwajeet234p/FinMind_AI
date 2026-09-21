import sys
import os

# Add backend directory to Python import path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.core.database import engine, Base, SessionLocal
from app.services.stock_service import StockService

def main():
    print("Initializing Database Tables...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        ticker = "AAPL"
        print(f"\nDownloading 1-year historical data for ticker: {ticker}...")
        added_count = StockService.sync_historical_prices(db, ticker=ticker, period="1y")
        print(f"Successfully added {added_count} price candles into the database for {ticker}!")
        
        # Query saved stock info
        stock_info = StockService.get_or_create_stock(db, ticker)
        print(f"\n--- Stock Info ---")
        print(f"Company Name : {stock_info.name}")
        print(f"Sector       : {stock_info.sector}")
        print(f"Industry     : {stock_info.industry}")
        
        # Query recent 5 candles
        prices = StockService.get_stock_prices(db, ticker, limit=5)
        print(f"\n--- Latest 5 Daily Price Candles ---")
        for p in prices:
            print(f"Date: {p.date.strftime('%Y-%m-%d')} | Close: ${p.close_price:.2f} | Volume: {p.volume:,}")

    finally:
        db.close()

if __name__ == "__main__":
    main()
