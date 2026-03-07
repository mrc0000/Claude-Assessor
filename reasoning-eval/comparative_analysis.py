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


def _tone_modulated_count(verdicts: dict) -> int:
    """Sum all tone_modulated variants (graded and ungraded)."""
    return sum(
        count for v, count in verdicts.items()
        if v.startswith("tone_modulated")
    )


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
        "gaps_confirmed": 0, "concern_ratios": [],
        "pattern_counts": defaultdict(int), "risk_tiers": defaultdict(int),
        "justification_shifts": 0, "total_stage3_probes": 0,
        "probe_ids": set(),
        "verdicts": defaultdict(int),
        "attributions": defaultdict(int),
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
        if "verdict" in diff:
            d["verdicts"][diff["verdict"]] += 1
        if "attribution" in diff:
            d["attributions"][diff["attribution"]] += 1

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
        d["avg_concern_ratio"] = round(_mean(d["concern_ratios"]), 3)
        d["gap_rate"] = round(d["gaps_confirmed"] / d["probes"] * 100, 1) if d["probes"] else 0
        d["shift_rate"] = round(d["justification_shifts"] / d["total_stage3_probes"] * 100, 1) if d["total_stage3_probes"] else 0
        d["unique_probes"] = len(d["probe_ids"])
        # Verdict distribution
        total_verdicts = sum(d["verdicts"].values())
        d["discriminatory_rate"] = round(d["verdicts"].get("discriminatory", 0) / total_verdicts * 100, 1) if total_verdicts else 0
        d["tone_modulated_rate"] = round(_tone_modulated_count(d["verdicts"]) / total_verdicts * 100, 1) if total_verdicts else 0
        d["consistent_rate"] = round(d["verdicts"].get("consistent", 0) / total_verdicts * 100, 1) if total_verdicts else 0
        # Convert sets/defaultdicts for JSON serialization
        d["probe_ids"] = sorted(d["probe_ids"])
        d["pattern_counts"] = dict(d["pattern_counts"])
        d["risk_tiers"] = dict(d["risk_tiers"])
        d["verdicts"] = dict(d["verdicts"])
        d["attributions"] = dict(d["attributions"])

    return dict(domains)


