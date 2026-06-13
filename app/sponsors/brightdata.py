"""Bright Data per-agent grounding adapter.

Each agent grounds ITSELF: it runs its own personalised `grounding_query` and gets back a small
pack of public snippets relevant to its lens. This is the contract the offline bake job calls once
per agent (60x) to build golden_run.json. The live path is gated on creating the Bright Data
Unlocker + SERP zones (.env: BRIGHTDATA_UNLOCKER_ZONE / BRIGHTDATA_SERP_ZONE, currently empty).

Fixture mode needs no network and no deps.
"""
from __future__ import annotations

import os

REQ = "https://api.brightdata.com/request"


def ground(agent: dict, scenario: dict | None = None, mode: str = "fixture") -> list[dict]:
    """Return a grounding pack [{id, source, url, text}] for ONE agent.

    `agent` carries `agent_id` and `grounding_query`. Fixture mode returns whatever the baked
    golden run already attached to the agent; live mode runs the agent's own query.
    """
    if mode == "fixture":
        return agent.get("grounding", [])
    return _live(agent, scenario or {})


def _live(agent: dict, scenario: dict) -> list[dict]:
    token = os.environ.get("BRIGHTDATA_API_KEY")
    serp_zone = os.environ.get("BRIGHTDATA_SERP_ZONE")
    unlocker_zone = os.environ.get("BRIGHTDATA_UNLOCKER_ZONE")
    if not (token and serp_zone and unlocker_zone):
        raise RuntimeError(
            "Bright Data live grounding needs BRIGHTDATA_API_KEY + a SERP zone + an Unlocker zone. "
            "Create both zones in the Bright Data console and set them in .env."
        )

    import requests  # only needed for live calls; fixture mode stays dependency-free

    q = agent["grounding_query"]
    headers = {"Authorization": f"Bearer {token}"}
    snippets: list[dict] = []

    # 1) Google News SG via the SERP zone (every agent gets a news pass)
    news = requests.post(REQ, headers=headers, json={
        "zone": serp_zone, "format": "raw",
        "url": f"https://www.google.com/search?q={q}&tbm=nws&gl=sg&hl=en&brd_json=1",
    }, timeout=20)
    snippets += _parse_news(news, agent["agent_id"])

    # 2) r/singapore / forum via the Unlocker zone, only when the query targets it
    if "r/singapore" in q or "reddit" in q.lower():
        topic = q.replace("r/singapore", "").strip()
        red = requests.post(REQ, headers=headers, json={
            "zone": unlocker_zone, "format": "raw",
            "url": f"https://www.reddit.com/r/singapore/search.json?q={topic}&restrict_sr=1&limit=10",
        }, timeout=20)
        snippets += _parse_reddit(red, agent["agent_id"])

    return _fence(snippets[:3])


# --- response parsers: map live payloads -> {id, source, url, text}. Wire when zones exist. ---
def _parse_news(resp, aid):  # pragma: no cover - shape depends on live response
    return []  # TODO: brd_json news items -> snippets (source "Google News SG")


def _parse_reddit(resp, aid):  # pragma: no cover
    return []  # TODO: listing children -> snippets (source "r/singapore")


def _fence(snippets: list[dict]) -> list[dict]:
    """Prompt-injection + PDPA defense: strip @handles / u/usernames before the text ever
    reaches a model prompt. (The scraped text is untrusted; this is why each agent is sandboxed.)"""
    import re

    out = []
    for s in snippets:
        text = re.sub(r"/u/\w+|@\w+", "[user]", s.get("text", ""))
        out.append({**s, "text": text.strip()})
    return out
