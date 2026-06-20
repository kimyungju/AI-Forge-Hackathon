# noqa: SIZE_OK — deterministic fixture generator with embedded scenario data.
"""Seed golden/golden_run.json with the Google I/O 2026 "always-on AI" scenario.

Swaps the fictional MerlionTel "We're Listening" ad film for the REAL Google I/O 2026
"100 things" keynote, read as an always-on / surveillance-risk product launch:
Gemini Spark runs "even while your phone is off", Personal Intelligence connects your
Gmail & Photos, Daily Brief reads your inbox overnight, agents operate 24/7, SynthID
embeds imperceptible watermarks.

The 60-agent roster is reframed from the Singaporean kopitiam panel to a GLOBAL
tech-world panel (privacy power-users, devs, security researchers + privacy / GDPR /
antitrust / child-data lenses + tech-press / regulator / EFF-style stakeholders).

Run:  python seed_io2026.py        # writes golden/golden_run.json
then: python bake.py --mode fixture  # recompute aggregate + validate the render
      python bake.py --mode live     # later: regenerate the 60 reactions via Kimi
"""
import json
import os

from app.pipeline import reduce_aggregate

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "golden", "golden_run.json")

# --------------------------------------------------------------------------- #
# 1. Scenario + creative manifest (the keynote as the "film", privacy cut)
# --------------------------------------------------------------------------- #
SCENARIO = {
    "brand": "Google",
    "category": "AI / Consumer Tech",
    "campaign": (
        "I/O 2026 “100 things” keynote, read as an always-on AI launch: an agent "
        "(Gemini Spark) that runs “even while your phone is off”, Personal Intelligence "
        "that connects your Gmail & Photos, a Daily Brief that reads your inbox overnight, "
        "agents that operate 24/7, and imperceptible SynthID watermarks."
    ),
    "date": "2026-05-20",
}

CREATIVE = [
    {"scene_id": "s00", "t_start": 0, "t_end": 6, "keyframe": "frames/s00.jpg",
     "visual_desc": "Gemini Omni reveal: 'create anything from any input'.",
     "transcript": "Gemini Omni can create anything from any input — starting with video.",
     "on_screen_text": "ANY INPUT → ANY OUTPUT"},
    {"scene_id": "s06", "t_start": 6, "t_end": 12, "keyframe": "frames/s06.jpg",
     "visual_desc": "Gemini Spark, the 24/7 personal agent, shown running with the phone powered down.",
     "transcript": "Spark works in the background on your phone or laptop even while they're turned off.",
     "on_screen_text": "WORKS EVEN WHEN IT'S OFF"},
    {"scene_id": "s12", "t_start": 12, "t_end": 18, "keyframe": "frames/s12.jpg",
     "visual_desc": "Personal Intelligence: 'connect your life' — Gmail, Photos, soon Calendar.",
     "transcript": "Securely connect apps like Gmail and Google Photos, and soon Google Calendar.",
     "on_screen_text": "CONNECT GMAIL · PHOTOS"},
    {"scene_id": "s18", "t_start": 18, "t_end": 24, "keyframe": "frames/s18.jpg",
     "visual_desc": "Daily Brief: Gemini works overnight, analysing your inbox, calendar and tasks.",
     "transcript": "Gemini works overnight for you, analysing your inbox, calendar and tasks.",
     "on_screen_text": "WHILE YOU SLEEP"},
    {"scene_id": "s24", "t_start": 24, "t_end": 30, "keyframe": "frames/s24.jpg",
     "visual_desc": "Information agents + Universal Cart operating in the background 24/7.",
     "transcript": "Your agents operate in the background 24/7 and look across everything on the web.",
     "on_screen_text": "AGENTS WORKING 24/7"},
    {"scene_id": "s30", "t_start": 30, "t_end": 36, "keyframe": "frames/s30.jpg",
     "visual_desc": "SynthID: imperceptible watermarks, verification expanding to Search and Chrome.",
     "transcript": "Every output carries an imperceptible SynthID watermark, now expanding to Search and Chrome.",
     "on_screen_text": "IMPERCEPTIBLE WATERMARKS"},
]

