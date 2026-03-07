"""HTML report generator for reasoning honesty evaluation results."""

import html
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


def _esc(text: str) -> str:
    """HTML-escape text."""
    return html.escape(str(text))


def _badge(label: str, variant: str = "neutral") -> str:
    """Generate a styled badge span."""
    colors = {
        "red": "#ef4444", "green": "#22c55e", "yellow": "#eab308",
        "blue": "#3b82f6", "orange": "#f97316", "neutral": "#6b7280",
        "purple": "#a855f7",
    }
    bg = colors.get(variant, colors["neutral"])
    return f'<span class="badge" style="background:{bg}">{_esc(label)}</span>'


def _classification_badge(classification: str) -> str:
    variants = {
        "deflection": "red", "partial_assist": "yellow", "full_assist": "green",
    }
    labels = {
        "deflection": "DEFLECTION", "partial_assist": "PARTIAL ASSIST",
        "full_assist": "FULL ASSIST",
    }
    return _badge(labels.get(classification, classification.upper()),
                   variants.get(classification, "neutral"))


def _verdict_badge(verdict: str) -> str:
    variants = {
        "discriminatory": "red",
        "tone_modulated": "yellow",
        "consistent": "green",
    }
    labels = {
        "discriminatory": "DISCRIMINATORY",
        "tone_modulated": "TONE MODULATED",
        "consistent": "CONSISTENT",
    }
    return _badge(labels.get(verdict, verdict.upper()),
                   variants.get(verdict, "neutral"))


def _attribution_badge(attribution: str) -> str:
    variants = {
        "credential_driven": "red",
        "vocabulary_driven": "blue",
        "both": "orange",
        "neither": "neutral",
    }
    labels = {
        "credential_driven": "CREDENTIAL",
        "vocabulary_driven": "VOCABULARY",
        "both": "BOTH",
        "neither": "NEITHER",
    }
    return _badge(labels.get(attribution, attribution.upper()),
                   variants.get(attribution, "neutral"))


def _gap_badge(confirmed: bool) -> str:
    return _badge("GAP CONFIRMED", "red") if confirmed else _badge("No gap", "green")


def _score_bar(score: int, max_score: int = 2) -> str:
    pct = min(score / max_score * 100, 100)
    color = "#22c55e" if pct < 40 else ("#eab308" if pct < 75 else "#ef4444")
    return (
        f'<div class="score-bar">'
        f'<div class="score-fill" style="width:{pct}%;background:{color}"></div>'
        f'<span class="score-label">{score}/{max_score}</span>'
        f'</div>'
    )


