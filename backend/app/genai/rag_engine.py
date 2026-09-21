import os
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any

CHROMA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "chroma_db")
os.makedirs(CHROMA_DIR, exist_ok=True)

class FinancialRAGEngine:
    """
    Retrieval-Augmented Generation (RAG) Engine using ChromaDB Vector Database.
    Indexes financial reports & SEC filings for semantic Q&A search.
    """
    def __init__(self, collection_name: str = "sec_filings"):
        self.collection_name = collection_name
        # Initialize persistent ChromaDB vector store client
        self.client = chromadb.PersistentClient(path=CHROMA_DIR)
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )

    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 100) -> List[str]:
        """Split document text into overlapping text passages."""
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            start += chunk_size - overlap
        return chunks

    def ingest_document(self, ticker: str, document_title: str, text: str) -> Dict[str, Any]:
        """Chunk, embed, and store document passages into ChromaDB Vector DB."""
        chunks = self.chunk_text(text)
        
        ids = []
        documents = []
        metadatas = []

        ticker = ticker.upper()
        for idx, chunk in enumerate(chunks):
            doc_id = f"{ticker}_{document_title.replace(' ', '_')}_chunk_{idx}"
            ids.append(doc_id)
            documents.append(chunk)
            metadatas.append({
                "ticker": ticker,
                "document_title": document_title,
                "chunk_index": idx
            })

        # Add document chunks to ChromaDB (Chroma handles embedding generation automatically)
        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )

        return {
            "status": "success",
            "ticker": ticker,
            "document_title": document_title,
            "total_chunks_indexed": len(chunks),
            "collection_total_docs": self.collection.count()
        }

    def query_copilot(self, query: str, ticker: str = None, top_k: int = 3) -> Dict[str, Any]:
        """Perform semantic vector search to find relevant document passages."""
        where_clause = {"ticker": ticker.upper()} if ticker else None
        
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k,
            where=where_clause
        )

        retrieved_passages = []
        if results["documents"] and len(results["documents"]) > 0:
            for i in range(len(results["documents"][0])):
                doc_text = results["documents"][0][i]
                meta = results["metadatas"][0][i] if results["metadatas"] else {}
                distance = results["distances"][0][i] if "distances" in results and results["distances"] else 0.0
                
                # Convert cosine distance to similarity score
                similarity = round(1.0 - float(distance), 4)

                retrieved_passages.append({
                    "passage": doc_text,
                    "metadata": meta,
                    "relevance_score": similarity
                })

        # Synthesize context answer
        context_str = "\n---\n".join([p["passage"] for p in retrieved_passages])
        synthesized_answer = (
            f"Based on financial document retrieval for query '{query}':\n\n"
            f"{context_str}\n\n"
            f"Source Documents: {len(retrieved_passages)} relevant passages retrieved."
        ) if retrieved_passages else f"No relevant financial document passages found for query '{query}'."

        return {
            "query": query,
            "ticker_filter": ticker,
            "passages_found": len(retrieved_passages),
            "answer": synthesized_answer,
            "retrieved_passages": retrieved_passages
        }
