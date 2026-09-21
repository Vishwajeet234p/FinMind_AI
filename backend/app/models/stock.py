from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class Stock(Base):
    __tablename__ = "stocks"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(10), unique=True, index=True, nullable=False)  # e.g., AAPL, TSLA
    name = Column(String(100), nullable=False)                           # e.g., Apple Inc.
    sector = Column(String(50), nullable=True)                          # e.g., Technology
    industry = Column(String(50), nullable=True)                        # e.g., Consumer Electronics
    currency = Column(String(10), default="USD")
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    prices = relationship("StockPrice", back_populates="stock", cascade="all, delete-orphan")
    sentiments = relationship("NewsSentiment", back_populates="stock", cascade="all, delete-orphan")


class StockPrice(Base):
    __tablename__ = "stock_prices"

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True)
    open_price = Column(Float, nullable=False)
    high_price = Column(Float, nullable=False)
    low_price = Column(Float, nullable=False)
    close_price = Column(Float, nullable=False)
    volume = Column(Integer, nullable=False)

    # Relationship back to parent Stock
    stock = relationship("Stock", back_populates="prices")


class NewsSentiment(Base):
    __tablename__ = "news_sentiments"

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False, index=True)
    headline = Column(Text, nullable=False)
    source = Column(String(100), nullable=True)
    url = Column(Text, nullable=True)
    published_at = Column(DateTime, nullable=False)
    sentiment_label = Column(String(20), nullable=False)  # 'positive', 'negative', 'neutral'
    sentiment_score = Column(Float, nullable=False)      # Confidence score (0.0 to 1.0)

    # Relationship back to parent Stock
    stock = relationship("Stock", back_populates="sentiments")
