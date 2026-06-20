import pytest

from app.sponsors import brightdata


class _FakeBrightDataResponse:
    def __init__(self, payload: dict) -> None:
        self._payload = payload

    def json(self) -> dict:
        return self._payload


def test_brightdata_parse_news_from_fast_serp_payload() -> None:
    # Given
    payload = {
        "news": [
            {
                "title": "Telco privacy launch triggers concern",
                "link": "https://example.com/privacy",
                "source": "Example News",
                "description": "Advocates question whether calls are analyzed.",
                "date": "2 hours ago",
            },
            {"title": "", "link": "https://example.com/empty"},
        ],
        "article_sets": [
            {
                "heading": "Related",
                "items": [
                    {
                        "title": "Regulators ask for consent details",
                        "link": "https://example.com/regulators",
                        "source": "Business Daily",
                        "story": "PDPA lawyers want clearer opt-outs.",
                    }
                ],
            }
        ],
    }

    # When
    snippets = brightdata._parse_news(_FakeBrightDataResponse(payload), "agent_1")

    # Then
    assert len(snippets) == 2
    assert snippets[0]["id"] == "agent_1:news:1"
    assert snippets[0]["source"] == "Google News SG"
    assert snippets[0]["url"] == "https://example.com/privacy"
    assert "Example News" in snippets[0]["text"]
    assert "Telco privacy launch" in snippets[0]["text"]
    assert snippets[1]["id"] == "agent_1:news:2"
    assert "Regulators ask" in snippets[1]["text"]


def test_brightdata_parse_reddit_listing_and_fence_handles() -> None:
    # Given
    payload = {
        "data": {
            "children": [
                {
                    "data": {
                        "title": "Anyone worried about always-on call analysis?",
                        "selftext": "Ask /u/privacyhawk or @telco_support before trusting this.",
                        "permalink": "/r/singapore/comments/abc123/privacy/",
                        "subreddit_name_prefixed": "r/singapore",
                    }
                }
            ]
        }
    }

    # When
    snippets = brightdata._fence(brightdata._parse_reddit(_FakeBrightDataResponse(payload), "agent_2"))

    # Then
    assert snippets == [
        {
            "id": "agent_2:reddit:1",
            "source": "r/singapore",
            "url": "https://www.reddit.com/r/singapore/comments/abc123/privacy/",
            "text": "Anyone worried about always-on call analysis? — Ask [user] or [user] before trusting this.",
        }
    ]


def test_brightdata_live_empty_requires_explicit_baked_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    # Given
    agent = {
        "agent_id": "privacy_1",
        "grounding_query": "MerlionTel privacy",
        "grounding": [{"id": "baked", "source": "fixture", "url": "", "text": "baked"}],
    }
    monkeypatch.setattr(brightdata, "_live", lambda _agent, _scenario: [])

    # When
    with pytest.raises(RuntimeError, match="returned no snippets"):
        brightdata.ground_with_receipt(
            agent,
            brightdata.GroundingOptions(mode="live", scenario={}, allow_baked_fallback=False),
        )

    # Then
    result = brightdata.ground_with_receipt(
        agent,
        brightdata.GroundingOptions(mode="live", scenario={}, allow_baked_fallback=True),
    )

    assert result.snippets == agent["grounding"]
    assert result.receipt.as_json()["status"] == "fallback"
