from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Protocol, Sequence


class VideoReceiptLike(Protocol):
    provider: str
    scenes: int
    source: str


@dataclass(frozen=True, slots=True)
class SponsorTraceInputs:
    provider: str
    reaction_count: int
    grounding_receipts: Sequence[Mapping[str, str | int]]
    sandbox_receipts: Sequence[Mapping[str, str | int]]
    video_receipt: VideoReceiptLike | None = None


def build_sponsor_trace(inputs: SponsorTraceInputs) -> list[dict[str, str]]:
    trace = [_panel_trace(inputs.provider, inputs.reaction_count)]
    if inputs.grounding_receipts:
        trace.append(_grounding_trace(inputs.grounding_receipts))
    if inputs.sandbox_receipts:
        trace.append(_sandbox_trace(inputs.sandbox_receipts))
    if inputs.video_receipt:
        trace.append({
            "sponsor": inputs.video_receipt.provider,
            "role": "creative ingestion",
            "detail": f"1 film, {inputs.video_receipt.scenes} scenes from {inputs.video_receipt.source}",
        })
    return trace


def _panel_trace(provider: str, reaction_count: int) -> dict[str, str]:
    sponsors = {"kimi": "Kimi K2.6", "openai": "OpenAI-compatible"}
    return {
        "sponsor": sponsors.get(provider, provider),
        "role": "60-agent multimodal panel",
        "detail": f"{reaction_count} agent calls requested via {provider}",
    }


def _grounding_trace(receipts: Sequence[Mapping[str, str | int]]) -> dict[str, str]:
    success = _count_status(receipts, "status", "success")
    fallback = _count_status(receipts, "status", "fallback")
    fixture = _count_status(receipts, "status", "fixture")
    snippets = sum(int(receipt.get("snippets", 0)) for receipt in receipts)
    return {
        "sponsor": "Bright Data",
        "role": "per-agent self-grounding",
        "detail": (
            f"{success} live-grounded, {fallback} fallback, {fixture} fixture, "
            f"{snippets} snippets"
        ),
    }


def _sandbox_trace(receipts: Sequence[Mapping[str, str | int]]) -> dict[str, str]:
    grounded = _count_status(receipts, "grounding_status", "success")
    snippets = sum(int(receipt.get("grounding_count", 0)) for receipt in receipts)
    return {
        "sponsor": "Daytona",
        "role": "per-agent sandbox isolation",
        "detail": f"{len(receipts)} sandboxes, {grounded} sandbox scrapes, {snippets} snippets",
    }


def _count_status(receipts: Sequence[Mapping[str, str | int]], field: str, status: str) -> int:
    return sum(1 for receipt in receipts if receipt.get(field) == status)
