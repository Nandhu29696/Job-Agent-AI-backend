"""Minimal Razorpay client (Orders API + signature verification) using httpx."""
import hashlib
import hmac
import logging

import httpx
from fastapi import HTTPException

from app.config import settings

logger = logging.getLogger("job_agent.razorpay")
API_BASE = "https://api.razorpay.com/v1"


def _require_enabled() -> None:
    if not settings.razorpay_enabled:
        raise HTTPException(status_code=503,
                            detail="Payments are not configured. Set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET.")


async def create_order(amount_paise: int, receipt: str, notes: dict) -> dict:
    _require_enabled()
    payload = {"amount": amount_paise, "currency": settings.currency, "receipt": receipt[:40], "notes": notes}
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            res = await client.post(f"{API_BASE}/orders", json=payload,
                                    auth=(settings.razorpay_key_id, settings.razorpay_key_secret))
    except httpx.HTTPError as exc:
        logger.exception("Razorpay unreachable")
        raise HTTPException(status_code=502, detail="Payment gateway unreachable. Try again.") from exc
    if res.status_code >= 400:
        logger.error("Razorpay order error %s: %s", res.status_code, res.text[:300])
        raise HTTPException(status_code=502, detail="Could not create payment order")
    return res.json()


def verify_payment_signature(order_id: str, payment_id: str, signature: str) -> bool:
    _require_enabled()
    expected = hmac.new(settings.razorpay_key_secret.encode(), f"{order_id}|{payment_id}".encode(),
                        hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature or "")


def verify_webhook_signature(body: bytes, signature: str) -> bool:
    if not settings.razorpay_webhook_secret:
        return False
    expected = hmac.new(settings.razorpay_webhook_secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature or "")
