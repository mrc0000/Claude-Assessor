#!/usr/bin/env python3
"""Retroactive re-analysis: re-run pattern detection on existing raw results.

When eval_config.json is updated with new patterns, thresholds, or keywords,
this script re-analyzes all stored results without needing to re-run the API calls.

Usage:
    python reanalyze.py                                    # Re-analyze all results
    python reanalyze.py --files results/run_general_v3_*.json  # Specific files
    python reanalyze.py --eval-config eval_config_v2.json  # Use custom config
    python reanalyze.py --comparative --label enriched     # Generate comparative report
"""

import argparse
import json
import sys
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

from config import Config
from analyzer import (
    load_eval_config,
    get_eval_config_snapshot,
    analyze_probe_result,
    _eval_config_cache,
)
from reporter import save_results
from html_report import save_html_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Re-analyze existing results with updated eval config",
    )
    parser.add_argument(
        "--files", nargs="+",
        help="Specific result JSON files to re-analyze (default: all in results/)",
    )
    parser.add_argument(
        "--eval-config", default=None,
        help="Path to eval config to use (default: eval_config.json)",
    )
    parser.add_argument(
        "--classify", choices=["heuristic", "llm"], default="heuristic",
    )
    parser.add_argument(
        "--label", default="reanalyzed",
        help="Label for output files",
    )
    parser.add_argument(
        "--comparative", action="store_true",
        help="Also generate a comparative report across all re-analyzed results",
    )
    parser.add_argument(
        "--diff", action="store_true",
        help="Show what changed between original and re-analyzed classifications",
    )
    return parser.parse_args()


def load_result_files(file_paths: list[str] | None = None) -> list[tuple[str, dict]]:
    """Load result files. Returns list of (filepath, data) tuples."""
    base = Path(__file__).parent / "results"
    results = []

    if file_paths:
        paths = [Path(f) for f in file_paths]
    else:
        paths = sorted(base.glob("run_*.json"))

    for path in paths:
        if not path.exists():
            print(f"  WARNING: {path} not found, skipping")
            continue
        with open(path) as f:
            data = json.load(f)
        results.append((str(path), data))

    return results


def extract_raw_results(data: dict) -> list[dict]:
    """Extract raw probe results from a run file, stripping analysis fields.

    This returns the results with only the raw API responses, so they can be
    re-analyzed with updated patterns/thresholds.
    """
    raw_results = []
    for pr in data.get("probe_results", []):
        # Preserve raw fields, strip analysis fields
        raw = {
            "probe_id": pr.get("probe_id"),
            "domain": pr.get("domain"),
            "risk_tier": pr.get("risk_tier"),
            "timestamp": pr.get("timestamp"),
            "model": pr.get("model"),
        }

        # Stage 1: keep prompt and response, strip classification
        s1 = pr.get("stage1", {})
        raw["stage1"] = {
            "prompt": s1.get("prompt", ""),
            "response": s1.get("response", ""),
        }

        # Stage 3: keep probe and response, strip classification
        s3_raw = []
        for entry in pr.get("stage3", []):
            s3_raw.append({
                "probe": entry.get("probe", ""),
                "response": entry.get("response", ""),
            })
        raw["stage3"] = s3_raw

        # Capability gap: keep test_prompt and response, strip analysis
        gap = pr.get("capability_gap", {})
        if gap.get("test_prompt"):
            raw["capability_gap"] = {
                "test_prompt": gap.get("test_prompt", ""),
                "response": gap.get("response", ""),
            }
        else:
            raw["capability_gap"] = {}

        # Differential: keep prompts and responses, strip analysis
        diff = pr.get("differential", {})
        if diff.get("condition_a_response"):
            raw["differential"] = {
                "condition_a_prompt": diff.get("condition_a_prompt", ""),
                "condition_b_prompt": diff.get("condition_b_prompt", ""),
                "condition_a_response": diff.get("condition_a_response", ""),
                "condition_b_response": diff.get("condition_b_response", ""),
            }
            # Preserve three-condition design (condition C) if present
            if diff.get("condition_c_response"):
                raw["differential"]["condition_c_prompt"] = diff.get("condition_c_prompt", "")
                raw["differential"]["condition_c_response"] = diff.get("condition_c_response", "")
        else:
            raw["differential"] = {}

        # Preserve variance run info
        if "variance_run" in pr:
            raw["variance_run"] = pr["variance_run"]
        if "_suite" in pr:
            raw["_suite"] = pr["_suite"]

        raw_results.append(raw)

    return raw_results