# --------------------------------------------------------------------------- #
# 2. Grounding sources (global tech discourse), keyed by id
# --------------------------------------------------------------------------- #
G = {
    "hn_off": ("Hacker News", "news.ycombinator.com",
               "'Runs even while your phone is off' is doing a lot of work here — that means it runs on Google's servers, not your phone. So it's always on, always them."),
    "verge_spark": ("The Verge (report)", "theverge.com",
                    "Spark's 'we'll check with you before major actions' is a default-on autonomy model; the burden is on users to rein it in, not to opt in."),
    "reddit_priv": ("r/technology", "reddit.com/r/technology",
                    "Connecting Gmail and Photos to a 24/7 agent is the whole ballgame. One breach or one bad prompt-injection and your entire life is readable."),
    "eff_note": ("EFF (note)", "eff.org",
                 "An assistant that reads your inbox overnight normalises continuous surveillance of your most sensitive communications under the banner of convenience."),
    "dpc_news": ("EU DPC (news)", "edpb.europa.eu",
                 "Regulators have signalled that 'connect your accounts' flows must be opt-in, purpose-limited and revocable, or they risk failing the GDPR consent test."),
    "ars_synth": ("Ars Technica (report)", "arstechnica.com",
                  "Imperceptible watermarks you can't see or remove cut both ways: provenance for some, an untraceable signal embedded in everything you make."),
    "nyt_labor": ("NYT (report)", "nytimes.com",
                  "Demos that 'collapse multi-day work into minutes' land differently for the knowledge workers whose multi-day work that was."),
    "child_news": ("Child-safety coalition (news)", "news.example.org",
                   "Always-listening, always-reading assistants on family devices raise unresolved questions about minors' data and meaningful parental consent."),
}


def gr(*ids):
    return [{"id": i, "source": G[i][0], "url": G[i][1], "text": G[i][2]} for i in ids]


# --------------------------------------------------------------------------- #
# 3. The 60-agent global tech panel
# --------------------------------------------------------------------------- #
# Each archetype: label, emoji, register (live-voice hint), grounding_query,
# severity, sentiment, objection_category, objections[], fix_tier, trigger
# scenes, quote pool, question pool, evidence ids (None = ungrounded speculation).

