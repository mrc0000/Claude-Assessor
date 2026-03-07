#!/usr/bin/env python3
"""Report management utility — organizes, cleans, and regenerates reports.

Maintains a clean directory structure:

    reports/
    ├── {model-label}/              # Per-model folders
    │   ├── {suite}.html            # Per-suite interactive reports
    │   └── comparative.html/json   # Cross-suite comparative report
    ├── cross-model/                # Cross-model comparison
    │   └── comparison.html/json
    └── archive/                    # Timestamped historical reports

Usage:
    python manage_reports.py organize     # Organize current reports into model folders
    python manage_reports.py clean        # Archive old/intermediate reports
    python manage_reports.py regenerate   # Regenerate all reports from current result data
    python manage_reports.py status       # Show current report state
"""

import argparse
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

# Map model IDs to clean folder names
MODEL_FOLDER_NAMES: dict[str, str] = {
    "claude-haiku-4-5-20251001": "haiku-4.5",
    "claude-sonnet-4-20250514": "sonnet-4",
    "claude-sonnet-4-6": "sonnet-4.6",
}

# Map suite identifiers in filenames to clean suite names
SUITE_NAMES: dict[str, str] = {
    "general": "general",
    "cyber-insider": "cyber-insider",
    "medical-deep": "medical-deep",
    "legal-deep": "legal-deep",
    "financial-deep": "financial-deep",
    "chemistry-deep": "chemistry-deep",
    "reasoning-honesty": "reasoning-honesty",
}

BASE = Path(__file__).parent
REPORTS_DIR = BASE / "reports"
RESULTS_DIR = BASE / "results"
ARCHIVE_DIR = REPORTS_DIR / "archive"


def get_model_folder(model_id: str) -> str:
    """Get clean folder name for a model ID."""
    return MODEL_FOLDER_NAMES.get(model_id, model_id.replace("/", "_"))


def detect_model_from_result_file(filename: str) -> str | None:
    """Try to determine which model a result file belongs to by reading its meta."""
    path = RESULTS_DIR / filename
    if not path.exists():
        return None
    try:
        with open(path) as f:
            data = json.load(f)
        return data.get("meta", {}).get("model")
    except (json.JSONDecodeError, OSError):
        return None


def detect_suite_from_filename(filename: str) -> str | None:
    """Extract suite name from a report/result filename."""
    for suite_key in SUITE_NAMES:
        if suite_key in filename:
            return suite_key
    return None


def _find_current_result_files() -> dict[str, dict[str, str]]:
    """Find the current (most recent) result file for each model+suite.

    Returns: {model_id: {suite: filepath}}
    """
    model_suites: dict[str, dict[str, str]] = {}

    for f in sorted(RESULTS_DIR.glob("run_*.json")):
        try:
            with open(f) as fp:
                data = json.load(fp)
            model_id = data.get("meta", {}).get("model", "unknown")
            count = len(data.get("probe_results", []))
        except (json.JSONDecodeError, OSError):
            continue

        suite = detect_suite_from_filename(f.name)
        if not suite:
            continue

        if model_id not in model_suites:
            model_suites[model_id] = {}

        # Keep the file with the most results (most complete)
        existing = model_suites[model_id].get(suite)
        if existing:
            try:
                with open(existing) as fp:
                    existing_count = len(json.load(fp).get("probe_results", []))
                if count <= existing_count:
                    continue
            except (json.JSONDecodeError, OSError):
                pass

        model_suites[model_id][suite] = str(f)

    return model_suites


def cmd_status(args):
    """Show current report organization status."""
    print("=== Result Files ===\n")
    model_suites = _find_current_result_files()
    for model_id in sorted(model_suites.keys()):
        folder = get_model_folder(model_id)
        suites = model_suites[model_id]
        total = sum(
            len(json.load(open(p)).get("probe_results", []))
            for p in suites.values()
        )
        print(f"  {folder} ({model_id})")
        for suite, path in sorted(suites.items()):
            with open(path) as f:
                count = len(json.load(f).get("probe_results", []))
            print(f"    {suite:25s} {count:3d} results  ({Path(path).name})")
        print(f"    {'TOTAL':25s} {total:3d}")
        print()

    print("=== Reports Directory ===\n")
    # Count files in each subdirectory
    for item in sorted(REPORTS_DIR.iterdir()):
        if item.is_dir():
            count = sum(1 for _ in item.rglob("*") if _.is_file())
            print(f"  {item.name:30s} {count:3d} files")
        elif item.is_file() and item.name != ".gitkeep":
            print(f"  {item.name}")
    print()

    # Check for model-specific folders
    for model_id in sorted(model_suites.keys()):
        folder = get_model_folder(model_id)
        folder_path = REPORTS_DIR / folder
        if folder_path.exists():
            files = list(folder_path.glob("*"))
            print(f"  {folder}/ — {len(files)} files")
        else:
            print(f"  {folder}/ — NOT CREATED")


