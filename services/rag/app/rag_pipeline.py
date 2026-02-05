from __future__ import annotations

import json
from typing import Dict
from dataclasses import dataclass
from typing import List, Tuple

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document
import numpy as np
from transformers import pipeline

from .config import settings

@dataclass
class RagSource:
    id: str
    title: str
    snippet: str
    score: float

class RagPipeline:
    def __init__(self) -> None:
        self.embedder = HuggingFaceEmbeddings(model_name=settings.embed_model)
        self.vectorstore = None
        self.generator = pipeline("text-generation", model=settings.gen_model)

    def load_seed_documents(self, path: str) -> None:
        docs = []
        with open(path, "r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                payload = json.loads(line)
                docs.append(
                    Document(
                        page_content=payload["text"],
                        metadata={"id": payload["id"], "title": payload["title"]},
                    )
                )
        if docs:
            self.vectorstore = FAISS.from_documents(docs, self.embedder)

    def add_document(self, doc_id: str, title: str, text: str) -> None:
        document = Document(page_content=text, metadata={"id": doc_id, "title": title})
        if self.vectorstore is None:
            self.vectorstore = FAISS.from_documents([document], self.embedder)
        else:
            self.vectorstore.add_documents([document])

    def _score_to_confidence(self, score: float) -> float:
        # FAISS returns distance-like scores; convert to a bounded confidence
        return 1.0 / (1.0 + max(score, 0.0))

    def retrieve(self, query: str, top_k: int) -> List[RagSource]:
        if self.vectorstore is None:
            return []

        results: List[Tuple[Document, float]] = self.vectorstore.similarity_search_with_score(query, k=top_k)
        sources = []
        for doc, score in results:
            confidence = self._score_to_confidence(score)
            snippet = doc.page_content[:240]
            sources.append(
                RagSource(
                    id=str(doc.metadata.get("id")),
                    title=str(doc.metadata.get("title")),
                    snippet=snippet,
                    score=round(confidence, 4),
                )
            )
        return sources

    def _cosine_sim(self, a: np.ndarray, b: np.ndarray) -> float:
        denom = (np.linalg.norm(a) * np.linalg.norm(b)) or 1.0
        return float(np.dot(a, b) / denom)

    def _evidence_check(self, answer: str, sources: List[RagSource]) -> Dict[str, float | list[str]]:
        if not sources:
            return {
                "consistency_score": 0.0,
                "min_source_score": 0.0,
                "flags": ["no_sources"],
            }

        answer_vec = np.array(self.embedder.embed_query(answer))
        source_scores = []
        for src in sources:
            src_vec = np.array(self.embedder.embed_query(src.snippet))
            source_scores.append(self._cosine_sim(answer_vec, src_vec))

        avg_score = float(np.mean(source_scores)) if source_scores else 0.0
        min_score = float(np.min(source_scores)) if source_scores else 0.0
        flags = []
        if avg_score < 0.2:
            flags.append("low_consistency")
        if min_score < 0.1:
            flags.append("weak_source_alignment")

        return {
            "consistency_score": round(avg_score, 4),
            "min_source_score": round(min_score, 4),
            "flags": flags,
        }

    def generate_answer(self, prompt: str, top_k: int) -> Tuple[str, List[RagSource], float, str, Dict[str, float | list[str]]]:
        sources = self.retrieve(prompt, top_k)
        context = "\n".join([f"- {s.title}: {s.snippet}" for s in sources])
        composed = (
            "You are a governance-aware assistant. Use the sources to answer the question. "
            "If the sources are insufficient, say so and highlight uncertainty.\n\n"
            f"Sources:\n{context}\n\n"
            f"Question: {prompt}\nAnswer:"
        )
        output = self.generator(composed, max_new_tokens=120, do_sample=False)
        text = output[0]["generated_text"].split("Answer:")[-1].strip()

        if sources:
            confidence = round(sum(s.score for s in sources) / len(sources), 4)
        else:
            confidence = 0.0

        evidence = self._evidence_check(text, sources)
        return text, sources, confidence, settings.gen_model, evidence
