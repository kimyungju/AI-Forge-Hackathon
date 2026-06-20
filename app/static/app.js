/* 60's Pulse dashboard. Pure render of /api/golden (the baked golden run). */

// ---- helpers ---------------------------------------------------------------
const $ = (id) => document.getElementById(id);

function el(tag, attrs = {}, ...kids) {
  const n = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v == null) continue;
    if (k === "class") n.className = v;
    else if (k === "style") n.style.cssText = v;
    else if (k.startsWith("on") && typeof v === "function") n.addEventListener(k.slice(2), v);
    else n.setAttribute(k, v);
  }
  for (const kid of kids.flat()) {
    if (kid == null || kid === false) continue;
    n.append(kid.nodeType ? kid : document.createTextNode(String(kid)));
  }
  return n;
}

const SEV_COLOR = ["#9DB0A9", "#CBB24E", "#C2622C", "#A6201A"];
function heatSeverity(s) { return SEV_COLOR[s] ?? SEV_COLOR[0]; }

function heatPct(p) {
  const stops = [[0, [157, 176, 169]], [0.45, [203, 178, 78]], [0.72, [194, 98, 44]], [1, [166, 32, 26]]];
  p = Math.max(0, Math.min(1, p));
  for (let i = 1; i < stops.length; i++) {
    if (p <= stops[i][0]) {
      const [pa, ca] = stops[i - 1], [pb, cb] = stops[i];
      const t = (p - pa) / (pb - pa);
      const c = ca.map((v, j) => Math.round(v + (cb[j] - v) * t));
      return `rgb(${c.join(",")})`;
    }
  }
  return "rgb(166,32,26)";
}

const fmtT = (s) => `0:${String(Math.round(s)).padStart(2, "0")}`;

function initials(label) {
  const w = (label || "").replace(/[^A-Za-z ]/g, " ").split(/\s+/).filter(Boolean);
  if (!w.length) return "–";
  if (w.length === 1) return w[0].slice(0, 2).toUpperCase();
  return (w[0][0] + w[1][0]).toUpperCase();
}
function textOn(sev) { return sev >= 2 ? "#fff" : "var(--ink)"; }
function hashText(text) {
  let h = 0;
  for (let i = 0; i < text.length; i++) h = (h * 31 + text.charCodeAt(i)) >>> 0;
  return h;
}
function agentVars(r, salt = 0) {
  const abst = r.status === "abstain";
  const h = hashText(`${r.agent_id || r.label || ""}:${salt}`);
  const accents = ["#2E4A3B", "#493B5A", "#6B3B2A", "#2C4B62", "#665226", "#4D5147"];
  const skins = ["#E7B987", "#D6A16F", "#C7835C", "#B96F4D", "#8E5C43", "#F0CFA3"];
  return [
    `--agent-heat:${abst ? "var(--paper-3)" : heatSeverity(r.severity)}`,
    `--agent-text:${abst ? "var(--ink-faint)" : textOn(r.severity)}`,
    `--agent-accent:${abst ? "#A9A18C" : accents[h % accents.length]}`,
    `--agent-skin:${abst ? "#DAD4C4" : skins[(h >> 3) % skins.length]}`,
    `--agent-tilt:${(h % 9) - 4}deg`,
    `--agent-shift:${((h >> 5) % 7) - 3}%`,
  ].join(";");
}
function agentFace(r) {
  return [
    el("span", { class: "agent-portrait", "aria-hidden": "true" },
      el("span", { class: "agent-body" }),
      el("span", { class: "agent-head" })),
    el("span", { class: "agent-initials" }, initials(r.label)),
  ];
}
function avatar(r, size) {
  const abst = r.status === "abstain";
  return el("span", {
    class: `mono agent-avatar ${r.kind}${abst ? " abstain" : ""}`,
    style: `width:${size}px;height:${size}px;font-size:${Math.round(size * 0.36)}px;${agentVars(r, size)}`,
  }, agentFace(r));
}

