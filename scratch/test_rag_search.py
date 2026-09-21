import sys
import os

# Add backend directory to Python import path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.genai.rag_engine import FinancialRAGEngine

def main():
    print("=== Testing Financial RAG Engine with ChromaDB Vector DB ===")
    
    rag = FinancialRAGEngine()

    # Sample SEC 10-K Report Document for Apple Inc.
    sample_report = """
    Apple Inc. Annual Financial Filing (Form 10-K) - Item 1A: Risk Factors.
    Global supply chain disruptions, semiconductor component shortages, and geopolitical tensions 
    could impact manufacturing output and delays in product delivery. Furthermore, foreign exchange 
    rate fluctuations may affect international sales margins. Consumer spending shifts towards 
    cheaper alternatives remain a competitive risk in emerging markets.
    """

    print("\n1. Ingesting SEC Document into ChromaDB Vector Store...")
    ingest_result = rag.ingest_document(
        ticker="AAPL",
        document_title="2025 SEC Form 10-K Risk Factors",
        text=sample_report
    )
    print(f"Document Ingested! Total chunks indexed: {ingest_result['total_chunks_indexed']}")

    # 2. Perform Semantic Vector Search
    query = "What are Apple's supply chain and component risks?"
    print(f"\n2. Querying RAG Copilot: '{query}'...")
    copilot_result = rag.query_copilot(query=query, ticker="AAPL", top_k=2)

    print("\n--- RAG Copilot Response ---")
    print(copilot_result['answer'])
    
    print("\n--- Retrieved Passages ---")
    for idx, passage in enumerate(copilot_result['retrieved_passages'], 1):
        print(f"[{idx}] Relevance: {passage['relevance_score']:.2%} | Text: {passage['passage'][:150]}...")

if __name__ == "__main__":
    main()
