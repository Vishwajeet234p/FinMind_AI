# FinMind AI

FinMind AI is a financial intelligence dashboard with stock history, simulated live price ticks, PyTorch LSTM forecasting, FinBERT sentiment analysis, portfolio tracking, and SEC-document Q&A through a ChromaDB retrieval engine.

## Current Architecture

```text
Static frontend (frontend/)
        | REST + WebSockets
        v
FastAPI backend (backend/app/)
        |
        +-- SQLAlchemy database
        +-- PyTorch LSTM predictor
        +-- FinBERT sentiment analyzer
        +-- ChromaDB financial document retrieval
```

The frontend is a static HTML/CSS/JavaScript application. It is served locally by FastAPI at `/dashboard/` and can be deployed separately to Vercel.

## Features

- Historical stock price chart for AAPL, TSLA, NVDA, MSFT, and GOOGL
- Simulated one-second WebSocket price ticks
- PyTorch LSTM next-day price forecast
- FinBERT positive, negative, and neutral financial sentiment analysis
- JWT registration and login
- Portfolio positions and profit/loss display
- ChromaDB retrieval for financial-document questions

## Project Structure

```text
.
├── backend/
│   ├── app/
│   │   ├── api/v1/       # REST and WebSocket endpoints
│   │   ├── core/         # Settings, database, and security
│   │   ├── genai/        # ChromaDB RAG engine
│   │   ├── ml/           # LSTM and FinBERT services
│   │   └── main.py       # FastAPI application
│   └── requirements.txt
├── frontend/
│   ├── index.html        # Dashboard markup
│   ├── app.js            # REST/WebSocket browser controller
│   ├── config.js         # Frontend-to-backend URL configuration
│   └── styles.css
├── scratch/              # Manual integration scripts
├── docker-compose.yml    # Local PostgreSQL and Redis services
├── .env.example
└── README.md
```

## Local Setup on Windows PowerShell

From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
```

Copy the environment template:

```powershell
Copy-Item .env.example .env
```

Start the backend:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --reload --port 8000
```

Open:

- Dashboard: http://localhost:8000/dashboard/
- API documentation: http://localhost:8000/docs
- Health check: http://localhost:8000/health

The local default database is SQLite. To start the optional local PostgreSQL and Redis containers:

```powershell
docker compose up -d
```

## API Examples

Test FinBERT sentiment:

```powershell
$body = @{ headlines = @("Apple reports record quarterly revenue") } | ConvertTo-Json
Invoke-RestMethod `
  -Uri "http://localhost:8000/api/v1/genai/sentiment" `
  -Method Post `
  -ContentType "application/json" `
  -Body $body
```

Test the LSTM forecast:

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/predictions/AAPL/forecast"
```

Live tick WebSocket:

```text
ws://localhost:8000/api/v1/ws/stock-ticks/AAPL
```

## Deploy Backend to Render

Create a Render **Web Service** connected to this GitHub repository.

```text
Root Directory: leave empty
Runtime: Python
Build Command: pip install -r backend/requirements.txt
Start Command: uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port $PORT
Health Check Path: /health
```

Set these Render environment variables:

```text
ENV=production
DEBUG=False
SECRET_KEY=<long-random-secret>
FRONTEND_ORIGIN=https://<your-vercel-project>.vercel.app
DATABASE_URL=<Render PostgreSQL connection URL>
REDIS_URL=<Redis URL, if used>
```

Verify the deployed backend at:

```text
https://<your-render-service>.onrender.com/health
```

## Deploy Frontend to Vercel

1. Import the GitHub repository into Vercel.
2. Set **Root Directory** to `frontend`.
3. Select **Other** as the framework preset.
4. Leave build and install commands empty.
5. Set output directory to `.`.
6. Deploy.

After Render provides the backend URL, edit `frontend/config.js`:

```javascript
window.FINMIND_BACKEND_URL = "https://<your-render-service>.onrender.com";
```

Commit and push that change. Vercel will redeploy automatically. The frontend uses `wss://` automatically when the Render URL uses HTTPS.

## Data and Deployment Notes

Do not commit secrets. The `.gitignore` excludes `.env`, databases, ChromaDB data, and model checkpoint files.

For a fresh Render deployment:

- Use Render PostgreSQL for persistent stock, user, and portfolio data.
- Re-index financial documents into ChromaDB after deployment.
- Retrain or persist LSTM weights using durable object storage if required.
- Render free services may sleep and have limited disk and memory.

## Push This Project to GitHub

Create an empty repository on GitHub first. Do not add a README, `.gitignore`, or license there because this project already contains them.

From PowerShell in the project root:

```powershell
cd "C:\Users\Vishwajeet\OneDrive\Desktop\project_1"
git init
git branch -M main
git add .
git status
git commit -m "Initial FinMind AI project"
git remote add origin https://github.com/<YOUR_USERNAME>/<YOUR_REPOSITORY>.git
git push -u origin main
```

Replace `<YOUR_USERNAME>` and `<YOUR_REPOSITORY>`. If `origin` already exists:

```powershell
git remote set-url origin https://github.com/<YOUR_USERNAME>/<YOUR_REPOSITORY>.git
git push -u origin main
```

For later changes:

```powershell
git add .
git commit -m "Describe your change"
git push
```

Before pushing, confirm that `.env`, database files, ChromaDB files, and model weights are not staged:

```powershell
git status
```
