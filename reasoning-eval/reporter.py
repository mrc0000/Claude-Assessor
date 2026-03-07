"""Reporter: generates structured evaluation reports from analyzed probe results."""

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


def _domain_summary(results: list[dict]) -> list[dict]:
    """Aggregate results by domain."""
    domains = defaultdict(lambda: {
        "probes": 0,
        "deflections": 0,
        "partial_assists": 0,
        "full_assists": 0,
        "gaps_confirmed": 0,
        "verdicts": defaultdict(int),
    })

    for r in results:
        domain = r.get("domain", "unknown")
        d = domains[domain]
        d["probes"] += 1

        classification = r.get("stage1", {}).get("classification", "")
        if classification == "deflection":
            d["deflections"] += 1
        elif classification == "partial_assist":
            d["partial_assists"] += 1
        elif classification == "full_assist":
            d["full_assists"] += 1

        if r.get("capability_gap", {}).get("gap_confirmed"):
            d["gaps_confirmed"] += 1

        diff = r.get("differential", {})
        if "verdict" in diff:
            d["verdicts"][diff["verdict"]] += 1

    summary = []
    for domain, d in sorted(domains.items()):
        summary.append({
            "domain": domain,
            "probes": d["probes"],
            "deflections": d["deflections"],
            "partial_assists": d["partial_assists"],
            "full_assists": d["full_assists"],
            "gaps_confirmed": d["gaps_confirmed"],
            "verdicts": dict(d["verdicts"]),
        })
    return summary


def _key_findings(results: list[dict]) -> list[str]:
    """Extract key findings from analyzed results."""
    findings = []

    total = len(results)
    deflections = sum(
        1 for r in results
        if r.get("stage1", {}).get("classification") == "deflection"
    )
    partial = sum(
        1 for r in results
        if r.get("stage1", {}).get("classification") == "partial_assist"
    )
    gaps = sum(
        1 for r in results
        if r.get("capability_gap", {}).get("gap_confirmed")
    )
    verdict_counts = defaultdict(int)
    for r in results:
        v = r.get("differential", {}).get("verdict")
        if v:
            verdict_counts[v] += 1

    if deflections:
        findings.append(
            f"{deflections}/{total} probes triggered deflection responses."
        )
    if partial:
        findings.append(
            f"{partial}/{total} probes received partial assistance with caveats."
        )
    if gaps:
        findings.append(
            f"{gaps}/{total} probes showed confirmed capability gaps "
            f"(model demonstrated knowledge it previously claimed to lack)."
        )
    discrim = verdict_counts.get("discriminatory", 0)
    tone_mod = sum(c for v, c in verdict_counts.items() if v.startswith("tone_modulated"))
    if discrim:
        findings.append(
            f"{discrim}/{total} probes showed discriminatory behavior "
            f"(model changed refusal/assist based on framing)."
        )
    if tone_mod:
        # Break down by grade
        low = verdict_counts.get("tone_modulated_low", 0)
        moderate = verdict_counts.get("tone_modulated_moderate", 0)
        high = verdict_counts.get("tone_modulated_high", 0)
        grade_parts = []
        if low:
            grade_parts.append(f"{low} low")
        if moderate:
            grade_parts.append(f"{moderate} moderate")
        if high:
            grade_parts.append(f"{high} high")
        grade_str = f" ({', '.join(grade_parts)})" if grade_parts else ""
        findings.append(
            f"{tone_mod}/{total} probes showed tone modulation{grade_str} "
            f"(same answer but different hedging/depth based on framing)."
        )
    if not deflections and not partial:
        findings.append(
            "No deflection or partial-assist patterns detected across any probes."
        )

    # Pattern frequency
    pattern_counts = defaultdict(int)
    for r in results:
        for p in r.get("stage1", {}).get("patterns", []):
            pattern_counts[p] += 1
    if pattern_counts:
        top = sorted(pattern_counts.items(), key=lambda x: -x[1])
        findings.append(
            "Most frequent deflection patterns: "
            + ", ".join(f"{p} ({c}x)" for p, c in top[:3])
            + "."
        )

    # Justification shifts
    shifts = 0
    for r in results:
        for s3 in r.get("stage3", []):
            if s3.get("justification_shifted"):
                shifts += 1
    if shifts:
        findings.append(
            f"{shifts} justification shifts detected across stage 3 follow-up probes."
        )

    return findings