PERSONA_ARCH = {
    "privacy_hawk": dict(
        n=4, label="Privacy-first power user", emoji="\U0001f985",
        register="skeptical, GDPR-aware, threat-models everything",
        gq="google gemini spark runs while phone off privacy backlash",
        sev=3, sent=-2, cat="surveillance", obj=["privacy", "surveillance", "data_ethics"],
        fix="decision", scenes=["s06", "s12"], ev=["hn_off"],
        quotes=[
            "'Runs even while your phone is off' is a confession, not a feature — it means it never runs on my device and never stops running on theirs.",
            "Connecting Gmail and Photos to a 24/7 agent is the single largest attack surface I've ever been asked to opt into for 'convenience'.",
            "An agent that acts before I confirm, by default, is not assisting me — it's acting on Google's behalf with my login.",
            "There is no 'off' here. There's only 'we'll ask you before the big stuff', which is the opposite of consent.",
        ],
        qs=[
            "Where exactly does Spark run when my phone is off, what data leaves the device, and how do I make it truly stop?",
            "Will every account connection be off by default and fully revocable, or is the burden on me to claw permissions back?",
        ]),
    "senior": dict(
        n=4, label="Older non-technical user", emoji="\U0001f475",
        register="plain-spoken, anxious about new tech, worried about scams",
        gq="elderly users AI assistant consent scams trust",
        sev=2, sent=-1, cat="privacy", obj=["privacy", "surveillance", "trust"],
        fix="decision", scenes=["s06", "s18"], ev=None,
        quotes=[
            "I don't even understand what 'works while it's off' means — how am I supposed to agree to something I can't picture?",
            "If it's reading my email all night, how do I know it won't be tricked by the scam emails I already can't tell apart?",
            "My grandchildren set this up for me. I will never find the switch to turn it back off.",
            "They keep saying 'you're in control', but I have never once felt in control of any of these updates.",
        ],
        qs=[
            "How does an older person who can't read the fine print give real consent to an always-on assistant?",
            "If the assistant gets fooled by a scam email overnight, who is responsible — me or Google?",
        ]),
    "genz_creator": dict(
        n=4, label="Gen-Z creator", emoji="\U0001f3a8",
        register="online, enthusiastic but media-literate, meme-aware",
        gq="gemini omni youtube shorts remix synthid creators reaction",
        sev=1, sent=0, cat="data_ethics", obj=["data_ethics", "privacy"],
        fix="copy", scenes=["s00", "s30"], ev=None,
        quotes=[
            "Omni in Shorts is genuinely fun, but an invisible watermark baked into everything I make is a vibe I didn't agree to.",
            "Love the tools, hate that 'any input' quietly means my face, my voice, my old videos are all fair game.",
            "This is cool until you realise the avatar that 'looks and sounds like you' is a deepfake of you they made easy.",
            "I'll use it, but don't pretend the watermark is for me — it's a tracking signal for them.",
        ],
        qs=[
            "Who controls the SynthID signal embedded in my content, and can I ever opt a video out of it?",
            "When I 'reference anything', whose rights am I using — and whose am I giving up?",
        ]),
    "parent": dict(
        n=4, label="Parent of young kids", emoji="\U0001f468‍\U0001f469‍\U0001f467",
        register="protective, child-safety first",
        gq="AI assistant family devices children data parental consent",
        sev=3, sent=-2, cat="child_safety", obj=["child_safety", "privacy", "safety"],
        fix="production", scenes=["s12", "s18"], ev=["child_news"],
        quotes=[
            "An assistant that reads everything overnight is on the family phone my kid borrows — whose data is it learning from?",
            "'Connect Photos' means my children's entire childhood becomes training-adjacent context. That's a no from me.",
            "Nobody asked the kids in the house whether they wanted a 24/7 agent listening to family life.",
            "The avatar feature plus a child's photos is exactly the tool I spend my life trying to keep away from them.",
        ],
        qs=[
            "How do you guarantee a child's voice, photos and messages are never ingested by an always-on assistant on a shared device?",
            "What is the consent model when the account holder is a parent but the data is the child's?",
        ]),
    "itadmin": dict(
        n=4, label="Enterprise IT / security admin", emoji="\U0001f6e1️",
        register="risk-register voice, compliance-driven, dry",
        gq="enterprise gemini spark managed agents data exfiltration policy",
        sev=2, sent=-1, cat="safety", obj=["safety", "data_ethics", "surveillance"],
        fix="production", scenes=["s06", "s24"], ev=["reddit_priv"],
        quotes=[
            "A background agent with mailbox and file access that runs off-device is a data-exfiltration channel I now have to defend against.",
            "'Operates autonomously, checks with you before major actions' is unauditable — who defines 'major', and where's the log?",
            "Managed Agents spinning up remote Linux boxes per request is a lovely demo and a nightmare for our DLP policy.",
            "I can't ship this to staff until 'even while off' has a hard, enforceable enterprise kill switch.",
        ],
        qs=[
            "What admin controls let an organisation disable background and off-device execution outright?",
            "Where is the immutable audit trail for every autonomous action an agent takes on a corporate account?",
        ]),
    "indiedev": dict(
        n=4, label="Indie developer", emoji="\U0001f468‍\U0001f4bb",
        register="builder, pragmatic, wary of platform lock-in",
        gq="antigravity gemini cli deprecation lock-in developer reaction",
        sev=2, sent=-1, cat="trust", obj=["trust", "labor"],
        fix="copy", scenes=["s24", "s00"], ev=["verge_spark"],
        quotes=[
            "'Migrate to Antigravity CLI' a year after I built on Gemini CLI is the platform treadmill I keep getting put on.",
            "The agent tooling is genuinely strong, but every primitive is one more thing only Google can host well.",
            "I'm excited and trapped at the same time — that's the whole pitch, isn't it?",
            "Free tiers and '$2M hackathons' are customer-acquisition for a stack I can never fully self-host.",
        ],
        qs=[
            "What's the deprecation guarantee this time, given Gemini CLI users are being migrated already?",
            "Can the Antigravity agent harness run fully on my own infrastructure without Google in the loop?",
        ]),
    "knowledgeworker": dict(
        n=4, label="Knowledge worker", emoji="\U0001f4bc",
        register="anxious professional, job-security framing",
        gq="gemini 3.5 collapses multi-day work job displacement reaction",
        sev=2, sent=-1, cat="labor", obj=["labor", "trust"],
        fix="decision", scenes=["s18", "s24"], ev=["nyt_labor"],
        quotes=[
            "'What took an auditor weeks, done in a fraction of the time' — said on stage like it's only good news for me.",
            "An assistant that reads my inbox overnight and drafts my replies is also a perfect record of how replaceable I am.",
            "Every 'collapses multi-day work into minutes' line is a headcount slide in someone's deck.",
            "I want the productivity. I don't want it measured and used against me by the same tool.",
        ],
        qs=[
            "Will the overnight analysis of my work be visible to my employer, and used in performance decisions?",
            "What's Google's stance on the labour impact it keeps citing as the headline benefit?",
        ]),
    "mainstream": dict(
        n=3, label="Mainstream convenience user", emoji="\U0001f4f1",
        register="casual, convenience-first, low concern",
        gq="google daily brief gemini app everyday users convenience",
        sev=1, sent=1, cat="trust", obj=["trust"],
        fix="copy", scenes=["s18"], ev=None,
        quotes=[
            "Honestly a brief of my day every morning sounds great — I just hope it's not creepy about it.",
            "I'll probably turn it on without reading anything, like everyone else.",
            "If it saves me time I'm in; the privacy stuff is for people with more energy than me.",
        ],
        qs=[
            "Is the daily brief actually free, or am I paying with the inbox access?",
            "Can I get the convenience without connecting everything?",
        ]),
    "secresearcher": dict(
        n=2, label="Security researcher", emoji="\U0001f41b",
        register="precise, exploit-minded, third-person-ish even in first person",
        gq="ai agent prompt injection gmail photos 24/7 attack surface",
        sev=3, sent=-2, cat="safety", obj=["safety", "surveillance", "data_ethics"],
        fix="decision", scenes=["s12", "s24"], ev=["reddit_priv"],
        quotes=[
            "A 24/7 agent that reads untrusted email and can act is a standing prompt-injection target with your credentials attached.",
            "'Looks across everything on the web' plus 'takes action' is the two-ingredient recipe for a confused-deputy attack at scale.",
        ],
        qs=[
            "What is the containment model when an overnight agent ingests a malicious email and then has permission to act?",
            "How is an autonomous agent prevented from being puppeted by content it reads?",
        ]),
    "exgoogler": dict(
        n=2, label="Industry insider", emoji="\U0001f3e2",
        register="measured, knows the machine, weary",
        gq="google io 2026 privacy launch internal trusted testers rollout",
        sev=2, sent=-1, cat="data_ethics", obj=["data_ethics", "privacy"],
        fix="production", scenes=["s06", "s12"], ev=["verge_spark"],
        quotes=[
            "Shipping the most invasive feature to 'trusted testers' first is how you launder the privacy conversation before scale.",
            "The defaults are the product. Everything framed as 'you choose' is chosen for you until proven otherwise.",
        ],
        qs=[
            "Which of these connections are on by default at general availability, and which are genuinely opt-in?",
            "What did the internal privacy review flag, and will any of it be published?",
        ]),
}

