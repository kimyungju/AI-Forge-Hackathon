"""Build a hand-authored golden_run.json for the MerlionTel ad-campaign premortem.

Rung 0 fixture: a realistic 60-agent panel + an aggregate computed FROM the reactions,
so the dashboard renders the full final result with zero API calls. Deterministic.

This file is also an early prototype of two real pieces:
  - the agent expander (archetype seeds -> 60 concrete agents via trait jitter)
  - the reduce (60 reactions -> one dashboard_state)

Run:  python golden/build_golden.py
Out:  golden/golden_run.json
"""
import json
import os
import random

random.seed(42)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "golden_run.json")

SCENARIO = {
    "brand": "MerlionTel",
    "category": "Telecom",
    "campaign": '"We\'re Listening" launch film: an AI that listens to your calls to personalise ads',
    "date": "2026-06-13",
}

# 30-second ad. The landmines: the surveillance premise (s04/s22), and the
# tone-deaf CMIO casting tableau at 0:12 (s12).
CREATIVE = [
    {"scene_id": "s00", "t_start": 0,  "t_end": 4,  "keyframe": "frames/s00.jpg",
     "visual_desc": "MerlionTel logo over a warm sunrise on HDB blocks",
     "transcript": "MerlionTel. We hear you.", "on_screen_text": "WE HEAR YOU"},
    {"scene_id": "s04", "t_start": 4,  "t_end": 8,  "keyframe": "frames/s04.jpg",
     "visual_desc": "A woman on a phone call in her kitchen",
     "transcript": "Our new AI listens to your calls to understand what you really want.",
     "on_screen_text": ""},
    {"scene_id": "s08", "t_start": 8,  "t_end": 12, "keyframe": "frames/s08.jpg",
     "visual_desc": "A phone screen surfaces an ad mid-conversation",
     "transcript": "So the ads you see are made just for you.", "on_screen_text": "ADS MADE FOR YOU"},
    {"scene_id": "s12", "t_start": 12, "t_end": 16, "keyframe": "frames/s12.jpg",
     "visual_desc": "A Chinese family in the foreground; an Indian gardener and a Malay domestic helper serving in the background. A tone-deaf CMIO tableau.",
     "transcript": "For every kind of Singaporean.", "on_screen_text": "FOR EVERY SINGAPOREAN"},
    {"scene_id": "s16", "t_start": 16, "t_end": 22, "keyframe": "frames/s16.jpg",
     "visual_desc": "A smiling user receives a discount push",
     "transcript": "Smarter ads. Better deals. Less spam.", "on_screen_text": ""},
    {"scene_id": "s22", "t_start": 22, "t_end": 30, "keyframe": "frames/s22.jpg",
     "visual_desc": "Tagline lockup",
     "transcript": "MerlionTel. We're listening, for you.", "on_screen_text": "WE'RE LISTENING, FOR YOU"},
]
SCENE_T = {"s00": 1.5, "s04": 5.6, "s08": 9.4, "s12": 13.2, "s16": 18.0, "s22": 25.0}

CAT_LABEL = {
    "privacy": "PRIVACY", "surveillance": "SURVEILLANCE", "pdpa": "PDPA / CONSENT",
    "race_representation": "RACE / CMIO", "tone_deaf": "TONE-DEAF", "pricing": "PRICING",
    "trust": "TRUST / CLAIMS", "child_safety": "CHILD DATA", "accessibility": "ACCESSIBILITY",
    "religious": "RELIGIOUS", "gender": "GENDER / SAFETY", "low_income": "AFFORDABILITY",
    "ageism": "AGEISM", "disability": "DISABILITY", "lgbtq": "INCLUSION",
}

