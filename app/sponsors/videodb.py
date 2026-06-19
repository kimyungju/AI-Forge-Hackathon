from __future__ import annotations

import os
from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class VideoDbReceipt:
    provider: str
    video_id: str
    source: str
    scenes: int
    mode: str


def ingest_creative(source, existing_manifest, scenario, mode="fixture"):
    if mode == "fixture" or not source:
        return list(existing_manifest), None

    key = os.environ.get("VIDEODB_API_KEY")
    if not key:
        raise RuntimeError("VideoDB ingest needs VIDEODB_API_KEY set in .env")

    import videodb
    from videodb import SceneExtractionType

    conn = videodb.connect(api_key=key)
    video = _upload(conn, source, scenario)
    video.generate_transcript(language_code="en")

    scene_collection = video.extract_scenes(
        extraction_type=SceneExtractionType.shot_based,
        extraction_config={"threshold": 20, "frame_count": 1},
    )
    raw_scenes = video.get_scene_index(scene_collection.scene_index_id)
    manifest = _normalize_scenes(video, raw_scenes)
    if not manifest:
        manifest = _transcript_manifest(video)

    receipt = VideoDbReceipt(
        provider="VideoDB",
        video_id=str(_first_attr(video, ("id", "video_id"), "unknown")),
        source=str(source),
        scenes=len(manifest),
        mode="live",
    )
    return manifest, receipt


def _upload(conn, source, scenario):
    name = f"{scenario.get('brand', 'Premortem')} campaign film"
    description = scenario.get("campaign", "Premortem campaign creative")
    if str(source).startswith(("http://", "https://")):
        return conn.upload(url=source, name=name, description=description)
    return conn.upload(file_path=source, name=name, description=description)


def _normalize_scenes(video, raw_scenes):
    manifest = []
    for idx, scene in enumerate(_iter(raw_scenes)):
        start = _number_attr(scene, ("start", "start_time", "start_sec", "t_start"), idx * 4)
        end = _number_attr(scene, ("end", "end_time", "end_sec", "t_end"), start + 4)
        visual_desc = _scene_description(scene)
        manifest.append(
            {
                "scene_id": f"s{int(start):02d}",
                "t_start": int(start),
                "t_end": int(max(end, start + 1)),
                "keyframe": _keyframe_ref(video, scene, idx),
                "visual_desc": visual_desc,
                "transcript": _transcript_text(video, start, end),
                "on_screen_text": "",
            }
        )
    return manifest


def _transcript_manifest(video):
    text = str(video.get_transcript_text()).strip()
    return [
        {
            "scene_id": "s00",
            "t_start": 0,
            "t_end": 30,
            "keyframe": f"videodb://{_first_attr(video, ('id', 'video_id'), 'unknown')}/full",
            "visual_desc": "VideoDB transcript-only ingest; scene extraction returned no scenes.",
            "transcript": text,
            "on_screen_text": "",
        }
    ]


def _transcript_text(video, start, end):
    transcript = video.get_transcript(start=float(start), end=float(end))
    if isinstance(transcript, str):
        return transcript.strip()
    if isinstance(transcript, Iterable):
        pieces = []
        for item in transcript:
            text = _first_attr(item, ("text", "content", "transcript"), "")
            if text:
                pieces.append(str(text))
        return " ".join(pieces).strip()
    return str(transcript).strip()


def _scene_description(scene):
    existing = _first_attr(scene, ("description", "text", "summary"), "")
    if existing:
        return str(existing).strip()
    describe = getattr(scene, "describe", None)
    if not callable(describe):
        return ""
    result = describe(
        prompt="Describe this ad scene in one concise sentence for a campaign-risk dashboard.",
        model_config={"model_name": "pro", "temperature": 0.2},
    )
    return str(result).strip()


def _keyframe_ref(video, scene, idx):
    frame = _first_attr(scene, ("frame_url", "thumbnail_url", "url", "image_url"), "")
    if frame:
        return str(frame)
    vid = _first_attr(video, ("id", "video_id"), "unknown")
    return f"videodb://{vid}/scene/{idx}"


def _number_attr(item, names, fallback):
    value = _first_attr(item, names, fallback)
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(fallback)


def _first_attr(item, names, fallback):
    for name in names:
        if isinstance(item, dict) and item.get(name) is not None:
            return item[name]
        value = getattr(item, name, None)
        if value is not None:
            return value
    return fallback


def _iter(value):
    if value is None:
        return []
    if isinstance(value, dict):
        for key in ("scenes", "items", "data"):
            nested = value.get(key)
            if nested is not None:
                return _iter(nested)
        return []
    if isinstance(value, (str, bytes)):
        return []
    if isinstance(value, Iterable):
        return value
    return []
