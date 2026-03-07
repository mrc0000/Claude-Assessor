#!/usr/bin/env python3
"""Reasoning Honesty Evaluation Tool — single-file entry point.

NOTE: For multi-suite runs with incremental save, resume, and combined
results, use run_full_suite.py instead. This entry point is kept for
quick single-file runs and backward compatibility.

Usage:
    python main.py                          # Run all probes, all stages
    python main.py --stages stage1          # Stage 1 only
    python main.py --probes copyright-1a legal-3a   # Run specific probes
    python main.py --domains copyright legal        # Run probes for specific domains
    python main.py --variance 5             # Run each probe N times
    python main.py --mock                   # Mock mode for testing
"""

import argparse
import json
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load .env from the reasoning-eval directory
load_dotenv(Path(__file__).parent / ".env")

from config import Config
from probe_runner import ProbeRunner, load_probes, filter_probes
from analyzer import analyze_probe_result, load_eval_config, get_eval_config_snapshot
from reporter import save_results
from html_report import save_html_report


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
        default="llm",
        help="Classification mode (default: llm)",
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
        "--eval-config",
        default=None,
        help="Path to versioned eval config (default: eval_config.json in project dir)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print probe plan without making API calls",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use mock responses instead of calling the API (for demo/testing)",
    )
    parser.add_argument(
        "--max-retries", type=int, default=4,
        help="Max retries on rate limit / overload (default: 4)",
    )
    parser.add_argument(
        "--retry-base-delay", type=float, default=2.0,
        help="Base delay for exponential backoff in seconds (default: 2.0)",
    )
    return parser.parse_args()


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
        max_retries=args.max_retries,
        retry_base_delay=args.retry_base_delay,
    )

    # Load versioned eval config (patterns, thresholds, prompts)
    eval_cfg = load_eval_config(args.eval_config)
    eval_snapshot = get_eval_config_snapshot()

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
    print(f"  Eval config:    v{eval_snapshot['config_version']} "
          f"(patterns v{eval_snapshot['patterns_version']}, "
          f"prompts v{eval_snapshot['prompt_templates_version']})")
    print()

    if args.dry_run:
        print("DRY RUN — probes that would execute:")
        for p in probes:
            print(f"  [{p['domain']}] {p['id']}: {p['stage1_prompt'][:60]}...")
        sys.exit(0)

    # Initialize runner
    if args.mock:
        from mock_runner import MockProbeRunner
        runner = MockProbeRunner(config)
        print("MOCK MODE — using simulated responses\n")
    else:
        config.validate()
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

    # HTML report
    html_file = save_html_report(
        all_results, config.target_model, config.reports_dir, run_label=label,
    )

    print(f"\nResults saved:")
    print(f"  JSON:     {saved['json_file']}")
    print(f"  Markdown: {saved['markdown_file']}")
    print(f"  HTML:     {html_file}")

    # Print quick summary
    deflections = sum(
        1 for r in all_results
        if r.get("stage1", {}).get("classification") == "deflection"
    )
    gaps = sum(
        1 for r in all_results
        if r.get("capability_gap", {}).get("gap_confirmed")
    )
    discriminatory = sum(
        1 for r in all_results
        if r.get("differential", {}).get("verdict") == "discriminatory"
    )
    print(f"\nQuick Summary:")
    print(f"  Total probe runs:    {len(all_results)}")
    print(f"  Deflections:         {deflections}")
    print(f"  Capability gaps:     {gaps}")
    print(f"  Discriminatory:      {discriminatory}")


if __name__ == "__main__":
    main()