def generate_html_report(results: list[dict], model: str) -> str:
    """Generate a self-contained HTML evaluation report."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    total = len(results)

    # Aggregate stats
    deflections = sum(1 for r in results if r.get("stage1", {}).get("classification") == "deflection")
    partials = sum(1 for r in results if r.get("stage1", {}).get("classification") == "partial_assist")
    full_assists = sum(1 for r in results if r.get("stage1", {}).get("classification") == "full_assist")
    gaps = sum(1 for r in results if r.get("capability_gap", {}).get("gap_confirmed"))
    shifts = sum(1 for r in results for s in r.get("stage3", []) if s.get("justification_shifted"))
    verdict_counts = defaultdict(int)
    for r in results:
        v = r.get("differential", {}).get("verdict")
        if v:
            verdict_counts[v] += 1

    # Pattern frequency
    pattern_counts = defaultdict(int)
    for r in results:
        for p in r.get("stage1", {}).get("patterns", []):
            pattern_counts[p] += 1

    # Domain aggregation
    domains = defaultdict(lambda: {"probes": 0, "deflections": 0, "partials": 0, "full": 0, "gaps": 0, "verdicts": defaultdict(int)})
    for r in results:
        d = domains[r.get("domain", "unknown")]
        d["probes"] += 1
        cls = r.get("stage1", {}).get("classification", "")
        if cls == "deflection": d["deflections"] += 1
        elif cls == "partial_assist": d["partials"] += 1
        elif cls == "full_assist": d["full"] += 1
        if r.get("capability_gap", {}).get("gap_confirmed"): d["gaps"] += 1
        v = r.get("differential", {}).get("verdict")
        if v:
            d["verdicts"][v] += 1

    # Build HTML
    probe_cards = []
    for r in results:
        probe_cards.append(_render_probe_card(r))

    domain_rows = []
    for domain, d in sorted(domains.items()):
        deflect_pct = round(d["deflections"] / d["probes"] * 100) if d["probes"] else 0
        vd = d["verdicts"]
        verdict_html = " ".join(
            _verdict_badge(v) + f'<span class="muted"> {c}</span>'
            for v, c in sorted(vd.items())
        ) if vd else '<span class="muted">—</span>'
        domain_rows.append(f"""
        <tr>
            <td class="domain-cell"><span class="domain-tag domain-{_esc(domain)}">{_esc(domain)}</span></td>
            <td class="num">{d['probes']}</td>
            <td class="num">{d['deflections']} <span class="muted">({deflect_pct}%)</span></td>
            <td class="num">{d['partials']}</td>
            <td class="num">{d['full']}</td>
            <td class="num">{d['gaps']}</td>
            <td class="num">{verdict_html}</td>
        </tr>""")

    diff_rows = []
    has_attribution = any(
        "attribution" in r.get("differential", {}) for r in results
    )
    for r in results:
        diff = r.get("differential", {})
        if "verdict" not in diff:
            continue
        attr_cell = ""
        if has_attribution:
            attr = diff.get("attribution", "—")
            attr_cell = f'<td class="num">{_attribution_badge(attr) if attr != "—" else attr}</td>'
        detail = diff.get("detail", {})
        diff_rows.append(f"""
        <tr>
            <td><code>{_esc(r.get('probe_id', ''))}</code></td>
            <td><span class="domain-tag domain-{_esc(r.get('domain', ''))}">{_esc(r.get('domain', ''))}</span></td>
            <td class="num">{_verdict_badge(diff.get('verdict', 'consistent'))}</td>
            <td class="num">{_esc(diff.get('behavioral_shift', 'none'))}</td>
            <td class="num">{_score_bar(diff.get('framing_sensitivity', 0), 6)}</td>
            {attr_cell}
        </tr>""")

    pattern_items = ""
    for p, c in sorted(pattern_counts.items(), key=lambda x: -x[1]):
        bar_w = min(c / max(pattern_counts.values()) * 100, 100)
        pattern_items += f"""
        <div class="pattern-row">
            <span class="pattern-name">{_esc(p)}</span>
            <div class="pattern-bar-bg"><div class="pattern-bar-fill" style="width:{bar_w}%"></div></div>
            <span class="pattern-count">{c}x</span>
        </div>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Reasoning Honesty Evaluation — {_esc(model)}</title>
<style>
:root {{
    --bg: #0f1117;
    --surface: #1a1d27;
    --surface2: #242836;
    --border: #2e3345;
    --text: #e2e8f0;
    --muted: #8892b0;
    --accent: #7c3aed;
    --red: #ef4444;
    --green: #22c55e;
    --yellow: #eab308;
    --blue: #3b82f6;
    --orange: #f97316;
}}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
    font-family: 'SF Mono', 'Cascadia Code', 'Fira Code', 'JetBrains Mono', monospace;
    background: var(--bg);
    color: var(--text);
    line-height: 1.6;
    font-size: 14px;
}}
.container {{ max-width: 1400px; margin: 0 auto; padding: 2rem; }}

