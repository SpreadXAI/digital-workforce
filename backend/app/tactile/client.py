"""Tactile API client (minimal subset for digital workforce)."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class TactileClient:
    def __init__(self) -> None:
        self.base_url = settings.tactile_base_url.rstrip("/")
        self.api_key = settings.tactile_api_key
        self.workspace_id = settings.tactile_workspace_id
        self._client: httpx.AsyncClient | None = None

    @property
    def configured(self) -> bool:
        return bool(self.api_key and self.workspace_id)

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=self._headers(),
                timeout=httpx.Timeout(60.0, connect=10.0),
            )
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        client = await self._get_client()
        resp = await client.request(method, path, **kwargs)
        if resp.status_code >= 400:
            logger.error("Tactile %s %s -> %s %s", method, path, resp.status_code, resp.text[:500])
            resp.raise_for_status()
        if resp.status_code == 204:
            return None
        return resp.json()

    async def list_agents(self) -> list[dict]:
        data = await self._request("GET", "/api/v1/agents")
        return data if isinstance(data, list) else data.get("items", data.get("agents", []))

    async def get_agent(self, agent_id: int) -> dict:
        return await self._request("GET", f"/api/v1/agents/{agent_id}")

    async def create_agent(self, name: str, instructions: str = "", model: str = "gpt-4o") -> dict:
        return await self._request(
            "POST",
            "/api/v1/agents",
            json={
                "name": name,
                "instructions": instructions,
                "model": model,
                "workspace_id": self.workspace_id,
            },
        )

    async def update_agent(self, agent_id: int, **fields: Any) -> dict:
        return await self._request("PATCH", f"/api/v1/agents/{agent_id}", json=fields)

    async def list_skills(self, agent_id: int) -> list[dict]:
        data = await self._request("GET", f"/api/v1/agents/{agent_id}/skills")
        return data if isinstance(data, list) else data.get("items", data.get("skills", []))

    async def install_skill(self, agent_id: int, skill_id: int) -> dict:
        return await self._request(
            "POST",
            f"/api/v1/agents/{agent_id}/skills",
            json={"skill_id": skill_id},
        )

    async def list_works(self, agent_id: int, limit: int = 20) -> list[dict]:
        data = await self._request("GET", f"/api/v1/agents/{agent_id}/works", params={"limit": limit})
        return data if isinstance(data, list) else data.get("items", data.get("works", []))

    async def get_work(self, work_id: int) -> dict:
        return await self._request("GET", f"/api/v1/works/{work_id}")

    async def create_work(
        self,
        agent_id: int,
        content: str,
        *,
        dispatch_env_json: str | None = None,
    ) -> dict:
        payload: dict[str, Any] = {"agent_id": agent_id, "content": content}
        if dispatch_env_json:
            payload["dispatch_env_json"] = dispatch_env_json
        return await self._request("POST", "/api/v1/works", json=payload)

    async def list_skill_plaza(self) -> list[dict]:
        data = await self._request("GET", "/api/v1/skill-plaza")
        return data if isinstance(data, list) else data.get("items", data.get("skills", []))


tactile = TactileClient()