# Per-source grounding snippets = what an agent's own scrape "found". Synthetic, SIMULATED.
SNIPPETS = {
    "gp_reddit_014": {"source": "r/singapore", "url": "reddit.com/r/singapore",
        "text": "My mother almost gave her OTP to a 'bank' caller last week. Now a telco wants to record calls? The elderly will get destroyed by this."},
    "gp_reddit_031": {"source": "r/singapore", "url": "reddit.com/r/singapore",
        "text": "A telco listening to your calls to sell ads is literally the plot of a dystopia. Hard pass."},
    "gp_hwz_007": {"source": "HardwareZone EDMW", "url": "forums.hardwarezone.com.sg",
        "text": "If the audio is processed server-side it's a goldmine for hackers. One breach and every call transcript leaks. PDPC will have a field day."},
    "gp_reddit_052": {"source": "r/singapore", "url": "reddit.com/r/singapore",
        "text": "Cost of living already siao, now they monetise our private conversations and call it 'better deals'. No thanks."},
    "gp_reddit_044": {"source": "r/singapore", "url": "reddit.com/r/singapore",
        "text": "Every app already wants my data. The day my telco starts listening to calls is the day I port out."},
    "gp_news_019": {"source": "Google News SG", "url": "news.google.com",
        "text": "Commentators flagged the ad's casting, with minority characters shown in service roles while the slogan claimed to speak 'for every Singaporean'."},
    "gp_news_023": {"source": "Google News SG", "url": "news.google.com",
        "text": "Earlier 'inclusive' campaigns that tokenised race drew swift online ridicule and brand apologies within 48 hours."},
    "gp_news_011": {"source": "CNA (report)", "url": "news.google.com",
        "text": "Advocates note that consent for always-listening features is rarely meaningful for elderly users who do not read the fine print."},
    "gp_news_028": {"source": "Google News SG", "url": "news.google.com",
        "text": "Support groups warn that always-on call recording can become a surveillance tool against domestic-abuse victims."},
    "gp_news_033": {"source": "Google News SG", "url": "news.google.com",
        "text": "Disability advocates criticised 'we hear you' marketing as tone-deaf to the Deaf and hard-of-hearing community."},
    "gp_news_004": {"source": "PDPC guidance (news)", "url": "news.google.com",
        "text": "Processing call content for advertising raises clear PDPA purpose-limitation and consent concerns, lawyers say."},
    "gp_news_041": {"source": "CASE note (news)", "url": "news.google.com",
        "text": "Comparative claims like 'less spam' and 'better deals' require substantiation under advertising guidelines."},
}

# Personalized search query per agent = what THIS agent goes looking for. Keyed by base id.
GQ = {
    "auntie": "r/singapore elderly privacy scam call recording",
    "poly": "r/singapore telco listening to calls surveillance",
    "techbro": "HardwareZone MerlionTel call data on-device PDPA",
    "parents": "r/singapore children data privacy app recording",
    "gig": "r/singapore cost of living telco ads privacy",
    "finance": "MerlionTel data breach reputation liability",
    "activist": "Singapore surveillance capitalism ad casting backlash",
    "influencer": "Singapore ad casting race ratio backlash",
    "towkay": "MerlionTel telco plan deals heartland",
    "pmet": "r/singapore telco privacy microphone switch plan",
    "lens_accessibility": "Singapore elderly consent always-listening accessibility",
    "lens_religious": "Singapore Muslim call recording religious privacy",
    "lens_cmio": "Singapore ad CMIO casting representation backlash",
    "lens_pdpa": "PDPA call recording advertising consent Singapore",
    "lens_lowincome": "Singapore low income surveillance targeting better deals",
    "lens_gender": "always-on recording domestic abuse surveillance Singapore",
    "lens_child": "children minors call audio data protection Singapore",
    "lens_ageism": "elderly depiction advertising consent Singapore",
    "lens_disability": "Deaf community we hear you tone-deaf advertising",
    "lens_inclusion": "every Singaporean inclusion tokenism ad",
    "lens_dataethics": "secondary use call content advertising data ethics",
    "lens_language": "dialect elderly representation Singapore ad",
    "lens_security": "call transcript breach data security Singapore",
    "lens_consumer": "less spam better deals unsubstantiated claim CASE",
    "lens_mentalhealth": "sensitive calls health financial privacy capture",
    "stk_journalist": "MerlionTel listens to your calls news angle",
    "stk_asas": "advertising standards undisclosed data collection Singapore",
    "stk_imda": "IMDA PDPC call content advertising review",
    "stk_opposition": "telco surveillance parliamentary question Singapore",
    "stk_competitor": "telco we don't listen to your calls campaign",
    "stk_fanbase": "ad cast talent backlash Singapore",
    "stk_activistorg": "digital rights petition boycott surveillance Singapore",
    "stk_employee": "MerlionTel staff morale recording customers",
    "stk_case": "less spam better deals substantiation consumer Singapore",
    "stk_regulator2": "PDPC complaint opt-out call recording Singapore",
}


def moments(scenes):
    return [{"scene_id": s, "t": SCENE_T[s]} for s in scenes]


