import asyncio
import websockets
import json

async def test_live_ticks():
    url = "ws://localhost:8000/api/v1/ws/stock-ticks/AAPL"
    print(f"Connecting to WebSockets live market feed: {url}...")
    
    async with websockets.connect(url) as ws:
        print("Connected! Listening for live 1-second stock market ticks...\n")
        # Receive top 5 live ticks
        for i in range(1, 6):
            message = await ws.recv()
            data = json.loads(message)
            print(f"[Tick #{i}] Time: {data['timestamp'][:19]} | Ticker: {data['ticker']} | Price: ${data['last_price']:.2f} | Bid: ${data['bid']:.2f} | Ask: ${data['ask']:.2f}")

if __name__ == "__main__":
    try:
        asyncio.run(test_live_ticks())
    except Exception as e:
        print(f"WebSocket test error (Ensure FastAPI Uvicorn server is running): {e}")
