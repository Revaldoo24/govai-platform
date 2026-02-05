from pydantic import BaseModel
import os

class Settings(BaseModel):
    gateway_port: int = int(os.getenv("GATEWAY_PORT", "8000"))
    rag_url: str = os.getenv("RAG_URL", "http://localhost:8001")
    bias_url: str = os.getenv("BIAS_URL", "http://localhost:8002")
    gov_url: str = os.getenv("GOV_URL", "http://localhost:8003")
    explain_url: str = os.getenv("EXPLAIN_URL", "http://localhost:8004")
    api_key: str = os.getenv("GOVAI_API_KEY", "")
    enforce_api_key: bool = os.getenv("GOVAI_ENFORCE_API_KEY", "true").lower() == "true"

settings = Settings()
