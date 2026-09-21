from fastapi import APIRouter
from app.api.v1.endpoints import stocks, predictions, genai, websockets, auth, portfolio

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["User Auth & Security"])
api_router.include_router(portfolio.router, prefix="/portfolio", tags=["User Portfolio & P&L"])
api_router.include_router(stocks.router, prefix="/stocks", tags=["Stocks & Market Data"])
api_router.include_router(predictions.router, prefix="/predictions", tags=["ML Predictions & Forecasting"])
api_router.include_router(genai.router, prefix="/genai", tags=["GenAI & FinBERT Sentiment"])
api_router.include_router(websockets.router, prefix="/ws", tags=["WebSockets Real-Time Feeds"])