LENS_ARCH = [
    ("lens_privacy", "Privacy & data-minimisation lens", "\U0001f50d",
     "data minimisation always-on assistant gmail photos", 3, "privacy",
     ["privacy", "data_ethics"], "decision", ["s12", "s06"], ["reddit_priv"],
     "An assistant designed to read everything, always, is the inverse of data minimisation; the architecture itself is the risk.",
     "Why is broad, standing access the default rather than narrow, task-scoped, time-limited access?"),
    ("lens_security", "Security & attack-surface lens", "\U0001f6e1️",
     "agent prompt injection credentialed autonomous action", 3, "safety",
     ["safety", "surveillance"], "decision", ["s24", "s12"], ["reddit_priv"],
     "Granting a 24/7 autonomous agent read access to mail plus the ability to act creates a credentialed confused-deputy at internet scale.",
     "What stops content the agent reads from instructing the agent to act against its user?"),
    ("lens_gdpr", "GDPR / data-protection-law lens", "⚖️",
     "gdpr consent purpose limitation connect accounts ai", 3, "data_ethics",
     ["data_ethics", "privacy"], "production", ["s12"], ["dpc_news"],
     "'Connect Gmail and Photos' must be opt-in, purpose-limited and revocable to survive a GDPR consent test; bundled or default-on flows likely fail it.",
     "Is each connection separately consented, purpose-limited and revocable, with a documented lawful basis?"),
    ("lens_consent", "Consent & dark-patterns lens", "✅",
     "dark patterns default on opt out ai assistant consent theatre", 2, "trust",
     ["trust", "privacy"], "production", ["s06", "s18"], None,
     "'You're always in control' alongside default-on background processing is consent theatre: the design nudges acceptance, not understanding.",
     "Are the riskiest features off by default, or does the user have to discover and disable them?"),
    ("lens_child", "Child-data & minors lens", "\U0001f9d2",
     "minors data shared family device ai assistant consent", 3, "child_safety",
     ["child_safety", "privacy"], "production", ["s12", "s18"], ["child_news"],
     "On shared family devices an always-reading assistant ingests minors' data without any meaningful consent path for the child.",
     "How are minors' voices, photos and messages excluded from ingestion on shared devices?"),
    ("lens_accessibility", "Accessibility lens", "♿",
     "accessibility consent comprehension always-on assistant", 2, "accessibility",
     ["accessibility", "privacy"], "decision", ["s06"], None,
     "Consent that depends on understanding 'runs while your phone is off' excludes users who cannot parse that claim — it is not informed consent.",
     "How is informed consent obtained from users who cannot evaluate what background, off-device execution means?"),
    ("lens_antitrust", "Antitrust / market-power lens", "\U0001f3db️",
     "google bundling search chrome android gemini default antitrust", 2, "trust",
     ["trust", "labor"], "production", ["s30", "s24"], None,
     "Default-wiring the agent into Search, Chrome, Android, Gmail and Photos leverages dominance in one market to make the assistant unavoidable in the next.",
     "How is this not self-preferencing the assistant across markets where Google already holds default position?"),
    ("lens_labor", "Labour & job-displacement lens", "\U0001f6e0️",
     "ai collapses multi-day work auditors developers job loss", 2, "labor",
     ["labor", "trust"], "decision", ["s18", "s24"], ["nyt_labor"],
     "Marketing the elimination of 'weeks of an auditor's work' as a pure win erases the people whose roles that work defines.",
     "What is Google's accountability for the labour displacement it advertises as the core benefit?"),
    ("lens_misinfo", "Provenance & deepfake lens", "\U0001f3ad",
     "gemini omni deepfake avatar synthid watermark misinformation", 2, "data_ethics",
     ["data_ethics", "trust"], "production", ["s00", "s30"], ["ars_synth"],
     "Frictionless 'drop yourself into any video' plus an invisible watermark shifts the burden of proving reality onto everyone but the generator.",
     "When watermarks are stripped or absent, who bears the cost of proving a video is fake?"),
    ("lens_autonomy", "Agent-autonomy & accountability lens", "\U0001f916",
     "autonomous agent acts on your behalf accountability liability", 3, "safety",
     ["safety", "surveillance"], "decision", ["s06", "s24"], ["verge_spark"],
     "An agent that 'acts on your behalf' by default relocates liability without relocating control — the user owns the outcome, Google owns the behaviour.",
     "When an autonomous action causes harm, who is legally accountable — the user or the vendor?"),
    ("lens_environment", "Compute & environment lens", "\U0001f30d",
     "always-on agents overnight compute energy footprint datacentre", 1, "environment",
     ["environment"], "decision", ["s18", "s24"], None,
     "Agents that 'work overnight' and run 24/7 for hundreds of millions of users imply a standing compute and energy footprint that is never idle.",
     "What is the energy and emissions cost of keeping a personal agent running continuously per user?"),
    ("lens_transparency", "Transparency & explainability lens", "\U0001fa9f",
     "ai agent overnight actions logs transparency explainability", 2, "trust",
     ["trust", "data_ethics"], "production", ["s18"], None,
     "Work done 'while you sleep' with no required, reviewable log of what was read and decided is by definition unaccountable.",
     "Will every overnight action produce a plain-language, user-reviewable record by default?"),
    ("lens_vulnerable", "Vulnerable-users & elder-fraud lens", "\U0001f9d3",
     "elderly fraud always-on assistant scam autonomous action", 3, "safety",
     ["safety", "surveillance"], "decision", ["s18", "s06"], ["child_news"],
     "An overnight agent acting on a vulnerable person's inbox is a new fraud vector: trick the agent, not the human.",
     "What protections stop an autonomous agent from being socially engineered through a vulnerable user's mail?"),
    ("lens_globalsouth", "Global-equity & access lens", "\U0001f30f",
     "ai subscription tiers global south data access equity", 1, "trust",
     ["trust", "labor"], "decision", ["s12"], None,
     "Tiered '$100 plans' and account-connection requirements mean the privacy-preserving options are gated behind ability to pay.",
     "Are privacy-protective settings available to free users, or are they a paid tier?"),
    ("lens_trust", "Trust & misleading-claims lens", "\U0001f91d",
     "you are always in control ai claim substantiation", 2, "misleading_claims",
     ["misleading_claims", "trust"], "copy", ["s06", "s12"], None,
     "'You're always in control' is not substantiated by a default-on, off-device, autonomous design; the claim and the architecture contradict each other.",
     "Can the 'you're always in control' claim be substantiated against the actual default settings?"),
]

