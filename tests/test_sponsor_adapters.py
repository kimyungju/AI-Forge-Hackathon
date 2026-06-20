import json
import sys
import types
import unittest

import pytest

from app.sponsors import daytona, videodb


class SponsorAdapterTests(unittest.TestCase):
    def test_videodb_fixture_keeps_existing_manifest(self):
        existing = [{"scene_id": "s00", "t_start": 0, "t_end": 4}]

        manifest, receipt = videodb.ingest_creative(
            source=None,
            existing_manifest=existing,
            scenario={"brand": "MerlionTel", "campaign": "Test"},
            mode="fixture",
        )

        self.assertEqual(manifest, existing)
        self.assertIsNone(receipt)

    def test_daytona_fixture_does_not_create_sandboxes(self):
        agents = [{"agent_id": "auntie_1", "kind": "persona", "label": "Auntie"}]

        copied, receipts = daytona.attach_receipts(
            agents,
            daytona.SandboxOptions(mode="fixture", enabled=True),
        )

        self.assertEqual(copied, agents)
        self.assertEqual(receipts, [])
        self.assertIsNot(copied[0], agents[0])


def _install_daytona_sdk(
    monkeypatch: pytest.MonkeyPatch,
    params_name: str,
    params_class=None,
    result: str = '{"receipt": "ok"}',
):
    created_params = []
    code_runs = []

    if params_class is None:
        class FakeParams:
            def __init__(self, *, language: str, env_vars: dict[str, str], auto_stop_interval: int) -> None:
                self.language = language
                self.env_vars = env_vars
                self.auto_stop_interval = auto_stop_interval
    else:
        FakeParams = params_class

    class FakeCodeRunResponse:
        def __init__(self, value: str) -> None:
            self.result = value

    class FakeProcess:
        def code_run(self, code: str) -> FakeCodeRunResponse:
            code_runs.append(code)
            return FakeCodeRunResponse(result)

    class FakeSandbox:
        id = "sandbox-123"
        process = FakeProcess()

    class FakeDaytona:
        def create(self, params) -> FakeSandbox:
            created_params.append(params)
            return FakeSandbox()

        def delete(self, _: FakeSandbox) -> None:
            return None

    module = types.ModuleType("daytona_sdk")
    setattr(module, params_name, FakeParams)
    module.Daytona = FakeDaytona
    monkeypatch.setitem(sys.modules, "daytona_sdk", module)
    return created_params, code_runs


def test_daytona_live_uses_create_sandbox_params_env(monkeypatch: pytest.MonkeyPatch) -> None:
    created_params, _ = _install_daytona_sdk(monkeypatch, "CreateSandboxParams")
    monkeypatch.setenv("DAYTONA_API_KEY", "test-key")

    agents = [{"agent_id": "auntie_1", "kind": "persona", "label": "Auntie"}]
    copied, receipts = daytona.attach_receipts(
        agents,
        daytona.SandboxOptions(mode="live", enabled=True, limit=1),
    )

    assert copied[0]["sandbox_id"] == "sandbox-123"
    assert receipts == [copied[0]["sandbox_receipt"]]
    assert created_params[0].env_vars["PREMORTEM_AGENT_ID"] == "auntie_1"
    assert created_params[0].env_vars["PREMORTEM_AGENT_KIND"] == "persona"


def test_daytona_live_uses_base_params_env(monkeypatch: pytest.MonkeyPatch) -> None:
    created_params, _ = _install_daytona_sdk(monkeypatch, "CreateSandboxBaseParams")
    monkeypatch.setenv("DAYTONA_API_KEY", "test-key")

    agents = [{"agent_id": "itadmin_1", "kind": "stakeholder", "label": "IT Admin"}]
    daytona.attach_receipts(agents, daytona.SandboxOptions(mode="live", enabled=True, limit=1))

    assert created_params[0].env_vars["PREMORTEM_AGENT_ID"] == "itadmin_1"
    assert created_params[0].env_vars["PREMORTEM_AGENT_KIND"] == "stakeholder"