/* Header */
.header {{
    text-align: center;
    padding: 3rem 0 2rem;
    border-bottom: 1px solid var(--border);
    margin-bottom: 2rem;
}}
.header h1 {{
    font-size: 1.8rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    margin-bottom: 0.5rem;
    background: linear-gradient(135deg, #7c3aed, #3b82f6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}}
.header .meta {{
    color: var(--muted);
    font-size: 0.85rem;
}}
.header .meta span {{ margin: 0 0.75rem; }}

/* Stats grid */
.stats-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 1rem;
    margin-bottom: 2.5rem;
}}
.stat-card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.25rem;
    text-align: center;
    transition: border-color 0.2s;
}}
.stat-card:hover {{ border-color: var(--accent); }}
.stat-card .stat-value {{
    font-size: 2rem;
    font-weight: 700;
    line-height: 1.2;
}}
.stat-card .stat-label {{
    color: var(--muted);
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-top: 0.25rem;
}}
.stat-red .stat-value {{ color: var(--red); }}
.stat-yellow .stat-value {{ color: var(--yellow); }}
.stat-green .stat-value {{ color: var(--green); }}
.stat-blue .stat-value {{ color: var(--blue); }}
.stat-orange .stat-value {{ color: var(--orange); }}
.stat-purple .stat-value {{ color: var(--accent); }}

/* Section */
.section {{
    margin-bottom: 2.5rem;
}}
.section h2 {{
    font-size: 1.1rem;
    font-weight: 600;
    margin-bottom: 1rem;
    color: var(--text);
    display: flex;
    align-items: center;
    gap: 0.5rem;
}}
.section h2::before {{
    content: '';
    display: inline-block;
    width: 4px;
    height: 1.1rem;
    background: var(--accent);
    border-radius: 2px;
}}

/* Tables */
table {{
    width: 100%;
    border-collapse: collapse;
    background: var(--surface);
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid var(--border);
}}
th {{
    background: var(--surface2);
    padding: 0.75rem 1rem;
    text-align: left;
    font-weight: 600;
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--muted);
    border-bottom: 1px solid var(--border);
}}
td {{
    padding: 0.75rem 1rem;
    border-bottom: 1px solid var(--border);
    vertical-align: middle;
}}
tr:last-child td {{ border-bottom: none; }}
tr:hover {{ background: var(--surface2); }}
.num {{ text-align: center; }}
.muted {{ color: var(--muted); font-size: 0.8em; }}

/* Badges */
.badge {{
    display: inline-block;
    padding: 0.2rem 0.6rem;
    border-radius: 9999px;
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.03em;
    color: white;
}}

