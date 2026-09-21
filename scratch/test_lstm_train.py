import sys
import os

# Add backend directory to Python import path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.core.database import SessionLocal
from app.ml.trainer import LSTMTrainer

def main():
    ticker = "AAPL"
    print(f"=== Training PyTorch LSTM Model for {ticker} ===")
    
    db = SessionLocal()
    try:
        trainer = LSTMTrainer(sequence_length=30)
        
        # 1. Train model for 25 epochs
        print("Starting training loop for 25 epochs...")
        results = trainer.train_model(db, ticker, epochs=25, lr=0.005)
        
        print("\n--- Training Results ---")
        print(f"Ticker        : {results['ticker']}")
        print(f"Epochs        : {results['epochs']}")
        print(f"Final Loss    : {results['final_loss']}")
        print(f"Model Saved   : {results['model_saved_path']}")

        # 2. Generate Next-Day Forecast
        print("\n=== Generating Next-Day Stock Price Trend Forecast ===")
        forecast = trainer.forecast_next_day(db, ticker)
        
        print("\n--- Forecast Output ---")
        print(f"Ticker                 : {forecast['ticker']}")
        print(f"Last Actual Price      : ${forecast['last_actual_price']:.2f}")
        print(f"Predicted Next Price   : ${forecast['predicted_next_day_price']:.2f}")
        print(f"Predicted Change ($)   : ${forecast['predicted_change_amount']:+.2f}")
        print(f"Predicted Change (%)   : {forecast['predicted_percentage_change']:+.2f}%")
        print(f"Trend Signal           : {forecast['trend_direction']}")

    finally:
        db.close()

if __name__ == "__main__":
    main()
