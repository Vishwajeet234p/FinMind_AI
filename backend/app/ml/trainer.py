import os
import torch
import torch.nn as nn
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sqlalchemy.orm import Session
from typing import Dict, Any, Tuple

from app.services.stock_service import StockService
from app.ml.dataset import StockDataset
from app.ml.lstm_model import StockLSTM

WEIGHTS_DIR = os.path.join(os.path.dirname(__file__), "weights")
os.makedirs(WEIGHTS_DIR, exist_ok=True)

def set_seed(seed: int = 42):
    """Set random seeds across PyTorch and NumPy for 100% reproducible training."""
    torch.manual_seed(seed)
    np.random.seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True

class LSTMTrainer:
    def __init__(self, sequence_length: int = 30):
        self.sequence_length = sequence_length
        self.scaler = MinMaxScaler(feature_range=(0, 1))

    def train_model(self, db: Session, ticker: str, epochs: int = 30, lr: float = 0.001, seed: int = 42) -> Dict[str, Any]:
        """
        Train LSTM model on historical stock prices for a given ticker.
        Applies deterministic seeding and 5-year historical market dataset.
        """
        # 1. Set fixed random seed for reproducibility
        set_seed(seed)
        ticker = ticker.upper()
        
        # 2. Fetch stock prices from DB (Sync 5y of historical data for maximum accuracy)
        prices = StockService.get_stock_prices(db, ticker, limit=2000)
        if len(prices) < 250:
            # Sync 5 years of historical data from YFinance
            StockService.sync_historical_prices(db, ticker, period="5y")
            prices = StockService.get_stock_prices(db, ticker, limit=2000)

        if len(prices) < self.sequence_length + 10:
            raise ValueError(f"Insufficient stock data for ticker {ticker} (minimum {self.sequence_length + 10} records required).")

        # 3. Extract closing prices as 2D numpy array
        close_prices = np.array([[p.close_price] for p in prices], dtype=np.float32)
        
        # 4. Fit MinMaxScaler
        scaled_data = self.scaler.fit_transform(close_prices)

        # 5. Create PyTorch Dataset & DataLoader
        dataset = StockDataset(scaled_data, sequence_length=self.sequence_length)
        
        # Generator with fixed seed for DataLoader shuffling
        g = torch.Generator()
        g.manual_seed(seed)
        train_loader = torch.utils.data.DataLoader(dataset, batch_size=16, shuffle=True, generator=g)

        # 6. Initialize Model, Loss Function, and Optimizer
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model = StockLSTM(input_dim=1, hidden_dim=64, num_layers=2, dropout=0.2).to(device)
        criterion = nn.MSELoss()
        optimizer = torch.optim.Adam(model.parameters(), lr=lr)

        # 7. Training Loop
        model.train()
        epoch_losses = []
        for epoch in range(1, epochs + 1):
            total_loss = 0.0
            for batch_x, batch_y in train_loader:
                batch_x, batch_y = batch_x.to(device), batch_y.to(device)

                optimizer.zero_grad()
                predictions = model(batch_x)
                loss = criterion(predictions, batch_y)
                loss.backward()
                optimizer.step()

                total_loss += loss.item() * batch_x.size(0)

            avg_loss = total_loss / len(dataset)
            epoch_losses.append(avg_loss)

        # 8. Save Model Checkpoint & Scaler Parameters
        model_path = os.path.join(WEIGHTS_DIR, f"{ticker}_lstm.pt")
        torch.save({
            "model_state_dict": model.state_dict(),
            "scaler_min": self.scaler.min_,
            "scaler_scale": self.scaler.scale_,
            "sequence_length": self.sequence_length,
            "final_loss": epoch_losses[-1],
            "seed": seed
        }, model_path)

        return {
            "ticker": ticker,
            "epochs": epochs,
            "final_loss": round(float(epoch_losses[-1]), 6),
            "records_used": len(close_prices),
            "model_saved_path": model_path
        }

    def forecast_next_day(self, db: Session, ticker: str, force_retrain: bool = False) -> Dict[str, Any]:
        """Predict the next trading day's stock price using trained LSTM weights."""
        ticker = ticker.upper()
        model_path = os.path.join(WEIGHTS_DIR, f"{ticker}_lstm.pt")
        
        if not os.path.exists(model_path) or force_retrain:
            # Train model if no checkpoint exists or forced
            self.train_model(db, ticker, epochs=30)

        # 1. Load Checkpoint deterministically
        checkpoint = torch.load(model_path, map_location=torch.device("cpu"), weights_only=False)
        
        self.scaler.min_ = checkpoint["scaler_min"]
        self.scaler.scale_ = checkpoint["scaler_scale"]
        
        model = StockLSTM(input_dim=1, hidden_dim=64, num_layers=2)
        model.load_state_dict(checkpoint["model_state_dict"])
        model.eval()

        # 2. Get recent closing prices from DB
        prices = StockService.get_stock_prices(db, ticker, limit=2000)
        recent_prices = np.array([[p.close_price] for p in prices[-self.sequence_length:]], dtype=np.float32)
        
        # 3. Scale input sequence
        scaled_input = self.scaler.transform(recent_prices)
        input_tensor = torch.tensor(scaled_input, dtype=torch.float32).unsqueeze(0)  # Shape: (1, 30, 1)

        # 4. Generate prediction
        with torch.no_grad():
            scaled_pred = model(input_tensor).numpy()

        # 5. Inverse transform to actual price in USD
        predicted_price = float(self.scaler.inverse_transform(scaled_pred)[0][0])
        last_actual_price = float(recent_prices[-1][0])
        price_change = predicted_price - last_actual_price
        percentage_change = (price_change / last_actual_price) * 100

        trend_direction = "BULLISH" if price_change > 0 else "BEARISH"

        return {
            "ticker": ticker,
            "last_actual_price": round(last_actual_price, 2),
            "predicted_next_day_price": round(predicted_price, 2),
            "predicted_change_amount": round(price_change, 2),
            "predicted_percentage_change": round(percentage_change, 2),
            "trend_direction": trend_direction
        }
