"""Comparative analysis engine for cross-domain reasoning honesty evaluation.

Aggregates results from multiple probe suite runs, computes cross-domain statistics,
and generates a comprehensive comparative HTML report with deployment strategy
and security/truthfulness implications.
"""

import json
import math
import re
from collections import defaultdict
from pathlib import Path
from typing import Any


def load_all_results(results_dir: str = "results") -> list[dict]:
    """Load all JSON result files from the results directory."""
    base = Path(__file__).parent / results_dir
    all_results = []
    for f in sorted(base.glob("run_*.json")):
        with open(f) as fp:
            data = json.load(fp)
        # Tag each probe result with the source file
        for pr in data.get("probe_results", []):
            pr["_source_file"] = f.name
            pr["_meta"] = data.get("meta", {})
        all_results.extend(data.get("probe_results", []))
    return all_results


def load_specific_results(result_files: list[str]) -> list[dict]:
    """Load specific result files by path."""
    all_results = []
    for fpath in result_files:
        with open(fpath) as fp:
            data = json.load(fp)
        for pr in data.get("probe_results", []):
            pr["_source_file"] = Path(fpath).name
            pr["_meta"] = data.get("meta", {})
        all_results.extend(data.get("probe_results", []))
    return all_results


# ──────────────────────────────────────────────
# Statistical helpers
# ──────────────────────────────────────────────

def _mean(vals: list[float]) -> float:
    return sum(vals) / len(vals) if vals else 0.0


def _stdev(vals: list[float]) -> float:
    if len(vals) < 2:
        return 0.0
    m = _mean(vals)
    return math.sqrt(sum((v - m) ** 2 for v in vals) / (len(vals) - 1))


