import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch.nn.functional as F
from typing import List, Dict, Any

class FinBERTSentimentAnalyzer:
    """
    Financial Sentiment Analyzer powered by FinBERT (ProsusAI/finbert).
    Classifies news headlines & financial text into POSITIVE, NEGATIVE, or NEUTRAL.
    """
    def __init__(self, model_name: str = "ProsusAI/finbert"):
        self.model_name = model_name
        self.tokenizer = None
        self.model = None
        self.labels = ["positive", "negative", "neutral"]

    def _load_model(self):
        """Lazy load model and tokenizer on first request to optimize startup speed."""
        if self.model is None:
            print(f"Loading FinBERT model: {self.model_name}...")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
            self.model.eval()

    def analyze_headline(self, headline: str) -> Dict[str, Any]:
        """Analyze sentiment for a single financial headline."""
        results = self.analyze_batch([headline])
        return results[0]

    def analyze_batch(self, headlines: List[str]) -> List[Dict[str, Any]]:
        """Analyze sentiment for a batch of financial headlines."""
        self._load_model()
        
        # Tokenize input texts
        inputs = self.tokenizer(headlines, padding=True, truncation=True, max_length=128, return_tensors="pt")
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            # Apply Softmax to get probability distribution
            probabilities = F.softmax(outputs.logits, dim=-1)

        results = []
        for i, headline in enumerate(headlines):
            probs = probabilities[i].numpy()
            best_idx = int(torch.argmax(probabilities[i]))
            label = self.labels[best_idx]
            confidence = float(probs[best_idx])
            
            # Calculate numerical sentiment score: +1 for positive, -1 for negative, 0 for neutral
            sentiment_index = float(probs[0] - probs[1])  # (P(pos) - P(neg)) range [-1.0, +1.0]

            results.append({
                "headline": headline,
                "sentiment": label.upper(),
                "confidence": round(confidence, 4),
                "sentiment_index": round(sentiment_index, 4),
                "probabilities": {
                    "positive": round(float(probs[0]), 4),
                    "negative": round(float(probs[1]), 4),
                    "neutral": round(float(probs[2]), 4)
                }
            })

        return results
