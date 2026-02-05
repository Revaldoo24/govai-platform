from pathlib import Path
from fastapi import FastAPI
from .schemas import GenerateRequest, GenerateResponse, IngestRequest
from .rag_pipeline import RagPipeline

app = FastAPI(title="GovAI RAG", version="0.1.0")

pipeline = RagPipeline()

@app.on_event("startup")
def load_docs():
    data_path = Path(__file__).resolve().parent / "data" / "sample_docs.jsonl"
    pipeline.load_seed_documents(str(data_path))

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/generate", response_model=GenerateResponse)
def generate(req: GenerateRequest):
    answer, sources, confidence, model_id, evidence = pipeline.generate_answer(req.prompt, req.top_k)
    return {
        "answer": answer,
        "sources": [s.__dict__ for s in sources],
        "confidence": confidence,
        "model_id": model_id,
        "evidence": evidence,
    }

@app.post("/ingest")
def ingest(req: IngestRequest):
    pipeline.add_document(req.id, req.title, req.text)
    return {"status": "ingested", "id": req.id}
