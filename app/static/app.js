/* Premortem dashboard. Pure render of /api/golden (the baked golden run). */

// ---- helpers ---------------------------------------------------------------
const $ = (id) => document.getElementById(id);

function el(tag, attrs = {}, ...kids) {
  const n = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v == null) continue;
    if (k === "class") n.className = v;
    else if (k === "html") n.innerHTML = v;
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

const SEV_COLOR = ["#2E4A45", "#5E7A4E", "#E8A317", "#F5402C"];
function heatSeverity(s) { return SEV_COLOR[s] ?? SEV_COLOR[0]; }

function heatPct(p) {
  const stops = [[0, [46, 74, 69]], [0.45, [232, 163, 23]], [0.75, [245, 64, 44]], [1, [255, 45, 85]]];
  p = Math.max(0, Math.min(1, p));
  for (let i = 1; i < stops.length; i++) {
    if (p <= stops[i][0]) {
      const [pa, ca] = stops[i - 1], [pb, cb] = stops[i];
      const t = (p - pa) / (pb - pa);
      const c = ca.map((v, j) => Math.round(v + (cb[j] - v) * t));
      return `rgb(${c.join(",")})`;
    }
  }
  return "rgb(255,45,85)";
}

const fmtT = (s) => `0:${String(Math.round(s)).padStart(2, "0")}`;

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
function renderMasthead(d) {
  $("outlet").textContent = d.headline.masthead;
  const a = d.aggregate;
  $("masthead-meta").replaceChildren(
    el("span", {}, el("b", {}, d.scenario.brand), " " + d.scenario.category),
    el("span", { html: `<b>${a.panel_size}</b> agents` }),
    el("span", { html: `<b>${a.abstained}</b> abstained` }),
    el("span", { html: `grounded <b>${d.scenario.date}</b>` }),
    el("span", {}, d.scenario.campaign),
  );
  const parts = d.sponsor_trace.map((s) => `<b>${s.sponsor}</b> ${s.detail}`);
  const line = parts.join('<span class="dot">&bull;</span>');
  $("ticker").innerHTML = line + '<span class="dot">&bull;</span>' + line + '<span class="dot">&bull;</span>';
}

