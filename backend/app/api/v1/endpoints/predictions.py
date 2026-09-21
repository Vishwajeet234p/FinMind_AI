from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.ml.trainer import LSTMTrainer

router = APIRouter()
trainer = LSTMTrainer(sequence_length=30)

@router.post("/{ticker}/train")
def train_prediction_model(ticker: str, epochs: int = 30, db: Session = Depends(get_db)):
    """Train PyTorch LSTM Stock Prediction Model for a given ticker."""
    try:
        results = trainer.train_model(db, ticker, epochs=epochs)
        return {
            "status": "success",
            "message": f"Successfully trained LSTM model for {ticker.upper()}",
            "details": results
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to train model: {str(e)}")

@router.get("/{ticker}/forecast")
def get_stock_forecast(ticker: str, db: Session = Depends(get_db)):
    """Generate next-day stock price trend forecast using trained PyTorch LSTM."""
    try:
        forecast = trainer.forecast_next_day(db, ticker)
        return {
            "status": "success",
            "forecast": forecast
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to generate forecast: {str(e)}")
