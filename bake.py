"""Bake a golden_run.json with the live (or fixture) sponsor pipeline.

The dashboard always replays golden_run.json. This script PRODUCES it:
  load agent specs  ->  per-agent grounding (Bright Data)  ->  Kimi panel  ->  reduce  ->  write.

  python bake.py --mode fixture            # reproduce the baked run, no network (testable now)
  python bake.py --mode live --mini 6      # cheap smoke test: 6 real agents, does not write
  python bake.py --mode live               # full 60-agent live bake -> golden/golden_run.json

"build real, demo baked": run this ONCE offline to make a real golden run; the demo replays it.
Dev against --mode fixture; spend Kimi/Bright Data credit only on deliberate live bakes.
"""
import argparse
import asyncio
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from app.pipeline import reduce_aggregate  # noqa: E402
from app.sponsors import brightdata, daytona, kimi, trace, videodb  # noqa: E402


def load_dotenv(path):
    if not os.path.exists(path):
        return
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["fixture", "live"], default="fixture")
    ap.add_argument("--provider", choices=["kimi", "openai"], default="kimi",
                    help="live LLM: kimi (Moonshot, sponsor) or openai (cheap dev)")
    ap.add_argument("--video-source", default="", help="VideoDB ingest source: local path, public URL, or YouTube URL")
    ap.add_argument("--sandbox", choices=["fixture", "daytona"], default="fixture",
                    help="attach Daytona per-agent sandbox receipts")
    ap.add_argument("--sandbox-mini", type=int, default=0, help="only sandbox the first N agents")
    ap.add_argument("--sandbox-keep", action="store_true", help="keep Daytona sandboxes instead of deleting them")
    ap.add_argument("--allow-baked-grounding", action="store_true",
                    help="allow live grounding failures to reuse baked snippets and record fallback receipts")
    ap.add_argument("--mini", type=int, default=0, help="only the first N agents; does not write")
    ap.add_argument("--src", default=os.path.join(ROOT, "golden", "golden_run.json"))
    ap.add_argument("--out", default=os.path.join(ROOT, "golden", "golden_run.json"))
    args = ap.parse_args()
    load_dotenv(os.path.join(ROOT, ".env"))

    golden = json.load(open(args.src, encoding="utf-8"))
    agents = golden["reactions"]
    if args.mini:
        agents = agents[: args.mini]
    scenario = golden["scenario"]
    creative, video_receipt = videodb.ingest_creative(
        source=args.video_source,
        existing_manifest=golden["creative_manifest"],
        scenario=scenario,
        mode=args.mode,
    )
    golden["creative_manifest"] = creative
    print(f"baking mode={args.mode} provider={args.provider} agents={len(agents)} brand={scenario['brand']}")
    if video_receipt:
        print(f"  videodb: ingested {video_receipt.scenes} scenes from {video_receipt.source}")

    agents, sandbox_receipts = daytona.attach_receipts(
        agents,
        daytona.SandboxOptions(
            mode=args.mode,
            enabled=args.sandbox == "daytona",
            limit=args.sandbox_mini,
            keep=args.sandbox_keep,
            run_brightdata=args.mode == "live" and args.sandbox == "daytona",
            allow_baked_grounding=args.allow_baked_grounding,
        ),
    )
    if sandbox_receipts:
        print(f"  daytona: captured {len(sandbox_receipts)} sandbox receipts")

    grounding_receipts = []
    for a in agents:
        sandbox_receipt = a.get("sandbox_receipt") or {}
        if sandbox_receipt.get("grounding_status") == "success":
            grounding_receipts.append({
                "agent_id": a["agent_id"],
                "status": "success",
                "source": "daytona+brightdata",
                "snippets": int(sandbox_receipt.get("grounding_count", 0)),
                "detail": "live Bright Data grounding parsed inside Daytona sandbox",
            })
            continue
        result = brightdata.ground_with_receipt(
            a,
            brightdata.GroundingOptions(
                mode=args.mode,
                scenario=scenario,
                allow_baked_fallback=args.allow_baked_grounding,
            ),
        )
        a["grounding"] = result.snippets
        grounding_receipts.append(result.receipt.as_json())
    if grounding_receipts:
        live_grounded = sum(1 for receipt in grounding_receipts if receipt["status"] == "success")
        fallback = sum(1 for receipt in grounding_receipts if receipt["status"] == "fallback")
        print(f"  grounding: {live_grounded} live, {fallback} fallback, {len(grounding_receipts)} receipts")

    reactions = await kimi.run_panel(agents, scenario, creative, mode=args.mode, provider=args.provider)

    aggregate, grounding_index = reduce_aggregate(reactions, creative)
    golden["reactions"] = reactions
    golden["aggregate"] = aggregate
    golden["grounding_index"] = grounding_index
    golden["grounding_receipts"] = grounding_receipts
    if sandbox_receipts:
        golden["sandbox_receipts"] = sandbox_receipts
    golden["sponsor_trace"] = trace.build_sponsor_trace(
        trace.SponsorTraceInputs(
            provider=args.provider,
            reaction_count=len(reactions),
            grounding_receipts=grounding_receipts,
            sandbox_receipts=sandbox_receipts,
            video_receipt=video_receipt,
        )
    )
    golden["mode"] = args.mode

    print(f"  blast={aggregate['blast_score']} decision={aggregate['decision']} "
          f"responders={aggregate['responders']} top={aggregate['clusters'][0]['label'] if aggregate['clusters'] else '-'}")

    if args.mini:
        print("  (mini smoke test: not writing)")
        return
    json.dump(golden, open(args.out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"wrote {args.out}")


if __name__ == "__main__":
    asyncio.run(main())
