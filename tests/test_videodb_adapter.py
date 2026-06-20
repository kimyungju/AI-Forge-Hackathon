import sys
import types

from app.sponsors import videodb


def test_videodb_live_uses_scene_collection_scenes_when_index_id_absent(monkeypatch) -> None:
    # Given
    class FakeSceneExtractionType:
        shot_based = "shot_based"

    class FakeFrame:
        url = "https://example.com/frame.jpg"

    class FakeScene:
        id = "scene-1"
        start = 2
        end = 6
        frames = [FakeFrame()]

        def describe(self, *, prompt: str, model_config: dict[str, str | float]) -> str:
            assert "campaign-risk dashboard" in prompt
            assert model_config["model_name"] == "pro"
            return "A flower opens in a short close-up shot."

    class FakeSceneCollection:
        id = "collection-123"
        scenes = [FakeScene()]

    class FakeVideo:
        id = "video-123"

        def generate_transcript(self, *, language_code: str) -> None:
            assert language_code == "en"

        def extract_scenes(self, *, extraction_type: str, extraction_config: dict[str, int]) -> FakeSceneCollection:
            assert extraction_type == "shot_based"
            assert extraction_config["frame_count"] == 1
            return FakeSceneCollection()

        def get_scene_index(self, _: str):
            raise AssertionError("scene_index_id fallback should not be used when scenes are present")

        def get_transcript(self, *, start: float, end: float) -> str:
            assert start == 2.0
            assert end == 6.0
            return "Flower transcript"

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

    # When
    manifest, receipt = videodb.ingest_creative(
        source="https://example.com/ad.mp4",
        existing_manifest=[],
        scenario={"brand": "MerlionTel", "campaign": "Test campaign"},
        mode="live",
    )

    # Then
    assert manifest == [
        {
            "scene_id": "s02",
            "t_start": 2,
            "t_end": 6,
            "keyframe": "https://example.com/frame.jpg",
            "visual_desc": "A flower opens in a short close-up shot.",
            "transcript": "Flower transcript",
            "on_screen_text": "",
        }
    ]
    assert receipt is not None
    assert receipt.scenes == 1