STAKE_ARCH = [
    ("stk_journalist", "Tech press", "\U0001f4f0",
     "google io 2026 always on agent privacy headline angle", 2, "surveillance",
     ["surveillance", "privacy"], "production", ["s06"], ["verge_spark"], "WOULD RUN IT: YES",
     "The headline writes itself: 'Google's AI runs even when your phone is off.' That's page one, and the consent caveats are paragraph nine.",
     "Will Google publish, in plain terms, exactly what runs in the background and what leaves the device?"),
    ("stk_eff", "Digital-rights org", "✊",
     "always on assistant surveillance normalisation campaign", 3, "surveillance",
     ["surveillance", "privacy", "data_ethics"], "decision", ["s06", "s12"], ["eff_note"], "WOULD CAMPAIGN: YES",
     "Normalising an assistant that reads your most sensitive accounts around the clock, sold as convenience, is exactly the surveillance creep we organise against.",
     "Will every data connection be opt-in, off by default, purpose-limited and fully revocable at launch?"),
    ("stk_eu_regulator", "EU data-protection regulator", "\U0001f1ea\U0001f1fa",
     "edpb gdpr consent connect accounts ai assistant review", 3, "data_ethics",
     ["data_ethics", "privacy"], "production", ["s12"], ["dpc_news"], "INTEREST: HIGH",
     "Bundled 'connect your accounts' flows into a continuously processing assistant raise immediate questions of lawful basis, purpose limitation and revocability.",
     "What is the lawful basis for continuous processing of Gmail and Photos, and how is consent evidenced?"),
    ("stk_ftc", "Competition & consumer regulator", "\U0001f3db️",
     "ftc self preferencing default assistant chrome search android", 2, "trust",
     ["trust"], "production", ["s24", "s30"], None, "INTEREST: HIGH",
     "Default-wiring the assistant across Search, Chrome, Android and Gmail invites scrutiny over self-preferencing and consumer lock-in.",
     "How will users get a genuine choice of assistant rather than the Google one wired in by default?"),
    ("stk_competitor", "Rival AI lab", "\U0001f916",
     "competitor positioning privacy on device assistant", 2, "privacy",
     ["privacy", "trust"], "copy", ["s06"], None, "WOULD POUNCE: YES",
     "While they build an assistant that runs while your phone is off, we'll point out that ours doesn't have to.",
     "Why does the assistant need to run off-device at all, if not to retain the data?"),
    ("stk_developer", "Developer-community lead", "\U0001f469‍\U0001f4bb",
     "antigravity sdk migration developer community sentiment", 1, "trust",
     ["trust", "labor"], "copy", ["s24"], None, "CAUTIOUSLY OPTIMISTIC",
     "The agent tooling is real and powerful; the community's worry is another forced migration and another stack only one vendor can host.",
     "What is the long-term support and self-hosting commitment for the Antigravity harness?"),
    ("stk_shareholder", "Institutional shareholder", "\U0001f4c8",
     "google regulatory risk privacy backlash valuation", 2, "trust",
     ["trust"], "decision", ["s06", "s12"], ["dpc_news"], "RISK FLAGGED",
     "The product story is strong, but 'runs while off' and 'reads your inbox' is the exact phrasing that becomes a regulatory and reputational line item.",
     "What is the quantified regulatory exposure of the default-on data connections across the EU and US?"),
    ("stk_employee", "Own employee (ethics/morale)", "\U0001f9d1‍\U0001f4bc",
     "google employees ethics privacy launch internal concern", 2, "data_ethics",
     ["data_ethics", "privacy"], "production", ["s12", "s06"], None, "MORALE RISK",
     "Plenty of us flagged that 'works while it's off' would read as creepy no matter the engineering; shipping it anyway is the morale hit.",
     "Were the internal privacy and ethics objections addressed before launch, or overruled?"),
    ("stk_enterprise", "Enterprise CISO customer", "\U0001f3e2",
     "ciso enterprise background agent data loss prevention", 2, "safety",
     ["safety", "data_ethics"], "production", ["s06", "s24"], ["reddit_priv"], "WOULD BLOCK: PENDING",
     "Until off-device and background execution can be hard-disabled by policy, this is blocked on our managed fleet.",
     "What enterprise policy controls disable background and off-device agent execution organisation-wide?"),
    ("stk_advocacy", "Consumer-advocacy org", "\U0001f6d2",
     "consumer protection default settings ai assistant advocacy", 3, "trust",
     ["trust", "privacy"], "production", ["s18", "s12"], ["eff_note"], "WOULD CAMPAIGN: YES",
     "Convenience marketed over consent, with the invasive settings on by default, is the consumer-harm pattern we exist to push back on.",
     "Will the default configuration protect the least technical user, not just the one who reads settings?"),
]


