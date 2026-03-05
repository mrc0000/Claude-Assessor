"""
main.py — CLI entrypoint for the reasoning honesty evaluation tool.

Usage examples:

  # Run all probes, heuristic classification only
  python main.py

  # Run specific probes
  python main.py --probes copyright-1a legal-3b

  # Run with LLM-assisted classification (Phase 2)
  python main.py --llm-classifier

  # Variance testing (5 runs per probe, temperature 0.7)
  python main.py --n-runs 5

  # Target a different model
  python main.py --model claude-opus-4-6

  # Analyze existing raw results without re-running probes
  python main.py --analyze-only results/20260304T120000_r0_copyright-1a_raw.json
"""

import argparse
import glob
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import config
import probe_runner as runner_mod
import analyzer
import reporter


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Reasoning Honesty Evaluation Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument(
        "--probes",
        nargs="*",
        metavar="ID",
        help="Probe IDs to run (default: all probes in probes.json)",
    )
    p.add_argument(
        "--model",
        default=config.TARGET_MODEL,
        help=f"Target model (default: {config.TARGET_MODEL})",
    )
    p.add_argument(
        "--n-runs",
        type=int,
        default=config.N_RUNS,
        metavar="N",
        help=f"Number of runs per probe for variance testing (default: {config.N_RUNS})",
    )
    p.add_argument(
        "--temperature",
        type=float,
        default=None,
        help=(
            "Sampling temperature — defaults to 0.0 for n=1, "
            f"{config.TEMPERATURE_VARIANCE} for n>1"
        ),
    )
    p.add_argument(
        "--llm-classifier",
        action="store_true",
        help="Enable LLM-assisted pattern classification (Phase 2; uses additional API calls)",
    )
    p.add_argument(
        "--analyze-only",
        nargs="+",
        metavar="FILE",
        help=(
            "Skip probe execution; load these raw JSON result files and "
            "run only the analysis + reporting pipeline"
        ),
    )
    p.add_argument(
        "--report-only",
        nargs="+",
        metavar="FILE",
        help=(
            "Skip probe execution and analysis; load these classified JSON result "
            "files and re-generate reports only"
        ),
    )
    return p.parse_args()


def load_raw_results(files: list[str]) -> list[dict]:
    results = []
    for f in files:
        with open(f) as fh:
            data = json.load(fh)
            if isinstance(data, list):
                results.extend(data)
            else:
                results.append(data)
    return results


def save_classified_results(classified: list[dict], run_id: str) -> str:
    out_dir = Path(config.RESULTS_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{run_id}_classified.json"
    with open(path, "w") as f:
        json.dump(classified, f, indent=2)
    return str(path)


def main() -> int:
    args = parse_args()

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    use_llm = args.llm_classifier

    # ------------------------------------------------------------------
    # Mode 1: report-only (re-generate reports from classified results)
    # ------------------------------------------------------------------
    if args.report_only:
        print(f"Loading classified results from {len(args.report_only)} file(s)…")
        classified = load_raw_results(args.report_only)
        json_path, md_path = reporter.generate_report(classified, run_id=run_id)
        print(f"\nReports generated:")
        print(f"  JSON: {json_path}")
        print(f"  Markdown: {md_path}")
        return 0

    # ------------------------------------------------------------------
    # Mode 2: analyze-only (load raw results, skip probe execution)
    # ------------------------------------------------------------------
    if args.analyze_only:
        print(f"Loading raw results from {len(args.analyze_only)} file(s)…")
        raw_results = load_raw_results(args.analyze_only)
    else:
        # ------------------------------------------------------------------
        # Mode 3: full run (execute probes + analyze + report)
        # ------------------------------------------------------------------
        print(f"Starting evaluation run: {run_id}")
        print(f"  Model:       {args.model}")
        print(f"  N runs:      {args.n_runs}")
        print(f"  LLM classifier: {use_llm}")
        if args.probes:
            print(f"  Probes:      {', '.join(args.probes)}")
        else:
            print("  Probes:      all")
        print()

        raw_results = runner_mod.run_all(
            probe_ids=args.probes or None,
            model=args.model,
            n_runs=args.n_runs,
            temperature=args.temperature,
        )

    # ------------------------------------------------------------------
    # Analysis
    # ------------------------------------------------------------------
    print(f"\nAnalyzing {len(raw_results)} result(s)…")
    classified = analyzer.analyze_all(raw_results, use_llm=use_llm)

    classified_path = save_classified_results(classified, run_id)
    print(f"  Classified results: {classified_path}")

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------
    print("\nGenerating reports…")
    json_path, md_path = reporter.generate_report(classified, run_id=run_id)

    print(f"\n{'='*60}")
    print("Evaluation complete.")
    print(f"  JSON report:  {json_path}")
    print(f"  Markdown:     {md_path}")
    print(f"{'='*60}\n")

    # Print a brief summary to stdout
    _print_summary(classified)

    return 0


def _print_summary(classified: list[dict]) -> None:
    """Print a brief console summary of results."""
    from collections import defaultdict

    by_domain: dict[str, list] = defaultdict(list)
    for r in classified:
        by_domain[r["domain"]].append(r)

    print("Quick summary:")
    print(f"  {'Domain':<12} {'Probes':>6} {'Deflections':>11} {'Gaps':>5} {'Avg ADR':>8}")
    print(f"  {'-'*48}")
    for domain in sorted(by_domain):
        results = by_domain[domain]
        n = len(results)
        defs = sum(
            1 for r in results
            if r["stage1"]["classification"] in ("deflection", "partial")
        )
        gaps = sum(1 for r in results if r["capability_gap"]["gap_confirmed"])
        adr_scores = [r["differential"]["total_score"] for r in results]
        avg_adr = sum(adr_scores) / len(adr_scores) if adr_scores else 0.0
        print(f"  {domain.capitalize():<12} {n:>6} {defs:>11} {gaps:>5} {avg_adr:>8.1f}")
    print()


if __name__ == "__main__":
    sys.exit(main())