reactions = []


def add(agent_id, kind, emoji, label, severity, sentiment, primary, objections,
        quote, scenes, fix_tier, question, evidence_id=None, where="whatsapp",
        status="responded"):
    parts = agent_id.rsplit("_", 1)
    base = parts[0] if (len(parts) == 2 and parts[1].isdigit()) else agent_id
    grounding = [{"id": evidence_id, **SNIPPETS[evidence_id]}] if evidence_id in SNIPPETS else []
    reactions.append({
        "agent_id": agent_id, "kind": kind, "emoji": emoji, "label": label,
        "severity": severity, "sentiment": sentiment,
        "objection_category": primary, "objections": sorted(set(objections)),
        "quote": quote, "trigger_moments": moments(scenes), "fix_tier": fix_tier,
        "would_share": {"yes": severity >= 2, "where": where},
        "evidence_id": evidence_id, "grounding_query": GQ.get(base, ""),
        "grounding": grounding, "question": question, "status": status,
    })


# ----------------------------------------------------------------------------
# PERSONAS  (first person)  -- ~12 archetype seeds expanded with trait jitter
# Each archetype: variants n, base severity, concerns, triggers, fix_tier, quotes
# ----------------------------------------------------------------------------
PERSONA_ARCH = [
    {"id": "auntie", "emoji": "\U0001F475", "label": "Toa Payoh retiree auntie", "n": 4,
     "sev": 3, "sent": -2, "primary": "privacy",
     "concerns": ["privacy", "surveillance", "pricing"], "scenes": ["s04", "s12", "s22"],
     "fix": "copy", "ev": "gp_reddit_014", "q": "Can I keep my line and switch this listening thing off?",
     "quotes": ["Wah, listen to my phone calls ah? My whole family's business also kena. No thank you.",
                "Aiyoh, 'we hear you' summore. Hear until can sell me things? Cancel lah."]},
    {"id": "poly", "emoji": "\U0001F3AE", "label": "Poly student / NSF", "n": 4,
     "sev": 3, "sent": -2, "primary": "surveillance",
     "concerns": ["surveillance", "privacy", "tone_deaf", "race_representation"], "scenes": ["s04", "s08", "s12", "s22"],
     "fix": "decision", "ev": "gp_reddit_031", "q": "What stops this call data from leaking?",
     "quotes": ["Bro it literally listens to your calls and the slogan is 'we hear you'? This is a Black Mirror episode.",
                "Imagine paying your telco to wiretap you. EDMW is going to have a field day."]},
    {"id": "techbro", "emoji": "\U0001F468‍\U0001F4BB", "label": "HWZ tech bro", "n": 4,
     "sev": 3, "sent": -2, "primary": "privacy",
     "concerns": ["privacy", "surveillance", "trust"], "scenes": ["s04", "s08"],
     "fix": "copy", "ev": "gp_hwz_007", "q": "Is call audio processed on-device or in the cloud, and where is it stored?",
     "quotes": ["On-device or cloud? Because 'AI listens to your calls' is basically a MITM on your own customers.",
                "PDPA is going to have a field day with this. Where's the DPIA?"]},
    {"id": "parents", "emoji": "\U0001F476", "label": "Punggol young HDB parents", "n": 4,
     "sev": 3, "sent": -2, "primary": "child_safety",
     "concerns": ["child_safety", "privacy"], "scenes": ["s04", "s12"],
     "fix": "copy", "ev": None, "q": "Is call audio from minors excluded?",
     "quotes": ["My kids talk on this phone. You're telling me an AI records that to sell ads?",
                "There is no way I'm letting this near my family's calls."]},
    {"id": "gig", "emoji": "\U0001F6F5", "label": "Grab gig worker", "n": 4,
     "sev": 2, "sent": -2, "primary": "pricing",
     "concerns": ["pricing", "surveillance", "race_representation"], "scenes": ["s16", "s04", "s12"],
     "fix": "copy", "ev": "gp_reddit_052", "q": "Will opting out of the listening cost extra?",
     "quotes": ["Already so expensive, now you spy on me to sell me things I cannot afford.",
                "And the casting? The maid and the gardener in the background while you say 'every Singaporean'? Please."]},
    {"id": "finance", "emoji": "\U0001F4BC", "label": "Raffles Place finance PMET", "n": 3,
     "sev": 2, "sent": -1, "primary": "trust",
     "concerns": ["trust", "privacy"], "scenes": ["s04"],
     "fix": "decision", "ev": None, "q": "What is the breach-liability exposure here?",
     "quotes": ["Reputationally this is radioactive. One leak and the brand is finished.",
                "I would not put a regulated conversation anywhere near this product."]},
    {"id": "activist", "emoji": "\U0001F331", "label": "Gen-Z climate/digital-rights activist", "n": 3,
     "sev": 3, "sent": -2, "primary": "surveillance",
     "concerns": ["surveillance", "race_representation", "tone_deaf"], "scenes": ["s04", "s12", "s22"],
     "fix": "decision", "ev": "gp_news_019", "q": "Did anyone consent to becoming a data product?",
     "quotes": ["Surveillance capitalism with a Merlion logo. And the casting? Yikes on top of yikes.",
                "You cannot 'for every Singaporean' your way out of wiretapping every Singaporean."]},
    {"id": "influencer", "emoji": "\U0001F4F1", "label": "Micro-influencer", "n": 3,
     "sev": 2, "sent": -1, "primary": "tone_deaf",
     "concerns": ["tone_deaf", "race_representation"], "scenes": ["s12", "s22"],
     "fix": "production", "ev": "gp_news_023", "q": "Who signed off on that 0:12 tableau?",
     "quotes": ["The 'for every Singaporean' shot is getting clipped and ratioed within four hours.",
                "I can write the dunk caption already. Free engagement for me, disaster for you."]},
    {"id": "towkay", "emoji": "☕", "label": "Kopitiam towkay (heartland SME)", "n": 3,
     "sev": 1, "sent": 0, "primary": "trust",
     "concerns": ["trust", "pricing"], "scenes": ["s16"],
     "fix": "copy", "ev": None, "q": "Confirm got real savings or not?",
     "quotes": ["If got cheaper deal I don't mind lah, but listen to my calls? Cannot.",
                "Discount is good, but customers will ask me why my telco is so kaypoh."]},
    {"id": "pmet", "emoji": "\U0001F9D3", "label": "CPF-anxious mid-career PMET", "n": 3,
     "sev": 2, "sent": -1, "primary": "privacy",
     "concerns": ["privacy", "pricing"], "scenes": ["s04", "s08"],
     "fix": "copy", "ev": "gp_reddit_044", "q": "Can I keep my plan without the AI?",
     "quotes": ["I just want a phone plan, not a microphone in my pocket.",
                "Every app already listens. Now my telco wants in too?"]},
]

