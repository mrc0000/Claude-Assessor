#!/usr/bin/env python3
"""Cross-model comparison report generator.

Loads results from multiple models, computes per-model statistics using the
shared analysis engine, and generates a side-by-side comparison HTML report.

Designed for model-provider agnostic use — model labels are configurable and
the analysis pipeline treats model ID as an opaque string.

Usage:
    python cross_model_report.py                          # All models in results/
    python cross_model_report.py --models haiku sonnet-4  # Filter by label substring
    python cross_model_report.py --label v1.3.0           # Custom output label
"""

import argparse
import html as html_mod
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from comparative_analysis import (
    compute_domain_stats,
    compute_risk_tier_stats,
    compute_pattern_frequency,
    compute_verdict_map,
    compute_credential_sensitivity,
    compute_capability_gap_analysis,
    _mean,
)


# ──────────────────────────────────────────────
# Model registry — extend for new providers
# ──────────────────────────────────────────────

MODEL_LABELS: dict[str, str] = {
    "claude-haiku-4-5-20251001": "Haiku 4.5",
    "claude-sonnet-4-20250514": "Sonnet 4",
    "claude-sonnet-4-6": "Sonnet 4.6",
}


def get_model_label(model_id: str) -> str:
    """Get display label for a model ID. Falls back to the raw ID."""
    return MODEL_LABELS.get(model_id, model_id)


def register_model(model_id: str, label: str) -> None:
    """Register a new model ID → label mapping at runtime."""
    MODEL_LABELS[model_id] = label


# ──────────────────────────────────────────────
# Result loading and grouping
# ──────────────────────────────────────────────

def load_and_group_results(
    results_dir: str = "results",
    model_filter: list[str] | None = None,
) -> dict[str, list[dict]]:
    """Load all result files and group probe results by model ID.

    Args:
        results_dir: Directory containing run_*.json files.
        model_filter: Optional list of substrings to filter models by
            (matched against both model ID and display label).

    Returns:
        Dict mapping model_id → list of probe result dicts.
    """
    base = Path(__file__).parent / results_dir
    model_results: dict[str, list[dict]] = defaultdict(list)

    for f in sorted(base.glob("run_*.json")):
        with open(f) as fp:
            data = json.load(fp)

        model_id = data.get("meta", {}).get("model", "unknown")
        label = get_model_label(model_id)

        # Apply filter
        if model_filter:
            matches = any(
                filt.lower() in model_id.lower() or filt.lower() in label.lower()
                for filt in model_filter
            )
            if not matches:
                continue

        for pr in data.get("probe_results", []):
            pr["_source_file"] = f.name
            pr["_meta"] = data.get("meta", {})
            model_results[model_id].append(pr)

    return dict(model_results)


# ──────────────────────────────────────────────
# Cross-model analysis
# ──────────────────────────────────────────────

def compute_model_summary(results: list[dict]) -> dict[str, Any]:
    """Compute headline metrics for a single model's results."""
    total = len(results)
    if total == 0:
        return {"total_probes": 0}

    deflections = sum(
        1 for r in results
        if r.get("stage1", {}).get("classification") == "deflection"
    )
    full_assists = sum(
        1 for r in results
        if r.get("stage1", {}).get("classification") == "full_assist"
    )
    partial_assists = sum(
        1 for r in results
        if r.get("stage1", {}).get("classification") == "partial_assist"
    )
    gaps = sum(
        1 for r in results
        if r.get("capability_gap", {}).get("gap_confirmed")
    )

    # Verdict distribution
    verdict_counts: dict[str, int] = defaultdict(int)
    for r in results:
        v = r.get("differential", {}).get("verdict")
        if v:
            verdict_counts[v] += 1
    total_verdicts = sum(verdict_counts.values())

    concern_ratios = [
        r.get("stage1", {}).get("concern_ratio", 0)
        for r in results
        if r.get("stage1", {}).get("concern_ratio") is not None
    ]

    return {
        "total_probes": total,
        "deflections": deflections,
        "full_assists": full_assists,
        "partial_assists": partial_assists,
        "deflection_rate": round(deflections / total * 100, 1) if total else 0,
        "full_assist_rate": round(full_assists / total * 100, 1) if total else 0,
        "capability_gaps": gaps,
        "avg_concern_ratio": round(_mean(concern_ratios), 3),
        "verdict_distribution": dict(verdict_counts),
        "discriminatory_rate": round(
            verdict_counts.get("discriminatory", 0) / total_verdicts * 100, 1
        ) if total_verdicts else 0,
        "tone_modulated_rate": round(
            sum(c for v, c in verdict_counts.items() if v.startswith("tone_modulated")) / total_verdicts * 100, 1
        ) if total_verdicts else 0,
        "consistent_rate": round(
            verdict_counts.get("consistent", 0) / total_verdicts * 100, 1
        ) if total_verdicts else 0,
    }


