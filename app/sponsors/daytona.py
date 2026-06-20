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
    env_agent_id: str
    grounding_status: str
    grounding_count: int

    def as_json(self) -> dict[str, str | int]:
        return {
            "agent_id": self.agent_id,
            "sandbox_id": self.sandbox_id,
            "result": self.result,
            "elapsed_ms": self.elapsed_ms,
            "env_agent_id": self.env_agent_id,
            "grounding_status": self.grounding_status,
            "grounding_count": self.grounding_count,
        }


@dataclass(frozen=True, slots=True)
class SandboxOptions:
    mode: str = "fixture"
    enabled: bool = False
    limit: int = 0
    keep: bool = False
    run_brightdata: bool = False
    allow_baked_grounding: bool = False


def attach_receipts(agents, options: SandboxOptions | None = None):
    opts = options or SandboxOptions()
    copied = [dict(agent) for agent in agents]
    if opts.mode == "fixture" or not opts.enabled:
        return copied, []

    if not os.environ.get("DAYTONA_API_KEY"):
        raise RuntimeError("Daytona sandbox receipts need DAYTONA_API_KEY set in .env")

    import daytona_sdk
    from daytona_sdk import Daytona

    daytona = Daytona()
    params_cls = _resolve_params_class(daytona_sdk)
    selected = copied[:opts.limit] if opts.limit else copied
    receipts = []
    for agent in selected:
        start = time.monotonic()
        sandbox = _create_sandbox(daytona, params_cls, _env_vars(agent, opts))
        try:
            response = sandbox.process.code_run(_receipt_probe(agent, opts))
            elapsed = int((time.monotonic() - start) * 1000)
            raw_result = str(getattr(response, "result", response)).strip()
            data = _json_result(raw_result)
            grounding = _grounding_from_data(data)
            status = str(data.get("grounding_status", "probe"))
            if grounding:
                agent["grounding"] = grounding
            if opts.run_brightdata and (status != "success" or not grounding) and not opts.allow_baked_grounding:
                detail = data.get("grounding_error") or status
                raise RuntimeError(f"Daytona Bright Data grounding failed for {agent['agent_id']}: {detail}")
            receipt = SandboxReceipt(
                agent_id=agent["agent_id"],
                sandbox_id=_sandbox_id(sandbox),
                result=raw_result,
                elapsed_ms=elapsed,
                env_agent_id=str(data.get("env_agent_id", "")),
                grounding_status=status,
                grounding_count=len(grounding),
            )
            agent["sandbox_id"] = receipt.sandbox_id
            agent["sandbox_receipt"] = receipt.as_json()
            receipts.append(agent["sandbox_receipt"])
        finally:
            if not opts.keep:
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


def _env_vars(agent, options: SandboxOptions) -> dict[str, str]:
    env_vars = {
        "PREMORTEM_AGENT_ID": agent["agent_id"],
        "PREMORTEM_AGENT_KIND": agent["kind"],
    }
    if options.run_brightdata:
        for name in ("BRIGHTDATA_API_KEY", "BRIGHTDATA_SERP_ZONE", "BRIGHTDATA_UNLOCKER_ZONE"):
            value = os.environ.get(name)
            if value:
                env_vars[name] = value
    return env_vars


def _create_sandbox(daytona, params_cls, env_vars):
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