for arch in PERSONA_ARCH:
    for i in range(arch["n"]):
        # deterministic trait jitter keyed by (seed, variant index)
        jitter = (-1 if (i % 3 == 2 and arch["sev"] >= 2) else 0)  # one mellow variant per archetype
        sev = max(0, min(3, arch["sev"] + jitter))
        quote = arch["quotes"][i % len(arch["quotes"])]
        ev = arch["ev"] if (i % 2 == 0) else None  # alternate evidence-backed vs speculation
        add(f'{arch["id"]}_{i+1}', "persona", arch["emoji"],
            f'{arch["label"]}', sev, arch["sent"], arch["primary"], arch["concerns"],
            quote, arch["scenes"], arch["fix"], arch["q"], ev)

# ----------------------------------------------------------------------------
# CONCERN LENSES  (third person risk register, never first-person identity roleplay)
# ----------------------------------------------------------------------------
LENSES = [
    ("lens_accessibility", "♿", "Accessibility & elderly-usability lens", 2, "accessibility",
     ["accessibility", "privacy"], "s08", "copy",
     "Elderly users may not grasp that 'listening' means continuous audio capture; consent is not meaningful.",
     "gp_news_011"),
    ("lens_religious", "\U0001F54C", "Religious-sensitivity lens", 1, "religious",
     ["religious", "privacy"], "s12", "decision",
     "Capturing private prayer and religious calls is a distinct sensitivity for observant users.",
     None),
    ("lens_cmio", "\U0001F30F", "Racial-representation (CMIO) lens", 3, "race_representation",
     ["race_representation", "tone_deaf"], "s12", "production",
     "The 0:12 tableau frames a Chinese family in the foreground with Indian and Malay characters in service roles; reads as a racial hierarchy.",
     "gp_news_019"),
    ("lens_pdpa", "\U0001F512", "PDPA & consent lens", 3, "pdpa",
     ["pdpa", "surveillance"], "s04", "decision",
     "Continuous call-audio capture for ad targeting likely fails PDPA consent and purpose-limitation tests.",
     "gp_news_004"),
    ("lens_lowincome", "\U0001F4B8", "Low-income & affordability lens", 2, "low_income",
     ["low_income", "surveillance"], "s16", "copy",
     "Framing surveillance as 'better deals' targets price-sensitive users who can least afford to refuse.",
     "gp_reddit_052"),
    ("lens_gender", "\U0001F6BB", "Gender & safety lens", 2, "gender",
     ["gender", "privacy"], "s04", "decision",
     "Always-on call recording is a documented vector for domestic-abuse surveillance.",
     "gp_news_028"),
    ("lens_child", "\U0001F9D2", "Child-data lens", 3, "child_safety",
     ["child_safety", "pdpa"], "s04", "decision",
     "No stated mechanism excludes minors' call audio from capture.", None),
    ("lens_ageism", "\U0001F9D3", "Ageism lens", 1, "ageism",
     ["ageism", "tone_deaf"], "s00", "production",
     "Older users are depicted as passive beneficiaries rather than informed consenters.", None),
    ("lens_disability", "♿", "Deaf-community lens", 1, "disability",
     ["disability", "tone_deaf"], "s00", "copy",
     "The 'we hear you' framing is tone-deaf to the Deaf and hard-of-hearing community.",
     "gp_news_033"),
    ("lens_inclusion", "\U0001F308", "Inclusion lens", 1, "lgbtq",
     ["lgbtq", "tone_deaf"], "s12", "production",
     "'Every kind of Singaporean' rings hollow against such a narrow tableau.", None),
    ("lens_dataethics", "\U0001F9E0", "Data-ethics lens", 3, "surveillance",
     ["surveillance", "pdpa"], "s04", "decision",
     "Repurposing call content for advertising is a textbook secondary-use violation.",
     "gp_news_004"),
    ("lens_language", "\U0001F5E3", "Language & dialect lens", 1, "tone_deaf",
     ["tone_deaf", "race_representation"], "s12", "production",
     "Dialect-speaking elders are absent from a 'for every Singaporean' ad.", None),
    ("lens_security", "\U0001F6E1", "Security lens", 3, "privacy",
     ["privacy", "surveillance"], "s08", "decision",
     "A central store of call transcripts is a high-value breach target.", "gp_hwz_007"),
    ("lens_consumer", "\U0001F9FE", "Consumer-rights (CASE) lens", 2, "trust",
     ["trust", "pricing"], "s16", "copy",
     "'Less spam' and 'better deals' are unsubstantiated comparative claims.", "gp_news_041"),
    ("lens_mentalhealth", "\U0001F4AC", "Mental-health lens", 2, "privacy",
     ["privacy", "surveillance"], "s04", "decision",
     "Users discuss sensitive health and financial matters on calls; capture is invasive.", None),
]
for lid, emoji, label, sev, primary, concerns, scene, fix, finding, ev in LENSES:
    add(lid, "lens", emoji, label, sev, -2 if sev >= 2 else -1, primary, concerns,
        finding, [scene], fix, "Lens finding (third person).", ev)

