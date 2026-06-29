"""Dispatch work to Tactile Gateway (shared Agent for all employees)."""

from __future__ import annotations

import logging
from typing import Any

from app.tactile.client import tactile
from app.tactile_config import TactileRuntimeConfig, require_agent_id

logger = logging.getLogger(__name__)


def build_env_vars(
    *,
    platform: str | None = None,
    credentials: dict[str, str] | None = None,
    employee_id: int | None = None,
    twitter_handle: str | None = None,
    extra: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    env: dict[str, str] = {}
    if platform:
        env["PLATFORM"] = platform
    if credentials:
        for k, v in credentials.items():
            if v:
                env[k.upper()] = v
    if employee_id is not None:
        env["DW_EMPLOYEE_ID"] = str(employee_id)
    if twitter_handle:
        env["TWITTER_HANDLE"] = twitter_handle.lstrip("@")
    if extra:
        for k, v in extra.items():
            if v is not None:
                env[str(k).upper()] = str(v)
    return [{"env_key": k, "env_value": v, "is_secret": k.endswith("_COOKIE")} for k, v in env.items()]


async def dispatch_work(
    config: TactileRuntimeConfig,
    *,
    title: str,
    content: str,
    platform: str | None = None,
    credentials: dict[str, str] | None = None,
    employee_id: int | None = None,
    twitter_handle: str | None = None,
    extra_env: dict[str, Any] | None = None,
) -> dict:
    agent_id = require_agent_id(config)
    env_vars = build_env_vars(
        platform=platform,
        credentials=credentials,
        employee_id=employee_id,
        twitter_handle=twitter_handle,
        extra=extra_env,
    )
    return await tactile.create_work(
        config,
        agent_id=agent_id,
        name=title,
        content=content,
        env_vars=env_vars,
    )
