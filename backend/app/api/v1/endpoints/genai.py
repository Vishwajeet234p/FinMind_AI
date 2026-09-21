from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from app.ml.sentiment_analyzer import FinBERTSentimentAnalyzer
from app.genai.rag_engine import FinancialRAGEngine

router = APIRouter()
sentiment_analyzer = FinBERTSentimentAnalyzer()
rag_engine = FinancialRAGEngine()

# Pydantic Request Models
class HeadlineRequest(BaseModel):
    headlines: List[str]

class DocumentUploadRequest(BaseModel):
    ticker: str
    document_title: str
    text: str

class CopilotQueryRequest(BaseModel):
    query: str
    ticker: Optional[str] = None
    top_k: int = 3

@router.post("/sentiment")
def analyze_news_sentiment(request: HeadlineRequest):
    """Analyze sentiment of financial headlines using FinBERT."""
    try:
        results = sentiment_analyzer.analyze_batch(request.headlines)
        return {
            "status": "success",
            "total_analyzed": len(results),
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Sentiment analysis failed: {str(e)}")

@router.post("/documents/upload")
def upload_financial_document(request: DocumentUploadRequest):
    """Chunk, embed, and store financial SEC filings into ChromaDB Vector DB."""
    try:
        result = rag_engine.ingest_document(
            ticker=request.ticker,
            document_title=request.document_title,
            text=request.text
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Document upload failed: {str(e)}")

@router.post("/copilot/query")
def query_financial_copilot(request: CopilotQueryRequest):
    """Perform semantic RAG search to answer user queries using SEC filings."""
    try:
        result = rag_engine.query_copilot(
            query=request.query,
            ticker=request.ticker,
            top_k=request.top_k
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Copilot query failed: {str(e)}")
