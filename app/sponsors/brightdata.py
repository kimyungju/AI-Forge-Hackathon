"""Bright Data per-agent grounding adapter.

Each agent grounds ITSELF: it runs its own personalised `grounding_query` and gets back a small
pack of public snippets relevant to its lens. This is the contract the offline bake job calls once
per agent (60x) to build golden_run.json. The live path is gated on creating the Bright Data
Unlocker + SERP zones (.env: BRIGHTDATA_UNLOCKER_ZONE / BRIGHTDATA_SERP_ZONE, currently empty).

Fixture mode needs no network and no deps.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Mapping
from urllib.parse import quote_plus

REQ = "https://api.brightdata.com/request"


class BrightDataGroundingError(RuntimeError):
    def __init__(self, detail: str) -> None:
        self.detail = detail
        super().__init__(detail)


@dataclass(frozen=True, slots=True)
class GroundingOptions:
    mode: str = "fixture"
    scenario: Mapping[str, str] | None = None
    allow_baked_fallback: bool = False


@dataclass(frozen=True, slots=True)
class GroundingReceipt:
    agent_id: str
    status: str
    source: str
    snippets: int
    detail: str

    def as_json(self) -> dict[str, str | int]:
        return {
            "agent_id": self.agent_id,
            "status": self.status,
            "source": self.source,
            "snippets": self.snippets,
            "detail": self.detail,
        }


@dataclass(frozen=True, slots=True)
class GroundingResult:
    snippets: list[dict[str, str]]
    receipt: GroundingReceipt


def ground(agent: dict, scenario: dict | None = None, mode: str = "fixture") -> list[dict]:
    """Return a grounding pack [{id, source, url, text}] for ONE agent.

    `agent` carries `agent_id` and `grounding_query`. Fixture mode returns whatever the baked
    golden run already attached to the agent; live mode runs the agent's own query.
    """
    return ground_with_receipt(
        agent,
        GroundingOptions(mode=mode, scenario=scenario or {}, allow_baked_fallback=True),
    ).snippets


def ground_with_receipt(agent: dict, options: GroundingOptions) -> GroundingResult:
    agent_id = str(agent["agent_id"])
    if options.mode == "fixture":
        snippets = _baked_grounding(agent)
        return GroundingResult(
            snippets=snippets,
            receipt=GroundingReceipt(
                agent_id=agent_id,
                status="fixture",
                source="baked",
                snippets=len(snippets),
                detail="fixture grounding reused",
            ),
        )

    try:
        snippets = _live(agent, dict(options.scenario or {}))
    except BrightDataGroundingError as exc:
        return _fallback_or_raise(agent, options, exc.detail)

    if snippets:
        return GroundingResult(
            snippets=snippets,
            receipt=GroundingReceipt(
                agent_id=agent_id,
                status="success",
                source="brightdata",
                snippets=len(snippets),
                detail="live Bright Data grounding parsed",
            ),
        )
    return _fallback_or_raise(agent, options, "live Bright Data returned no snippets")


def _live(agent: dict, scenario: dict) -> list[dict]:
    token = os.environ.get("BRIGHTDATA_API_KEY")
    serp_zone = os.environ.get("BRIGHTDATA_SERP_ZONE")
    unlocker_zone = os.environ.get("BRIGHTDATA_UNLOCKER_ZONE")
    if not (token and serp_zone and unlocker_zone):
        raise BrightDataGroundingError(
            "Bright Data live grounding needs BRIGHTDATA_API_KEY + a SERP zone + an Unlocker zone. "
            "Create both zones in the Bright Data console and set them in .env."
        )

    import requests  # only needed for live calls; fixture mode stays dependency-free

    q = agent["grounding_query"]
    headers = {"Authorization": f"Bearer {token}"}
    snippets: list[dict] = []

    encoded = quote_plus(q)
    try:
        news = requests.post(REQ, headers=headers, json={
            "zone": serp_zone, "format": "raw",
            "url": f"https://www.google.com/search?q={encoded}&tbm=nws&gl=sg&hl=en&brd_json=1",
        }, timeout=20)
        news.raise_for_status()
    except requests.RequestException as exc:
        raise BrightDataGroundingError(f"Google News request failed: {exc}") from exc
    snippets += _parse_news(news, agent["agent_id"])

    if "r/singapore" in q or "reddit" in q.lower():
        topic = q.replace("r/singapore", "").strip()
        try:
            red = requests.post(REQ, headers=headers, json={
                "zone": unlocker_zone, "format": "raw",
                "url": (
                    "https://www.reddit.com/r/singapore/search.json"
                    f"?q={quote_plus(topic)}&restrict_sr=1&limit=10"
                ),
            }, timeout=20)
            red.raise_for_status()
        except requests.RequestException as exc:
            raise BrightDataGroundingError(f"Reddit request failed: {exc}") from exc
        snippets += _parse_reddit(red, agent["agent_id"])

    return _fence(snippets[:3])


def _parse_news(resp, aid: str) -> list[dict[str, str]]:
    payload = _response_payload(resp)
    items = []
    items.extend(payload.get("news") or [])
    top_stories = payload.get("top_stories") or {}
    if not isinstance(top_stories, dict):
        top_stories = {}
    items.extend(top_stories.get("items") or [])
    for article_set in payload.get("article_sets") or []:
        if not isinstance(article_set, dict):
            continue
        items.extend(article_set.get("items") or [])
        items.extend(article_set.get("posts") or [])

    snippets: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in items:
        if not isinstance(item, dict):
            continue
        text = _news_text(item)
        url = _clean(item.get("link"))
        key = url or text
        if not text or key in seen:
            continue
        seen.add(key)
        snippets.append({
            "id": f"{aid}:news:{len(snippets) + 1}",
            "source": "Google News SG",
            "url": url,
            "text": text,
        })
    return snippets


def _parse_reddit(resp, aid: str) -> list[dict[str, str]]:
    payload = _response_payload(resp)
    data = payload.get("data") or payload
    if not isinstance(data, dict):
        return []
    children = data.get("children") or []
    snippets: list[dict[str, str]] = []
    for child in children:
        if not isinstance(child, dict):
            continue
        post = child.get("data") or child
        if not isinstance(post, dict):
            continue
        title = _clean(post.get("title"))
        body = _clean(post.get("selftext") or post.get("text"))
        text = _join_parts(title, body)
        if not text:
            continue
        snippets.append({
            "id": f"{aid}:reddit:{len(snippets) + 1}",
            "source": _clean(post.get("subreddit_name_prefixed")) or "r/singapore",
            "url": _reddit_url(_clean(post.get("permalink") or post.get("url"))),
            "text": text,
        })
    return snippets


def _fence(snippets: list[dict]) -> list[dict]:
    """Prompt-injection + PDPA defense: strip @handles / u/usernames before the text ever
    reaches a model prompt. (The scraped text is untrusted; this is why each agent is sandboxed.)"""
    out = []
    for s in snippets:
        text = re.sub(r"/u/\w+|@\w+", "[user]", s.get("text", ""))
        out.append({**s, "text": text.strip()})
    return out


def _fallback_or_raise(agent: dict, options: GroundingOptions, detail: str) -> GroundingResult:
    if not options.allow_baked_fallback:
        raise BrightDataGroundingError(f"{agent['agent_id']}: {detail}")
    snippets = _baked_grounding(agent)
    return GroundingResult(
        snippets=snippets,
        receipt=GroundingReceipt(
            agent_id=str(agent["agent_id"]),
            status="fallback",
            source="baked",
            snippets=len(snippets),
            detail=f"{detail}; using baked grounding",
        ),
    )


def _baked_grounding(agent: dict) -> list[dict[str, str]]:
    return list(agent.get("grounding", []))


def _response_payload(resp) -> dict:
    try:
        payload = resp.json()
    except ValueError:
        payload = json.loads(getattr(resp, "text", "{}") or "{}")
    if isinstance(payload, dict):
        return payload
    return {}


def _news_text(item) -> str:
    publisher = _clean(item.get("source"))
    title = _clean(item.get("title"))
    description = _clean(item.get("description") or item.get("story") or item.get("text"))
    date = _clean(item.get("date"))
    return _join_parts(publisher, title, description, date)


def _join_parts(*parts: str) -> str:
    return " — ".join(part for part in parts if part)[:480]


def _clean(value) -> str:
    return str(value or "").strip()


def _reddit_url(value: str) -> str:
    if value.startswith("http"):
        return value
    if value.startswith("/"):
        return f"https://www.reddit.com{value}"
    return value