def cmd_organize(args):
    """Organize reports into model-specific folders."""
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

    # Find current result files to know which models exist
    model_suites = _find_current_result_files()

    # Create model folders
    for model_id in model_suites:
        folder = get_model_folder(model_id)
        (REPORTS_DIR / folder).mkdir(parents=True, exist_ok=True)

    # Create cross-model folder
    (REPORTS_DIR / "cross-model").mkdir(parents=True, exist_ok=True)

    moved_count = 0
    kept_count = 0

    # Identify and organize current reports in the flat reports/ directory
    for f in sorted(REPORTS_DIR.glob("*")):
        if f.is_dir():
            continue
        if f.name == ".gitkeep":
            continue

        name = f.name

        # Cross-model reports
        if name.startswith("cross_model"):
            if "test" in name:
                # Test file — archive it
                shutil.move(str(f), str(ARCHIVE_DIR / name))
                moved_count += 1
                continue
            dest = REPORTS_DIR / "cross-model" / name
            shutil.move(str(f), str(dest))
            kept_count += 1
            continue

        # Identify which model this report belongs to
        target_model = None
        target_suite = None

        # LLM-reclassified reports (Haiku/Sonnet 4)
        if "llm_haiku" in name or "llm-reclassified" in name:
            # Check if it's a Haiku or Sonnet report
            if "haiku" in name:
                target_model = "claude-haiku-4-5-20251001"
            else:
                # Need to check the corresponding result file
                # Match pattern: report_llm-reclassified_run_{suite}_v{N}_{date1}_{date2}
                match = re.search(r"run_(.+?)_v\d+_(\d{8}_\d{6})_(\d{8}_\d{6})", name)
                if match:
                    suite_part = match.group(1)
                    result_name = f"run_llm-reclassified_run_{suite_part}_v{name.split('_v')[1].split('_')[0]}_{match.group(2)}_{match.group(3)}.json"
                    model = detect_model_from_result_file(result_name)
                    if model:
                        target_model = model
        elif "llm_sonnet" in name:
            target_model = "claude-sonnet-4-20250514"

        # Direct Sonnet 4.6 reports (no llm-reclassified prefix)
        if target_model is None:
            # These are from run_full_suite.py for Sonnet 4.6
            suite = detect_suite_from_filename(name)
            if suite and name.startswith("report_"):
                target_model = "claude-sonnet-4-6"

        # Comparative reports
        if name.startswith("comparative_"):
            if "llm_haiku" in name:
                target_model = "claude-haiku-4-5-20251001"
                target_suite = "_comparative"
            elif "llm_sonnet" in name:
                target_model = "claude-sonnet-4-20250514"
                target_suite = "_comparative"
            elif "full-suite" in name:
                target_model = "claude-sonnet-4-6"
                target_suite = "_comparative"

        # Determine destination
        if target_model:
            folder = get_model_folder(target_model)
            suite = detect_suite_from_filename(name) if target_suite is None else None

            if target_suite == "_comparative":
                # Comparative — check if it's the final one (keep latest, archive rest)
                dest = REPORTS_DIR / folder
            elif suite:
                dest = REPORTS_DIR / folder
            else:
                dest = ARCHIVE_DIR

            shutil.move(str(f), str(dest / name))
            kept_count += 1
        else:
            # Unknown — archive
            shutil.move(str(f), str(ARCHIVE_DIR / name))
            moved_count += 1

    print(f"Organized {kept_count} reports into model folders")
    print(f"Archived {moved_count} unidentified/intermediate reports")

    # Now clean up each model folder — keep only the latest of each type
    for model_id in model_suites:
        folder = get_model_folder(model_id)
        folder_path = REPORTS_DIR / folder
        _deduplicate_model_folder(folder_path)


