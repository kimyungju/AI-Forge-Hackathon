# 60's Pulse

**See tomorrow's backlash before you launch today.**

60's Pulse is an AI premortem for campaigns, product launches, keynotes, and announcement films.
Paste a launch or bake a film through the sponsor pipeline, and it simulates a 60-member
public-and-press reaction panel before the real audience gets to it. The output is not a generic
sentiment score. It is a launch decision, a blast map, the objections that will spread, and the
cheapest fix path.

The current baked demo is a synthetic Google I/O 2026 "always-on AI" launch premortem. The original
Singaporean MerlionTel ad-campaign run is preserved as an archived golden artifact.

## The Problem

Brands usually discover ad backlash after the media cycle starts:

- The campaign is already live.
- The apology is already being drafted.
- The production budget is already sunk.
- The issue is not always the copy; sometimes it is the casting, the premise, the timing, or the
  stakeholder who can turn a bad comment into a headline.

Focus groups are slow, expensive, and often too polite. Social listening only works after the
damage is public. 60's Pulse moves that backlash test to before launch.

## What It Does

60's Pulse takes a campaign or launch narrative and returns a premortem:

1. **Blast Score**
   The share of the simulated panel likely to object strongly enough to go public, boycott, report,
   or generate negative coverage.

2. **60-Agent Reaction Panel**
   A grid of personas, issue lenses, and stakeholder roles reacting to the same creative. Each
   response includes a quote, severity, trigger moment, fix tier, and press-conference question.

3. **Timeline Blast Map**
   For video campaigns and segmented launch scripts, it identifies which scene or second detonates
   the panel. This turns "people may dislike it" into "0:12 is the shot that causes the issue."

4. **Top Objection Clusters**
   The system groups reactions into categories like privacy, PDPA/consent, representation, pricing,
   accessibility, child safety, religious sensitivity, or trust.

5. **Three-Tier Fix Triage**
   It separates objections by what kind of intervention can actually fix them:
   - **Copy**: rewrite the line, claim, tagline, or voiceover.
   - **Production**: cut/recast/reshoot imagery that wording cannot repair.
   - **Decision**: the concept itself is the risk; this is a launch call, not a copy edit.

6. **Tomorrow's Headline**
   A fictional front page shows the likely public narrative if the campaign ships unchanged.

## The Core Insight

Most brand-safety tools answer:

> Is this campaign positive or negative?

60's Pulse answers:

> What exactly will people attack, who will amplify it, which second caused it, and what is the
> cheapest fix before launch?

That is the selling point: **from vibe check to launch decision.**

## Why 60 Agents

The panel is designed for risk coverage, not census polling.

- **35 public personas** capture audience reactions and social-sharing behavior.
- **15 concern lenses** inspect sensitive risk areas in third person, such as PDPA, accessibility,
  child data, religious sensitivity, racial representation, privacy, labour, and safety.
- **10 stakeholder agents** represent the groups that can escalate a problem: journalists,
  regulators, ad standards, opposition MPs, competitor PR, employees, activist groups, and consumer
  associations.

Identity-sensitive perspectives are not roleplayed in first person. They are handled as third-person
concern lenses, which is safer and more defensible.

## Demo Story

The current baked demo uses a synthetic Google I/O 2026-style launch scenario:

> Google announces an always-on AI stack: Gemini Spark works in the background even while the phone
> is off, Personal Intelligence connects Gmail and Photos, Daily Brief reads inbox/calendar/tasks
> overnight, agents operate 24/7, and SynthID watermarks outputs.

60's Pulse catches three different failure modes:

- **Copy risk**: convenience language reads like a euphemism for continuous monitoring.
- **Production risk**: the keynote framing makes "always on" feel like a feature, not a risk.
- **Decision risk**: off-device background agents connected to personal accounts may be
  fundamentally hard to sell as a trust story.

The current `golden/golden_run.json` fixture returns:

```text
Blast Score 86
Decision DELAY
58 responders / 60 agents
Peak moment 0:06-0:12
Top clusters: Privacy, Trust / Claims, Data Ethics, Surveillance, Safety
```

The archived MerlionTel ad-campaign run is still available in `golden/golden_merliontel.json` and
`golden/golden_live.json`. It demonstrates the original Singapore telco story: privacy panic,
CMIO representation risk, and a residual surveillance-premise decision.

## Product Differentiators

### It Is Creative-Specific

The output is tied to campaign scenes, lines, and moments. It does not just say "privacy risk";
it points to the line or shot that causes the reaction.

### It Is Fix-Oriented

Every objection is tagged by the cheapest fix tier. This makes the output useful to marketers,
creatives, legal, and leadership in the same meeting.

### It Models Escalation

The panel includes not only consumers, but also the people who turn backlash into consequences:
press, regulators, opposition voices, competitors, staff, and advocacy groups.

### It Is Demo-Safe

The live-capable system bakes a golden run offline. The stage demo replays a single JSON artifact,
so the presentation does not depend on Wi-Fi, sponsor latency, or 60 live calls.

