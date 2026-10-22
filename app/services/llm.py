"""
Client for the remote Ollama server configured in .env (OLLAMA_BASE_URL /
OLLAMA_MODEL). Talks to its REST API directly over HTTP — no local Ollama
install or `ollama` Python package is needed.
"""
import json
import logging
import re
from types import SimpleNamespace

import httpx
from fastapi import HTTPException

from app.config import settings

logger = logging.getLogger("job_agent.llm")

CHAT_URL = f"{settings.ollama_base_url.rstrip('/')}/api/chat"


class LLMUnavailable(HTTPException):
    def __init__(self, detail: str = "AI service is unavailable right now. Please try again shortly."):
        super().__init__(status_code=503, detail=detail)


def _to_message(raw: dict) -> SimpleNamespace:
    """Expose .content and .tool_calls[i].function.{name,arguments} like the old client did."""
    calls = []
    for call in raw.get("tool_calls") or []:
        fn = call.get("function") or {}
        args = fn.get("arguments") or {}
        if isinstance(args, str):  # some models return a JSON string
            try:
                args = json.loads(args)
            except json.JSONDecodeError:
                args = {}
        calls.append(SimpleNamespace(function=SimpleNamespace(name=fn.get("name", ""), arguments=args)))
    return SimpleNamespace(role=raw.get("role", "assistant"), content=raw.get("content") or "", tool_calls=calls)


async def chat(messages: list[dict], *, tools: list | None = None, format: dict | str | None = None,
               temperature: float = 0.4) -> SimpleNamespace:
    """POST /api/chat on the configured Ollama server and return the assistant message."""
    payload = {
        "model": settings.ollama_model,
        "messages": messages,
        "stream": False,
        "options": {"temperature": temperature},
    }
    if tools:
        payload["tools"] = tools
    if format:
        payload["format"] = format
    try:
        async with httpx.AsyncClient(timeout=settings.ollama_timeout_seconds) as client:
            res = await client.post(CHAT_URL, json=payload)
    except httpx.HTTPError as exc:
        logger.exception("Ollama server unreachable at %s", CHAT_URL)
        raise LLMUnavailable() from exc
    if res.status_code != 200:
        logger.error("Ollama error %s: %s", res.status_code, res.text[:300])
        raise LLMUnavailable()
    return _to_message(res.json().get("message") or {})


async def complete(system: str, prompt: str, temperature: float = 0.5) -> str:
    msg = await chat(
        [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
        temperature=temperature,
    )
    return (msg.content or "").strip()


def _extract_json(raw: str):
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, re.S)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
    return None


async def complete_json(system: str, prompt: str, schema: dict, temperature: float = 0.2) -> dict:
    """Ask for JSON matching `schema` (Ollama structured outputs). Retries once."""
    messages = [{"role": "system", "content": system}, {"role": "user", "content": prompt}]
    for attempt in range(2):
        msg = await chat(messages, format=schema, temperature=temperature)
        data = _extract_json(msg.content or "")
        if isinstance(data, dict):
            return data
        logger.warning("LLM returned invalid JSON (attempt %s): %r", attempt + 1, (msg.content or "")[:300])
    raise HTTPException(status_code=502, detail="AI returned an unexpected response. Please try again.")
