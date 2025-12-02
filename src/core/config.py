import os
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    PROJECT_NAME: str = "Deep Research v1"
    ENVIRONMENT: str = "dev"
    
    # --- SECURITY (API Keys) ---
    # We use 'google_aistudio' or 'vertex_ai' depending on your setup.
    # For simplicity with API Keys, we use the standard Google setup.
    GEMINI_API_KEY: str
    TAVILY_API_KEY: str | None = None

    # --- GOD TIER ROUTING ARCHITECTURE ---
    
    # The BRAIN: Gemini 1.5 Pro
    # Role: Planning, Reflection, Final Synthesis
    # Cost: High (Funded by Credits)
    # Limit: 150 RPM (Plenty for reasoning)
    MODEL_BRAIN: str = "gemini/gemini-2.5-pro"
    
    # The MUSCLE: Gemini 1.5 Flash
    # Role: Reading PDFs, Summarizing Search Results, Extraction
    # Cost: Extremely Low
    # Limit: 1000 RPM (High throughput)
    MODEL_MUSCLE: str = "gemini/gemini-2.5-flash"

    # EMBEDDINGS (Local fallback)
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"

    class Config:
        env_file = ".env"
        extra = "ignore" # Ignore extra fields in .env

@lru_cache()
def get_settings():
    return Settings() #type:ignore