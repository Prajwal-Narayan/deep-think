import os
from typing import List, Dict, Any
from tavily import TavilyClient
import chromadb
from chromadb.utils import embedding_functions
from src.core.config import get_settings

settings = get_settings()

# --- 1. INITIALIZATION ---

# Initialize Tavily (Web Search)
try:
    tavily_client = TavilyClient(api_key=settings.TAVILY_API_KEY)
except Exception:
    print("⚠️ Tavily API Key missing. Web search will return mock data.")
    tavily_client = None

# Initialize ChromaDB (Local Vector Store)
# We use a persistent folder so data survives restarts
CHROMA_DATA_PATH = "chroma_db_data"
chroma_client = chromadb.PersistentClient(path=CHROMA_DATA_PATH)

# Use a free, local embedding model (no API cost)
embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name=settings.EMBEDDING_MODEL
)

# Get or create the collection
collection = chroma_client.get_or_create_collection(
    name="research_docs",
    embedding_function=embedding_func
)

# --- 2. TOOL FUNCTIONS ---

def perform_web_search(query: str) -> str:
    """
    Searches the web using Tavily and returns a summarized string.
    """
    if not tavily_client:
        return "Error: Web search tool is disabled (No API Key)."
        
    print(f"🌐 [Web] Searching for: {query}")
    try:
        # q = query, search_depth="advanced" for deep research
        response = tavily_client.search(query=query, search_depth="advanced", max_results=3)
        
        # Format results into a clean string context
        context = []
        for result in response.get("results", []):
            context.append(f"Source: {result['url']}\nContent: {result['content']}\n")
            
        return "\n---\n".join(context)
        
    except Exception as e:
        return f"Error executing web search: {str(e)}"

def perform_document_search(query: str) -> str:
    """
    Searches local vector database for relevant chunks.
    """
    print(f"📂 [Doc] Searching local knowledge for: {query}")
    try:
        results = collection.query(
            query_texts=[query],
            n_results=3
        )
        
        # Chroma returns lists of lists. We flatten them.
        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        
        context = []
        for doc, meta in zip(documents, metadatas):
            source = meta.get("source", "Unknown")
            context.append(f"Source: {source}\nContent: {doc}\n")
            
        if not context:
            return "No relevant documents found in the local database."
            
        return "\n---\n".join(context)
        
    except Exception as e:
        return f"Error executing document search: {str(e)}"

# --- 3. HELPER: INGESTION (To feed the beast) ---
def ingest_text(text: str, source: str):
    """
    Splits text into chunks and saves to ChromaDB.
    """
    # Simple chunking by 1000 characters for v1
    chunk_size = 1000
    chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
    
    ids = [f"{source}_{i}" for i in range(len(chunks))]
    metadatas = [{"source": source} for _ in chunks]
    
    collection.add(
        documents=chunks,
        ids=ids,
        metadatas=metadatas
    )
    print(f"✅ Ingested {len(chunks)} chunks from {source}")

# --- SMOKE TEST ---
if __name__ == "__main__":
    # 1. Ingest dummy data
    ingest_text("NVIDIA's 2024 strategy focuses on the Blackwell B200 GPU.", "internal_memo.txt")
    
    # 2. Test Doc Search
    print("\n🔍 TEST DOC SEARCH:")
    print(perform_document_search("Blackwell B200"))
    
    # 3. Test Web Search (Only works if you have Tavily Key)
    print("\n🌐 TEST WEB SEARCH:")
    print(perform_web_search("Current AMD stock price"))