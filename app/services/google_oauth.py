"""Google OAuth2 authorization-code flow (Sign in with Google)."""
from urllib.parse import urlencode

import httpx

from app.config import settings

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"


class GoogleOAuthError(Exception):
    pass


def build_authorize_url(state: str) -> str:
    params = {
        "client_id": settings.gmail_client_id,
        "redirect_uri": settings.gmail_redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "online",
        "prompt": "select_account",
    }
    return f"{AUTH_URL}?{urlencode(params)}"


async def exchange_code_for_profile(code: str) -> dict:
    """Exchange the auth code and return Google's verified userinfo."""
    async with httpx.AsyncClient(timeout=15) as client:
        token_res = await client.post(
            TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.gmail_client_id,
                "client_secret": settings.gmail_client_secret,
                "redirect_uri": settings.gmail_redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        if token_res.status_code != 200:
            raise GoogleOAuthError(f"Token exchange failed: {token_res.text[:200]}")
        access_token = token_res.json().get("access_token")
        if not access_token:
            raise GoogleOAuthError("No access token returned")

        info_res = await client.get(USERINFO_URL, headers={"Authorization": f"Bearer {access_token}"})
        if info_res.status_code != 200:
            raise GoogleOAuthError("Failed to fetch user info")
        profile = info_res.json()

    if not profile.get("email") or not profile.get("email_verified"):
        raise GoogleOAuthError("Google account email is not verified")
    return profile
