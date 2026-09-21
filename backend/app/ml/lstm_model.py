import torch
import torch.nn as nn

class StockLSTM(nn.Module):
    """
    Multi-layer LSTM Neural Network for Time-Series Stock Trend Forecasting.
    
    Architecture:
    - Input Layer: Shape (batch_size, sequence_length=30, input_dim=1)
    - LSTM Layers: 2 stacked LSTM layers (hidden_dim=64)
    - Dropout Layer: 20% dropout rate to prevent overfitting
    - FC Dense Layer: Fully connected linear output layer (hidden_dim -> 1)
    """
    def __init__(self, input_dim: int = 1, hidden_dim: int = 64, num_layers: int = 2, dropout: float = 0.2):
        super(StockLSTM, self).__init__()
        
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        
        # Stacked LSTM Layers
        self.lstm = nn.LSTM(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0
        )
        
        # Dropout layer
        self.dropout = nn.Dropout(dropout)
        
        # Dense linear output layer
        self.fc = nn.Linear(hidden_dim, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        x shape: (batch_size, sequence_length, input_dim)
        Returns: predicted_price shape (batch_size, 1)
        """
        # Initialize hidden and cell states to zeros
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_dim).to(x.device)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_dim).to(x.device)
        
        # Forward pass through LSTM
        # out shape: (batch_size, sequence_length, hidden_dim)
        out, (hn, cn) = self.lstm(x, (h0, c0))
        
        # Extract last time step output: (batch_size, hidden_dim)
        out_last = out[:, -1, :]
        out_last = self.dropout(out_last)
        
        # Final linear prediction: (batch_size, 1)
        prediction = self.fc(out_last)
        
        return prediction