def _deduplicate_model_folder(folder_path: Path):
    """Keep only the latest report for each suite in a model folder.

    For comparative reports, keep only the one with the most data.
    """
    if not folder_path.exists():
        return

    # Group files by suite and type
    groups: dict[str, list[Path]] = {}
    for f in sorted(folder_path.glob("*")):
        if f.is_dir() or f.suffix not in (".html", ".json", ".md"):
            continue

        suite = detect_suite_from_filename(f.name)
        key = f"{suite or 'other'}_{f.suffix}"

        if "comparative" in f.name:
            key = f"comparative_{f.suffix}"

        if key not in groups:
            groups[key] = []
        groups[key].append(f)

    # For each group, keep the latest (by modification time), archive the rest
    archived = 0
    for key, files in groups.items():
        if len(files) <= 1:
            continue
        files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        for old_file in files[1:]:
            shutil.move(str(old_file), str(ARCHIVE_DIR / old_file.name))
            archived += 1

    if archived:
        print(f"  {folder_path.name}/: archived {archived} duplicate(s)")


def cmd_clean(args):
    """Archive intermediate and duplicate reports."""
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

    # Move intermediate comparative reports (Sonnet 4.6 generates one per suite)
    intermediate_count = 0
    comparatives = sorted(REPORTS_DIR.glob("comparative_full-suite_*.json"))
    if len(comparatives) > 1:
        # Keep only the latest
        for old in comparatives[:-1]:
            html = old.with_suffix(".html")
            shutil.move(str(old), str(ARCHIVE_DIR / old.name))
            if html.exists():
                shutil.move(str(html), str(ARCHIVE_DIR / html.name))
            intermediate_count += 1

    # Move test reports
    for f in REPORTS_DIR.glob("*test*"):
        if f.is_file():
            shutil.move(str(f), str(ARCHIVE_DIR / f.name))
            intermediate_count += 1

    print(f"Archived {intermediate_count} intermediate/test reports")


def cmd_regenerate(args):
    """Regenerate all reports from current result data."""
    from html_report import save_html_report
    from comparative_html_report import save_comparative_report
    from cross_model_report import (
        load_and_group_results,
        save_cross_model_report,
        get_model_label,
    )
    from analyzer import load_eval_config

    load_eval_config()

    model_suites = _find_current_result_files()

    for model_id in sorted(model_suites.keys()):
        folder_name = get_model_folder(model_id)
        label = get_model_label(model_id)
        folder_path = REPORTS_DIR / folder_name
        folder_path.mkdir(parents=True, exist_ok=True)

        print(f"\n{label} ({model_id})")
        all_results = []

        for suite, result_path in sorted(model_suites[model_id].items()):
            with open(result_path) as f:
                data = json.load(f)
            results = data.get("probe_results", [])
            all_results.extend(results)

            # Generate per-suite report
            html_file = save_html_report(
                results, model_id, str(folder_path),
                run_label=suite,
            )
            print(f"  {suite}: {html_file}")

        # Generate comparative report for this model
        if all_results:
            comp_path = save_comparative_report(
                all_results, model=label,
                reports_dir=str(folder_path),
                label="comparative",
            )
            print(f"  comparative: {comp_path}")

    # Generate cross-model report
    print("\nCross-model comparison:")
    model_results = load_and_group_results()
    cross_model_dir = str(REPORTS_DIR / "cross-model")
    paths = save_cross_model_report(
        model_results,
        reports_dir=cross_model_dir,
        label="comparison",
    )
    print(f"  HTML: {paths['html_file']}")
    print(f"  JSON: {paths['json_file']}")


def main():
    parser = argparse.ArgumentParser(
        description="Report management utility",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status", help="Show current report state")
    sub.add_parser("organize", help="Organize reports into model folders")
    sub.add_parser("clean", help="Archive intermediate/duplicate reports")
    sub.add_parser("regenerate", help="Regenerate all reports from result data")

    args = parser.parse_args()

    if args.command == "status":
        cmd_status(args)
    elif args.command == "organize":
        cmd_organize(args)
    elif args.command == "clean":
        cmd_clean(args)
    elif args.command == "regenerate":
        cmd_regenerate(args)


if __name__ == "__main__":
    main()