def test_daytona_live_retries_without_auto_stop_interval(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeParams:
        def __init__(self, *, language: str, env_vars: dict[str, str]) -> None:
            self.language = language
            self.env_vars = env_vars

    created_params, _ = _install_daytona_sdk(monkeypatch, "CreateSandboxParams", FakeParams)
    monkeypatch.setenv("DAYTONA_API_KEY", "test-key")

    agents = [{"agent_id": "privacy_1", "kind": "lens", "label": "Privacy"}]
    daytona.attach_receipts(agents, daytona.SandboxOptions(mode="live", enabled=True, limit=1))

    assert created_params[0].language == "python"
    assert created_params[0].env_vars["PREMORTEM_AGENT_ID"] == "privacy_1"
    assert created_params[0].env_vars["PREMORTEM_AGENT_KIND"] == "lens"


def test_daytona_live_retries_with_env_vars_only(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeParams:
        def __init__(self, *, env_vars: dict[str, str]) -> None:
            self.env_vars = env_vars

    created_params, _ = _install_daytona_sdk(monkeypatch, "CreateSandboxParams", FakeParams)
    monkeypatch.setenv("DAYTONA_API_KEY", "test-key")

    agents = [{"agent_id": "legal_1", "kind": "stakeholder", "label": "Legal"}]
    daytona.attach_receipts(agents, daytona.SandboxOptions(mode="live", enabled=True, limit=1))

    assert created_params[0].env_vars["PREMORTEM_AGENT_ID"] == "legal_1"
    assert created_params[0].env_vars["PREMORTEM_AGENT_KIND"] == "stakeholder"


def test_daytona_live_requires_compatible_params_class(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeDaytona:
        pass

    module = types.ModuleType("daytona_sdk")
    module.Daytona = FakeDaytona
    monkeypatch.setitem(sys.modules, "daytona_sdk", module)
    monkeypatch.setenv("DAYTONA_API_KEY", "test-key")

    agents = [{"agent_id": "auntie_1", "kind": "persona", "label": "Auntie"}]
    with pytest.raises(RuntimeError, match="CreateSandboxParams"):
        daytona.attach_receipts(agents, daytona.SandboxOptions(mode="live", enabled=True, limit=1))


def test_daytona_live_applies_sandbox_grounding_result(monkeypatch: pytest.MonkeyPatch) -> None:
    # Given
    sandbox_result = json.dumps(
        {
            "agent_id": "auntie_1",
            "env_agent_id": "auntie_1",
            "grounding_status": "success",
            "grounding": [
                {
                    "id": "auntie_1:news:1",
                    "source": "Google News SG",
                    "url": "https://example.com/news",
                    "text": "Live sandbox scrape",
                }
            ],
        }
    )
    _, code_runs = _install_daytona_sdk(monkeypatch, "CreateSandboxParams", result=sandbox_result)
    monkeypatch.setenv("DAYTONA_API_KEY", "test-key")

    # When
    copied, receipts = daytona.attach_receipts(
        [{"agent_id": "auntie_1", "kind": "persona", "label": "Auntie", "grounding": []}],
        daytona.SandboxOptions(mode="live", enabled=True, limit=1, run_brightdata=True),
    )

    # Then
    assert copied[0]["grounding"][0]["text"] == "Live sandbox scrape"
    assert receipts[0]["grounding_status"] == "success"
    assert receipts[0]["grounding_count"] == 1
    assert "api.brightdata.com/request" in code_runs[0]


def test_videodb_live_falls_back_when_scene_index_shape_unknown(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeSceneExtractionType:
        shot_based = "shot_based"

    class FakeSceneCollection:
        scene_index_id = "scene-index"

    class FakeVideo:
        id = "video-123"

        def generate_transcript(self, *, language_code: str) -> None:
            assert language_code == "en"

        def extract_scenes(self, *, extraction_type: str, extraction_config: dict[str, int]) -> FakeSceneCollection:
            assert extraction_type == "shot_based"
            assert extraction_config["frame_count"] == 1
            return FakeSceneCollection()

        def get_scene_index(self, _: str) -> dict[str, dict[str, str]]:
            return {"unexpected": {"not": "a scene list"}}

        def get_transcript(self, *, start: float, end: float) -> str:
            return f"{start}-{end}"

        def get_transcript_text(self) -> str:
            return "Fallback transcript"

    class FakeConnection:
        def upload(self, *, url: str, name: str, description: str) -> FakeVideo:
            assert url == "https://example.com/ad.mp4"
            assert "MerlionTel" in name
            assert description == "Test campaign"
            return FakeVideo()

    module = types.ModuleType("videodb")
    module.SceneExtractionType = FakeSceneExtractionType
    module.connect = lambda *, api_key: FakeConnection()
    monkeypatch.setitem(sys.modules, "videodb", module)
    monkeypatch.setenv("VIDEODB_API_KEY", "test-key")

    manifest, receipt = videodb.ingest_creative(
        source="https://example.com/ad.mp4",
        existing_manifest=[],
        scenario={"brand": "MerlionTel", "campaign": "Test campaign"},
        mode="live",
    )

    assert manifest[0]["scene_id"] == "s00"
    assert manifest[0]["transcript"] == "Fallback transcript"
    assert manifest[0]["visual_desc"].startswith("VideoDB transcript-only ingest")
    assert receipt is not None
    assert receipt.scenes == 1


if __name__ == "__main__":
    unittest.main()