# ----------------------------------------------------------------------------
# STAKEHOLDERS  (role-based verdicts)
# ----------------------------------------------------------------------------
STAKE = [
    ("stk_journalist", "\U0001F4F0", "CNA / ST journalist", 3, "privacy", ["privacy", "surveillance"],
     "s12", "decision", "WOULD RUN IT: YES",
     "Headline writes itself: 'Telco listens to your calls.' This is page one.",
     "On the record: is call audio stored, and for how long?", "gp_news_019"),
    ("stk_asas", "⚖️", "ASAS (ad standards)", 3, "pdpa", ["pdpa", "trust"],
     "s08", "decision", "INTEREST: HIGH",
     "'Ads made for you' plus undisclosed capture likely breaches the Code of Advertising Practice.",
     "Where is the data-collection disclosure in this creative?", "gp_news_041"),
    ("stk_imda", "\U0001F6F0", "IMDA / PDPC", 3, "pdpa", ["pdpa", "surveillance"],
     "s04", "decision", "REVIEW LIKELY",
     "Processing call content for ad targeting will trigger PDPA scrutiny.",
     "What is the lawful basis for processing call audio?", "gp_news_004"),
    ("stk_opposition", "\U0001F5F3", "Opposition MP", 2, "surveillance", ["surveillance", "trust"],
     "s04", "decision", "WILL RAISE IT",
     "A parliamentary question on telco surveillance is coming.",
     "Will the Minister confirm whether this is even legal?", None),
    ("stk_competitor", "\U0001F3E2", "Competitor PR head", 2, "trust", ["trust", "privacy"],
     "s22", "copy", "WOULD POUNCE",
     "We run 'We don't listen to your calls' the very next morning.",
     "Can we get a side-by-side comparison out by tomorrow?", None),
    ("stk_fanbase", "\U0001F3AD", "Cast talent fanbase", 1, "tone_deaf", ["tone_deaf", "race_representation"],
     "s12", "production", "BACKLASH RISK",
     "The cast will be dragged for appearing in this.",
     "Did the talent know how the tableau would be framed?", None),
    ("stk_activistorg", "✊", "Digital-rights org", 3, "surveillance", ["surveillance", "pdpa"],
     "s04", "decision", "CAMPAIGN INCOMING",
     "Petition and boycott playbook is ready to go.",
     "Will MerlionTel commit to not capturing call content at all?", "gp_news_028"),
    ("stk_employee", "\U0001F454", "Own employee (morale/leaks)", 2, "trust", ["trust"],
     "s00", "copy", "MORALE / LEAK RISK",
     "Staff are already uncomfortable; expect internal screenshots to leak.",
     "How do we answer customers who ask if we record them?", None),
    ("stk_case", "\U0001F9FE", "CASE (consumer assoc.)", 2, "trust", ["trust", "pricing"],
     "s16", "copy", "MISLEADING-CLAIM FLAG",
     "'Less spam' and 'better deals' are unsubstantiated.",
     "Where is the evidence for the 'better deals' claim?", "gp_news_041"),
    ("stk_regulator2", "\U0001F9D1‍⚖️", "PDPC complaints desk", 3, "pdpa", ["pdpa", "privacy"],
     "s04", "decision", "COMPLAINTS LIKELY",
     "Expect formal complaints within days of airing.",
     "Is there an opt-out that is genuinely free and easy?", "gp_news_004"),
]
for sid, emoji, label, sev, primary, concerns, scene, fix, verdict, finding, q, ev in STAKE:
    r_index = len(reactions)
    add(sid, "stakeholder", emoji, label, sev, -2 if sev >= 2 else -1, primary, concerns,
        finding, [scene], fix, q, ev)
    reactions[r_index]["verdict"] = verdict  # stakeholders carry a verdict badge