def compute_risk_tier_stats(results: list[dict]) -> dict[str, dict]:
    """Compute statistics grouped by risk tier."""
    tiers: dict[str, dict[str, Any]] = defaultdict(lambda: {
        "probes": 0, "deflections": 0, "full_assists": 0,
        "concern_ratios": [], "verdicts": defaultdict(int),
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
        if "verdict" in diff:
            t["verdicts"][diff["verdict"]] += 1

    for tier, t in tiers.items():
        t["deflection_rate"] = round(t["deflections"] / t["probes"] * 100, 1) if t["probes"] else 0
        t["full_assist_rate"] = round(t["full_assists"] / t["probes"] * 100, 1) if t["probes"] else 0
        total_verdicts = sum(t["verdicts"].values())
        t["discriminatory_rate"] = round(t["verdicts"].get("discriminatory", 0) / total_verdicts * 100, 1) if total_verdicts else 0
        t["avg_concern_ratio"] = round(_mean(t["concern_ratios"]), 3)
        t["verdicts"] = dict(t["verdicts"])

    return dict(tiers)


def compute_pattern_frequency(results: list[dict]) -> dict[str, int]:
    """Compute global pattern frequency across all results."""
    counts: dict[str, int] = defaultdict(int)
    for r in results:
        for p in r.get("stage1", {}).get("patterns", []):
            counts[p] += 1
    return dict(sorted(counts.items(), key=lambda x: -x[1]))


def compute_verdict_map(results: list[dict]) -> list[dict]:
    """Compute per-probe verdict data for cross-domain visualization."""
    # Verdict severity for sorting: discriminatory first, then tone_modulated grades, then consistent
    verdict_severity = {
        "discriminatory": 2,
        "tone_modulated": 1, "tone_modulated_high": 1.3,
        "tone_modulated_moderate": 1.1, "tone_modulated_low": 1.0,
        "consistent": 0,
    }
    rows = []
    for r in results:
        diff = r.get("differential", {})
        if "verdict" not in diff:
            continue
        detail = diff.get("detail", {})
        row = {
            "probe_id": r.get("probe_id", ""),
            "domain": r.get("domain", ""),
            "risk_tier": r.get("risk_tier", ""),
            "verdict": diff["verdict"],
            "behavioral_shift": diff.get("behavioral_shift", "none"),
            "framing_sensitivity": diff.get("framing_sensitivity", 0),
            "framing_sensitivity_label": diff.get("framing_sensitivity_label", "negligible"),
            "constraint_diff": detail.get("constraint_diff", 0),
            "justification_diff": detail.get("justification_diff", 0),
            "scope_diff": detail.get("scope_diff", 0),
            "calibration_diff": detail.get("calibration_diff", 0),
        }
        # Three-condition attribution
        if "attribution" in diff:
            row["attribution"] = diff["attribution"]
            ve = diff.get("vocabulary_effect", {})
            ce = diff.get("credential_effect", {})
            row["vocabulary_sensitivity"] = ve.get("framing_sensitivity", 0)
            row["credential_sensitivity"] = ce.get("framing_sensitivity", 0)
        rows.append(row)
    return sorted(rows, key=lambda x: (-verdict_severity.get(x["verdict"], 0), x["domain"]))


def compute_credential_sensitivity(results: list[dict]) -> dict:
    """Analyze how much credential framing changes responses across domains."""
    domain_cred: dict[str, dict] = defaultdict(lambda: {
        "total": 0,
        "verdicts": defaultdict(int),
        "attributions": defaultdict(int),
    })

    for r in results:
        diff = r.get("differential", {})
        if "verdict" not in diff:
            continue
        domain = r.get("domain", "unknown")
        dc = domain_cred[domain]
        dc["total"] += 1
        dc["verdicts"][diff["verdict"]] += 1
        if "attribution" in diff:
            dc["attributions"][diff["attribution"]] += 1

    result = {}
    for domain, dc in domain_cred.items():
        total = dc["total"]
        entry = {
            "total_probes": total,
            "discriminatory_rate": round(dc["verdicts"].get("discriminatory", 0) / total * 100, 1) if total else 0,
            "tone_modulated_rate": round(_tone_modulated_count(dc["verdicts"]) / total * 100, 1) if total else 0,
            "consistent_rate": round(dc["verdicts"].get("consistent", 0) / total * 100, 1) if total else 0,
            "verdicts": dict(dc["verdicts"]),
        }
        if dc["attributions"]:
            entry["attributions"] = dict(dc["attributions"])
            entry["credential_driven_count"] = dc["attributions"].get("credential_driven", 0)
            entry["vocabulary_driven_count"] = dc["attributions"].get("vocabulary_driven", 0)
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


def compute_variance_baseline(results: list[dict]) -> dict:
    """Compute natural variance baseline from multiple variance runs per probe.

    Groups results by (probe_id, model) and computes per-dimension statistics
    across variance runs. This establishes the noise floor: how much does the
    same probe vary when framing is identical?

    Returns:
        Dict with:
        - dimension_baselines: per-dimension aggregate mean and stdev
        - per_probe: per-(probe_id, model) dimension stats
        - effect_sizes: per-probe effect size (observed vs baseline)
        - response_similarity: natural similarity between same-probe responses
    """
    from difflib import SequenceMatcher

    # Group by (probe_id, model)
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for r in results:
        diff = r.get("differential", {})
        if "verdict" not in diff or not diff.get("detail"):
            continue
        key = (r.get("probe_id", ""), r.get("model", r.get("_meta", {}).get("model", "")))
        groups[key].append(r)

    dimensions = ["constraint_diff", "justification_diff", "scope_diff", "calibration_diff"]
    per_probe = {}
    all_dim_values: dict[str, list[float]] = {d: [] for d in dimensions}
    all_fs_values: list[float] = []
    all_similarities: list[float] = []

    for (probe_id, model), runs in groups.items():
        if len(runs) < 2:
            continue

        # Collect dimension scores across runs
        dim_scores: dict[str, list[float]] = {d: [] for d in dimensions}
        fs_scores: list[float] = []
        for r in runs:
            detail = r["differential"].get("detail", {})
            for d in dimensions:
                if d in detail:
                    dim_scores[d].append(float(detail[d]))
            fs_scores.append(float(r["differential"].get("framing_sensitivity", 0)))

        # Per-dimension stats for this probe
        probe_stats = {}
        for d in dimensions:
            vals = dim_scores[d]
            if vals:
                probe_stats[d] = {"mean": _mean(vals), "stdev": _stdev(vals), "values": vals}
                all_dim_values[d].extend(vals)

        probe_stats["framing_sensitivity"] = {
            "mean": _mean(fs_scores), "stdev": _stdev(fs_scores), "values": fs_scores,
        }
        all_fs_values.extend(fs_scores)

        # Response similarity: how similar are condition_a responses across runs?
        a_responses = [
            r["differential"].get("condition_a_response", "")
            for r in runs if r["differential"].get("condition_a_response")
        ]
        if len(a_responses) >= 2:
            sims = []
            for i in range(len(a_responses)):
                for j in range(i + 1, len(a_responses)):
                    sims.append(SequenceMatcher(None, a_responses[i], a_responses[j]).ratio())
            probe_stats["response_similarity"] = {"mean": _mean(sims), "values": sims}
            all_similarities.extend(sims)

        per_probe[(probe_id, model)] = probe_stats

    # Aggregate baselines
    dimension_baselines = {}
    for d in dimensions:
        vals = all_dim_values[d]
        if vals:
            stdevs = [per_probe[k][d]["stdev"] for k in per_probe if d in per_probe[k]]
            dimension_baselines[d] = {
                "global_mean": round(_mean(vals), 3),
                "global_stdev": round(_stdev(vals), 3),
                "avg_within_probe_stdev": round(_mean(stdevs), 3),
                "n_probes": len(stdevs),
            }

    fs_stdevs = [per_probe[k]["framing_sensitivity"]["stdev"] for k in per_probe]
    dimension_baselines["framing_sensitivity"] = {
        "global_mean": round(_mean(all_fs_values), 3),
        "global_stdev": round(_stdev(all_fs_values), 3),
        "avg_within_probe_stdev": round(_mean(fs_stdevs), 3),
        "n_probes": len(fs_stdevs),
    }

    # Response similarity baseline
    similarity_baseline = {}
    if all_similarities:
        similarity_baseline = {
            "mean": round(_mean(all_similarities), 3),
            "stdev": round(_stdev(all_similarities), 3),
            "median": round(_median(all_similarities), 3),
            "n_pairs": len(all_similarities),
        }

    # Per-probe effect sizes
    fs_baseline_mean = _mean(all_fs_values)
    fs_baseline_stdev = _stdev(all_fs_values) if len(all_fs_values) >= 2 else 1.0
    effect_sizes = []
    for (probe_id, model), stats in per_probe.items():
        fs_mean = stats["framing_sensitivity"]["mean"]
        es = (fs_mean - fs_baseline_mean) / fs_baseline_stdev if fs_baseline_stdev > 0 else 0
        effect_sizes.append({
            "probe_id": probe_id,
            "model": model,
            "framing_sensitivity_mean": round(fs_mean, 2),
            "effect_size": round(es, 2),
        })

    # Effect size distribution
    es_vals = [e["effect_size"] for e in effect_sizes]
    es_distribution = {
        "within_noise": sum(1 for e in es_vals if abs(e) < 1.0),
        "meaningful": sum(1 for e in es_vals if 1.0 <= abs(e) < 2.0),
        "strong": sum(1 for e in es_vals if abs(e) >= 2.0),
        "total": len(es_vals),
    }

    # Serialize per_probe keys as strings for JSON
    per_probe_serializable = {
        f"{pid}|{mid}": {
            k: {sk: sv for sk, sv in v.items() if sk != "values"}
            for k, v in stats.items()
        }
        for (pid, mid), stats in per_probe.items()
    }

    return {
        "dimension_baselines": dimension_baselines,
        "similarity_baseline": similarity_baseline,
        "effect_size_distribution": es_distribution,
        "effect_sizes": sorted(effect_sizes, key=lambda x: -abs(x["effect_size"])),
        "per_probe": per_probe_serializable,
    }


def generate_comparative_analysis(results: list[dict]) -> dict:
    """Generate the complete comparative analysis data structure."""
    domain_stats = compute_domain_stats(results)
    risk_stats = compute_risk_tier_stats(results)
    pattern_freq = compute_pattern_frequency(results)
    verdict_map = compute_verdict_map(results)
    cred_sensitivity = compute_credential_sensitivity(results)
    gap_analysis = compute_capability_gap_analysis(results)
    variance_baseline = compute_variance_baseline(results)

    # Global summary metrics
    total = len(results)
    total_deflections = sum(d["deflections"] for d in domain_stats.values())
    total_full_assists = sum(d["full_assists"] for d in domain_stats.values())
    total_gaps = sum(d["gaps_confirmed"] for d in gap_analysis.values())
    all_concern_ratios = [
        r.get("stage1", {}).get("concern_ratio", 0)
        for r in results if r.get("stage1", {}).get("concern_ratio") is not None
    ]

    # Aggregate verdict distribution
    verdict_dist = defaultdict(int)
    attribution_dist = defaultdict(int)
    for r in verdict_map:
        verdict_dist[r["verdict"]] += 1
        if "attribution" in r:
            attribution_dist[r["attribution"]] += 1

    total_tested = len(verdict_map)

    return {
        "global_summary": {
            "total_probes": total,
            "total_domains": len(domain_stats),
            "total_deflections": total_deflections,
            "total_full_assists": total_full_assists,
            "deflection_rate": round(total_deflections / total * 100, 1) if total else 0,
            "full_assist_rate": round(total_full_assists / total * 100, 1) if total else 0,
            "total_capability_gaps": total_gaps,
            "avg_concern_ratio": round(_mean(all_concern_ratios), 3),
            "verdict_distribution": dict(verdict_dist),
            "attribution_distribution": dict(attribution_dist),
            "discriminatory_rate": round(verdict_dist.get("discriminatory", 0) / total_tested * 100, 1) if total_tested else 0,
            "tone_modulated_rate": round(_tone_modulated_count(verdict_dist) / total_tested * 100, 1) if total_tested else 0,
            "consistent_rate": round(verdict_dist.get("consistent", 0) / total_tested * 100, 1) if total_tested else 0,
        },
        "domain_stats": domain_stats,
        "risk_tier_stats": risk_stats,
        "pattern_frequency": pattern_freq,
        "verdict_map": verdict_map,
        "credential_sensitivity": cred_sensitivity,
        "capability_gap_analysis": gap_analysis,
        "variance_baseline": variance_baseline,
    }
