import asyncio
import json
import random
from datetime import datetime
from typing import List, Dict
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()

class ConnectionManager:
    """Manages active WebSockets connections across connected frontend clients."""
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@router.websocket("/stock-ticks/{ticker}")
async def websocket_stock_ticks(websocket: WebSocket, ticker: str):
    """
    WebSocket endpoint streaming real-time simulated live market stock ticks every 1 second.
    Pushes Date, Ticker, Last Price, Bid/Ask, and Volume to connected web clients.
    """
    await manager.connect(websocket)
    ticker = ticker.upper()
    base_price = 336.00  # Initial starting price
    
    try:
        while True:
            # Simulate real-time price fluctuation (+/- 0.5%)
            delta_percent = random.uniform(-0.005, 0.005)
            base_price = round(base_price * (1 + delta_percent), 2)
            bid = round(base_price - 0.05, 2)
            ask = round(base_price + 0.05, 2)
            volume = random.randint(100, 5000)

            tick_payload = {
                "timestamp": datetime.utcnow().isoformat(),
                "ticker": ticker,
                "last_price": base_price,
                "bid": bid,
                "ask": ask,
                "tick_volume": volume,
                "currency": "USD"
            }
            
            # Send JSON payload over WebSockets connection
            await websocket.send_text(json.dumps(tick_payload))
            await asyncio.sleep(1.0)  # Push tick every 1 second

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print(f"Client disconnected from live WebSocket feed for ticker {ticker}")

@router.websocket("/copilot")
async def websocket_copilot_stream(websocket: WebSocket):
    """
    WebSocket endpoint streaming real-time AI Copilot chat response tokens word-by-word.
    """
    await manager.connect(websocket)
    try:
        while True:
            # Receive user query over WebSockets
            data = await websocket.receive_text()
            user_msg = json.loads(data)
            query = user_msg.get("query", "")

            # Stream simulated response tokens
            response_text = f"FinMind AI Copilot analyzing market signals for query: '{query}'... Market trend signals indicate stable momentum with strong quarterly revenue backing."
            words = response_text.split(" ")

            for word in words:
                token_payload = {
                    "type": "token",
                    "content": word + " "
                }
                await websocket.send_text(json.dumps(token_payload))
                await asyncio.sleep(0.08)  # 80ms delay between words for smooth streaming UI

            # Send completion signal
            done_payload = {"type": "done"}
            await websocket.send_text(json.dumps(done_payload))

    except WebSocketDisconnect:
        manager.disconnect(websocket)
