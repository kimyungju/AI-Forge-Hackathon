from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass


LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class SandboxReceipt:
    agent_id: str
    sandbox_id: str
    result: str
    elapsed_ms: int


def attach_receipts(agents, mode="fixture", enabled=False, limit=0, keep=False):
    copied = [dict(agent) for agent in agents]
    if mode == "fixture" or not enabled:
        return copied, []

    if not os.environ.get("DAYTONA_API_KEY"):
        raise RuntimeError("Daytona sandbox receipts need DAYTONA_API_KEY set in .env")

    import daytona_sdk
    from daytona_sdk import Daytona

    daytona = Daytona()
    params_cls = _resolve_params_class(daytona_sdk)
    selected = copied[:limit] if limit else copied
    receipts = []
    for agent in selected:
        start = time.monotonic()
        sandbox = _create_sandbox(daytona, params_cls, agent)
        try:
            response = sandbox.process.code_run(_receipt_probe(agent))
            elapsed = int((time.monotonic() - start) * 1000)
            receipt = SandboxReceipt(
                agent_id=agent["agent_id"],
                sandbox_id=_sandbox_id(sandbox),
                result=str(getattr(response, "result", response)).strip(),
                elapsed_ms=elapsed,
            )
            agent["sandbox_id"] = receipt.sandbox_id
            agent["sandbox_receipt"] = {
                "agent_id": receipt.agent_id,
                "sandbox_id": receipt.sandbox_id,
                "result": receipt.result,
                "elapsed_ms": receipt.elapsed_ms,
            }
            receipts.append(agent["sandbox_receipt"])
        finally:
            if not keep:
                try:
                    daytona.delete(sandbox)
                except Exception:  # noqa: BROAD_EXCEPT_OK
                    LOGGER.warning("failed to delete Daytona sandbox %s", _sandbox_id(sandbox), exc_info=True)
    return copied, receipts


def _resolve_params_class(daytona_sdk):
    for name in ("CreateSandboxParams", "CreateSandboxBaseParams"):
        params_cls = getattr(daytona_sdk, name, None)
        if params_cls is not None:
            return params_cls
    raise RuntimeError("Daytona SDK must expose CreateSandboxParams or CreateSandboxBaseParams")


def _create_sandbox(daytona, params_cls, agent):
    env_vars = {
        "PREMORTEM_AGENT_ID": agent["agent_id"],
        "PREMORTEM_AGENT_KIND": agent["kind"],
    }
    params = _create_params(params_cls, env_vars)
    return daytona.create(params)


def _create_params(params_cls, env_vars):
    attempts = (
        {"language": "python", "env_vars": env_vars, "auto_stop_interval": 10},
        {"language": "python", "env_vars": env_vars},
        {"env_vars": env_vars},
    )
    last_error = None
    for kwargs in attempts:
        try:
            return params_cls(**kwargs)
        except TypeError as exc:
            last_error = exc
    raise RuntimeError("Daytona SDK params class does not support sandbox env_vars") from last_error


def _receipt_probe(agent):
    payload = {
        "agent_id": agent["agent_id"],
        "kind": agent["kind"],
        "label": agent["label"],
    }
    return (
        "import json, os\n"
        f"payload = {json.dumps(payload, ensure_ascii=False)!r}\n"
        "data = json.loads(payload)\n"
        "data['env_agent_id'] = os.environ.get('PREMORTEM_AGENT_ID', '')\n"
        "print(json.dumps(data, ensure_ascii=False, sort_keys=True))\n"
    )


def _sandbox_id(sandbox):
    for name in ("id", "sandbox_id"):
        value = getattr(sandbox, name, None)
        if value:
            return str(value)
    info = getattr(sandbox, "info", None)
    for name in ("id", "sandbox_id"):
        value = getattr(info, name, None)
        if value:
            return str(value)
    return "unknown"
