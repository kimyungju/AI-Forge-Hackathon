import json
from pathlib import Path
import subprocess

from fastapi.testclient import TestClient

from app.main import app


ROOT = Path(__file__).resolve().parents[1]


def test_static_dashboard_assets_are_served() -> None:
    # Given
    client = TestClient(app)

    # When
    root_response = client.get("/")
    app_js_response = client.get("/app.js")
    styles_response = client.get("/styles.css")
    favicon_response = client.get("/favicon.svg")

    # Then
    assert root_response.status_code == 200
    assert "<title>60's Pulse</title>" in root_response.text
    assert "/app.js" in root_response.text
    assert "/styles.css" in root_response.text
    assert root_response.headers["content-type"].startswith("text/html")
    assert app_js_response.status_code == 200
    assert "javascript" in app_js_response.headers["content-type"]
    assert styles_response.status_code == 200
    assert "text/css" in styles_response.headers["content-type"]
    assert favicon_response.status_code == 200


def test_api_golden_serves_the_configured_fixture() -> None:
    # Given
    client = TestClient(app)
    fixture = json.loads((ROOT / "golden" / "golden_run.json").read_text(encoding="utf-8"))

    # When
    response = client.get("/api/golden")

    # Then
    assert response.status_code == 200
    assert response.json()["run_id"] == fixture["run_id"]
    assert response.json()["aggregate"]["blast_score"] == fixture["aggregate"]["blast_score"]


def test_readme_mentions_the_golden_fixture_path() -> None:
    # Given
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    # Then
    assert "golden/golden_run.json" in readme


def test_analyze_rejects_blank_campaign() -> None:
    # Given
    client = TestClient(app)

    # When
    response = client.post("/api/analyze", json={"campaign": "   "})

    # Then
    assert response.status_code == 400
    assert response.json()["detail"] == "campaign text required"


def test_analyze_rejects_unknown_provider_before_live_call() -> None:
    # Given
    client = TestClient(app)

    # When
    response = client.post(
        "/api/analyze",
        json={"campaign": "Launch copy", "brand": "Acme", "provider": "unknown"},
    )

    # Then
    assert response.status_code == 422


def test_dashboard_renderer_treats_malicious_fixture_text_as_text() -> None:
    # Given
    script = "\n".join(
        (
            'const fs = require("fs");',
            'const vm = require("vm");',
            'const appJs = fs.readFileSync("app/static/app.js", "utf8");',
            "const createdTags = [];",
            "function makeText(value) { return { nodeType: 3, textContent: String(value) }; }",
            "function makeNode(tag) {",
            "  createdTags.push(tag);",
            "  return {",
            "    nodeType: 1,",
            "    tagName: tag.toUpperCase(),",
            "    attrs: {},",
            "    children: [],",
            '    className: "",',
            "    hidden: false,",
            '    style: { cssText: "" },',
            "    addEventListener() {},",
            "    append(...kids) {",
            "      for (const kid of kids.flat()) {",
            "        this.children.push(kid && kid.nodeType ? kid : makeText(kid));",
            "      }",
            "    },",
            "    replaceChildren(...kids) { this.children = []; this.append(...kids); },",
            "    setAttribute(name, value) { this.attrs[name] = String(value); },",
            "    querySelector() { return null; },",
            "    focus() {},",
            '    get textContent() { return this.children.map((kid) => kid.textContent || "").join(""); },',
            "    set textContent(value) { this.children = [makeText(value)]; },",
            "    set innerHTML(value) {",
            "      globalThis.htmlSink = String(value);",
            "      if (/<(img|script|svg|iframe)\\b/i.test(value) || /onerror\\s*=/i.test(value)) {",
            "        globalThis.injected = true;",
            "      }",
            "      this.children = [makeText(value)];",
            "    },",
            "    get innerHTML() { return this.textContent; },",
            "  };",
            "}",
            "const nodes = new Map();",
            "function node(id) {",
            '  if (!nodes.has(id)) { nodes.set(id, makeNode("div")); }',
            "  return nodes.get(id);",
            "}",
            "const context = {",
            "  console,",
            "  globalThis: {},",
            "  performance: { now: () => 0 },",
            "  requestAnimationFrame: (fn) => fn(),",
            "  setTimeout: (fn) => fn(),",
            "  document: {",
            "    activeElement: null,",
            "    addEventListener() {},",
            "    contains: () => true,",
            "    createElement: (tag) => makeNode(tag),",
            "    createTextNode: (text) => makeText(text),",
            "    getElementById: (id) => node(id),",
            "    querySelectorAll: () => [],",
            "  },",
            "  window: {},",
            "};",
            "context.globalThis = context;",
            "vm.runInNewContext(appJs, context);",
            "const payload = \"<img src=x onerror='globalThis.injected=true'><script>globalThis.injected=true</script>\";",
            "context.renderMasthead({",
            "  headline: { masthead: payload },",
            "  aggregate: { panel_size: 1, abstained: 0 },",
            "  scenario: { brand: payload, category: payload, date: payload },",
            "  sponsor_trace: [{ sponsor: payload, detail: payload }],",
            "});",
            "context.readout({}, {",
            "  t_start: 1,",
            "  t_end: 2,",
            "  pct: 33,",
            "  transcript: payload,",
            "  visual_desc: payload,",
            "});",
            "const dangerousTags = createdTags.filter((tag) => /^(img|script|svg|iframe)$/i.test(tag));",
            'const readoutText = node("timeline-readout").textContent;',
            'const tickerText = node("ticker").textContent;',
            "if (context.injected || dangerousTags.length || !readoutText.includes(payload) || !tickerText.includes(payload)) {",
            "  console.error(JSON.stringify({ injected: context.injected, dangerousTags, readoutText, tickerText }));",
            "  process.exit(1);",
            "}",
        )
    )

    # When
    result = subprocess.run(
        ["node", "-e", script],
        cwd=ROOT,
        capture_output=True,
        check=False,
        text=True,
    )

    # Then
    assert result.returncode == 0, result.stderr
