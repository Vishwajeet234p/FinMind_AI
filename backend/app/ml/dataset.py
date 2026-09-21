import torch
from torch.utils.data import Dataset
import numpy as np

class StockDataset(Dataset):
    """
    PyTorch Dataset for converting 1D stock price series into sequence windows.
    Lookback window length = sequence_length (default 30 days).
    Target = Stock price on day 31.
    """
    def __init__(self, data: np.ndarray, sequence_length: int = 30):
        self.sequence_length = sequence_length
        self.X, self.y = self._create_sequences(data, sequence_length)

    def _create_sequences(self, data: np.ndarray, seq_len: int):
        X, y = [], []
        for i in range(len(data) - seq_len):
            X.append(data[i : i + seq_len])
            y.append(data[i + seq_len])
        
        # Convert to float32 PyTorch tensors
        # X shape: (num_samples, seq_len, 1)
        # y shape: (num_samples, 1)
        X_tensor = torch.tensor(np.array(X), dtype=torch.float32)
        y_tensor = torch.tensor(np.array(y), dtype=torch.float32)
        
        return X_tensor, y_tensor

    def __len__(self):
        return len(self.X)

    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]