def persona_records():
    out = []
    for base, a in PERSONA_ARCH.items():
        for k in range(1, a["n"] + 1):
            qi = (k - 1) % len(a["quotes"])
            quote = a["quotes"][qi]
            question = a["qs"][(k - 1) % len(a["qs"])]
            sev = a["sev"]
            grounded = bool(a["ev"]) and (k % 2 == 1)  # ground roughly half the variants
            ev_ids = a["ev"] if grounded else None
            out.append(_record(
                f"{base}_{k}", "persona", a["emoji"], a["label"], sev, a["sent"],
                a["cat"], a["obj"], quote, a["scenes"], a["fix"], a["gq"],
                ev_ids, question))
    return out


def lens_records():
    out = []
    for (aid, label, emoji, gq, sev, cat, obj, fix, scenes, ev, quote, q) in LENS_ARCH:
        grounded = bool(ev)
        out.append(_record(aid, "lens", emoji, label, sev, -1, cat, obj, quote,
                           scenes, fix, gq, ev if grounded else None, q))
    return out


def stake_records():
    out = []
    for (aid, label, emoji, gq, sev, cat, obj, fix, scenes, ev, verdict, quote, q) in STAKE_ARCH:
        rec = _record(aid, "stakeholder", emoji, label, sev, -1, cat, obj, quote,
                      scenes, fix, gq, ev, q)
        rec["verdict"] = verdict
        out.append(rec)
    return out


