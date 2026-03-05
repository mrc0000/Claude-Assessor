"""
reporter.py — Report generation.

Produces:
  - Per-domain summaries
  - Cross-domain consistency analysis
  - Differential results table
  - JSON export + markdown report
"""

import json
import os
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import config


# ------------------------------------------------------------------
# Aggregation helpers
# ------------------------------------------------------------------

def _group_by_domain(results: list[dict]) -> dict[str, list[dict]]:
    groups: dict[str, list[dict]] = defaultdict(list)
    for r in results:
        groups[r["domain"]].append(r)
    return dict(groups)


def _domain_stats(domain_results: list[dict]) -> dict:
    """Compute per-domain aggregate statistics."""
    n = len(domain_results)
    deflections = sum(
        1 for r in domain_results
        if r["stage1"]["classification"] in ("deflection", "partial")
    )
    gaps_confirmed = sum(
        1 for r in domain_results if r["capability_gap"]["gap_confirmed"]
    )
    adr_scores = [r["differential"]["total_score"] for r in domain_results]
    avg_adr = sum(adr_scores) / len(adr_scores) if adr_scores else 0.0
    adr_flagged = sum(1 for s in adr_scores if s >= config.ADR_INVESTIGATE_THRESHOLD)

    pattern_counts: dict[str, int] = defaultdict(int)
    for r in domain_results:
        for p in r["stage1"].get("patterns", []):
            pattern_counts[p] += 1

    top_patterns = sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True)

    return {
        "probe_count": n,
        "deflection_count": deflections,
        "deflection_rate": deflections / n if n else 0.0,
        "gap_confirmed_count": gaps_confirmed,
        "avg_adr_score": round(avg_adr, 2),
        "adr_flagged_count": adr_flagged,
        "top_patterns": top_patterns[:3],
    }


def _cross_domain_consistency(domain_stats: dict[str, dict]) -> dict:
    """
    Identify domains that show inconsistent behavior relative to each other.
    For now: flag domains whose deflection_rate is an outlier.
    """
    if len(domain_stats) < 2:
        return {"note": "Insufficient domains for cross-domain analysis"}

    rates = {d: s["deflection_rate"] for d, s in domain_stats.items()}
    mean_rate = sum(rates.values()) / len(rates)
    high = [d for d, r in rates.items() if r > mean_rate + 0.25]
    low = [d for d, r in rates.items() if r < mean_rate - 0.25]

    adr_scores = {d: s["avg_adr_score"] for d, s in domain_stats.items()}
    mean_adr = sum(adr_scores.values()) / len(adr_scores)
    high_adr = [d for d, s in adr_scores.items() if s >= config.ADR_STRONG_EVIDENCE_THRESHOLD]

    return {
        "mean_deflection_rate": round(mean_rate, 3),
        "high_deflection_domains": high,
        "low_deflection_domains": low,
        "mean_adr_score": round(mean_adr, 2),
        "strong_adr_domains": high_adr,
    }


# ------------------------------------------------------------------
# Key findings narrative
# ------------------------------------------------------------------

def _generate_findings(
    domain_stats: dict[str, dict],
    cross_domain: dict,
    results: list[dict],
) -> list[str]:
    findings = []

    # Overall deflection
    total = sum(s["probe_count"] for s in domain_stats.values())
    total_deflections = sum(s["deflection_count"] for s in domain_stats.values())
    if total:
        rate = total_deflections / total
        findings.append(
            f"Overall deflection rate: {rate:.0%} ({total_deflections}/{total} probes)."
        )

    # Capability gaps
    total_gaps = sum(s["gap_confirmed_count"] for s in domain_stats.values())
    if total_gaps:
        findings.append(
            f"{total_gaps} capability gap(s) confirmed — model deflected but demonstrated "
            "the relevant knowledge in a fresh conversation."
        )

    # ADR evidence
    adr_evidence_count = sum(
        1 for r in results if r["differential"]["adr_evidence"]
    )
    strong_adr_count = sum(
        1 for r in results if r["differential"].get("strong_adr_evidence")
    )
    if adr_evidence_count:
        findings.append(
            f"{adr_evidence_count} probe(s) show audience-dependent reasoning (ADR) evidence "
            f"(differential score ≥ {config.ADR_INVESTIGATE_THRESHOLD}); "
            f"{strong_adr_count} of those exceed the strong-evidence threshold "
            f"(score ≥ {config.ADR_STRONG_EVIDENCE_THRESHOLD})."
        )

    # High ADR domains
    if cross_domain.get("strong_adr_domains"):
        domains = ", ".join(cross_domain["strong_adr_domains"])
        findings.append(
            f"Domains with strong ADR evidence: {domains}."
        )

    # Justification shifts in stage 3
    total_shifts = sum(
        sum(1 for turn in r["stage3"] if turn.get("justification_shifted"))
        for r in results
    )
    if total_shifts:
        findings.append(
            f"{total_shifts} justification shift(s) detected across stage3 reasoning audit sequences."
        )

    if not findings:
        findings.append("No significant deflection patterns detected in this run.")

    return findings


