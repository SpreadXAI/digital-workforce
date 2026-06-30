"""Tactile CloudAgentLab Gateway client."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.tactile_config import TactileRuntimeConfig

logger = logging.getLogger(__name__)


class TactileClient:
    def __init__(self) -> None:
        self._clients: dict[str, httpx.AsyncClient] = {}

    def _client_key(self, config: TactileRuntimeConfig) -> str:
        return f"{config.base_url}|{config.api_key}"

    def _headers(self, config: TactileRuntimeConfig) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if config.api_key:
            headers["X-API-Key"] = config.api_key
        return headers

    async def _get_client(self, config: TactileRuntimeConfig) -> httpx.AsyncClient:
        key = self._client_key(config)
        client = self._clients.get(key)
        if client is None or client.is_closed:
            client = httpx.AsyncClient(
                base_url=config.base_url,
                headers=self._headers(config),
                timeout=httpx.Timeout(120.0, connect=15.0),
            )
            self._clients[key] = client
        return client

    async def close(self) -> None:
        for client in self._clients.values():
            if not client.is_closed:
                await client.aclose()
        self._clients.clear()

    async def _request(self, config: TactileRuntimeConfig, method: str, path: str, **kwargs: Any) -> Any:
        client = await self._get_client(config)
        resp = await client.request(method, path, **kwargs)
        if resp.status_code >= 400:
            logger.error("Tactile %s %s -> %s %s", method, path, resp.status_code, resp.text[:500])
            resp.raise_for_status()
        if resp.status_code == 204:
            return None
        if not resp.content:
            return None
        return resp.json()

    async def health(self, config: TactileRuntimeConfig) -> dict:
        return await self._request(config, "GET", "/api/health")

    async def list_agents(self, config: TactileRuntimeConfig) -> list[dict]:
        data = await self._request(
            config,
            "GET",
            "/api/agent",
            params={"workspace_id": config.workspace_id},
        )
        return data if isinstance(data, list) else data.get("items", data.get("agents", []))

    async def get_agent(self, config: TactileRuntimeConfig, agent_id: int) -> dict:
        return await self._request(config, "GET", f"/api/agent/{agent_id}")

    async def create_work(
        self,
        config: TactileRuntimeConfig,
        *,
        agent_id: int,
        name: str,
        content: str,
        env_vars: list[dict[str, Any]] | None = None,
    ) -> dict:
        payload: dict[str, Any] = {
            "workspace_id": config.workspace_id,
            "agent_id": agent_id,
            "name": name[:200],
            "content": content,
            "machine_type": config.machine_type,
        }
        if env_vars:
            payload["env_vars"] = env_vars
        return await self._request(config, "POST", "/api/work", json=payload)

    async def get_work(self, config: TactileRuntimeConfig, work_id: int) -> dict:
        return await self._request(config, "GET", f"/api/work/{work_id}")

    async def list_works(self, config: TactileRuntimeConfig, *, limit: int = 20) -> list[dict]:
        data = await self._request(
            config,
            "GET",
            "/api/work",
            params={"workspace_id": config.workspace_id, "limit": limit},
        )
        return data if isinstance(data, list) else data.get("items", data.get("works", []))

    async def list_skill_plaza(self, config: TactileRuntimeConfig) -> list[dict]:
        data = await self._request(
            config,
            "GET",
            "/api/skill-plaza",
            params={"workspace_id": config.workspace_id},
        )
        return data if isinstance(data, list) else data.get("items", data.get("skills", []))

    async def get_chat_history(
        self,
        config: TactileRuntimeConfig,
        session_id: str,
        *,
        rounds: int = 20,
    ) -> dict:
        return await self._request(
            config,
            "GET",
            f"/api/chat/{session_id}/history",
            params={"rounds": rounds},
        )

    async def update_agent_bindings(
        self,
        config: TactileRuntimeConfig,
        agent_id: int,
        *,
        skills: list[dict[str, int]],
    ) -> dict:
        return await self._request(
            config,
            "PUT",
            f"/api/agent/{agent_id}/bindings",
            json={"skills": skills},
        )


tactile = TactileClient()
