import sys
import os

# Add backend directory to Python import path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.ml.sentiment_analyzer import FinBERTSentimentAnalyzer

def main():
    print("=== Testing FinBERT Financial News Sentiment Analyzer ===")
    
    analyzer = FinBERTSentimentAnalyzer()
    
    headlines = [
        "Apple reports record high quarterly revenue driven by strong iPhone 16 sales.",
        "Tesla stock drops 5% due to EV delivery delays and margin pressures.",
        "Federal Reserve maintains interest rates unchanged at 5.25%."
    ]

    print("\nAnalyzing Batch Headlines...\n")
    results = analyzer.analyze_batch(headlines)

    for i, res in enumerate(results, 1):
        print(f"[{i}] Headline : {res['headline']}")
        print(f"    Sentiment: {res['sentiment']} (Confidence: {res['confidence']:.2%})")
        print(f"    Probs    : Positive={res['probabilities']['positive']:.2f} | Negative={res['probabilities']['negative']:.2f} | Neutral={res['probabilities']['neutral']:.2f}\n")

if __name__ == "__main__":
    main()