### It Uses Sponsors With A Clear Role

- **Kimi / Moonshot**: 60-agent structured reaction panel, with JSON mode and prefix-cache-friendly
  shared prompts.
- **Bright Data**: per-agent public-discourse grounding hooks.
- **Daytona**: optional sandbox isolation and agent execution receipts.
- **VideoDB**: optional video transcript, scene extraction, and creative manifest ingestion.
- **SenseNova**: fictional scandal-front-page image concept in the sponsor trace.

Each sponsor maps to a production concern: reasoning, grounding, isolation, video understanding,
and future-artifact generation.

## What The User Gets

The final dashboard is a war-room broadsheet:

- a giant Blast Score,
- the fake tomorrow headline,
- the 60-agent panel,
- top objection clusters,
- a timeline blast map,
- stakeholder escalation badges,
- and a fix triage showing what to rewrite, reshoot, or cancel.

It is built for the meeting where a brand asks:

> Should we launch this?

## Current Demo Surface

The repository currently supports:

- a FastAPI app that serves the input screen, agent-run animation, and final dashboard,
- a baked Google I/O 2026 golden run at `golden/golden_run.json`,
- archived MerlionTel golden runs in `golden/golden_merliontel.json` and `golden/golden_live.json`,
- a text-only live campaign path through `POST /api/analyze`,
- a fixture/live bake script for regenerating golden artifacts,
- Kimi/Moonshot or OpenAI-compatible panel generation,
- optional Daytona sandbox receipts through the bake CLI,
- optional VideoDB creative ingest through the bake CLI,
- Bright Data grounding hooks; live response parsers are still stubbed until zones and payload
  shapes are finalized.

The dashboard intentionally renders one JSON object. That keeps the product story simple: live work
produces the premortem artifact; the user-facing surface explains the decision.

Browser image/video attachments are currently presentation chips only. The implemented browser live
path sends `campaign` and `brand` text to `/api/analyze`. Real video ingestion happens through
`bake.py --video-source`.

## Repository Map

```text
app/main.py                 FastAPI app, /api/golden, /api/analyze, static mount
app/analyze.py              typed-campaign live analysis path
app/pipeline.py             reaction reduction into Blast Score, clusters, timeline
app/sponsors/               Kimi, Bright Data, Daytona, and VideoDB adapters
app/static/                 input flow, run animation, and dashboard UI
golden/golden_run.json      current default Google fixture rendered by the app
golden/golden_merliontel.json
                              archived MerlionTel run
bake.py                     fixture/live bake CLI
seed_io2026.py              reseeds the Google I/O 2026 fixture
decks/premortem-pitch/      hackathon pitch deck HTML slides and previews
```

## API Surface

```text
GET  /healthz       app health check
GET  /api/golden    returns the current baked golden artifact
POST /api/analyze   regenerates a 60-agent panel for pasted campaign text
```

`POST /api/analyze` accepts:

```json
{
  "brand": "Google",
  "campaign": "Launch copy, keynote excerpt, or announcement text",
  "provider": "kimi"
}
```

## Run It

Create an environment and install dependencies:

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Start the app:

```bash
uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000
```

Run the tests:

```bash
python -m unittest discover -s tests
```

Run the no-network fixture smoke. With `--mini`, the script recomputes the artifact but does not
write `golden/golden_run.json`:

```bash
python bake.py --mode fixture --mini 2
```

Run a cheap live smoke:

```bash
python bake.py --mode live --mini 6
```

Run live with the OpenAI-compatible dev provider:

```bash
python bake.py --mode live --provider openai --mini 6
```

Attach Daytona sandbox receipts:

```bash
python bake.py --mode live --mini 3 --sandbox daytona --sandbox-mini 3
```

Ingest a video through VideoDB:

```bash
python bake.py --mode live --video-source "https://example.com/ad.mp4" --mini 6
```

Reseed the current Google fixture:

```bash
python seed_io2026.py
python bake.py --mode fixture
```

Regenerate the original MerlionTel fixture:

```bash
python golden/build_golden.py
```

## Environment

Fixture mode needs no keys. Live mode uses the keys relevant to the provider path:

```env
KIMI_API_KEY=
KIMI_BASE_URL=https://api.moonshot.ai/v1
KIMI_MODEL=moonshot-v1-8k
KIMI_CONCURRENCY=16
KIMI_MAX_TOKENS=400

OPENAI_API_KEY=
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini

BRIGHTDATA_API_KEY=
BRIGHTDATA_SERP_ZONE=
BRIGHTDATA_UNLOCKER_ZONE=

DAYTONA_API_KEY=
DAYTONA_API_URL=https://app.daytona.io/api

VIDEODB_API_KEY=

SENSENOVA_API_KEY=
TERMINAL3_API_KEY=

PREMORTEM_MODE=fixture
PYTHONIOENCODING=utf-8
```

Copy `.env.example` to `.env` when running live paths.

## One-Line Pitch

**60's Pulse is a launch premortem that shows the backlash, the blast moment, and the fix path
before the campaign becomes tomorrow's apology.**
