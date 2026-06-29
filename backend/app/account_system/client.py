"""SpreadX Account System API client."""

from __future__ import annotations

import logging

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class AccountSystemClient:
    def __init__(self) -> None:
        self.base_url = settings.account_system_base_url.rstrip("/")
        self.api_key = settings.account_system_api_key

    @property
    def configured(self) -> bool:
        return bool(self.base_url and self.api_key)

    async def fetch_cookie(self, username: str) -> str:
        if not self.configured:
            raise RuntimeError("Account System API not configured")
        url = f"{self.base_url}/api/v2/accounts/{username}/cookie"
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(url, headers={"x-api-key": self.api_key})
            resp.raise_for_status()
            body = resp.json()
        if not body.get("success"):
            raise ValueError(body.get("message") or "Account System API error")
        cookie = body.get("data", {}).get("cookie", "").strip()
        if not cookie:
            raise ValueError("Empty cookie in response")
        return cookie


account_system = AccountSystemClient()