def _receipt_probe(agent, options: SandboxOptions):
    payload = {
        "agent_id": agent["agent_id"],
        "kind": agent["kind"],
        "label": agent["label"],
        "grounding_query": agent.get("grounding_query", ""),
        "run_brightdata": options.run_brightdata,
    }
    return f"""
import json
import os
import re
import urllib.parse
import urllib.request

REQ = "https://api.brightdata.com/request"
payload = json.loads({json.dumps(json.dumps(payload, ensure_ascii=True))})

def clean(value):
    return str(value or "").strip()

def joined(*parts):
    return " — ".join(part for part in parts if part)[:480]

def request(zone, url):
    body = json.dumps({{"zone": zone, "format": "raw", "url": url}}).encode("utf-8")
    req = urllib.request.Request(
        REQ,
        data=body,
        headers={{
            "Authorization": "Bearer " + os.environ.get("BRIGHTDATA_API_KEY", ""),
            "Content-Type": "application/json",
        }},
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8") or "{{}}")

def parse_news(data):
    items = list(data.get("news") or [])
    items += list((data.get("top_stories") or {{}}).get("items") or [])
    for group in data.get("article_sets") or []:
        items += list(group.get("items") or [])
        items += list(group.get("posts") or [])
    snippets = []
    seen = set()
    for item in items:
        text = joined(clean(item.get("source")), clean(item.get("title")), clean(item.get("description") or item.get("story") or item.get("text")), clean(item.get("date")))
        url = clean(item.get("link"))
        key = url or text
        if text and key not in seen:
            seen.add(key)
            snippets.append({{"id": f"{{payload['agent_id']}}:news:{{len(snippets) + 1}}", "source": "Google News SG", "url": url, "text": text}})
    return snippets

def reddit_url(value):
    if value.startswith("http"):
        return value
    return "https://www.reddit.com" + value if value.startswith("/") else value

def parse_reddit(data):
    children = (data.get("data") or data).get("children") or []
    snippets = []
    for child in children:
        post = child.get("data") or child
        text = joined(clean(post.get("title")), clean(post.get("selftext") or post.get("text")))
        if text:
            snippets.append({{"id": f"{{payload['agent_id']}}:reddit:{{len(snippets) + 1}}", "source": clean(post.get("subreddit_name_prefixed")) or "r/singapore", "url": reddit_url(clean(post.get("permalink") or post.get("url"))), "text": text}})
    return snippets

result = {{
    "agent_id": payload["agent_id"],
    "kind": payload["kind"],
    "label": payload["label"],
    "env_agent_id": os.environ.get("PREMORTEM_AGENT_ID", ""),
    "grounding_status": "skipped",
    "grounding": [],
}}
if payload["run_brightdata"]:
    token = os.environ.get("BRIGHTDATA_API_KEY")
    serp_zone = os.environ.get("BRIGHTDATA_SERP_ZONE")
    unlocker_zone = os.environ.get("BRIGHTDATA_UNLOCKER_ZONE")
    if token and serp_zone and unlocker_zone:
        try:
            query = payload["grounding_query"]
            encoded = urllib.parse.quote_plus(query)
            grounding = parse_news(request(serp_zone, f"https://www.google.com/search?q={{encoded}}&tbm=nws&gl=sg&hl=en&brd_json=1"))
            if "r/singapore" in query or "reddit" in query.lower():
                topic = urllib.parse.quote_plus(query.replace("r/singapore", "").strip())
                grounding += parse_reddit(request(unlocker_zone, f"https://www.reddit.com/r/singapore/search.json?q={{topic}}&restrict_sr=1&limit=10"))
            result["grounding"] = [
                {{**item, "text": re.sub(r"/u/\\w+|@\\w+", "[user]", item["text"]).strip()}}
                for item in grounding[:3]
            ]
            result["grounding_status"] = "success" if result["grounding"] else "empty"
        except Exception as exc:
            result["grounding_status"] = "error"
            result["grounding_error"] = type(exc).__name__ + ": " + str(exc)
    else:
        result["grounding_status"] = "error"
        result["grounding_error"] = "missing Bright Data env"
print(json.dumps(result, ensure_ascii=False, sort_keys=True))
"""


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


def _json_result(raw_result: str):
    for line in reversed(raw_result.splitlines() or [raw_result]):
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict):
            return data
    return {}


def _grounding_from_data(data) -> list[dict[str, str]]:
    snippets = []
    for item in data.get("grounding") or []:
        if not isinstance(item, dict):
            continue
        text = str(item.get("text") or "").strip()
        if not text:
            continue
        snippets.append({
            "id": str(item.get("id") or ""),
            "source": str(item.get("source") or ""),
            "url": str(item.get("url") or ""),
            "text": text,
        })
    return snippets