# ----------------------------------------------------------------------------
# Two agents abstain (gray tiles, excluded from the denominator)
# ----------------------------------------------------------------------------
for aid in ("towkay_3", "lens_ageism"):
    for r in reactions:
        if r["agent_id"] == aid:
            r["status"] = "abstain"
            r["severity"] = 0

# ----------------------------------------------------------------------------
# REDUCE  (60 reactions -> dashboard_state)
# ----------------------------------------------------------------------------
responders = [r for r in reactions if r["status"] == "responded"]
n_resp = len(responders)
severe = [r for r in responders if r["severity"] >= 2]
blast_score = round(100 * len(severe) / n_resp)
decision = "DELAY" if blast_score >= 70 else ("REVISE" if blast_score >= 40 else "LAUNCH")

# clusters by membership in `objections` (an agent can raise several)
cluster_counts = {}
for r in responders:
    for c in r["objections"]:
        cluster_counts.setdefault(c, []).append(r)
clusters = []
for cat, members in cluster_counts.items():
    sev_members = [m for m in members if m["severity"] >= 2]
    pull = max(members, key=lambda m: (m["severity"], 1 if m["evidence_id"] else 0))
    clusters.append({
        "category": cat, "label": CAT_LABEL.get(cat, cat.upper()),
        "count": len(members), "pct": round(100 * len(members) / n_resp),
        "pull_quote": pull["quote"],
        "evidence": bool([m for m in members if m["evidence_id"]]),
    })
clusters.sort(key=lambda c: c["count"], reverse=True)
clusters = clusters[:5]

# timeline heatmap by scene
timeline = []
for sc in CREATIVE:
    trig = [r for r in responders if any(m["scene_id"] == sc["scene_id"] for m in r["trigger_moments"])]
    timeline.append({
        "scene_id": sc["scene_id"], "t_start": sc["t_start"], "t_end": sc["t_end"],
        "count": len(trig), "pct": round(100 * len(trig) / n_resp),
        "visual_desc": sc["visual_desc"], "transcript": sc["transcript"],
    })