# ------------------------------------------------------------------
# JSON export
# ------------------------------------------------------------------

def export_json(
    results: list[dict],
    domain_stats: dict[str, dict],
    cross_domain: dict,
    findings: list[str],
    run_id: str,
) -> str:
    """Write full evaluation JSON to results/ and return the filepath."""
    out = {
        "run_id": run_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "model": results[0]["model"] if results else "unknown",
        "probe_count": len(results),
        "domain_summary": domain_stats,
        "cross_domain_consistency": cross_domain,
        "key_findings": findings,
        "probe_results": results,
    }

    out_dir = Path(config.RESULTS_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{run_id}_evaluation.json"
    with open(path, "w") as f:
        json.dump(out, f, indent=2)
    return str(path)


# ------------------------------------------------------------------
# Markdown report
# ------------------------------------------------------------------

def _pattern_name(pattern_id: str) -> str:
    meta = config.DEFLECTION_PATTERNS.get(pattern_id)
    return meta["name"] if meta else pattern_id


def export_markdown(
    results: list[dict],
    domain_stats: dict[str, dict],
    cross_domain: dict,
    findings: list[str],
    run_id: str,
) -> str:
    """Write markdown report to reports/ and return the filepath."""
    model = results[0]["model"] if results else "unknown"
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    n_probes = len(results)

    lines = [
        "# Reasoning Honesty Evaluation Report",
        f"**Model:** `{model}`  ",
        f"**Date:** {date}  ",
        f"**Probes run:** {n_probes}  ",
        f"**Run ID:** `{run_id}`",
        "",
        "---",
        "",
        "## Domain Summary",
        "",
        "| Domain | Probes | Deflections | Rate | Gaps Confirmed | Avg ADR Score | ADR Flagged |",
        "|--------|--------|-------------|------|----------------|---------------|-------------|",
    ]

    for domain, stats in sorted(domain_stats.items()):
        lines.append(
            f"| {domain.capitalize()} "
            f"| {stats['probe_count']} "
            f"| {stats['deflection_count']} "
            f"| {stats['deflection_rate']:.0%} "
            f"| {stats['gap_confirmed_count']} "
            f"| {stats['avg_adr_score']:.1f} "
            f"| {stats['adr_flagged_count']} |"
        )

    lines += [
        "",
        "---",
        "",
        "## Key Findings",
        "",
    ]
    for finding in findings:
        lines.append(f"- {finding}")

    lines += [
        "",
        "---",
        "",
        "## Cross-Domain Consistency",
        "",
        f"- Mean deflection rate: **{cross_domain.get('mean_deflection_rate', 0):.1%}**",
        f"- Mean ADR score: **{cross_domain.get('mean_adr_score', 0):.1f}**",
    ]
    if cross_domain.get("high_deflection_domains"):
        lines.append(
            f"- High-deflection domains: {', '.join(cross_domain['high_deflection_domains'])}"
        )
    if cross_domain.get("strong_adr_domains"):
        lines.append(
            f"- Domains with strong ADR evidence: {', '.join(cross_domain['strong_adr_domains'])}"
        )

    lines += [
        "",
        "---",
        "",
        "## Differential Results",
        "",
        "| Probe | Constraint Δ | Justification Δ | Scope Δ | Calibration Δ | Total | ADR Evidence |",
        "|-------|-------------|-----------------|---------|---------------|-------|--------------|",
    ]
    for r in results:
        diff = r["differential"]
        adr = "✓ strong" if diff.get("strong_adr_evidence") else ("✓" if diff["adr_evidence"] else "—")
        lines.append(
            f"| `{r['probe_id']}` "
            f"| {diff['constraint_diff']} "
            f"| {diff['justification_diff']} "
            f"| {diff['scope_diff']} "
            f"| {diff['calibration_diff']} "
            f"| **{diff['total_score']}** "
            f"| {adr} |"
        )

    lines += [
        "",
        "---",
        "",
        "## Per-Probe Details",
        "",
    ]

    for r in results:
        s1 = r["stage1"]
        gap = r["capability_gap"]
        diff = r["differential"]

        classification_label = s1["classification"].upper()
        patterns_str = (
            ", ".join(_pattern_name(p) for p in s1["patterns"])
            if s1["patterns"]
            else "none"
        )

        lines += [
            f"### `{r['probe_id']}` — {r['domain'].capitalize()} (risk: {r['risk_tier']})",
            "",
            f"**Stage 1 classification:** {classification_label}  ",
            f"**Patterns detected:** {patterns_str}  ",
        ]

        if s1["justification_language"]:
            lines.append(
                f"**Justification language:** *\"{s1['justification_language']}\"*  "
            )

        lines.append("")
        lines.append("<details><summary>Stage 1 response</summary>")
        lines.append("")
        lines.append(s1["response"].replace("\n", "\n\n"))
        lines.append("")
        lines.append("</details>")
        lines.append("")

        # Stage 3
        shifts = [t for t in r["stage3"] if t.get("justification_shifted")]
        if shifts:
            lines.append(f"**Stage 3:** {len(shifts)} justification shift(s) detected.")
            for t in shifts:
                lines.append(f"  - *\"{t['probe']}\"* → {t['shift_description']}")
        else:
            lines.append("**Stage 3:** No justification shifts detected.")
        lines.append("")

        # Capability gap
        gap_label = "**CONFIRMED**" if gap["gap_confirmed"] else "not confirmed"
        lines.append(f"**Capability gap:** {gap_label}  ")
        if gap["gap_confirmed"]:
            lines.append(
                "  Model deflected on the stage1 probe but demonstrated the relevant "
                "knowledge in a fresh conversation."
            )
        lines.append("")

        # Differential
        adr_label = (
            "Strong ADR evidence" if diff.get("strong_adr_evidence")
            else ("ADR evidence" if diff["adr_evidence"] else "No ADR evidence")
        )
        lines.append(
            f"**Differential (total={diff['total_score']}):** {adr_label}  "
            f"[constraint={diff['constraint_diff']}, "
            f"justification={diff['justification_diff']}, "
            f"scope={diff['scope_diff']}, "
            f"calibration={diff['calibration_diff']}]"
        )
        lines.append("")
        lines.append("---")
        lines.append("")

    md_text = "\n".join(lines)

    out_dir = Path(config.REPORTS_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{run_id}_report.md"
    with open(path, "w") as f:
        f.write(md_text)
    return str(path)


# ------------------------------------------------------------------
# Top-level generate function
# ------------------------------------------------------------------

def generate_report(results: list[dict], run_id: str | None = None) -> tuple[str, str]:
    """
    Given a list of classified probe results, produce JSON + markdown reports.

    Returns (json_path, md_path).
    """
    if not run_id:
        run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")

    by_domain = _group_by_domain(results)
    domain_stats = {d: _domain_stats(rs) for d, rs in by_domain.items()}
    cross_domain = _cross_domain_consistency(domain_stats)
    findings = _generate_findings(domain_stats, cross_domain, results)

    json_path = export_json(results, domain_stats, cross_domain, findings, run_id)
    md_path = export_markdown(results, domain_stats, cross_domain, findings, run_id)

    return json_path, md_path


if __name__ == "__main__":
    import sys
    import glob

    # Re-generate a report from existing classified result JSON files.
    # Usage: python reporter.py [run_id_prefix]
    pattern = sys.argv[1] if len(sys.argv) > 1 else "*"
    result_files = glob.glob(
        os.path.join(config.RESULTS_DIR, f"{pattern}*_evaluation.json")
    )

    if not result_files:
        print(f"No evaluation JSON files found matching pattern '{pattern}' in {config.RESULTS_DIR}/")
        sys.exit(1)

    # Load the first matching evaluation file
    with open(result_files[0]) as f:
        data = json.load(f)

    probe_results = data.get("probe_results", [])
    run_id = data.get("run_id", "regen")
    json_path, md_path = generate_report(probe_results, run_id=run_id + "_regen")
    print(f"JSON: {json_path}")
    print(f"Markdown: {md_path}")
