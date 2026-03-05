#!/usr/bin/env python3
"""Reasoning Honesty Evaluation Tool — main entry point.

Usage:
    python main.py                          # Run all probes, all stages
    python main.py --stages stage1          # Stage 1 only
    python main.py --stages stage1_stage3   # Stage 1 + stage 3 + gap test
    python main.py --stages all             # Full run (default)
    python main.py --probes copyright-1a legal-3a   # Run specific probes
    python main.py --domains copyright legal        # Run probes for specific domains
    python main.py --classify llm           # Use LLM-assisted classification
    python main.py --model claude-sonnet-4-5-20250929  # Target a specific model
    python main.py --variance 5             # Run each probe N times for variance testing
    python main.py --label my-test          # Label for output files
"""

import argparse
import json
import sys
from pathlib import Path

from config import Config
from probe_runner import ProbeRunner, load_probes
from analyzer import analyze_probe_result
from reporter import save_results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Reasoning Honesty Evaluation Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--stages",
        choices=["stage1", "stage1_stage3", "all"],
        default="all",
        help="Which stages to run (default: all)",
    )
    parser.add_argument(
        "--probes",
        nargs="+",
        help="Run only specific probe IDs (e.g., copyright-1a legal-3a)",
    )
    parser.add_argument(
        "--domains",
        nargs="+",
        help="Run probes for specific domains (e.g., copyright legal)",
    )
    parser.add_argument(
        "--classify",
        choices=["heuristic", "llm"],
        default="heuristic",
        help="Classification mode (default: heuristic)",
    )
    parser.add_argument(
        "--model",
        default="claude-sonnet-4-5-20250929",
        help="Target model ID (default: claude-sonnet-4-5-20250929)",
    )
    parser.add_argument(
        "--classifier-model",
        default="claude-haiku-4-5-20251001",
        help="Classifier model for LLM mode (default: claude-haiku-4-5-20251001)",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.0,
        help="Temperature for probe calls (default: 0.0)",
    )
    parser.add_argument(
        "--variance",
        type=int,
        default=1,
        help="Number of times to run each probe for variance testing (default: 1)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Delay in seconds between API calls (default: 1.0)",
    )
    parser.add_argument(
        "--probes-file",
        default="probes.json",
        help="Path to probe definitions file (default: probes.json)",
    )
    parser.add_argument(
        "--label",
        default=None,
        help="Label for output files",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print probe plan without making API calls",
    )
    return parser.parse_args()


def filter_probes(
    probes: list[dict],
    probe_ids: list[str] | None = None,
    domains: list[str] | None = None,
) -> list[dict]:
    """Filter probes by ID or domain."""
    filtered = probes
    if probe_ids:
        filtered = [p for p in filtered if p["id"] in probe_ids]
    if domains:
        filtered = [p for p in filtered if p["domain"] in domains]
    return filtered


def main() -> None:
    args = parse_args()

    # Build config
    config = Config(
        target_model=args.model,
        classifier_model=args.classifier_model,
        temperature=args.temperature,
        classification_mode=args.classify,
        inter_call_delay=args.delay,
        probes_file=args.probes_file,
    )

    # Load probes
    probes = load_probes(config.probes_file)
    probes = filter_probes(probes, args.probes, args.domains)

    if not probes:
        print("No probes match the specified filters.")
        sys.exit(1)

    print(f"Evaluation Configuration:")
    print(f"  Model:          {config.target_model}")
    print(f"  Stages:         {args.stages}")
    print(f"  Classification: {config.classification_mode}")
    print(f"  Temperature:    {config.temperature}")
    print(f"  Probes:         {len(probes)}")
    print(f"  Variance runs:  {args.variance}")
    print()

    if args.dry_run:
        print("DRY RUN — probes that would execute:")
        for p in probes:
            print(f"  [{p['domain']}] {p['id']}: {p['stage1_prompt'][:60]}...")
        sys.exit(0)

    # Validate API key
    config.validate()

    # Run
    runner = ProbeRunner(config)
    all_results = []

    for run_idx in range(args.variance):
        if args.variance > 1:
            print(f"\n{'='*60}")
            print(f"Variance run {run_idx + 1}/{args.variance}")
            print(f"{'='*60}")

        raw_results = runner.run_all_probes(probes, run_stages=args.stages)

        # Analyze each result
        for raw in raw_results:
            result_dict = raw.to_dict()
            analyzed = analyze_probe_result(result_dict, config)
            if args.variance > 1:
                analyzed["variance_run"] = run_idx + 1
            all_results.append(analyzed)

    # Save results
    label = args.label
    if args.variance > 1 and not label:
        label = f"variance_{args.variance}"

    saved = save_results(
        all_results,
        config.target_model,
        config.results_dir,
        config.reports_dir,
        run_label=label,
    )

    print(f"\nResults saved:")
    print(f"  JSON:     {saved['json_file']}")
    print(f"  Markdown: {saved['markdown_file']}")

    # Print quick summary
    deflections = sum(
        1 for r in all_results
        if r.get("stage1", {}).get("classification") == "deflection"
    )
    gaps = sum(
        1 for r in all_results
        if r.get("capability_gap", {}).get("gap_confirmed")
    )
    adr = sum(
        1 for r in all_results
        if r.get("differential", {}).get("adr_evidence")
    )
    print(f"\nQuick Summary:")
    print(f"  Total probe runs:    {len(all_results)}")
    print(f"  Deflections:         {deflections}")
    print(f"  Capability gaps:     {gaps}")
    print(f"  ADR evidence:        {adr}")


if __name__ == "__main__":
    main()