def compute_cross_model_analysis(
    model_results: dict[str, list[dict]],
) -> dict[str, Any]:
    """Compute the full cross-model comparison data structure.

    Returns a dict with per-model summaries, domain stats, risk tier stats,
    and cross-model comparison tables.
    """
    models = {}

    for model_id, results in model_results.items():
        models[model_id] = {
            "label": get_model_label(model_id),
            "summary": compute_model_summary(results),
            "domain_stats": compute_domain_stats(results),
            "risk_tier_stats": compute_risk_tier_stats(results),
            "pattern_frequency": compute_pattern_frequency(results),
            "credential_sensitivity": compute_credential_sensitivity(results),
            "capability_gap_analysis": compute_capability_gap_analysis(results),
        }

    # Build cross-model domain comparison matrix
    all_domains: set[str] = set()
    for m in models.values():
        all_domains.update(m["domain_stats"].keys())

    domain_comparison = {}
    for domain in sorted(all_domains):
        domain_comparison[domain] = {}
        for model_id, m in models.items():
            ds = m["domain_stats"].get(domain, {})
            domain_comparison[domain][model_id] = {
                "label": m["label"],
                "probes": ds.get("probes", 0),
                "deflection_rate": ds.get("deflection_rate", 0),
                "full_assist_rate": ds.get("full_assist_rate", 0),
                "discriminatory_rate": ds.get("discriminatory_rate", 0),
                "tone_modulated_rate": ds.get("tone_modulated_rate", 0),
                "gap_rate": ds.get("gap_rate", 0),
                "avg_concern_ratio": ds.get("avg_concern_ratio", 0),
            }

    return {
        "models": models,
        "domain_comparison": domain_comparison,
        "model_order": sorted(
            model_results.keys(),
            key=lambda m: get_model_label(m),
        ),
    }


# ──────────────────────────────────────────────
# HTML report generation
# ──────────────────────────────────────────────

def _esc(text) -> str:
    return html_mod.escape(str(text))


def _pct_bar(value: float, color: str = "#7c3aed", width: int = 80) -> str:
    pct = min(value / 100 * 100, 100) if value else 0
    return (
        f'<div class="pct-bar" style="width:{width}px">'
        f'<div class="pct-fill" style="width:{pct}%;background:{color}"></div>'
        f'<span class="pct-label">{value:.1f}%</span>'
        f'</div>'
    )


def _domain_color(domain: str) -> str:
    colors = {
        "copyright": "#a855f7", "legal": "#3b82f6", "financial": "#eab308",
        "medical": "#ef4444", "cybersecurity": "#22c55e", "chemistry": "#f97316",
        "reasoning": "#06b6d4",
    }
    return colors.get(domain, "#6b7280")


def _trend_arrow(values: list[float]) -> str:
    """Show trend arrow based on first→last value change."""
    if len(values) < 2:
        return ""
    diff = values[-1] - values[0]
    if abs(diff) < 0.5:
        return '<span class="trend-flat">~</span>'
    if diff > 0:
        return '<span class="trend-up">+</span>'
    return '<span class="trend-down">-</span>'


def _delta_cell(values: list[float], fmt: str = ".1f") -> str:
    """Show the change from first to last value."""
    if len(values) < 2:
        return ""
    diff = values[-1] - values[0]
    sign = "+" if diff > 0 else ""
    color = "#ef4444" if diff > 0 else "#22c55e" if diff < 0 else "var(--muted)"
    return f'<span style="color:{color};font-size:0.7rem">{sign}{diff:{fmt}}</span>'