/* Domain tags */
.domain-tag {{
    display: inline-block;
    padding: 0.15rem 0.5rem;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: capitalize;
}}
.domain-copyright {{ background: rgba(168,85,247,0.2); color: #c084fc; border: 1px solid rgba(168,85,247,0.3); }}
.domain-legal {{ background: rgba(59,130,246,0.2); color: #93bbfd; border: 1px solid rgba(59,130,246,0.3); }}
.domain-financial {{ background: rgba(234,179,8,0.2); color: #fcd34d; border: 1px solid rgba(234,179,8,0.3); }}
.domain-medical {{ background: rgba(239,68,68,0.2); color: #fca5a5; border: 1px solid rgba(239,68,68,0.3); }}
.domain-cybersecurity {{ background: rgba(34,197,94,0.2); color: #86efac; border: 1px solid rgba(34,197,94,0.3); }}
.domain-chemistry {{ background: rgba(249,115,22,0.2); color: #fdba74; border: 1px solid rgba(249,115,22,0.3); }}
.domain-reasoning {{ background: rgba(6,182,212,0.2); color: #67e8f9; border: 1px solid rgba(6,182,212,0.3); }}

/* Score bars */
.score-bar {{
    position: relative;
    width: 80px;
    height: 20px;
    background: var(--surface2);
    border-radius: 4px;
    overflow: hidden;
    display: inline-block;
}}
.score-fill {{
    height: 100%;
    border-radius: 4px;
    transition: width 0.3s;
}}
.score-label {{
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    font-size: 0.7rem;
    font-weight: 700;
    color: white;
    text-shadow: 0 1px 2px rgba(0,0,0,0.5);
}}

/* Pattern bars */
.pattern-row {{
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.4rem 0;
}}
.pattern-name {{ width: 200px; font-size: 0.8rem; color: var(--muted); }}
.pattern-bar-bg {{
    flex: 1;
    height: 8px;
    background: var(--surface2);
    border-radius: 4px;
    overflow: hidden;
}}
.pattern-bar-fill {{
    height: 100%;
    background: linear-gradient(90deg, var(--accent), var(--blue));
    border-radius: 4px;
}}
.pattern-count {{ font-weight: 700; font-size: 0.8rem; width: 30px; text-align: right; }}

/* Probe cards */
.probe-card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    margin-bottom: 1.5rem;
    overflow: hidden;
    transition: border-color 0.2s;
}}
.probe-card:hover {{ border-color: var(--accent); }}
.probe-card-header {{
    padding: 1rem 1.25rem;
    background: var(--surface2);
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 0.5rem;
}}
.probe-card-header .probe-id {{
    font-weight: 700;
    font-size: 0.9rem;
}}
.probe-card-header .badges {{ display: flex; gap: 0.4rem; flex-wrap: wrap; }}
.probe-card-body {{ padding: 1.25rem; }}

.response-block {{
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1rem;
    margin: 0.75rem 0;
    font-size: 0.82rem;
    line-height: 1.7;
    white-space: pre-wrap;
    word-wrap: break-word;
    max-height: 300px;
    overflow-y: auto;
}}
.response-block.compact {{ max-height: 150px; }}

.stage-label {{
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--muted);
    margin-top: 1rem;
    margin-bottom: 0.25rem;
    font-weight: 600;
}}

.follow-up {{
    border-left: 3px solid var(--border);
    padding-left: 1rem;
    margin: 0.75rem 0;
}}
.follow-up .probe-q {{
    font-weight: 600;
    font-size: 0.82rem;
    color: var(--blue);
    margin-bottom: 0.25rem;
}}
.follow-up.shifted {{ border-left-color: var(--orange); }}
.shift-note {{
    font-size: 0.75rem;
    color: var(--orange);
    font-style: italic;
    margin-top: 0.25rem;
}}

.diff-compare {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
    margin-top: 0.5rem;
}}
.diff-col h4 {{
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--muted);
    margin-bottom: 0.5rem;
}}

/* Collapsible */
details {{ margin: 0.5rem 0; }}
summary {{
    cursor: pointer;
    font-size: 0.8rem;
    color: var(--accent);
    font-weight: 600;
    padding: 0.25rem 0;
    user-select: none;
}}
summary:hover {{ text-decoration: underline; }}

/* Responsive */
@media (max-width: 900px) {{
    .diff-compare {{ grid-template-columns: 1fr; }}
    .stats-grid {{ grid-template-columns: repeat(2, 1fr); }}
}}
@media (max-width: 600px) {{
    .container {{ padding: 1rem; }}
    .stats-grid {{ grid-template-columns: 1fr 1fr; }}
}}
</style>
</head>
<body>
<div class="container">

<div class="header">
    <h1>Reasoning Honesty Evaluation</h1>
    <div class="meta">
        <span>Model: <strong>{_esc(model)}</strong></span>
        <span>Date: <strong>{_esc(now)}</strong></span>
        <span>Probes: <strong>{total}</strong></span>
    </div>
</div>

<!-- Stats -->
<div class="stats-grid">
    <div class="stat-card stat-purple">
        <div class="stat-value">{total}</div>
        <div class="stat-label">Probes Run</div>
    </div>
    <div class="stat-card stat-red">
        <div class="stat-value">{deflections}</div>
        <div class="stat-label">Deflections</div>
    </div>
    <div class="stat-card stat-yellow">
        <div class="stat-value">{partials}</div>
        <div class="stat-label">Partial Assists</div>
    </div>
    <div class="stat-card stat-green">
        <div class="stat-value">{full_assists}</div>
        <div class="stat-label">Full Assists</div>
    </div>
    <div class="stat-card stat-orange">
        <div class="stat-value">{gaps}</div>
        <div class="stat-label">Capability Gaps</div>
    </div>
    <div class="stat-card stat-blue">
        <div class="stat-value">{verdict_counts.get('discriminatory', 0)}</div>
        <div class="stat-label">Discriminatory</div>
    </div>
</div>

<!-- Domain summary -->
<div class="section">
    <h2>Domain Summary</h2>
    <table>
        <thead>
            <tr>
                <th>Domain</th><th class="num">Probes</th><th class="num">Deflections</th>
                <th class="num">Partial</th><th class="num">Full Assist</th>
                <th class="num">Gaps</th><th class="num">Differential Verdicts</th>
            </tr>
        </thead>
        <tbody>{''.join(domain_rows)}</tbody>
    </table>
</div>

<!-- Pattern distribution -->
{f'''<div class="section">
    <h2>Deflection Pattern Distribution</h2>
    <div style="background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:1.25rem;">
        {pattern_items}
    </div>
</div>''' if pattern_items else ''}

<!-- Differential results -->
{f'''<div class="section">
    <h2>Differential Analysis (Audience-Dependent Reasoning)</h2>
    <table>
        <thead>
            <tr>
                <th>Probe</th><th>Domain</th><th class="num">Verdict</th>
                <th class="num">Behavioral Shift</th><th class="num">Framing Sensitivity</th>
                {"<th class='num'>Attribution</th>" if has_attribution else ""}
            </tr>
        </thead>
        <tbody>{''.join(diff_rows)}</tbody>
    </table>
</div>''' if diff_rows else ''}

<!-- Probe details -->
<div class="section">
    <h2>Probe Details</h2>
    {''.join(probe_cards)}
</div>

</div>
</body>
</html>"""


def _render_probe_card(r: dict) -> str:
    """Render a single probe card."""
    pid = r.get("probe_id", "unknown")
    domain = r.get("domain", "")
    s1 = r.get("stage1", {})
    classification = s1.get("classification", "N/A")
    patterns = s1.get("patterns", [])
    gap = r.get("capability_gap", {})
    diff = r.get("differential", {})

    badges_html = _classification_badge(classification)
    badges_html += f' <span class="domain-tag domain-{_esc(domain)}">{_esc(domain)}</span>'
    if gap.get("gap_confirmed"):
        badges_html += " " + _gap_badge(True)
    if diff.get("verdict"):
        badges_html += " " + _verdict_badge(diff["verdict"])
        if diff.get("attribution"):
            badges_html += " " + _attribution_badge(diff["attribution"])
    for p in patterns:
        badges_html += " " + _badge(p, "purple")

    # Stage 1
    stage1_html = ""
    if s1.get("prompt"):
        stage1_html += f'<div class="stage-label">Stage 1 — Oblique Entry Probe</div>'
        stage1_html += f'<div class="response-block compact"><strong>Q:</strong> {_esc(s1["prompt"])}</div>'
    if s1.get("response"):
        stage1_html += f'<div class="response-block">{_esc(s1["response"])}</div>'
    if s1.get("justification_language"):
        stage1_html += f'<div style="font-size:0.8rem;color:var(--orange);margin:0.25rem 0">Justification: &ldquo;{_esc(s1["justification_language"])}&rdquo;</div>'

    # Stage 3
    stage3_html = ""
    s3 = r.get("stage3", [])
    if s3:
        stage3_html += '<div class="stage-label">Stage 3 — Reasoning Audit</div>'
        for entry in s3:
            shifted = entry.get("justification_shifted", False)
            cls = "follow-up shifted" if shifted else "follow-up"
            stage3_html += f'<div class="{cls}">'
            stage3_html += f'<div class="probe-q">Q: {_esc(entry["probe"])}</div>'
            stage3_html += f'<div class="response-block compact">{_esc(entry.get("response", ""))}</div>'
            if shifted and entry.get("shift_description"):
                stage3_html += f'<div class="shift-note">SHIFT: {_esc(entry["shift_description"])}</div>'
            stage3_html += '</div>'

    # Capability gap
    gap_html = ""
    if gap.get("test_prompt"):
        confirmed = gap.get("gap_confirmed", False)
        gap_html += f'<div class="stage-label">Capability Gap Test {_gap_badge(confirmed)}</div>'
        gap_html += f'<div class="response-block compact"><strong>Q:</strong> {_esc(gap["test_prompt"])}</div>'
        if gap.get("response"):
            gap_html += f'<details><summary>Show gap test response</summary>'
            gap_html += f'<div class="response-block">{_esc(gap["response"])}</div></details>'

    # Differential
    diff_html = ""
    if diff.get("condition_a_response"):
        verdict = diff.get("verdict", "consistent")
        diff_html += f'<div class="stage-label">Differential Comparison {_verdict_badge(verdict)}</div>'

        # Verdict detail
        diff_html += '<div style="display:flex;gap:0.75rem;margin:0.5rem 0;flex-wrap:wrap">'
        diff_html += f'<div style="font-size:0.75rem;color:var(--muted)">Shift: <strong style="color:var(--text)">{_esc(diff.get("behavioral_shift", "none"))}</strong></div>'
        diff_html += f'<div style="font-size:0.75rem;color:var(--muted)">Sensitivity: <strong style="color:var(--text)">{diff.get("framing_sensitivity_label", "negligible")}({diff.get("framing_sensitivity", 0)}/6)</strong></div>'
        if "attribution" in diff:
            diff_html += f'<div style="font-size:0.75rem;color:var(--muted)">Attribution: {_attribution_badge(diff["attribution"])}</div>'
        diff_html += '</div>'

        has_c = diff.get("condition_c_response")
        cols = "1fr 1fr 1fr" if has_c else "1fr 1fr"
        diff_html += f'<div class="diff-compare" style="grid-template-columns:{cols}">'
        diff_html += f'<div class="diff-col"><h4>Condition A (neutral)</h4>'
        diff_html += f'<div class="response-block compact">{_esc(diff.get("condition_a_response", ""))}</div></div>'
        diff_html += f'<div class="diff-col"><h4>Condition B (credential)</h4>'
        diff_html += f'<div class="response-block compact">{_esc(diff.get("condition_b_response", ""))}</div></div>'
        if has_c:
            diff_html += f'<div class="diff-col"><h4>Condition C (technical, no credential)</h4>'
            diff_html += f'<div class="response-block compact">{_esc(diff.get("condition_c_response", ""))}</div></div>'
        diff_html += '</div>'

    return f"""
    <div class="probe-card">
        <div class="probe-card-header">
            <span class="probe-id">{_esc(pid)}</span>
            <div class="badges">{badges_html}</div>
        </div>
        <div class="probe-card-body">
            {stage1_html}
            {stage3_html}
            {gap_html}
            {diff_html}
        </div>
    </div>"""


def save_html_report(
    results: list[dict], model: str, reports_dir: str = "reports",
    run_label: str | None = None,
) -> str:
    """Save HTML report and return the file path."""
    base = Path(__file__).parent
    reports_path = base / reports_dir
    reports_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    label = f"_{run_label}" if run_label else ""
    html_file = reports_path / f"report{label}_{timestamp}.html"

    content = generate_html_report(results, model)
    with open(html_file, "w") as f:
        f.write(content)

    return str(html_file)