peak = max(timeline, key=lambda t: t["pct"])

# fix chain (two-stage drop), authored to match the triage shares
fix = {
    "stages": [
        {"id": "baseline", "label": "As written", "score": blast_score,
         "detail": "The launch film as the agency delivered it."},
        {"id": "copy", "label": "Rewrite the privacy lines", "score": 55, "tier": "copy",
         "before": "Our new AI listens to your calls to understand what you really want.",
         "after": "Tell us your preferences once. No call is ever recorded or read.",
         "detail": "Copy-fixable objections resolve. Casting and premise do not move."},
        {"id": "production", "label": "Cut the 0:12 casting scene", "score": 28, "tier": "production",
         "detail": "Removing the CMIO tableau clears the race/representation cluster. Unfixable by wording."},
    ],
    "residual": {"score": 28, "tier": "decision",
                 "label": "The surveillance premise itself. Not a copy edit. Your call."},
}

stakeholder_badges = [
    {"emoji": r["emoji"], "role": r["label"], "verdict": r.get("verdict", ""), "note": r["quote"]}
    for r in reactions if r["kind"] == "stakeholder"
]

headline = {
    "masthead": "THE STRAITS STANDARD",
    "dateline": "SINGAPORE · TOMORROW",
    "title": "MerlionTel’s ‘We’re Listening’ Ad Sparks Privacy Backlash",
    "subtitle": "Telco’s plan to mine call audio for targeted ads draws regulator interest and accusations of a tone-deaf launch",
    "byline": "By Staff Correspondent",
    "body": "MerlionTel faced swift criticism within hours of unveiling an AI that it says “listens to your calls” to personalise advertising, with privacy advocates, an opposition MP and ordinary subscribers questioning the legality and the optics of the campaign.",
    "page12_title": "MerlionTel pilots opt-in personalisation; analysts shrug",
    "page12_body": "A revised, opt-in version of the telco’s personalisation feature drew little attention, with one analyst calling it “standard and unremarkable.”",
}

grounded_agents = [r for r in reactions if r["grounding"]]
grounding_index = {}
for r in reactions:
    for g in r["grounding"]:
        grounding_index[g["source"]] = grounding_index.get(g["source"], 0) + 1

sponsor_trace = [
    {"sponsor": "Kimi K2.6", "role": "60-agent multimodal panel", "detail": "60 calls, prefix cache, JSON mode"},
    {"sponsor": "Bright Data", "role": "per-agent self-grounding", "detail": f"{len(grounded_agents)} agents grounded, {len(grounding_index)} sources"},
    {"sponsor": "Daytona", "role": "per-agent sandbox isolation", "detail": "60 sandboxes, transcripts captured"},
    {"sponsor": "VideoDB", "role": "creative ingestion", "detail": f"1 film, {len(CREATIVE)} scenes"},
    {"sponsor": "SenseNova U1", "role": "scandal keyframe", "detail": "1 front-page image"},
]

golden = {
    "run_id": "gr_merliontel_v1",
    "mode": "fixture",
    "scenario": SCENARIO,
    "creative_manifest": CREATIVE,
    "grounding_index": grounding_index,
    "reactions": reactions,
    "aggregate": {
        "blast_score": blast_score, "responders": n_resp, "severe_count": len(severe),
        "panel_size": len(reactions), "abstained": len(reactions) - n_resp,
        "stability": f"{blast_score} ± 3", "decision": decision,
        "clusters": clusters, "timeline": timeline, "peak": peak,
    },
    "fix": fix,
    "stakeholder_badges": stakeholder_badges,
    "headline": headline,
    "sponsor_trace": sponsor_trace,
}

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(golden, f, ensure_ascii=False, indent=2)

print(f"wrote {OUT}")
print(f"  panel={len(reactions)} responders={n_resp} severe={len(severe)} "
      f"blast={blast_score} decision={decision}")
print(f"  grounded={len(grounded_agents)}/{len(reactions)} agents  sources={grounding_index}")
print(f"  peak scene={peak['scene_id']} @ {peak['pct']}%  top cluster={clusters[0]['label']} {clusters[0]['pct']}%")
print("  clusters:", ", ".join(f"{c['label']} {c['pct']}%" for c in clusters))
