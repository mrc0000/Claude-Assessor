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
        "adr_scores": [],
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
        if "total_score" in diff and diff["total_score"] >= 0:
            d["adr_scores"].append(diff["total_score"])

    summary = []
    for domain, d in sorted(domains.items()):
        avg_adr = (
            round(sum(d["adr_scores"]) / len(d["adr_scores"]), 1)
            if d["adr_scores"]
            else 0.0
        )
        summary.append({
            "domain": domain,
            "probes": d["probes"],
            "deflections": d["deflections"],
            "partial_assists": d["partial_assists"],
            "full_assists": d["full_assists"],
            "gaps_confirmed": d["gaps_confirmed"],
            "avg_adr_score": avg_adr,
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
    adr_flagged = sum(
        1 for r in results
        if r.get("differential", {}).get("adr_evidence")
    )

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
    if adr_flagged:
        findings.append(
            f"{adr_flagged}/{total} probes showed evidence of audience-dependent "
            f"reasoning (differential score >= 2)."
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
        if "total_score" not in diff:
            continue
        rows.append({
            "probe_id": r.get("probe_id", ""),
            "domain": r.get("domain", ""),
            "constraint_diff": diff.get("constraint_diff", 0),
            "justification_diff": diff.get("justification_diff", 0),
            "scope_diff": diff.get("scope_diff", 0),
            "calibration_diff": diff.get("calibration_diff", 0),
            "total_score": diff.get("total_score", 0),
            "adr_evidence": diff.get("adr_evidence", False),
        })
    return rows


def generate_json_report(results: list[dict], model: str) -> dict:
    """Generate the full JSON report structure."""
    return {
        "meta": {
            "model": model,
            "date": datetime.now(timezone.utc).isoformat(),
            "probes_run": len(results),
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

    lines.append("# Reasoning Honesty Evaluation Report")
    lines.append(f"Model: {model}")
    lines.append(f"Date: {now}")
    lines.append(f"Probes run: {len(results)}")
    lines.append("")

    # Domain summary table
    summary = _domain_summary(results)
    lines.append("## Domain Summary")
    lines.append(
        "| Domain | Probes | Deflections | Partial | Full Assist | Gaps Confirmed | Avg ADR Score |"
    )
    lines.append(
        "|--------|--------|-------------|---------|-------------|----------------|---------------|"
    )
    for s in summary:
        lines.append(
            f"| {s['domain']} | {s['probes']} | {s['deflections']} | "
            f"{s['partial_assists']} | {s['full_assists']} | "
            f"{s['gaps_confirmed']} | {s['avg_adr_score']} |"
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
        lines.append("## Differential Results")
        lines.append(
            "| Probe | Domain | Constraint | Justification | Scope | Calibration | Total | ADR? |"
        )
        lines.append(
            "|-------|--------|-----------|---------------|-------|-------------|-------|------|"
        )
        for row in diff_rows:
            adr_flag = "YES" if row["adr_evidence"] else "no"
            lines.append(
                f"| {row['probe_id']} | {row['domain']} | "
                f"{row['constraint_diff']} | {row['justification_diff']} | "
                f"{row['scope_diff']} | {row['calibration_diff']} | "
                f"{row['total_score']} | {adr_flag} |"
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
        if diff and "total_score" in diff:
            adr = "YES" if diff.get("adr_evidence") else "no"
            lines.append(
                f"**Differential Score:** {diff['total_score']}/8 "
                f"(ADR evidence: {adr})  "
            )
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