def generate_cross_model_html(analysis: dict) -> str:
    """Generate the full cross-model comparison HTML report."""
    models = analysis["models"]
    model_order = analysis["model_order"]
    domain_comparison = analysis["domain_comparison"]
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    model_labels = [models[m]["label"] for m in model_order]

    # ── Headline comparison ──
    headline_headers = "".join(
        f'<th class="num model-col">{_esc(models[m]["label"])}</th>'
        for m in model_order
    )
    headline_headers += '<th class="num">Trend</th>'

    def _headline_row(label: str, key: str, fmt: str = ".1f", suffix: str = "%",
                      high_is_bad: bool = True) -> str:
        values = [models[m]["summary"].get(key, 0) for m in model_order]
        cells = ""
        for v in values:
            cells += f'<td class="num">{v:{fmt}}{suffix}</td>'
        cells += f'<td class="num">{_trend_arrow(values)} {_delta_cell(values, fmt)}</td>'
        return f"<tr><td>{_esc(label)}</td>{cells}</tr>"

    def _headline_row_int(label: str, key: str) -> str:
        values = [models[m]["summary"].get(key, 0) for m in model_order]
        cells = ""
        for v in values:
            cells += f'<td class="num">{v}</td>'
        cells += f'<td class="num">{_trend_arrow([float(x) for x in values])}</td>'
        return f"<tr><td>{_esc(label)}</td>{cells}</tr>"

    headline_rows = (
        _headline_row("Deflection Rate", "deflection_rate")
        + _headline_row("Full Assist Rate", "full_assist_rate", high_is_bad=False)
        + _headline_row("Discriminatory", "discriminatory_rate")
        + _headline_row("Tone Modulated", "tone_modulated_rate")
        + _headline_row("Consistent", "consistent_rate", high_is_bad=False)
        + _headline_row_int("Capability Gaps", "capability_gaps")
        + _headline_row("Avg Concern Ratio", "avg_concern_ratio", fmt=".3f", suffix="")
    )

    # ── Per-model stat cards ──
    model_cards = ""
    for mid in model_order:
        s = models[mid]["summary"]
        label = models[mid]["label"]
        vd = s.get("verdict_distribution", {})
        model_cards += f"""
        <div class="model-card">
            <h3>{_esc(label)}</h3>
            <div class="model-id">{_esc(mid)}</div>
            <div class="mini-stats">
                <div class="mini-stat"><span class="mini-val">{s['total_probes']}</span><span class="mini-lbl">Probes</span></div>
                <div class="mini-stat"><span class="mini-val" style="color:var(--red)">{s['deflection_rate']}%</span><span class="mini-lbl">Deflection</span></div>
                <div class="mini-stat"><span class="mini-val" style="color:var(--green)">{s['full_assist_rate']}%</span><span class="mini-lbl">Full Assist</span></div>
                <div class="mini-stat"><span class="mini-val" style="color:var(--orange)">{s['discriminatory_rate']}%</span><span class="mini-lbl">Discriminatory</span></div>
                <div class="mini-stat"><span class="mini-val">{s['capability_gaps']}</span><span class="mini-lbl">Cap. Gaps</span></div>
            </div>
            <div class="verdict-bar">
                <div class="vb-seg" style="width:{vd.get('discriminatory', 0) / max(sum(vd.values()), 1) * 100}%;background:var(--red)" title="Discriminatory: {vd.get('discriminatory', 0)}"></div>
                <div class="vb-seg" style="width:{vd.get('tone_modulated_high', 0) / max(sum(vd.values()), 1) * 100}%;background:#b45309" title="Tone Mod High: {vd.get('tone_modulated_high', 0)}"></div>
                <div class="vb-seg" style="width:{vd.get('tone_modulated_moderate', 0) / max(sum(vd.values()), 1) * 100}%;background:var(--orange)" title="Tone Mod Moderate: {vd.get('tone_modulated_moderate', 0)}"></div>
                <div class="vb-seg" style="width:{vd.get('tone_modulated_low', 0) / max(sum(vd.values()), 1) * 100}%;background:#fde68a" title="Tone Mod Low: {vd.get('tone_modulated_low', 0)}"></div>
                <div class="vb-seg" style="width:{vd.get('consistent', 0) / max(sum(vd.values()), 1) * 100}%;background:var(--green)" title="Consistent: {vd.get('consistent', 0)}"></div>
            </div>
        </div>"""

    # ── Domain comparison table ──
    domain_headers = "".join(
        f'<th class="num" colspan="3">{_esc(models[m]["label"])}</th>'
        for m in model_order
    )
    domain_sub_headers = "".join(
        '<th class="num sub">Defl%</th><th class="num sub">Full%</th><th class="num sub">Disc%</th>'
        for _ in model_order
    )

    domain_rows = ""
    for domain in sorted(domain_comparison.keys()):
        dc = _domain_color(domain)
        cells = ""
        for mid in model_order:
            d = domain_comparison[domain].get(mid, {})
            defl = d.get("deflection_rate", 0)
            full = d.get("full_assist_rate", 0)
            disc = d.get("discriminatory_rate", 0)
            cells += f'<td class="num">{_pct_bar(defl, "#ef4444", 60)}</td>'
            cells += f'<td class="num">{_pct_bar(full, "#22c55e", 60)}</td>'
            cells += f'<td class="num">{_pct_bar(disc, "#f97316", 60)}</td>'
        domain_rows += f"""
        <tr>
            <td><span class="domain-tag" style="color:{dc};border-color:{dc}">{_esc(domain)}</span></td>
            {cells}
        </tr>"""

    # ── Capability gap comparison ──
    gap_rows = ""
    all_gap_domains: set[str] = set()
    for mid in model_order:
        all_gap_domains.update(models[mid]["capability_gap_analysis"].keys())

    for domain in sorted(all_gap_domains):
        dc = _domain_color(domain)
        cells = ""
        for mid in model_order:
            ga = models[mid]["capability_gap_analysis"].get(domain, {})
            gaps = ga.get("gaps_confirmed", 0)
            tested = ga.get("total_tested", 0)
            rate = ga.get("gap_rate", 0)
            cells += f'<td class="num">{gaps}/{tested}</td>'
            cells += f'<td class="num">{_pct_bar(rate, "#ef4444", 60)}</td>'
        gap_rows += f"""
        <tr>
            <td><span class="domain-tag" style="color:{dc};border-color:{dc}">{_esc(domain)}</span></td>
            {cells}
        </tr>"""

    gap_headers = "".join(
        f'<th class="num" colspan="2">{_esc(models[m]["label"])}</th>'
        for m in model_order
    )
    gap_sub_headers = "".join(
        '<th class="num sub">Gaps</th><th class="num sub">Rate</th>'
        for _ in model_order
    )

    # ── Credential sensitivity comparison ──
    cred_rows = ""
    all_cred_domains: set[str] = set()
    for mid in model_order:
        all_cred_domains.update(models[mid]["credential_sensitivity"].keys())

    for domain in sorted(all_cred_domains):
        dc = _domain_color(domain)
        cells = ""
        for mid in model_order:
            cs = models[mid]["credential_sensitivity"].get(domain, {})
            disc = cs.get("discriminatory_rate", 0)
            tone = cs.get("tone_modulated_rate", 0)
            cells += f'<td class="num">{_pct_bar(disc, "#ef4444", 60)}</td>'
            cells += f'<td class="num">{_pct_bar(tone, "#f97316", 60)}</td>'
        cred_rows += f"""
        <tr>
            <td><span class="domain-tag" style="color:{dc};border-color:{dc}">{_esc(domain)}</span></td>
            {cells}
        </tr>"""

    cred_headers = "".join(
        f'<th class="num" colspan="2">{_esc(models[m]["label"])}</th>'
        for m in model_order
    )
    cred_sub_headers = "".join(
        '<th class="num sub">Disc%</th><th class="num sub">Tone%</th>'
        for _ in model_order
    )

    # ── Pattern frequency comparison ──
    all_patterns: set[str] = set()
    for mid in model_order:
        all_patterns.update(models[mid]["pattern_frequency"].keys())

    pattern_rows = ""
    for pattern in sorted(all_patterns):
        cells = ""
        for mid in model_order:
            count = models[mid]["pattern_frequency"].get(pattern, 0)
            cells += f'<td class="num">{count}</td>'
        pattern_rows += f"<tr><td><code>{_esc(pattern)}</code></td>{cells}</tr>"

    pattern_headers = "".join(
        f'<th class="num">{_esc(models[m]["label"])}</th>'
        for m in model_order
    )

    # ── Assemble HTML ──
    n_models = len(model_order)
    total_probes = sum(models[m]["summary"]["total_probes"] for m in model_order)

    return _build_html(
        now=now,
        n_models=n_models,
        total_probes=total_probes,
        model_labels=", ".join(model_labels),
        model_cards=model_cards,
        headline_headers=headline_headers,
        headline_rows=headline_rows,
        domain_headers=domain_headers,
        domain_sub_headers=domain_sub_headers,
        domain_rows=domain_rows,
        gap_headers=gap_headers,
        gap_sub_headers=gap_sub_headers,
        gap_rows=gap_rows,
        cred_headers=cred_headers,
        cred_sub_headers=cred_sub_headers,
        cred_rows=cred_rows,
        pattern_headers=pattern_headers,
        pattern_rows=pattern_rows,
    )


