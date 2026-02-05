from typing import Any, Dict
import asyncio
import httpx
from .config import settings

async def post_json(url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    backoff = 0.5
    last_error: Exception | None = None
    for _ in range(5):
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                return resp.json()
        except Exception as exc:
            last_error = exc
            await asyncio.sleep(backoff)
            backoff *= 2
    raise last_error if last_error else RuntimeError("Request failed")

async def call_rag(payload: Dict[str, Any]) -> Dict[str, Any]:
    return await post_json(f"{settings.rag_url}/generate", payload)

async def call_bias(payload: Dict[str, Any]) -> Dict[str, Any]:
    return await post_json(f"{settings.bias_url}/analyze", payload)

async def call_governance(payload: Dict[str, Any]) -> Dict[str, Any]:
    return await post_json(f"{settings.gov_url}/evaluate", payload)

async def call_explain(payload: Dict[str, Any]) -> Dict[str, Any]:
    return await post_json(f"{settings.explain_url}/explain", payload)