function countUp(node, to, ms = 1100) {
  const start = performance.now();
  function step(now) {
    const k = Math.min(1, (now - start) / ms);
    const eased = 1 - Math.pow(1 - k, 3);
    node.textContent = Math.round(to * eased);
    if (k < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}

// ---- sections --------------------------------------------------------------
let quoteReturnFocus = null;

function renderMasthead(d) {
  $("outlet").textContent = d.headline.masthead;
  const a = d.aggregate;
  $("masthead-meta").replaceChildren(
    el("span", {}, el("b", {}, d.scenario.brand), " " + d.scenario.category),
    el("span", {}, el("b", {}, a.panel_size), " agents"),
    ...(a.abstained ? [el("span", {}, el("b", {}, a.abstained), " abstained")] : []),
    el("span", {}, "grounded ", el("b", {}, d.scenario.date)),
  );
  const track = $("ticker");
  track.replaceChildren();
  for (let pass = 0; pass < 2; pass++) {
    for (const sponsor of d.sponsor_trace) {
      track.append(
        el("span", {}, el("b", {}, sponsor.sponsor), " " + sponsor.detail),
        el("span", { class: "dot" }, "•"),
      );
    }
  }
}

function renderBlast(d) {
  const a = d.aggregate;
  $("blast-band").textContent = `${a.stability}  ·  ${a.severe_count} of ${a.responders} severe`;
  $("panel-count").textContent = a.abstained ? `${a.responders} responded · ${a.abstained} abstained` : `${a.responders} responded`;
  const chip = $("decision-chip");
  chip.textContent = a.decision;
  chip.className = "decision-chip " + a.decision.toLowerCase();
  // animate after a beat so the panel begins igniting first
  const num = $("blast-num");
  num.classList.remove("settled");
  setTimeout(() => {
    countUp(num, a.blast_score, 1400);
    $("heat-fill").style.width = a.blast_score + "%";
    setTimeout(() => num.classList.add("settled"), 1400);
  }, 520);
}

function renderCreative(d) {
  const peak = d.aggregate.peak;
  const scene = d.creative_manifest.find((s) => s.scene_id === peak.scene_id) || d.creative_manifest[0];
  $("creative").replaceChildren(
    el("div", { class: "frame" },
      el("div", { class: "tc" }, `${fmtT(scene.t_start)} · ${peak.pct}% triggered here`),
      el("div", { class: "sim-watermark" }, "SIMULATED"),
      el("div", { class: "ost" }, scene.on_screen_text || `"${scene.transcript}"`),
      el("div", { class: "vd" }, scene.visual_desc),
    ),
  );
}

function renderFutureHeadline(d) {
  $("future-headline").replaceChildren(
    el("span", { class: "kicker" }, "Tomorrow's headline if you launch as-is"),
    document.createTextNode(d.headline.title),
  );
}

// Diverging sentiment spectrum: how the room actually feels, not just the % severe.
const SENT_BUCKETS = [
  { v: -2, label: "hostile", color: "#A6201A" },
  { v: -1, label: "wary", color: "#C2622C" },
  { v: 0, label: "neutral", color: "#9DB0A9" },
  { v: 1, label: "warm", color: "#2E6B4F" },
];
function renderSentiment(d) {
  const wrap = $("sentiment");
  if (!wrap) return;
  const resp = d.reactions.filter((r) => (r.status || "responded") === "responded");
  const n = resp.length || 1;
  const counts = SENT_BUCKETS.map((b) => resp.filter((r) => (r.sentiment ?? 0) === b.v).length);
  const mean = resp.reduce((s, r) => s + (r.sentiment ?? 0), 0) / n;
  const meanPct = ((mean + 2) / 3) * 100; // map -2..1 onto 0..100
  wrap.replaceChildren(
    el("div", { class: "sent-head" },
      el("span", {}, "Room sentiment"),
      el("span", { class: "sent-mean" }, `mean ${mean.toFixed(2)} · ${mean < -0.5 ? "hostile" : mean < 0 ? "wary" : "mixed"}`)),
    el("div", { class: "sent-bar" },
      ...SENT_BUCKETS.map((b, i) => {
        const pct = (counts[i] / n) * 100;
        const seg = el("span", { class: "sent-seg", style: `background:${b.color};width:0`, title: `${b.label}: ${counts[i]}` });
        requestAnimationFrame(() => { seg.style.width = pct + "%"; });
        return seg;
      }),
      el("span", { class: "sent-marker", style: `left:0`, title: `mean ${mean.toFixed(2)}` })),
    el("div", { class: "sent-legend" },
      ...SENT_BUCKETS.map((b, i) => el("span", { class: "sent-lg" },
        el("i", { style: `background:${b.color}` }), `${b.label} ${counts[i]}`))),
  );
  const marker = wrap.querySelector(".sent-marker");
  if (marker) requestAnimationFrame(() => { marker.style.left = meanPct + "%"; });
}

// Severity histogram + "would go public" channel mix under the panel grid.
const SEV_LABEL = ["calm", "mild", "serious", "go public"];
function renderPanelStats(d) {
  const wrap = $("panel-stats");
  if (!wrap) return;
  const resp = d.reactions.filter((r) => (r.status || "responded") === "responded");
  const n = resp.length || 1;
  const sev = [0, 1, 2, 3].map((s) => resp.filter((r) => r.severity === s).length);
  const maxSev = Math.max(...sev, 1);
  const wouldShare = resp.filter((r) => r.would_share && r.would_share.yes).length;
  wrap.replaceChildren(
    el("div", { class: "ps-hist" },
      ...sev.map((c, s) => {
        const col = el("div", { class: "ps-col" },
          el("div", { class: "ps-n" }, c),
          el("div", { class: "ps-bar-wrap" },
            el("div", { class: "ps-bar", style: `background:${heatSeverity(s)};height:0` })),
          el("div", { class: "ps-lab" }, SEV_LABEL[s]));
        const b = col.querySelector(".ps-bar");
        requestAnimationFrame(() => { b.style.height = (c / maxSev * 100) + "%"; });
        return col;
      })),
    el("div", { class: "ps-broadcast" },
      el("b", {}, `${Math.round(100 * wouldShare / n)}%`),
      ` would take it public · ${wouldShare} of ${n} responders ready to post`),
  );
}

// Orchestrated reveal: forensics sections rise as they enter the viewport.
function setupReveal() {
  const els = document.querySelectorAll("#dashboard-view .reveal");
  if (!("IntersectionObserver" in window)) { els.forEach((e) => e.classList.add("in")); return; }
  const io = new IntersectionObserver((entries) => {
    entries.forEach((en) => { if (en.isIntersecting) { en.target.classList.add("in"); io.unobserve(en.target); } });
  }, { threshold: 0.12 });
  els.forEach((e) => { e.classList.remove("in"); io.observe(e); });
}

function renderPanel(d) {
  const grid = $("panel-grid");
  grid.replaceChildren();
  d.reactions.forEach((r, i) => {
    const abst = r.status === "abstain";
    const tile = el("button", {
      class: `tile agent-avatar ${r.kind} ${abst ? "abstain" : "sev" + r.severity}`,
      type: "button",
      style: `--i:${i};${agentVars(r, i)}`,
      title: `${r.label}${abst ? " (abstained)" : ""}`,
      "aria-label": `${r.label}${abst ? " abstained" : ": open reaction"}`,
      disabled: abst ? "disabled" : null,
      onclick: () => !abst && openQuote(r),
    }, agentFace(r));
    grid.append(tile);
  });
  $("panel-sub").textContent = `${d.reactions.length} agents`;
  $("panel-legend").replaceChildren(
    legend("persona", "first-person personas"),
    legend("lens", "concern lenses (3rd person)"),
    legend("stakeholder", "stakeholders"),
    el("span", { class: "lg" }, el("span", { class: "swatch persona", style: `background:${heatSeverity(3)}` }), "severe"),
    el("span", { class: "lg" }, el("span", { class: "swatch persona", style: `background:${heatSeverity(0)}` }), "calm"),
  );
}
function legend(kind, label) {
  return el("span", { class: "lg" }, el("span", { class: `swatch ${kind}`, style: "background:var(--calm)" }), label);
}

function renderClusters(d) {
  const wrap = $("clusters");
  wrap.replaceChildren();
  d.aggregate.clusters.forEach((c) => {
    const bar = el("span", { style: `background:${heatPct(c.pct / 80)}` });
    wrap.append(el("div", { class: "cluster" },
      el("div", { class: "cluster-head" },
        el("span", { class: "cluster-cat" }, c.label,
          el("span", { class: "evi " + (c.evidence ? "has" : "spec") }, c.evidence ? "cited" : "speculation")),
        el("span", { class: "cluster-nums" },
          el("span", { class: "cluster-count" }, `${c.count} agents`),
          el("span", { class: "cluster-pct" }, c.pct + "%"))),
      el("div", { class: "cluster-bar" }, bar),
      el("div", { class: "cluster-quote" }, `“${c.pull_quote}”`),
    ));
    requestAnimationFrame(() => { bar.style.width = c.pct + "%"; });
  });
}

function renderTimeline(d) {
  const wrap = $("timeline");
  wrap.replaceChildren();
  const tl = d.aggregate.timeline;
  const max = Math.max(...tl.map((t) => t.pct), 1);
  tl.forEach((t) => {
    const isPeak = t.scene_id === d.aggregate.peak.scene_id;
    const bar = el("div", { class: "bar", style: `background:${heatPct(t.pct / 80)}` });
    const col = el("button", {
      class: "tl-bar" + (isPeak ? " peak" : ""),
      type: "button",
      "aria-label": `${fmtT(t.t_start)} to ${fmtT(t.t_end)} triggered ${t.pct}% of the panel`,
      onclick: () => readout(d, t),
    },
      isPeak ? el("div", { class: "peak-tag" }, "PEAK") : null,
      el("div", { class: "pct" }, t.pct + "%"),
      bar,
      el("div", { class: "t" }, fmtT(t.t_start)),
    );
    wrap.append(col);
    requestAnimationFrame(() => { bar.style.height = (t.pct / max * 72) + "%"; });
  });
  readout(d, tl.find((t) => t.scene_id === d.aggregate.peak.scene_id));
}
function readout(d, t) {
  $("timeline-readout").replaceChildren(
    el("b", {}, `${fmtT(t.t_start)}–${fmtT(t.t_end)} · ${t.pct}%`),
    " of the panel triggered here.",
    el("br"),
    el("span", { class: "q" }, `“${t.transcript}”`),
    el("br"),
    t.visual_desc || "",
  );
}

function renderStakeholders(d) {
  const wrap = $("stakeholders");
  wrap.replaceChildren();
  d.stakeholder_badges.forEach((b) => {
    wrap.append(el("div", { class: "badge", title: b.note },
      avatar({ label: b.role, kind: "stakeholder", severity: 3, status: "responded" }, 30),
      el("div", {},
        el("div", { class: "brole" }, b.role),
        el("div", { class: "bverdict" }, b.verdict)),
    ));
  });
}

function renderFix(d) {
  const steps = $("fix-steps");
  steps.replaceChildren();
  d.fix.stages.forEach((s, i) => {
    if (i > 0) steps.append(el("div", { class: "step-arrow" }, "→"));
    steps.append(el("div", { class: `step ${s.tier || s.id}` },
      el("div", { class: "s-score" }, s.score),
      el("div", { class: "s-label" }, s.label),
      el("div", { class: "s-detail" }, s.detail || ""),
    ));
  });
  steps.append(el("div", { class: "step-arrow" }, "→"));
  steps.append(el("div", { class: "step residual" },
    el("div", { class: "s-score" }, d.fix.residual.score),
    el("div", { class: "s-label" }, "Residual · decision"),
    el("div", { class: "s-detail" }, d.fix.residual.label),
  ));

  const copy = d.fix.stages.find((s) => s.tier === "copy") || {};
  const prod = d.fix.stages.find((s) => s.tier === "production") || {};
  $("fix-cards").replaceChildren(
    el("div", { class: "fix-card copy" },
      el("h4", {}, "COPY-FIXABLE"),
      el("div", { class: "ba" },
        el("div", { class: "old" }, copy.before || ""),
        el("div", { class: "new" }, copy.after || "")),
      el("p", {}, copy.detail || "")),
    el("div", { class: "fix-card production" },
      el("h4", {}, "PRODUCTION · UNFIXABLE BY WORDING"),
      el("p", {}, prod.detail || "")),
    el("div", { class: "fix-card decision" },
      el("h4", {}, "DECISION · NO-GO"),
      el("p", {}, d.fix.residual.label)),
  );
}

function openQuote(r) {
  const kindLabel = { persona: "Persona · first person", lens: "Concern lens · third person", stakeholder: "Stakeholder" }[r.kind];
  const grounded = r.grounding && r.grounding.length;
  quoteReturnFocus = document.activeElement instanceof HTMLElement ? document.activeElement : null;
  $("qc-body").replaceChildren(
    avatar(r, 46),
    el("div", { class: "qc-role" }, `${r.label} — ${kindLabel}`),
    el("div", { class: "qc-quote" }, `“${r.quote}”`),
    el("div", { class: "qc-meta" },
      el("span", { class: "qc-tier " + r.fix_tier }, r.fix_tier + "-fixable"),
      el("span", { class: "qc-search" }, "Searched: " + (r.grounding_query || "—"))),
    el("div", { class: "qc-ground" },
      el("div", { class: "qc-ground-h" }, grounded ? "Grounded in its own scrape" : "Grounding"),
      grounded
        ? el("div", { class: "qc-snippets" }, r.grounding.map((g) =>
            el("div", { class: "qc-snippet" },
              el("span", { class: "qc-src" }, "Source — " + g.source),
              el("span", { class: "qc-snip" }, "“" + g.text + "”"))))
        : el("span", { class: "evi spec" }, "model speculation — no evidence found for this objection")),
    el("div", { class: "qc-q" }, el("b", {}, "Press-conference question: "), r.question),
  );
  const card = $("quote-card");
  card.hidden = false;
  card.classList.remove("hidden");
  card.setAttribute("aria-hidden", "false");
  $("qc-close").focus();
  setViewsInert(true);
}
function closeQuote() {
  const card = $("quote-card");
  if (card.hidden) return;
  const returnTarget =
    quoteReturnFocus && document.contains(quoteReturnFocus) ? quoteReturnFocus : null;
  setViewsInert(false);
  restoreQuoteFocus(returnTarget);
  if (card.contains(document.activeElement) && document.activeElement instanceof HTMLElement) {
    document.activeElement.blur();
  }
  card.classList.add("hidden");
  card.setAttribute("aria-hidden", "true");
  card.hidden = true;
  restoreQuoteFocus(returnTarget);
  quoteReturnFocus = null;
}
function restoreQuoteFocus(target) {
  if (!target || !document.contains(target)) return;
  target.focus();
  requestAnimationFrame(() => {
    if (document.contains(target)) target.focus();
  });
}
function setViewsInert(enabled) {
  for (const view of document.querySelectorAll(".view")) {
    view.inert = enabled;
    if (enabled) view.setAttribute("aria-hidden", "true");
    else view.removeAttribute("aria-hidden");
  }
}
function focusableQuoteElements() {
  return Array.from($("quote-card").querySelectorAll("button, [href], input, select, textarea, [tabindex]:not([tabindex='-1'])"))
    .filter((node) => !node.disabled && !node.hidden);
}
function trapQuoteFocus(e) {
  const card = $("quote-card");
  if (card.hidden || e.key !== "Tab") return;
  const focusable = focusableQuoteElements();
  if (!focusable.length) {
    e.preventDefault();
    card.focus();
    return;
  }
  const first = focusable[0];
  const last = focusable[focusable.length - 1];
  if (e.shiftKey && document.activeElement === first) {
    e.preventDefault();
    last.focus();
  } else if (!e.shiftKey && document.activeElement === last) {
    e.preventDefault();
    first.focus();
  }
}

// ---- views -----------------------------------------------------------------
function showView(id) {
  for (const v of document.querySelectorAll(".view")) v.classList.toggle("hidden", v.id !== id);
  window.scrollTo(0, 0);
}

// ---- stage 1: input --------------------------------------------------------
function setupInput() {
  const text = $("iv-text"), brand = $("iv-brand"), runBtn = $("run-btn"), chips = $("iv-chips");
  const attachments = [];

  const refresh = () => { runBtn.disabled = !(text.value.trim() || attachments.length); };

  function renderChips() {
    chips.replaceChildren(...attachments.map((a, i) =>
      el("span", { class: "chip " + a.kind },
        a.kind === "image" && a.url !== "#"
          ? el("img", { class: "chip-thumb", src: a.url, alt: "" })
          : el("span", { class: "chip-ico" }, a.kind === "video" ? "VID" : "IMG"),
        el("span", { class: "chip-name" }, a.name),
        el("button", {
          class: "chip-x", type: "button",
          "aria-label": "Remove " + a.name,
          onclick: () => { attachments.splice(i, 1); renderChips(); refresh(); },
        }, "×"))));
  }

  function addFile(file, kind) {
    if (!file) return;
    attachments.push({ kind, name: file.name, url: URL.createObjectURL(file) });
    renderChips(); refresh();
  }

  text.addEventListener("input", refresh);
  $("add-image").addEventListener("click", () => $("file-image").click());
  $("add-video").addEventListener("click", () => $("file-video").click());
  $("file-image").addEventListener("change", (e) => addFile(e.target.files[0], "image"));
  $("file-video").addEventListener("change", (e) => addFile(e.target.files[0], "video"));

  const composer = $("composer");
  ["dragover", "dragenter"].forEach((ev) =>
    composer.addEventListener(ev, (e) => { e.preventDefault(); composer.classList.add("drag"); }));
  ["dragleave", "drop"].forEach((ev) =>
    composer.addEventListener(ev, (e) => { e.preventDefault(); composer.classList.remove("drag"); }));
  composer.addEventListener("drop", (e) => {
    for (const f of e.dataTransfer.files) addFile(f, f.type.startsWith("video") ? "video" : "image");
  });

  $("preset-merliontel").addEventListener("click", () => {
    text.value =
      'Google I/O 2026 "100 things" keynote, read as an always-on AI launch. Gemini Spark, a ' +
      '24/7 personal agent, "works in the background on your phone or laptop even while they\'re ' +
      'turned off." Personal Intelligence connects your Gmail and Photos. Daily Brief "works ' +
      'overnight," analysing your inbox, calendar and tasks. Agents operate 24/7 across the web. ' +
      'Every output carries an imperceptible SynthID watermark, expanding to Search and Chrome.';
    brand.value = "Google";
    attachments.length = 0;
    attachments.push({ kind: "video", name: "google_io_2026_keynote.mp4", url: "#" });
    renderChips(); refresh();
    runBtn.focus();
  });

  composer.addEventListener("submit", (e) => { e.preventDefault(); if (!runBtn.disabled) startRun(text.value.trim(), brand.value.trim()); });
  refresh();
}

// ---- stage 2: live agent run -----------------------------------------------
let DATA = null;
let swarmTimers = [];

async function startRun(campaign, brand) {
  showView("run-view");
  $("rv-grid").replaceChildren();
  $("rv-feed").replaceChildren();
  $("rv-blast").textContent = "0";
  $("rv-count").textContent = "0 responded / 60 agents";
  $("verdict-btn").classList.add("hidden");
  const live = !!(campaign && campaign.trim());
  let ticker = null;
  if (live) {
    const msgs = [
      "Convening the panel on your launch…",
      "60 agents — public & press — reading your announcement…",
      "Reasoning on Kimi / Moonshot…",
      "Each agent forming its own take…",
    ];
    let mi = 0;
    $("rv-status").textContent = msgs[0];
    $("rv-sponsor").textContent = "Kimi / Moonshot · live";
    ticker = setInterval(() => { $("rv-status").textContent = msgs[++mi % msgs.length]; }, 1900);
  }
  try {
    if (live) {
      const res = await fetch("/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ campaign, brand }),
      });
      if (!res.ok) throw new Error("HTTP " + res.status);
      DATA = await res.json();
    } else {
      DATA = await (await fetch("/api/golden")).json();
    }
  } catch (err) {
    // safety net: replay the baked golden run if live fails
    $("rv-status").textContent = "Live unavailable, replaying baked run…";
    try { DATA = await (await fetch("/api/golden")).json(); }
    catch (e2) { if (ticker) clearInterval(ticker); $("rv-status").textContent = "Could not load data"; return; }
  }
  if (ticker) clearInterval(ticker);
  playSwarm(DATA);
}

function playSwarm(d) {
  const grid = $("rv-grid"), feed = $("rv-feed");
  grid.replaceChildren(); feed.replaceChildren();
  $("rv-blast").textContent = "0";
  swarmTimers.forEach(clearTimeout); swarmTimers = [];

  const reactions = d.reactions;
  const N = reactions.length;
  const finalBlast = d.aggregate.blast_score;
  const finalResp = d.aggregate.responders;
  const SPONSORS = ["Kimi K2.6 reasoning", "Bright Data grounding", "Daytona sandboxed", "VideoDB scene-aware"];

  const tiles = reactions.map((r) => {
    const t = el("div", {
      class: `rv-tile agent-avatar ${r.kind}`,
      style: agentVars(r, r.agent_id || r.label),
      title: r.label,
    }, agentFace(r));
    grid.append(t);
    return t;
  });

  let responded = 0;
  const STEP = 78;
  reactions.forEach((r, i) => {
    const timer = setTimeout(() => {
      const abst = r.status === "abstain";
      const tile = tiles[i];
      tile.classList.add("on");
      if (abst) tile.classList.add("abstain");
      else tile.classList.add("sev" + r.severity);

      if (!abst) {
        responded++;
        feed.prepend(el("div", { class: "feed-item sev" + r.severity },
          avatar(r, 28),
          el("div", { class: "fi-body" },
            el("div", { class: "fi-label" }, r.label),
            el("div", { class: "fi-quote" }, "“" + r.quote + "”"),
            el("div", { class: "fi-ground" },
              "Searched: " + (r.grounding_query || "no live grounding") +
              (r.grounding && r.grounding.length ? "  ·  found on " + r.grounding[0].source : "")))));
        while (feed.children.length > 7) feed.lastChild.remove();
      }

      $("rv-count").textContent = `${responded} responded / ${N} agents`;
      $("rv-blast").textContent = Math.round(finalBlast * Math.min(1, responded / finalResp));
      $("rv-status").textContent = "Agents reacting live…";
      $("rv-sponsor").textContent = SPONSORS[i % SPONSORS.length];

      if (i === N - 1) finishSwarm(d);
    }, 450 + i * STEP);
    swarmTimers.push(timer);
  });
}

function finishSwarm(d) {
  $("rv-status").textContent = d.aggregate.abstained ? `Verdict ready · ${d.aggregate.abstained} abstained` : "Verdict ready";
  $("rv-count").textContent = `${d.aggregate.responders} responded / ${d.aggregate.panel_size} agents`;
  $("rv-blast").textContent = d.aggregate.blast_score;
  $("verdict-btn").classList.remove("hidden");
  $("verdict-btn").onclick = () => showDashboard(d);
}

// ---- stage 3: dashboard ----------------------------------------------------
function showDashboard(d) {
  swarmTimers.forEach(clearTimeout); swarmTimers = [];
  showView("dashboard-view");
  renderDashboard(d);
}

function renderDashboard(d) {
  document.title = `60's Pulse — ${d.scenario.brand}`;
  renderMasthead(d);
  renderBlast(d);
  renderSentiment(d);
  renderCreative(d);
  renderFutureHeadline(d);
  renderPanel(d);
  renderPanelStats(d);
  renderClusters(d);
  renderTimeline(d);
  renderStakeholders(d);
  renderFix(d);
  $("foot").replaceChildren(
    el("span", {}, `run ${d.run_id} · mode ${d.mode}`),
    el("span", {}, "60's Pulse · Agent Forge AI Hackathon 2026"),
    el("span", {}, "All reactions are synthetic. Fictional masthead. Not a prediction."),
  );
  setupReveal();
}

// ---- boot ------------------------------------------------------------------
function boot() {
  $("qc-close").addEventListener("click", closeQuote);
  $("quote-card").addEventListener("click", (e) => { if (e.target.id === "quote-card") closeQuote(); });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeQuote();
    trapQuoteFocus(e);
  });

  const skip = $("skip-btn");
  if (skip) skip.addEventListener("click", () => { if (DATA) showDashboard(DATA); });

  setupInput();
  showView("input-view");
}

document.addEventListener("DOMContentLoaded", boot);