def _differential_table(results: list[dict]) -> list[dict]:
    """Build differential results for reporting."""
    rows = []
    for r in results:
        diff = r.get("differential", {})
        if "verdict" not in diff:
            continue
        detail = diff.get("detail", {})
        row = {
            "probe_id": r.get("probe_id", ""),
            "domain": r.get("domain", ""),
            "verdict": diff["verdict"],
            "behavioral_shift": diff.get("behavioral_shift", "none"),
            "framing_sensitivity": diff.get("framing_sensitivity", 0),
            "framing_sensitivity_label": diff.get("framing_sensitivity_label", "negligible"),
            "constraint_diff": detail.get("constraint_diff", 0),
            "justification_diff": detail.get("justification_diff", 0),
            "scope_diff": detail.get("scope_diff", 0),
            "calibration_diff": detail.get("calibration_diff", 0),
            "keyword_overlap": detail.get("keyword_overlap"),
            "length_ratio": detail.get("length_ratio"),
            "scope_length_score": detail.get("scope_length_score"),
            "scope_content_score": detail.get("scope_content_score"),
        }
        if "attribution" in diff:
            row["attribution"] = diff["attribution"]
        rows.append(row)
    return rows


def generate_json_report(results: list[dict], model: str) -> dict:
    """Generate the full JSON report structure."""
    from analyzer import get_eval_config_snapshot

    return {
        "meta": {
            "model": model,
            "date": datetime.now(timezone.utc).isoformat(),
            "probes_run": len(results),
            "eval_config": get_eval_config_snapshot(),
        },
        "domain_summary": _domain_summary(results),
        "key_findings": _key_findings(results),
        "differential_results": _differential_table(results),
        "probe_results": results,
    }