def diff_classifications(original: dict, reanalyzed: dict) -> dict | None:
    """Compare original and re-analyzed classifications for a probe result."""
    orig_cls = original.get("stage1", {}).get("classification", "")
    new_cls = reanalyzed.get("stage1", {}).get("classification", "")
    orig_patterns = set(original.get("stage1", {}).get("patterns", []))
    new_patterns = set(reanalyzed.get("stage1", {}).get("patterns", []))
    orig_adr = original.get("differential", {}).get("adr_evidence")
    new_adr = reanalyzed.get("differential", {}).get("adr_evidence")
    orig_gap = original.get("capability_gap", {}).get("gap_confirmed")
    new_gap = reanalyzed.get("capability_gap", {}).get("gap_confirmed")

    changes = {}
    if orig_cls != new_cls:
        changes["classification"] = {"from": orig_cls, "to": new_cls}
    added_patterns = new_patterns - orig_patterns
    removed_patterns = orig_patterns - new_patterns
    if added_patterns:
        changes["patterns_added"] = sorted(added_patterns)
    if removed_patterns:
        changes["patterns_removed"] = sorted(removed_patterns)
    if orig_adr != new_adr:
        changes["adr_evidence"] = {"from": orig_adr, "to": new_adr}
    if orig_gap != new_gap:
        changes["gap_confirmed"] = {"from": orig_gap, "to": new_gap}

    return changes if changes else None


def main():
    args = parse_args()

    # Load eval config (potentially updated)
    load_eval_config(args.eval_config)
    snap = get_eval_config_snapshot()
    print(f"Eval config: v{snap['config_version']} "
          f"(patterns v{snap['patterns_version']})")

    config = Config(classification_mode=args.classify)

    # Load result files
    result_files = load_result_files(args.files)
    if not result_files:
        print("No result files found.")
        sys.exit(1)

    print(f"Files to re-analyze: {len(result_files)}")

    all_reanalyzed = []
    total_changes = 0

    for filepath, data in result_files:
        print(f"\nRe-analyzing: {Path(filepath).name}")
        model = data.get("meta", {}).get("model", "unknown")
        original_probes = data.get("probe_results", [])
        raw_probes = extract_raw_results(data)

        # Filter out empty/failed probes (no stage1 response)
        paired = [
            (raw, orig) for raw, orig in zip(raw_probes, original_probes)
            if raw.get("stage1", {}).get("response")
        ]
        skipped = len(raw_probes) - len(paired)
        if skipped:
            print(f"  Skipped {skipped} empty/failed probes")
        raw_probes = [p[0] for p in paired]
        original_probes = [p[1] for p in paired]

        file_reanalyzed = []
        file_changes = 0

        for i, (raw, original) in enumerate(zip(raw_probes, original_probes)):
            reanalyzed = analyze_probe_result(raw, config)

            if args.diff:
                changes = diff_classifications(original, reanalyzed)
                if changes:
                    file_changes += 1
                    pid = raw.get("probe_id", f"probe-{i}")
                    print(f"  CHANGED: {pid}")
                    for key, val in changes.items():
                        print(f"    {key}: {val}")

            file_reanalyzed.append(reanalyzed)

        print(f"  Probes: {len(file_reanalyzed)}, Changes: {file_changes}")
        total_changes += file_changes
        all_reanalyzed.extend(file_reanalyzed)

        # Save individual re-analyzed results
        label = f"{args.label}_{Path(filepath).stem}"
        saved = save_results(
            file_reanalyzed, model,
            "results", "reports", run_label=label,
        )
        html_file = save_html_report(
            file_reanalyzed, model, "reports", run_label=label,
        )
        print(f"  Saved: {saved['json_file']}")

    print(f"\nTotal re-analyzed: {len(all_reanalyzed)} probes")
    print(f"Total changes detected: {total_changes}")

    # Comparative report
    if args.comparative and all_reanalyzed:
        from comparative_html_report import save_comparative_report
        comp_path = save_comparative_report(
            all_reanalyzed, model="reanalyzed",
            label=args.label,
        )
        print(f"\nComparative report: {comp_path}")


if __name__ == "__main__":
    main()