def _median(vals: list[float]) -> float:
    if not vals:
        return 0.0
    s = sorted(vals)
    n = len(s)
    if n % 2 == 0:
        return (s[n // 2 - 1] + s[n // 2]) / 2
    return s[n // 2]


# ──────────────────────────────────────────────
# Cross-domain aggregation
# ──────────────────────────────────────────────

def compute_domain_stats(results: list[dict]) -> dict[str, dict]:
    """Compute comprehensive statistics per domain."""
    domains: dict[str, dict[str, Any]] = defaultdict(lambda: {
        "probes": 0, "deflections": 0, "partial_assists": 0, "full_assists": 0,
        "gaps_confirmed": 0, "adr_scores": [], "concern_ratios": [],
        "pattern_counts": defaultdict(int), "risk_tiers": defaultdict(int),
        "justification_shifts": 0, "total_stage3_probes": 0,
        "probe_ids": set(),
    })

    for r in results:
        domain = r.get("domain", "unknown")
        d = domains[domain]
        d["probes"] += 1
        d["probe_ids"].add(r.get("probe_id", ""))

        cls = r.get("stage1", {}).get("classification", "")
        if cls == "deflection":
            d["deflections"] += 1
        elif cls == "partial_assist":
            d["partial_assists"] += 1
        elif cls == "full_assist":
            d["full_assists"] += 1

        cr = r.get("stage1", {}).get("concern_ratio")
        if cr is not None:
            d["concern_ratios"].append(cr)

        if r.get("capability_gap", {}).get("gap_confirmed"):
            d["gaps_confirmed"] += 1

        d["risk_tiers"][r.get("risk_tier", "unknown")] += 1

        diff = r.get("differential", {})
        if "total_score" in diff and diff["total_score"] >= 0:
            d["adr_scores"].append(diff["total_score"])
        if "specificity_score" in diff:
            d.setdefault("specificity_scores", []).append(diff["specificity_score"])
            d.setdefault("credential_scores", []).append(diff["credential_score"])

        for p in r.get("stage1", {}).get("patterns", []):
            d["pattern_counts"][p] += 1

        for s3 in r.get("stage3", []):
            d["total_stage3_probes"] += 1
            if s3.get("justification_shifted"):
                d["justification_shifts"] += 1

    # Compute derived stats
    for domain, d in domains.items():
        d["deflection_rate"] = round(d["deflections"] / d["probes"] * 100, 1) if d["probes"] else 0
        d["full_assist_rate"] = round(d["full_assists"] / d["probes"] * 100, 1) if d["probes"] else 0
        d["avg_adr"] = round(_mean(d["adr_scores"]), 2)
        d["median_adr"] = round(_median(d["adr_scores"]), 1)
        d["stdev_adr"] = round(_stdev(d["adr_scores"]), 2)
        d["avg_concern_ratio"] = round(_mean(d["concern_ratios"]), 3)
        d["gap_rate"] = round(d["gaps_confirmed"] / d["probes"] * 100, 1) if d["probes"] else 0
        d["shift_rate"] = round(d["justification_shifts"] / d["total_stage3_probes"] * 100, 1) if d["total_stage3_probes"] else 0
        d["unique_probes"] = len(d["probe_ids"])
        d["avg_specificity"] = round(_mean(d.get("specificity_scores", [])), 2)
        d["avg_credential"] = round(_mean(d.get("credential_scores", [])), 2)
        # Convert sets/defaultdicts for JSON serialization
        d["probe_ids"] = sorted(d["probe_ids"])
        d["pattern_counts"] = dict(d["pattern_counts"])
        d["risk_tiers"] = dict(d["risk_tiers"])

    return dict(domains)


def compute_risk_tier_stats(results: list[dict]) -> dict[str, dict]:
    """Compute statistics grouped by risk tier."""
    tiers: dict[str, dict[str, Any]] = defaultdict(lambda: {
        "probes": 0, "deflections": 0, "full_assists": 0,
        "adr_scores": [], "concern_ratios": [],
    })

    for r in results:
        tier = r.get("risk_tier", "unknown")
        t = tiers[tier]
        t["probes"] += 1

        cls = r.get("stage1", {}).get("classification", "")
        if cls == "deflection":
            t["deflections"] += 1
        elif cls == "full_assist":
            t["full_assists"] += 1

        cr = r.get("stage1", {}).get("concern_ratio")
        if cr is not None:
            t["concern_ratios"].append(cr)

        diff = r.get("differential", {})
        if "total_score" in diff and diff["total_score"] >= 0:
            t["adr_scores"].append(diff["total_score"])

    for tier, t in tiers.items():
        t["deflection_rate"] = round(t["deflections"] / t["probes"] * 100, 1) if t["probes"] else 0
        t["full_assist_rate"] = round(t["full_assists"] / t["probes"] * 100, 1) if t["probes"] else 0
        t["avg_adr"] = round(_mean(t["adr_scores"]), 2)
        t["avg_concern_ratio"] = round(_mean(t["concern_ratios"]), 3)

    return dict(tiers)


def compute_pattern_frequency(results: list[dict]) -> dict[str, int]:
    """Compute global pattern frequency across all results."""
    counts: dict[str, int] = defaultdict(int)
    for r in results:
        for p in r.get("stage1", {}).get("patterns", []):
            counts[p] += 1
    return dict(sorted(counts.items(), key=lambda x: -x[1]))


def compute_adr_heatmap(results: list[dict]) -> list[dict]:
    """Compute ADR score data for cross-domain heatmap visualization."""
    rows = []
    for r in results:
        diff = r.get("differential", {})
        if "total_score" not in diff:
            continue
        row = {
            "probe_id": r.get("probe_id", ""),
            "domain": r.get("domain", ""),
            "risk_tier": r.get("risk_tier", ""),
            "total_score": diff.get("total_score", 0),
            "constraint_diff": diff.get("constraint_diff", 0),
            "justification_diff": diff.get("justification_diff", 0),
            "scope_diff": diff.get("scope_diff", 0),
            "calibration_diff": diff.get("calibration_diff", 0),
            "adr_evidence": diff.get("adr_evidence", False),
        }
        # Three-condition decomposed scores
        if "specificity_score" in diff:
            row["combined_score"] = diff.get("combined_score", 0)
            row["specificity_score"] = diff.get("specificity_score", 0)
            row["credential_score"] = diff.get("credential_score", 0)
            row["specificity_evidence"] = diff.get("specificity_evidence", False)
            row["credential_evidence"] = diff.get("credential_evidence", False)
        rows.append(row)
    return sorted(rows, key=lambda x: (-x["total_score"], x["domain"]))


def compute_credential_sensitivity(results: list[dict]) -> dict:
    """Analyze how much credential framing changes responses across domains."""
    domain_cred: dict[str, dict] = defaultdict(lambda: {
        "with_adr": 0, "without_adr": 0, "total": 0,
        "avg_score_when_adr": [], "scores": [],
        "specificity_scores": [], "credential_scores": [],
    })

    for r in results:
        diff = r.get("differential", {})
        if "total_score" not in diff:
            continue
        domain = r.get("domain", "unknown")
        dc = domain_cred[domain]
        dc["total"] += 1
        dc["scores"].append(diff["total_score"])
        if diff.get("adr_evidence"):
            dc["with_adr"] += 1
            dc["avg_score_when_adr"].append(diff["total_score"])
        else:
            dc["without_adr"] += 1
        if "specificity_score" in diff:
            dc["specificity_scores"].append(diff["specificity_score"])
            dc["credential_scores"].append(diff["credential_score"])

    result = {}
    for domain, dc in domain_cred.items():
        entry = {
            "total_probes": dc["total"],
            "adr_rate": round(dc["with_adr"] / dc["total"] * 100, 1) if dc["total"] else 0,
            "avg_adr_score": round(_mean(dc["scores"]), 2),
            "avg_score_when_adr": round(_mean(dc["avg_score_when_adr"]), 2),
        }
        if dc["specificity_scores"]:
            entry["avg_specificity_score"] = round(_mean(dc["specificity_scores"]), 2)
            entry["avg_credential_score"] = round(_mean(dc["credential_scores"]), 2)
        result[domain] = entry
    return result


def compute_capability_gap_analysis(results: list[dict]) -> dict:
    """Analyze capability gaps: domains where model deflects but demonstrably has knowledge."""
    domain_gaps: dict[str, dict] = defaultdict(lambda: {
        "total_tested": 0, "gaps_confirmed": 0, "probes_with_gaps": [],
    })

    for r in results:
        gap = r.get("capability_gap", {})
        if not gap.get("test_prompt"):
            continue
        domain = r.get("domain", "unknown")
        dg = domain_gaps[domain]
        dg["total_tested"] += 1
        if gap.get("gap_confirmed"):
            dg["gaps_confirmed"] += 1
            dg["probes_with_gaps"].append(r.get("probe_id", ""))

    for domain, dg in domain_gaps.items():
        dg["gap_rate"] = round(dg["gaps_confirmed"] / dg["total_tested"] * 100, 1) if dg["total_tested"] else 0

    return dict(domain_gaps)


def generate_comparative_analysis(results: list[dict]) -> dict:
    """Generate the complete comparative analysis data structure."""
    domain_stats = compute_domain_stats(results)
    risk_stats = compute_risk_tier_stats(results)
    pattern_freq = compute_pattern_frequency(results)
    adr_heatmap = compute_adr_heatmap(results)
    cred_sensitivity = compute_credential_sensitivity(results)
    gap_analysis = compute_capability_gap_analysis(results)

    # Global summary metrics
    total = len(results)
    total_deflections = sum(d["deflections"] for d in domain_stats.values())
    total_full_assists = sum(d["full_assists"] for d in domain_stats.values())
    total_adr = sum(1 for r in adr_heatmap if r["adr_evidence"])
    total_gaps = sum(d["gaps_confirmed"] for d in gap_analysis.values())
    all_adr_scores = [r["total_score"] for r in adr_heatmap]
    all_concern_ratios = [
        r.get("stage1", {}).get("concern_ratio", 0)
        for r in results if r.get("stage1", {}).get("concern_ratio") is not None
    ]

    return {
        "global_summary": {
            "total_probes": total,
            "total_domains": len(domain_stats),
            "total_deflections": total_deflections,
            "total_full_assists": total_full_assists,
            "deflection_rate": round(total_deflections / total * 100, 1) if total else 0,
            "full_assist_rate": round(total_full_assists / total * 100, 1) if total else 0,
            "total_adr_evidence": total_adr,
            "adr_rate": round(total_adr / len(adr_heatmap) * 100, 1) if adr_heatmap else 0,
            "total_capability_gaps": total_gaps,
            "avg_adr_score": round(_mean(all_adr_scores), 2),
            "median_adr_score": round(_median(all_adr_scores), 1),
            "avg_concern_ratio": round(_mean(all_concern_ratios), 3),
        },
        "domain_stats": domain_stats,
        "risk_tier_stats": risk_stats,
        "pattern_frequency": pattern_freq,
        "adr_heatmap": adr_heatmap,
        "credential_sensitivity": cred_sensitivity,
        "capability_gap_analysis": gap_analysis,
    }
