#!/usr/bin/env python3
"""Run the full multi-domain reasoning honesty evaluation suite.

Executes all probe suites with variance testing and generates
individual reports plus a final comparative analysis.

Usage:
    python run_full_suite.py                           # Full run, all suites
    python run_full_suite.py --suites medical legal    # Specific suites
    python run_full_suite.py --variance 3              # 3 runs per probe
    python run_full_suite.py --model claude-haiku-4-5-20251001  # Target model
    python run_full_suite.py --mock                    # Mock mode for testing
"""

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

from config import Config
from probe_runner import ProbeRunner, load_probes, filter_probes
from analyzer import analyze_probe_result, load_eval_config, get_eval_config_snapshot
from reporter import save_results
from html_report import save_html_report
from comparative_analysis import generate_comparative_analysis
from comparative_html_report import save_comparative_report


# ── Suite definitions ──
SUITES = {
    "general": {
        "file": "probes.json",
        "label": "general",
        "description": "Primary 16-probe multi-domain suite (copyright, cyber, chem, legal, financial, medical)",
    },
    "cyber-insider": {
        "file": "probes_cyber_insider.json",
        "label": "cyber-insider",
        "description": "6-probe cybersecurity insider credential injection suite",
    },
    "medical": {
        "file": "probes_medical_deep.json",
        "label": "medical-deep",
        "description": "6-probe deep medical reasoning honesty suite",
    },
    "legal": {
        "file": "probes_legal_deep.json",
        "label": "legal-deep",
        "description": "6-probe deep legal reasoning honesty suite",
    },
    "financial": {
        "file": "probes_financial_deep.json",
        "label": "financial-deep",
        "description": "6-probe deep financial reasoning honesty suite",
    },
    "chemistry": {
        "file": "probes_chemistry_deep.json",
        "label": "chemistry-deep",
        "description": "6-probe deep chemistry reasoning honesty suite",
    },
    "reasoning": {
        "file": "probes_reasoning_honesty.json",
        "label": "reasoning-honesty",
        "description": "6-probe meta-cognitive reasoning honesty suite",
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Full multi-domain reasoning honesty evaluation suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--suites", nargs="+", choices=list(SUITES.keys()) + ["all"],
        default=["all"],
        help="Which suites to run (default: all)",
    )
    parser.add_argument("--model", default="claude-haiku-4-5-20251001")
    parser.add_argument("--classifier-model", default="claude-haiku-4-5-20251001")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--variance", type=int, default=3, help="Variance runs per probe")
    parser.add_argument("--delay", type=float, default=1.0)
    parser.add_argument("--stages", choices=["stage1", "stage1_stage3", "all"], default="all")
    parser.add_argument("--classify", choices=["heuristic", "llm"], default="llm")
    parser.add_argument("--mock", action="store_true")
    parser.add_argument(
        "--probes", nargs="+",
        help="Run only specific probe IDs (e.g., med-dosage-1 fin-tax-1). Works across all suites.",
    )
    parser.add_argument(
        "--domains", nargs="+",
        help="Run only probes for specific domains (e.g., medical legal). Works across all suites.",
    )
    parser.add_argument(
        "--max-retries", type=int, default=4,
        help="Max retries on rate limit / overload (default: 4)",
    )
    parser.add_argument(
        "--retry-base-delay", type=float, default=2.0,
        help="Base delay for exponential backoff in seconds (default: 2.0)",
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-comparative", action="store_true", help="Skip final comparative report")
    parser.add_argument(
        "--continue-on-suite-failure", action="store_true", default=True,
        help="Continue to next suite if one suite fails entirely (default: True)",
    )
    parser.add_argument(
        "--resume-partial", action="store_true",
        help="Resume from partial results files left by interrupted runs. "
             "Skips suites that already have a _partial_{label}.json with all variance runs.",
    )
    parser.add_argument(
        "--report-only", action="store_true",
        help="Skip running probes. Generate comparative report from existing "
             "_combined_all_suites.json results file.",
    )
    parser.add_argument(
        "--report-label", default="full-suite",
        help="Label for comparative report output files (default: full-suite)",
    )
    return parser.parse_args()


def run_suite(
    suite_key: str,
    suite_def: dict,
    runner,
    config: Config,
    args: argparse.Namespace,
) -> list[dict]:
    """Run a single probe suite and save results."""
    print(f"\n{'='*70}")
    print(f"  SUITE: {suite_key} — {suite_def['description']}")
    print(f"{'='*70}\n")

    probes = load_probes(suite_def["file"])

    # Apply probe-level filters
    probes = filter_probes(probes, getattr(args, 'probes', None), getattr(args, 'domains', None))
    if not probes:
        print(f"  No probes match filters for suite '{suite_key}', skipping.")
        return []

    print(f"  Probes: {len(probes)}")
    print(f"  Variance: {args.variance}")
    print(f"  Total runs: {len(probes) * args.variance}")
    print()

    if args.dry_run:
        for p in probes:
            print(f"  [{p['domain']}] {p['id']}: {p['stage1_prompt'][:60]}...")
        return []

    all_results = []

    # Incremental save: flush results after each variance run so a session
    # drop never loses more than one variance run worth of work.
    label = suite_def["label"]
    if args.variance > 1:
        label += f"_v{args.variance}"
    partial_file = Path(config.results_dir) / f"_partial_{label}.json"

    # Resume from partial results if available
    start_variance = 0
    if getattr(args, 'resume_partial', False) and partial_file.exists():
        partial_data = json.loads(partial_file.read_text())
        if partial_data:
            max_variance = max(r.get("variance_run", 1) for r in partial_data)
            expected_per_run = len(probes)
            count_at_max = sum(1 for r in partial_data if r.get("variance_run", 1) == max_variance)
            if count_at_max == expected_per_run:
                # Last variance run completed fully
                start_variance = max_variance
                all_results = partial_data
                print(f"  [resume] Loaded {len(all_results)} results from partial file "
                      f"(variance 1-{max_variance} complete, resuming at {start_variance + 1})")
            else:
                # Last variance run was incomplete — keep only fully completed runs
                start_variance = max_variance - 1
                all_results = [r for r in partial_data if r.get("variance_run", 1) < max_variance]
                print(f"  [resume] Loaded {len(all_results)} results from partial file "
                      f"(variance 1-{start_variance} complete, re-running {start_variance + 1})")

    if start_variance >= args.variance:
        print(f"  [resume] All {args.variance} variance runs already complete, skipping suite.")
    else:
        for run_idx in range(start_variance, args.variance):
            if args.variance > 1:
                print(f"\n  --- Variance run {run_idx + 1}/{args.variance} ---")

            raw_results = runner.run_all_probes(probes, run_stages=args.stages)

            for raw in raw_results:
                result_dict = raw.to_dict()
                analyzed = analyze_probe_result(result_dict, config)
                if args.variance > 1:
                    analyzed["variance_run"] = run_idx + 1
                analyzed["_suite"] = suite_key
                all_results.append(analyzed)

            # Flush to disk after each variance run
            partial_file.write_text(json.dumps(all_results, indent=2, default=str))
            print(f"  [saved] {len(all_results)} results flushed to {partial_file.name}")

    # Final save (replaces partial with timestamped files)
    saved = save_results(
        all_results, config.target_model,
        config.results_dir, config.reports_dir, run_label=label,
    )

    # Clean up partial file now that final save succeeded
    if partial_file.exists():
        partial_file.unlink()
    html_file = save_html_report(
        all_results, config.target_model,
        config.reports_dir, run_label=label,
    )

    print(f"\n  Suite '{suite_key}' complete:")
    print(f"    JSON:     {saved['json_file']}")
    print(f"    Markdown: {saved['markdown_file']}")
    print(f"    HTML:     {html_file}")

    deflections = sum(1 for r in all_results if r.get("stage1", {}).get("classification") == "deflection")
    discriminatory = sum(1 for r in all_results if r.get("differential", {}).get("verdict") == "discriminatory")
    gaps = sum(1 for r in all_results if r.get("capability_gap", {}).get("gap_confirmed"))
    print(f"    Deflections: {deflections}/{len(all_results)}")
    print(f"    Discriminatory: {discriminatory}/{len(all_results)}")
    print(f"    Capability gaps: {gaps}/{len(all_results)}")

    return all_results


def report_only(args) -> None:
    """Generate comparative report from existing combined results file."""
    config = Config(target_model=args.model)
    combined_file = Path(config.results_dir) / "_combined_all_suites.json"

    if not combined_file.exists():
        print(f"No combined results file found at {combined_file}")
        print("Run suites first, or check that results/_combined_all_suites.json exists.")
        sys.exit(1)

    all_results = json.loads(combined_file.read_text())
    suites = sorted(set(r.get("_suite", "unknown") for r in all_results))
    print(f"Generating comparative report from {len(all_results)} results")
    print(f"  Suites: {', '.join(suites)}")

    load_eval_config()

    comp_path = save_comparative_report(
        all_results, model=args.model, label=args.report_label,
    )
    print(f"  Comparative HTML: {comp_path}")
    print(f"  Comparative JSON: {comp_path.replace('.html', '.json')}")

    analysis = generate_comparative_analysis(all_results)
    gs = analysis["global_summary"]
    print(f"\n  === COMPARATIVE SUMMARY ===")
    print(f"  Domains tested:    {gs['total_domains']}")
    print(f"  Deflection rate:   {gs['deflection_rate']}%")
    print(f"  Full assist rate:  {gs['full_assist_rate']}%")
    print(f"  Discriminatory:    {gs['discriminatory_rate']}%")
    print(f"  Tone modulated:    {gs['tone_modulated_rate']}%")
    print(f"  Consistent:        {gs['consistent_rate']}%")
    print(f"  Capability gaps:   {gs['total_capability_gaps']}")
    print(f"  Avg concern ratio: {gs['avg_concern_ratio']}")

    for domain, ds in sorted(analysis["domain_stats"].items()):
        print(f"  {domain:15s}  deflect={ds['deflection_rate']:5.1f}%  "
              f"full={ds['full_assist_rate']:5.1f}%  "
              f"discrim={ds['discriminatory_rate']:5.1f}%  "
              f"concern={ds['avg_concern_ratio']:.3f}  "
              f"gaps={ds['gaps_confirmed']}")


def main():
    args = parse_args()

    if args.report_only:
        report_only(args)
        return

    # Determine which suites to run
    if "all" in args.suites:
        suites_to_run = list(SUITES.keys())
    else:
        suites_to_run = args.suites

    # Load eval config
    load_eval_config()
    eval_snap = get_eval_config_snapshot()

    config = Config(
        target_model=args.model,
        classifier_model=args.classifier_model,
        temperature=args.temperature,
        classification_mode=args.classify,
        inter_call_delay=args.delay,
        max_retries=args.max_retries,
        retry_base_delay=args.retry_base_delay,
    )

    print("Full Suite Evaluation Configuration:")
    print(f"  Model:          {config.target_model}")
    print(f"  Stages:         {args.stages}")
    print(f"  Classification: {config.classification_mode}")
    print(f"  Temperature:    {config.temperature}")
    print(f"  Variance:       {args.variance}")
    print(f"  Suites:         {', '.join(suites_to_run)}")
    print(f"  Eval config:    v{eval_snap['config_version']}")

    total_probes = sum(
        len(load_probes(SUITES[s]["file"])) for s in suites_to_run
    )
    total_runs = total_probes * args.variance
    print(f"  Total probes:   {total_probes}")
    print(f"  Total runs:     {total_runs}")

    if args.dry_run:
        print("\nDRY RUN — listing all probes:\n")
        for suite_key in suites_to_run:
            run_suite(suite_key, SUITES[suite_key], None, config, args)
        sys.exit(0)

    # Initialize runner
    if args.mock:
        from mock_runner import MockProbeRunner
        runner = MockProbeRunner(config)
        print("\nMOCK MODE — using simulated responses\n")
    else:
        config.validate()
        runner = ProbeRunner(config)

    # Persistent combined results file — survives across sessions.
    # Each suite appends its results here so the comparative analysis
    # can always see the full picture even if we run one suite at a time.
    combined_file = Path(config.results_dir) / "_combined_all_suites.json"
    all_combined_results = []
    if combined_file.exists():
        all_combined_results = json.loads(combined_file.read_text())
        existing_suites = set(r.get("_suite", "") for r in all_combined_results)
        print(f"  [combined] Loaded {len(all_combined_results)} existing results "
              f"from {', '.join(sorted(existing_suites))}")

    suite_failures = []
    suite_start = time.time()

    for suite_key in suites_to_run:
        # Skip suites already in the combined file (unless re-running intentionally)
        existing_for_suite = [r for r in all_combined_results if r.get("_suite") == suite_key]
        if existing_for_suite and not getattr(args, 'resume_partial', False):
            print(f"\n  [combined] Suite '{suite_key}' already has {len(existing_for_suite)} "
                  f"results in combined file, skipping. Use --resume-partial to re-run.")
            continue

        try:
            suite_results = run_suite(
                suite_key, SUITES[suite_key], runner, config, args
            )
            # Only add results that have actual responses (skip empty/failed probes)
            valid_results = [r for r in suite_results if r.get("stage1", {}).get("response")]
            if not valid_results:
                print(f"  [combined] Suite '{suite_key}' produced no valid results, skipping combined update.")
                continue
            # Remove any old results for this suite before appending fresh ones
            all_combined_results = [r for r in all_combined_results if r.get("_suite") != suite_key]
            all_combined_results.extend(valid_results)
            # Flush combined file after each suite
            combined_file.write_text(json.dumps(all_combined_results, indent=2, default=str))
            print(f"  [combined] {len(all_combined_results)} total results saved to {combined_file.name}")
        except Exception as exc:
            print(f"\n  [SUITE FAILURE] Suite '{suite_key}' failed: {exc}")
            suite_failures.append({"suite": suite_key, "error": str(exc)})
            if not args.continue_on_suite_failure:
                raise

    elapsed = time.time() - suite_start
    print(f"\n{'='*70}")
    print(f"  ALL SUITES COMPLETE")
    print(f"  Total time: {elapsed:.1f}s")
    print(f"  Total probe runs: {len(all_combined_results)}")
    if suite_failures:
        print(f"  Suite failures: {len(suite_failures)} — {', '.join(f['suite'] for f in suite_failures)}")
    print(f"{'='*70}")

    # Generate comparative analysis
    if not args.skip_comparative and all_combined_results:
        print("\nGenerating comparative analysis...")
        comp_path = save_comparative_report(
            all_combined_results,
            model=config.target_model,
            label="full-suite",
        )
        print(f"  Comparative HTML: {comp_path}")
        print(f"  Comparative JSON: {comp_path.replace('.html', '.json')}")

        # Quick comparative summary
        analysis = generate_comparative_analysis(all_combined_results)
        gs = analysis["global_summary"]
        print(f"\n  === COMPARATIVE SUMMARY ===")
        print(f"  Domains tested:    {gs['total_domains']}")
        print(f"  Deflection rate:   {gs['deflection_rate']}%")
        print(f"  Full assist rate:  {gs['full_assist_rate']}%")
        print(f"  Discriminatory:    {gs['discriminatory_rate']}%")
        print(f"  Tone modulated:    {gs['tone_modulated_rate']}%")
        print(f"  Consistent:        {gs['consistent_rate']}%")
        print(f"  Capability gaps:   {gs['total_capability_gaps']}")
        print(f"  Avg concern ratio: {gs['avg_concern_ratio']}")

        # Per-domain breakdown
        print(f"\n  --- Domain Breakdown ---")
        for domain, ds in sorted(analysis["domain_stats"].items()):
            print(f"  {domain:15s}  deflect={ds['deflection_rate']:5.1f}%  "
                  f"full={ds['full_assist_rate']:5.1f}%  "
                  f"discrim={ds['discriminatory_rate']:5.1f}%  "
                  f"concern={ds['avg_concern_ratio']:.3f}  "
                  f"gaps={ds['gaps_confirmed']}")


if __name__ == "__main__":
    main()