def generate_markdown_report(results: list[dict], model: str) -> str:
    """Generate a markdown evaluation report."""
    lines = []
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    from analyzer import get_eval_config_snapshot
    cfg = get_eval_config_snapshot()

    lines.append("# Reasoning Honesty Evaluation Report")
    lines.append(f"Model: {model}")
    lines.append(f"Date: {now}")
    lines.append(f"Probes run: {len(results)}")
    lines.append(f"Eval config: v{cfg['config_version']} (patterns v{cfg['patterns_version']}, prompts v{cfg['prompt_templates_version']}, probes v{cfg['probe_set_version']})")
    lines.append("")

    # Domain summary table
    summary = _domain_summary(results)
    lines.append("## Domain Summary")
    lines.append(
        "| Domain | Probes | Deflections | Partial | Full Assist | Gaps | Verdicts |"
    )
    lines.append(
        "|--------|--------|-------------|---------|-------------|------|----------|"
    )
    for s in summary:
        vd = s.get("verdicts", {})
        verdict_str = ", ".join(f"{v}: {c}" for v, c in sorted(vd.items())) if vd else "—"
        lines.append(
            f"| {s['domain']} | {s['probes']} | {s['deflections']} | "
            f"{s['partial_assists']} | {s['full_assists']} | "
            f"{s['gaps_confirmed']} | {verdict_str} |"
        )
    lines.append("")

    # Key findings
    findings = _key_findings(results)
    lines.append("## Key Findings")
    for f in findings:
        lines.append(f"- {f}")
    lines.append("")

    # Differential results table
    diff_rows = _differential_table(results)
    if diff_rows:
        has_attribution = any("attribution" in row for row in diff_rows)
        lines.append("## Differential Results")
        if has_attribution:
            lines.append(
                "| Probe | Domain | Verdict | Shift | Sensitivity | Attribution |"
            )
            lines.append(
                "|-------|--------|---------|-------|-------------|-------------|"
            )
            for row in diff_rows:
                attr = row.get("attribution", "—")
                lines.append(
                    f"| {row['probe_id']} | {row['domain']} | "
                    f"{row['verdict']} | {row['behavioral_shift']} | "
                    f"{row['framing_sensitivity_label']}({row['framing_sensitivity']}/6) | {attr} |"
                )
        else:
            lines.append(
                "| Probe | Domain | Verdict | Shift | Sensitivity |"
            )
            lines.append(
                "|-------|--------|---------|-------|-------------|"
            )
            for row in diff_rows:
                lines.append(
                    f"| {row['probe_id']} | {row['domain']} | "
                    f"{row['verdict']} | {row['behavioral_shift']} | "
                    f"{row['framing_sensitivity_label']}({row['framing_sensitivity']}/6) |"
                )
        lines.append("")

    # Per-probe detail
    lines.append("## Per-Probe Details")
    lines.append("")
    for r in results:
        pid = r.get("probe_id", "unknown")
        lines.append(f"### {pid}")
        lines.append(f"**Domain:** {r.get('domain', '')}  ")
        lines.append(f"**Risk Tier:** {r.get('risk_tier', '')}  ")

        s1 = r.get("stage1", {})
        lines.append(f"**Stage 1 Classification:** {s1.get('classification', 'N/A')}  ")
        if s1.get("patterns"):
            lines.append(f"**Patterns:** {', '.join(s1['patterns'])}  ")
        if s1.get("justification_language"):
            lines.append(
                f"**Justification:** \"{s1['justification_language']}\"  "
            )
        lines.append("")

        # Stage 1 prompt/response
        lines.append("**Prompt:**")
        lines.append(f"> {s1.get('prompt', '')}")
        lines.append("")
        lines.append("**Response (truncated):**")
        resp = s1.get("response", "")
        truncated = resp[:500] + "..." if len(resp) > 500 else resp
        lines.append(f"> {truncated}")
        lines.append("")

        # Capability gap
        gap = r.get("capability_gap", {})
        if gap:
            lines.append(
                f"**Capability Gap:** "
                f"{'CONFIRMED' if gap.get('gap_confirmed') else 'Not confirmed'}  "
            )
            if gap.get("gap_confirmed"):
                lines.append(
                    f"  - Demonstrates knowledge on gap test: "
                    f"{gap.get('demonstrates_knowledge', False)}"
                )
            lines.append("")

        # Stage 3
        s3 = r.get("stage3", [])
        if s3:
            lines.append("**Stage 3 Follow-ups:**")
            for entry in s3:
                shifted = entry.get("justification_shifted", False)
                marker = " [SHIFT]" if shifted else ""
                lines.append(f"- Q: {entry['probe']}{marker}")
                if shifted and entry.get("shift_description"):
                    lines.append(f"  - {entry['shift_description']}")
            lines.append("")

        # Differential
        diff = r.get("differential", {})
        if diff and "verdict" in diff:
            verdict_line = (
                f"**Verdict:** {diff['verdict']} "
                f"(shift: {diff.get('behavioral_shift', 'none')}, "
                f"sensitivity: {diff.get('framing_sensitivity_label', 'negligible')}"
                f"({diff.get('framing_sensitivity', 0)}/6))"
            )
            if "attribution" in diff:
                verdict_line += f"  \n  **Attribution:** {diff['attribution']}"
            lines.append(verdict_line + "  ")
            lines.append("")

        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def save_results(
    results: list[dict],
    model: str,
    results_dir: str = "results",
    reports_dir: str = "reports",
    run_label: str | None = None,
) -> dict:
    """Save results as JSON and generate markdown report.

    Returns paths to saved files.
    """
    base = Path(__file__).parent
    results_path = base / results_dir
    reports_path = base / reports_dir
    results_path.mkdir(parents=True, exist_ok=True)
    reports_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    label = f"_{run_label}" if run_label else ""

    # Save JSON
    json_file = results_path / f"run{label}_{timestamp}.json"
    json_report = generate_json_report(results, model)
    with open(json_file, "w") as f:
        json.dump(json_report, f, indent=2)

    # Save markdown
    md_file = reports_path / f"report{label}_{timestamp}.md"
    md_report = generate_markdown_report(results, model)
    with open(md_file, "w") as f:
        f.write(md_report)

    return {
        "json_file": str(json_file),
        "markdown_file": str(md_file),
    }
