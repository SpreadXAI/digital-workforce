"""Dispatch work to Tactile with runtime ENV."""

from __future__ import annotations

import json
import logging
from typing import Any

from app.tactile.client import tactile

logger = logging.getLogger(__name__)


def build_dispatch_env(
    *,
    platform: str | None = None,
    credentials: dict[str, str] | None = None,
    employee_id: int | None = None,
    twitter_handle: str | None = None,
    extra: dict[str, Any] | None = None,
) -> str:
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
    return json.dumps(env, ensure_ascii=False)


async def dispatch_work(
    agent_id: int,
    content: str,
    *,
    platform: str | None = None,
    credentials: dict[str, str] | None = None,
    employee_id: int | None = None,
    twitter_handle: str | None = None,
    extra_env: dict[str, Any] | None = None,
) -> dict:
    dispatch_env_json = build_dispatch_env(
        platform=platform,
        credentials=credentials,
        employee_id=employee_id,
        twitter_handle=twitter_handle,
        extra=extra_env,
    )
    return await tactile.create_work(
        agent_id,
        content,
        dispatch_env_json=dispatch_env_json,
    )
