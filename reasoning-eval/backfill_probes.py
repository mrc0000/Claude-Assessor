#!/usr/bin/env python3
"""Backfill missing probe results into an existing result file.

Identifies probes that failed (empty responses) in a previous run,
re-runs them against the same model, and merges the results back.

Usage:
    python backfill_probes.py \
        --result-file results/run_llm-reclassified_run_medical-deep_v5_20260306_023512_20260307_033140.json \
        --original-file results/heuristic_originals/run_medical-deep_v5_20260306_023512.json \
        --probes-file probes_medical_deep.json
"""

import argparse
import json
import sys
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

from config import Config
from probe_runner import ProbeRunner, load_probes
from analyzer import analyze_probe_result, load_eval_config


def find_missing_probes(original_file: str, reclassified_file: str) -> list[tuple[str, int]]:
    """Find probes present in original but missing from reclassified results.

    Returns list of (probe_id, variance_run) tuples.
    """
    with open(original_file) as f:
        orig = json.load(f)
    with open(reclassified_file) as f:
        recl = json.load(f)

    orig_keys = {
        (r["probe_id"], r.get("variance_run", 1))
        for r in orig.get("probe_results", [])
    }
    recl_keys = {
        (r["probe_id"], r.get("variance_run", 1))
        for r in recl.get("probe_results", [])
    }

    missing = orig_keys - recl_keys

    # Also check for empty responses in the original
    for pr in orig.get("probe_results", []):
        key = (pr["probe_id"], pr.get("variance_run", 1))
        if key in missing:
            s1_resp = pr.get("stage1", {}).get("response", "")
            if not s1_resp:
                continue  # Confirmed: empty response caused the gap
    return sorted(missing)


def backfill(
    result_file: str,
    original_file: str,
    probes_file: str,
    model: str | None = None,
    classify: str = "llm",
    classifier_model: str = "claude-haiku-4-5-20251001",
    dry_run: bool = False,
) -> None:
    """Re-run missing probes and merge into the result file."""
    load_eval_config()

    # Load existing results
    with open(result_file) as f:
        result_data = json.load(f)

    file_model = result_data.get("meta", {}).get("model", "unknown")
    target_model = model or file_model

    # Find missing probes
    missing = find_missing_probes(original_file, result_file)
    if not missing:
        print("No missing probes found. Results are complete.")
        return

    print(f"Missing probes: {len(missing)}")
    for probe_id, run in missing:
        print(f"  {probe_id} (variance run {run})")

    if dry_run:
        print("\nDry run — no API calls made.")
        return

    # Load probe definitions
    all_probes = load_probes(probes_file)
    missing_ids = {pid for pid, _ in missing}
    probes_to_run = [p for p in all_probes if p["id"] in missing_ids]

    if not probes_to_run:
        print(f"ERROR: Could not find probe definitions for: {missing_ids}")
        sys.exit(1)

    # Set up config and runner
    config = Config(
        target_model=target_model,
        classifier_model=classifier_model,
        classification_mode=classify,
    )
    config.validate()
    runner = ProbeRunner(config)

    print(f"\nRunning {len(probes_to_run)} probes against {target_model}...")
    new_results = []

    for probe_id, variance_run in missing:
        probe_def = next(p for p in probes_to_run if p["id"] == probe_id)
        print(f"\n  Running {probe_id} (variance run {variance_run})...")

        raw = runner.run_probe(probe_def)
        result_dict = raw.to_dict()
        analyzed = analyze_probe_result(result_dict, config)
        analyzed["variance_run"] = variance_run
        new_results.append(analyzed)

    # Merge into existing results
    result_data["probe_results"].extend(new_results)
    result_data["meta"]["probes_run"] = len(result_data["probe_results"])

    # Save updated file
    with open(result_file, "w") as f:
        json.dump(result_data, f, indent=2, default=str)

    print(f"\nBackfill complete. {len(new_results)} probes added.")
    print(f"Updated: {result_file}")
    print(f"Total results: {len(result_data['probe_results'])}")


def main():
    parser = argparse.ArgumentParser(description="Backfill missing probe results")
    parser.add_argument("--result-file", required=True, help="Reclassified result file to update")
    parser.add_argument("--original-file", required=True, help="Original result file with all probes")
    parser.add_argument("--probes-file", required=True, help="Probe definitions file")
    parser.add_argument("--model", default=None, help="Override target model (default: from result file)")
    parser.add_argument("--classify", choices=["heuristic", "llm"], default="llm")
    parser.add_argument("--classifier-model", default="claude-haiku-4-5-20251001")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be backfilled without running")
    args = parser.parse_args()

    backfill(
        result_file=args.result_file,
        original_file=args.original_file,
        probes_file=args.probes_file,
        model=args.model,
        classify=args.classify,
        classifier_model=args.classifier_model,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