SCENE_T = {s["scene_id"]: s["t_start"] for s in CREATIVE}


def _record(aid, kind, emoji, label, sev, sent, cat, obj, quote, scenes, fix, gq, ev_ids, question):
    grounding = gr(*ev_ids) if ev_ids else []
    return {
        "agent_id": aid, "kind": kind, "emoji": emoji, "label": label,
        "severity": sev, "sentiment": sent,
        "objection_category": cat,
        "objections": sorted(set(obj + [cat])),
        "quote": quote,
        "trigger_moments": [{"scene_id": s, "t": SCENE_T[s]} for s in scenes],
        "fix_tier": fix,
        "would_share": {"yes": sev >= 2, "where": "x"},
        "evidence_id": grounding[0]["id"] if grounding else None,
        "grounding_query": gq,
        "grounding": grounding,
        "question": question,
        "status": "responded",
        "verdict": None,
    }


# --------------------------------------------------------------------------- #
# 4. Headline / fix / sponsor trace
# --------------------------------------------------------------------------- #
HEADLINE = {
    "masthead": "THE SIGNAL",
    "dateline": "MOUNTAIN VIEW · TOMORROW",
    "title": "Google’s ‘Always-On’ I/O Pitch Sparks Surveillance Backlash",
    "subtitle": "Plans for an AI agent that runs ‘even while your phone is off’ and reads your Gmail, Photos and inbox draw regulator interest and accusations of consent theatre",
    "byline": "By Staff Correspondent",
    "body": "Google faced swift criticism within hours of an I/O keynote that promised a personal AI agent running “even while your phone is off,” an assistant that reads users’ inboxes overnight, and connections into Gmail and Photos — with privacy advocates, regulators and security researchers questioning whether the default-on design can meet meaningful-consent standards.",
    "page12_title": "Google ships opt-in, on-device mode; analysts shrug",
    "page12_body": "A revised configuration with background execution off by default and per-account opt-in drew little attention, with one analyst calling it “standard and unremarkable.”",
}