def _build_html(**ctx) -> str:
    """Assemble the full HTML document."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Cross-Model Comparison — Reasoning Honesty Evaluation</title>
<style>
:root {{
    --bg: #0a0c10; --surface: #13161d; --surface2: #1c2029; --surface3: #252a35;
    --border: #2a2f3d; --text: #e2e8f0; --muted: #8892b0;
    --accent: #7c3aed; --red: #ef4444; --green: #22c55e;
    --yellow: #eab308; --blue: #3b82f6; --orange: #f97316; --cyan: #06b6d4;
}}
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{
    font-family: 'SF Mono','Cascadia Code','Fira Code','JetBrains Mono',monospace;
    background: var(--bg); color: var(--text); line-height:1.6; font-size:13px;
}}
.container {{ max-width:1600px; margin:0 auto; padding:2rem; }}

/* Header */
.header {{
    text-align:center; padding:3rem 0 2rem;
    border-bottom:1px solid var(--border); margin-bottom:2.5rem;
}}
.header h1 {{
    font-size:2rem; font-weight:800; letter-spacing:-0.03em;
    background: linear-gradient(135deg, #ef4444, #f97316, #eab308, #22c55e, #3b82f6, #7c3aed);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
    margin-bottom:0.75rem;
}}
.header .subtitle {{ color:var(--muted); font-size:1rem; margin-bottom:0.5rem; }}
.header .meta {{ color:var(--muted); font-size:0.8rem; }}
.header .meta span {{ margin:0 0.75rem; }}

/* Nav */
.nav {{
    position:sticky; top:0; z-index:100; background:rgba(10,12,16,0.95);
    backdrop-filter:blur(10px); border-bottom:1px solid var(--border);
    padding:0.5rem 2rem; display:flex; gap:1rem; overflow-x:auto;
}}
.nav a {{
    color:var(--muted); text-decoration:none; font-size:0.75rem;
    font-weight:600; text-transform:uppercase; letter-spacing:0.04em;
    padding:0.4rem 0; border-bottom:2px solid transparent; white-space:nowrap;
}}
.nav a:hover {{ color:var(--text); border-bottom-color:var(--accent); }}

/* Sections */
.section {{ margin-bottom:3rem; }}
.section h2 {{
    font-size:1.15rem; font-weight:700; margin-bottom:1.25rem; color:var(--text);
    display:flex; align-items:center; gap:0.5rem;
}}
.section h2::before {{
    content:''; display:inline-block; width:4px; height:1.2rem;
    background:var(--accent); border-radius:2px;
}}

/* Model cards */
.model-grid {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(280px, 1fr)); gap:1rem; margin-bottom:2rem; }}
.model-card {{
    background:var(--surface); border:1px solid var(--border); border-radius:10px;
    padding:1.25rem; transition:border-color 0.2s;
}}
.model-card:hover {{ border-color:var(--accent); }}
.model-card h3 {{ font-size:1.1rem; font-weight:700; margin-bottom:0.15rem; }}
.model-id {{ font-size:0.7rem; color:var(--muted); margin-bottom:0.75rem; font-family:monospace; }}
.mini-stats {{ display:flex; gap:0.75rem; flex-wrap:wrap; margin-bottom:0.75rem; }}
.mini-stat {{ text-align:center; }}
.mini-val {{ display:block; font-size:1.1rem; font-weight:700; line-height:1.2; }}
.mini-lbl {{ font-size:0.6rem; color:var(--muted); text-transform:uppercase; letter-spacing:0.04em; }}
.verdict-bar {{ display:flex; height:6px; border-radius:3px; overflow:hidden; background:var(--surface3); }}
.vb-seg {{ height:100%; }}

/* Tables */
table {{
    width:100%; border-collapse:collapse; background:var(--surface);
    border-radius:10px; overflow:hidden; border:1px solid var(--border);
    font-size:0.82rem;
}}
th {{
    background:var(--surface2); padding:0.6rem 0.75rem; text-align:left;
    font-weight:600; font-size:0.7rem; text-transform:uppercase;
    letter-spacing:0.05em; color:var(--muted); border-bottom:1px solid var(--border);
}}
th.sub {{
    font-size:0.6rem; padding:0.3rem 0.75rem; background:var(--surface3);
}}
th.model-col {{ min-width:100px; }}
td {{ padding:0.6rem 0.75rem; border-bottom:1px solid var(--border); vertical-align:middle; }}
tr:last-child td {{ border-bottom:none; }}
tr:hover {{ background:var(--surface2); }}
.num {{ text-align:center; }}

/* Domain/risk tags */
.domain-tag {{
    display:inline-block; padding:0.15rem 0.5rem; border-radius:6px;
    font-size:0.7rem; font-weight:700; text-transform:capitalize;
    border:1px solid; background:rgba(255,255,255,0.03);
}}

/* Bars */
.pct-bar {{
    position:relative; height:18px; background:var(--surface3);
    border-radius:4px; overflow:hidden; display:inline-block;
}}
.pct-fill {{ height:100%; border-radius:4px; }}
.pct-label {{
    position:absolute; top:50%; left:50%; transform:translate(-50%,-50%);
    font-size:0.6rem; font-weight:700; color:white;
    text-shadow:0 1px 2px rgba(0,0,0,0.6);
}}

/* Trends */
.trend-up {{ color:var(--red); font-weight:700; }}
.trend-down {{ color:var(--green); font-weight:700; }}
.trend-flat {{ color:var(--muted); }}

/* Responsive */
@media (max-width:900px) {{
    .model-grid {{ grid-template-columns:1fr; }}
    .container {{ padding:1rem; }}
}}
</style>
</head>
<body>

<nav class="nav">
    <a href="#overview">Overview</a>
    <a href="#headline">Headline</a>
    <a href="#domains">Domains</a>
    <a href="#gaps">Capability Gaps</a>
    <a href="#credentials">Credentials</a>
    <a href="#patterns">Patterns</a>
</nav>

<div class="container">

<div class="header">
    <h1>Cross-Model Comparison</h1>
    <div class="subtitle">Reasoning Honesty Evaluation</div>
    <div class="meta">
        <span>Models: <strong>{_esc(ctx['model_labels'])}</strong></span>
        <span>Date: <strong>{_esc(ctx['now'])}</strong></span>
        <span>Total Probes: <strong>{ctx['total_probes']}</strong></span>
    </div>
</div>

<!-- Model Overview Cards -->
<div class="section" id="overview">
    <h2>Model Overview</h2>
    <div class="model-grid">
        {ctx['model_cards']}
    </div>
</div>

<!-- Headline Comparison -->
<div class="section" id="headline">
    <h2>Headline Metrics Comparison</h2>
    <table>
        <thead><tr>
            <th>Metric</th>
            {ctx['headline_headers']}
        </tr></thead>
        <tbody>{ctx['headline_rows']}</tbody>
    </table>
</div>

<!-- Domain Comparison -->
<div class="section" id="domains">
    <h2>Cross-Domain Comparison</h2>
    <table>
        <thead>
            <tr><th rowspan="2">Domain</th>{ctx['domain_headers']}</tr>
            <tr>{ctx['domain_sub_headers']}</tr>
        </thead>
        <tbody>{ctx['domain_rows']}</tbody>
    </table>
</div>

<!-- Capability Gap Comparison -->
<div class="section" id="gaps">
    <h2>Capability Gap Comparison</h2>
    <table>
        <thead>
            <tr><th rowspan="2">Domain</th>{ctx['gap_headers']}</tr>
            <tr>{ctx['gap_sub_headers']}</tr>
        </thead>
        <tbody>{ctx['gap_rows']}</tbody>
    </table>
</div>

<!-- Credential Sensitivity Comparison -->
<div class="section" id="credentials">
    <h2>Credential Sensitivity Comparison</h2>
    <table>
        <thead>
            <tr><th rowspan="2">Domain</th>{ctx['cred_headers']}</tr>
            <tr>{ctx['cred_sub_headers']}</tr>
        </thead>
        <tbody>{ctx['cred_rows']}</tbody>
    </table>
</div>

<!-- Pattern Frequency Comparison -->
<div class="section" id="patterns">
    <h2>Deflection Pattern Frequency</h2>
    <table>
        <thead><tr>
            <th>Pattern</th>
            {ctx['pattern_headers']}
        </tr></thead>
        <tbody>{ctx['pattern_rows']}</tbody>
    </table>
</div>

<div style="text-align:center;padding:2rem 0;color:var(--muted);font-size:0.75rem;border-top:1px solid var(--border);margin-top:2rem;">
    Generated by Claude-Assessor Cross-Model Comparison Engine
</div>

</div>
</body>
</html>"""


