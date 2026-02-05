from pydantic import BaseModel
import os

class Settings(BaseModel):
    rag_port: int = int(os.getenv("RAG_PORT", "8001"))
    embed_model: str = os.getenv("HF_EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    gen_model: str = os.getenv("HF_GEN_MODEL", "distilgpt2")

settings = Settings()
