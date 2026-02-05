# GovAI - Cloud-Native Responsible Generative AI Governance Platform

This repository contains a cloud-native, microservices-based platform for governed Generative AI. It provides RAG grounding, bias checks, explainability, audit logs, policy enforcement, and human-in-the-loop approvals.

## Services
- gateway: Orchestrates the end-to-end pipeline
- rag: Retrieval-augmented generation with evidence grounding
- bias: Bias detection at input/output
- governance: Policy enforcement, audit logs, and approvals
- explainability: Compiles model/source/uncertainty explanations

## Quick Start (Docker Compose)
1. Copy `.env.example` to `.env` and adjust if needed
2. Run `docker compose up --build`
3. Send a request to the gateway at `http://localhost:8000`

Example request:
```json
{
  "tenant_id": "gov-dept-a",
  "user_id": "analyst-1",
  "prompt": "Draft a policy memo on responsible AI usage in public services.",
  "top_k": 4
}
```

## Architecture Overview
- RAG service builds a vector index from documents and generates grounded answers
- Bias service scores potential bias risk
- Governance service evaluates policies, writes audit logs, and manages approvals
- Explainability service returns evidence, model metadata, and uncertainty

## Key Endpoints
- Gateway: `POST /generate`
- RAG: `POST /generate`, `POST /ingest`
- Bias: `POST /analyze`
- Governance: `POST /evaluate`, `POST /policies`, `GET /policies`, `POST /decisions/{id}`
- Explainability: `POST /explain`

## Notes
- Default models are CPU-friendly but can be swapped via env vars
- PostgreSQL is used for policies and audit logs
- Kubernetes manifests are included under `k8s/`

## Frontend (Local)
Frontend lives in `frontend/` (Next.js). It proxies requests to the backend gateway.

Local dev:
1. Copy `frontend/.env.example` to `frontend/.env.local`
2. Run `npm install` then `npm run dev`