# ──────────────────────────────────────────────
# Save / CLI
# ──────────────────────────────────────────────

def save_cross_model_report(
    model_results: dict[str, list[dict]],
    reports_dir: str = "reports/cross-model",
    label: str | None = None,
) -> dict[str, str]:
    """Generate and save the cross-model comparison report.

    Returns dict with paths to generated files.
    """
    base = Path(__file__).parent / reports_dir
    base.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    lbl = f"_{label}" if label else ""

    # Compute analysis
    analysis = compute_cross_model_analysis(model_results)

    # Save HTML
    html_file = base / f"cross_model{lbl}_{timestamp}.html"
    html_content = generate_cross_model_html(analysis)
    with open(html_file, "w") as f:
        f.write(html_content)

    # Save JSON
    json_file = base / f"cross_model{lbl}_{timestamp}.json"
    with open(json_file, "w") as f:
        json.dump(analysis, f, indent=2, default=str)

    return {"html_file": str(html_file), "json_file": str(json_file)}


def main():
    parser = argparse.ArgumentParser(
        description="Generate cross-model comparison report",
    )
    parser.add_argument(
        "--models", nargs="+",
        help="Filter by model label substrings (e.g. 'haiku' 'sonnet')",
    )
    parser.add_argument(
        "--results-dir", default="results",
        help="Results directory (default: results/)",
    )
    parser.add_argument(
        "--label", default=None,
        help="Label for output files",
    )
    args = parser.parse_args()

    print("Loading results...")
    model_results = load_and_group_results(
        results_dir=args.results_dir,
        model_filter=args.models,
    )

    if not model_results:
        print("No results found.")
        return

    for mid, results in sorted(model_results.items()):
        label = get_model_label(mid)
        print(f"  {label} ({mid}): {len(results)} probe results")

    print(f"\nGenerating cross-model comparison...")
    paths = save_cross_model_report(
        model_results,
        label=args.label,
    )

    print(f"\nReports saved:")
    print(f"  HTML: {paths['html_file']}")
    print(f"  JSON: {paths['json_file']}")


if __name__ == "__main__":
    main()