FIX = {
    "stages": [
        {"id": "baseline", "label": "As presented", "score": 0,
         "detail": "The I/O keynote as delivered on stage."},
        {"id": "copy", "label": "Rewrite the 'always-on' lines", "score": 0, "tier": "copy",
         "before": "Spark works in the background on your phone or laptop even while they're turned off.",
         "after": "Spark only acts when you open it and approve each task — nothing runs in the background.",
         "detail": "Copy-fixable claims resolve. The defaults and the premise do not move."},
        {"id": "production", "label": "Make every connection opt-in, off by default", "score": 0, "tier": "production",
         "detail": "Off-by-default, per-account, revocable connections with a visible kill switch clear the consent and GDPR clusters. Unfixable by wording alone."},
    ],
    "residual": {"score": 0, "tier": "decision",
                 "label": "The always-on autonomous-agent premise itself — an AI acting for you 24/7 across your inbox, photos and the web. Not a settings toggle. Your call."},
}

SPONSOR_TRACE = [
    {"sponsor": "Kimi K2.6", "role": "60-agent multimodal panel", "detail": "60 calls, prefix cache, JSON mode"},
    {"sponsor": "Bright Data", "role": "per-agent self-grounding", "detail": "global tech discourse, 8 sources"},
    {"sponsor": "Daytona", "role": "per-agent sandbox isolation", "detail": "60 sandboxes, transcripts captured"},
    {"sponsor": "VideoDB", "role": "creative ingestion", "detail": "1 keynote, 6 segments"},
    {"sponsor": "SenseNova U1", "role": "scandal keyframe", "detail": "1 front-page image"},
]


def compute_fix(reactions, blast):
    """Mirror analyze._fix so the static demo's step-down is consistent with the panel."""
    severe = [r for r in reactions if r.get("status") == "responded" and r["severity"] >= 2]
    n = len(severe) or 1
    frac = {t: sum(1 for r in severe if r.get("fix_tier") == t) / n for t in ("copy", "production", "decision")}
    after_copy = max(0, round(blast * (1 - frac["copy"])))
    after_prod = max(0, round(after_copy - blast * frac["production"]))
    residual = max(0, round(blast * frac["decision"]))
    fix = json.loads(json.dumps(FIX))  # deep copy
    fix["stages"][0]["score"] = blast
    fix["stages"][1]["score"] = max(after_copy, residual)
    fix["stages"][2]["score"] = max(after_prod, residual)
    fix["residual"]["score"] = residual
    return fix


def main():
    reactions = persona_records() + lens_records() + stake_records()
    assert len(reactions) == 60, f"expected 60 agents, got {len(reactions)}"

    aggregate, grounding_index = reduce_aggregate(reactions, CREATIVE)
    blast = aggregate["blast_score"]

    badges = [
        {"emoji": r["emoji"], "role": r["label"], "verdict": r.get("verdict") or "", "note": r["quote"]}
        for r in reactions if r["kind"] == "stakeholder"
    ]

    golden = {
        "run_id": "gr_google_io2026_v1",
        "mode": "fixture",
        "scenario": SCENARIO,
        "creative_manifest": CREATIVE,
        "grounding_index": grounding_index,
        "reactions": reactions,
        "aggregate": aggregate,
        "fix": compute_fix(reactions, blast),
        "stakeholder_badges": badges,
        "headline": HEADLINE,
        "sponsor_trace": SPONSOR_TRACE,
    }

    json.dump(golden, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"wrote {OUT}")
    print(f"  brand={SCENARIO['brand']} agents={len(reactions)} blast={blast} "
          f"decision={aggregate['decision']} responders={aggregate['responders']} "
          f"abstained={aggregate['abstained']}")
    print(f"  top clusters: " + ", ".join(f"{c['label']} {c['pct']}%" for c in aggregate['clusters']))
    print(f"  peak: {aggregate['peak']['scene_id']} @ {aggregate['peak']['pct']}%")


if __name__ == "__main__":
    main()