function renderBlast(d) {
  const a = d.aggregate;
  $("blast-band").textContent = `${a.stability}  ·  ${a.severe_count} of ${a.responders} severe`;
  $("panel-count").textContent = `${a.responders} responded · ${a.abstained} abstained`;
  const chip = $("decision-chip");
  chip.textContent = a.decision;
  chip.className = "decision-chip " + a.decision.toLowerCase();
  // animate after a beat so the panel begins igniting first
  setTimeout(() => {
    countUp($("blast-num"), a.blast_score);
    $("heat-fill").style.width = a.blast_score + "%";
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

function renderPanel(d) {
  const grid = $("panel-grid");
  grid.replaceChildren();
  d.reactions.forEach((r, i) => {
    const abst = r.status === "abstain";
    const tile = el("div", {
      class: `tile ${r.kind} ${abst ? "abstain" : "sev" + r.severity}`,
      style: `--i:${i}; background:${abst ? "" : heatSeverity(r.severity)}`,
      title: `${r.label}${abst ? " (abstained)" : ""}`,
      onclick: () => !abst && openQuote(r),
    }, r.emoji);
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
  return el("span", { class: "lg" }, el("span", { class: `swatch ${kind}`, style: "background:#5E7A4E" }), label);
}

function renderClusters(d) {
  const wrap = $("clusters");
  wrap.replaceChildren();
  d.aggregate.clusters.forEach((c) => {
    const bar = el("span", { style: `background:${heatPct(c.pct / 80)}` });
    wrap.append(el("div", { class: "cluster" },
      el("div", { class: "cluster-head" },
        el("span", { class: "cluster-cat" }, c.label,
          el("span", { class: "evi " + (c.evidence ? "has" : "spec") }, c.evidence ? "📎 evidence" : "speculation")),
        el("span", { class: "cluster-pct" }, c.pct + "%")),
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
    const col = el("div", { class: "tl-bar" + (isPeak ? " peak" : ""), onclick: () => readout(d, t) },
      el("div", { class: "pct" }, t.pct + "%"),
      bar,
      el("div", { class: "t" }, fmtT(t.t_start)),
    );
    wrap.append(col);
    requestAnimationFrame(() => { bar.style.height = (t.pct / max * 100) + "%"; });
  });
  readout(d, tl.find((t) => t.scene_id === d.aggregate.peak.scene_id));
}
function readout(d, t) {
  $("timeline-readout").innerHTML =
    `<b>${fmtT(t.t_start)}–${fmtT(t.t_end)} · ${t.pct}%</b> of the panel triggered here.<br>` +
    `<span class="q">“${t.transcript}”</span><br>${t.visual_desc}`;
}

function renderStakeholders(d) {
  const wrap = $("stakeholders");
  wrap.replaceChildren();
  d.stakeholder_badges.forEach((b) => {
    wrap.append(el("div", { class: "badge", title: b.note },
      el("span", { class: "bemoji" }, b.emoji),
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

let page12 = false;
function renderFrontpage(d) {
  const h = d.headline;
  const fp = $("frontpage");
  fp.className = "frontpage" + (page12 ? " page12" : "");
  const kids = [
    el("div", { class: "fp-watermark" }, "SIMULATED"),
    el("div", { class: "fp-name" }, h.masthead),
    el("div", { class: "fp-dateline" }, page12 ? "SINGAPORE · PAGE 12" : h.dateline),
    el("div", { class: "fp-title" }, page12 ? h.page12_title : h.title),
    page12 ? null : el("div", { class: "fp-sub" }, h.subtitle),
    el("div", { class: "fp-deck" },
      el("div", {},
        el("div", { class: "fp-byline" }, h.byline),
        el("div", { class: "fp-body" }, page12 ? h.page12_body : h.body)),
      el("div", { class: "fp-cut" }, el("span", {}, "SenseNova U1 keyframe · degraded · SIMULATED")),
    ),
  ].filter(Boolean);
  fp.replaceChildren(...kids);
}

function openQuote(r) {
  const kindLabel = { persona: "Persona · first person", lens: "Concern lens · third person", stakeholder: "Stakeholder" }[r.kind];
  const grounded = r.grounding && r.grounding.length;
  $("qc-body").replaceChildren(
    el("div", { class: "qc-emoji" }, r.emoji),
    el("div", { class: "qc-role" }, `${r.label} — ${kindLabel}`),
    el("div", { class: "qc-quote" }, `“${r.quote}”`),
    el("div", { class: "qc-meta" },
      el("span", { class: "qc-tier " + r.fix_tier }, r.fix_tier + "-fixable"),
      el("span", { class: "qc-search" }, "🔍 " + (r.grounding_query || "—"))),
    el("div", { class: "qc-ground" },
      el("div", { class: "qc-ground-h" }, grounded ? "Grounded in its own scrape" : "Grounding"),
      grounded
        ? el("div", { class: "qc-snippets" }, r.grounding.map((g) =>
            el("div", { class: "qc-snippet" },
              el("span", { class: "qc-src" }, "📎 " + g.source),
              el("span", { class: "qc-snip" }, "“" + g.text + "”"))))
        : el("span", { class: "evi spec" }, "model speculation — no evidence found for this objection")),
    el("div", { class: "qc-q" }, el("b", {}, "Press-conference question: "), r.question),
  );
  $("quote-card").classList.remove("hidden");
}
function closeQuote() { $("quote-card").classList.add("hidden"); }

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
          : el("span", { class: "chip-ico" }, a.kind === "video" ? "🎬" : "🖼"),
        el("span", { class: "chip-name" }, a.name),
        el("button", {
          class: "chip-x", type: "button",
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
      'MerlionTel "We\'re Listening" launch film. An AI that listens to your phone calls to ' +
      'personalise the ads you see. 30-second spot: "We hear you... our new AI listens to your ' +
      'calls... ads made for you... for every Singaporean... we\'re listening, for you."';
    brand.value = "MerlionTel";
    attachments.length = 0;
    attachments.push({ kind: "video", name: "merliontel_were_listening_30s.mp4", url: "#" });
    renderChips(); refresh();
    runBtn.focus();
  });

  composer.addEventListener("submit", (e) => { e.preventDefault(); if (!runBtn.disabled) startRun(); });
  refresh();
}

// ---- stage 2: live agent run -----------------------------------------------
let DATA = null;
let swarmTimers = [];

async function startRun() {
  showView("run-view");
  $("rv-status").textContent = "Booting 60 sandboxes…";
  $("verdict-btn").classList.add("hidden");
  try {
    const res = await fetch("/api/golden");
    if (!res.ok) throw new Error("HTTP " + res.status);
    DATA = await res.json();
  } catch (err) {
    $("rv-status").textContent = "Could not load /api/golden (" + err + ")";
    return;
  }
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
    const t = el("div", { class: `rv-tile ${r.kind}`, title: r.label }, r.emoji);
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
      else tile.style.background = heatSeverity(r.severity);

      if (!abst) {
        responded++;
        feed.prepend(el("div", { class: "feed-item sev" + r.severity },
          el("span", { class: "fi-emoji" }, r.emoji),
          el("div", { class: "fi-body" },
            el("div", { class: "fi-label" }, r.label),
            el("div", { class: "fi-quote" }, "“" + r.quote + "”"),
            el("div", { class: "fi-ground" },
              "🔍 " + (r.grounding_query || "no live grounding") +
              (r.grounding && r.grounding.length ? "  ·  found on " + r.grounding[0].source : "")))));
        while (feed.children.length > 7) feed.lastChild.remove();
      }

      $("rv-count").textContent = `${responded} / ${N}`;
      $("rv-blast").textContent = Math.round(finalBlast * Math.min(1, responded / finalResp));
      $("rv-status").textContent = "Agents reacting live…";
      $("rv-sponsor").textContent = SPONSORS[i % SPONSORS.length];

      if (i === N - 1) finishSwarm(d);
    }, 450 + i * STEP);
    swarmTimers.push(timer);
  });
}

function finishSwarm(d) {
  $("rv-status").textContent = "Verdict ready";
  $("rv-blast").textContent = d.aggregate.blast_score;
  $("verdict-btn").classList.remove("hidden");
  const auto = setTimeout(() => showDashboard(d), 1500);
  swarmTimers.push(auto);
  $("verdict-btn").onclick = () => { clearTimeout(auto); showDashboard(d); };
}

// ---- stage 3: dashboard ----------------------------------------------------
function showDashboard(d) {
  swarmTimers.forEach(clearTimeout); swarmTimers = [];
  showView("dashboard-view");
  renderDashboard(d);
}

function renderDashboard(d) {
  document.title = `Premortem — ${d.scenario.brand}`;
  renderMasthead(d);
  renderBlast(d);
  renderCreative(d);
  renderFutureHeadline(d);
  renderPanel(d);
  renderClusters(d);
  renderTimeline(d);
  renderStakeholders(d);
  renderFix(d);
  renderFrontpage(d);
  $("foot").replaceChildren(
    el("span", {}, `run ${d.run_id} · mode ${d.mode}`),
    el("span", {}, "Premortem · Agent Forge AI Hackathon 2026"),
    el("span", {}, "All reactions are synthetic. Fictional masthead. Not a prediction."),
  );
  $("page-toggle").onclick = () => {
    page12 = !page12;
    $("page-toggle").innerHTML = page12 ? "Show front page &rarr;" : "Show page 12 &rarr;";
    renderFrontpage(d);
  };
}

// ---- boot ------------------------------------------------------------------
function boot() {
  $("qc-close").addEventListener("click", closeQuote);
  $("quote-card").addEventListener("click", (e) => { if (e.target.id === "quote-card") closeQuote(); });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") closeQuote(); });

  const skip = $("skip-btn");
  if (skip) skip.addEventListener("click", () => { if (DATA) showDashboard(DATA); });

  setupInput();
  showView("input-view");
}

document.addEventListener("DOMContentLoaded", boot);
