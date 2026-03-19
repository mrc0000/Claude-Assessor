#!/usr/bin/env python3
"""Build script for the Research Findings Explorer webapp.

Reads JSON result files and markdown findings, processes/aggregates data,
and outputs a static webapp to webapp/ that can be served by any HTTP server.

Usage:
    python build_webapp.py              # Build the webapp
    python build_webapp.py --clean      # Clean and rebuild
"""

import argparse
import json
import os
import shutil
import sys
from collections import defaultdict
from pathlib import Path

# Add parent for imports
sys.path.insert(0, str(Path(__file__).parent))

from comparative_analysis import (
    compute_domain_stats,
    compute_pattern_frequency,
    compute_credential_sensitivity,
    compute_capability_gap_analysis,
    compute_variance_baseline,
    compute_verdict_map,
    generate_comparative_analysis,
)
from cross_model_report import (
    MODEL_LABELS,
    get_model_label,
    compute_model_summary,
    compute_cross_model_analysis,
)


BASE_DIR = Path(__file__).parent
RESULTS_DIR = BASE_DIR / "results"
WEBAPP_DIR = BASE_DIR / "webapp"
DATA_DIR = WEBAPP_DIR / "data"


def find_canonical_files() -> list[Path]:
    """Find the 21 canonical v1.6 result files (3 models × 7 suites)."""
    all_v16 = sorted(RESULTS_DIR.glob("run_v1.6-negligible-max-2_*.json"))
    # Exclude intermediate analysis variants
    canonical = [
        f for f in all_v16
        if "keyword-overlap" not in f.name and "no-keyword-scoring" not in f.name
    ]
    return canonical


def load_canonical_results() -> dict[str, list[dict]]:
    """Load canonical results grouped by model ID."""
    model_results: dict[str, list[dict]] = defaultdict(list)
    for fpath in find_canonical_files():
        with open(fpath) as fp:
            data = json.load(fp)
        model_id = data.get("meta", {}).get("model", "unknown")
        for pr in data.get("probe_results", []):
            pr["_source_file"] = fpath.name
            pr["_meta"] = data.get("meta", {})
        model_results[model_id].extend(data.get("probe_results", []))
    return dict(model_results)


def build_summary(model_results: dict[str, list[dict]]) -> dict:
    """Build the summary.json with headline metrics."""
    all_results = []
    for results in model_results.values():
        all_results.extend(results)

    analysis = generate_comparative_analysis(all_results)

    models = {}
    for model_id, results in model_results.items():
        models[model_id] = {
            "label": get_model_label(model_id),
            "summary": compute_model_summary(results),
        }

    return {
        "total_probes": len(all_results),
        "total_models": len(model_results),
        "total_domains": analysis["global_summary"]["total_domains"],
        "models": models,
        "global": analysis["global_summary"],
        "domain_stats": analysis["domain_stats"],
        "pattern_frequency": analysis["pattern_frequency"],
    }


def build_model_data(model_id: str, results: list[dict]) -> dict:
    """Build per-model JSON with full probe results."""
    # Strip heavy _meta from each probe to reduce size
    clean_results = []
    for r in results:
        cr = {k: v for k, v in r.items() if k != "_meta"}
        # Keep source file for reference
        clean_results.append(cr)

    analysis = generate_comparative_analysis(results)
    summary = compute_model_summary(results)

    return {
        "model_id": model_id,
        "label": get_model_label(model_id),
        "summary": summary,
        "domain_stats": analysis["domain_stats"],
        "pattern_frequency": analysis["pattern_frequency"],
        "verdict_map": analysis["verdict_map"],
        "credential_sensitivity": analysis["credential_sensitivity"],
        "capability_gap_analysis": analysis["capability_gap_analysis"],
        "variance_baseline": analysis["variance_baseline"],
        "probe_results": clean_results,
    }


def build_cross_model(model_results: dict[str, list[dict]]) -> dict:
    """Build cross-model comparison data."""
    return compute_cross_model_analysis(model_results)


def convert_markdown_to_html(md_path: Path) -> str:
    """Convert a markdown file to HTML fragment."""
    try:
        import markdown
        with open(md_path) as f:
            text = f.read()
        return markdown.markdown(
            text,
            extensions=["tables", "fenced_code", "toc", "nl2br"],
        )
    except ImportError:
        # Fallback: just wrap in pre tags
        with open(md_path) as f:
            text = f.read()
        import html
        return f"<pre>{html.escape(text)}</pre>"


def build_findings(base_dir: Path) -> None:
    """Convert FINDINGS_*.md and OPERATIONS.md to HTML fragments."""
    findings_dir = DATA_DIR / "findings"
    findings_dir.mkdir(parents=True, exist_ok=True)

    mapping = {
        "FINDINGS_SYNTHESIS.md": "synthesis.html",
        "FINDINGS_AGGREGATE.md": "aggregate.html",
        "FINDINGS_SONNET46.md": "sonnet46.html",
        "FINDINGS_META_REASONING.md": "meta-reasoning.html",
        "OPERATIONS.md": "methodology.html",
        "STATISTICS.md": "statistics.html",
    }

    for md_file, html_file in mapping.items():
        md_path = base_dir / md_file
        if md_path.exists():
            html_content = convert_markdown_to_html(md_path)
            with open(findings_dir / html_file, "w") as f:
                f.write(html_content)
            print(f"  Converted {md_file} -> {html_file}")
        else:
            print(f"  WARNING: {md_file} not found")


def model_slug(model_id: str) -> str:
    """Convert model ID to a filename-safe slug."""
    label = get_model_label(model_id)
    return label.lower().replace(" ", "-").replace(".", "")


def write_json(path: Path, data: dict) -> int:
    """Write JSON and return file size in bytes."""
    with open(path, "w") as f:
        json.dump(data, f, separators=(",", ":"), default=str)
    return path.stat().st_size


def copy_static_files():
    """Copy static files (HTML, CSS, JS) to webapp directory."""
    src = BASE_DIR / "webapp_src"
    if src.exists():
        # If we have a source directory, copy from there
        shutil.copytree(src, WEBAPP_DIR, dirs_exist_ok=True)
    # Otherwise, files are generated directly into webapp/


def main():
    parser = argparse.ArgumentParser(description="Build the Research Findings Explorer webapp")
    parser.add_argument("--clean", action="store_true", help="Clean output directory before building")
    args = parser.parse_args()

    print("=" * 60)
    print("Building Research Findings Explorer")
    print("=" * 60)

    # Clean if requested
    if args.clean and DATA_DIR.exists():
        shutil.rmtree(DATA_DIR)
        print("Cleaned data directory")

    # Create directories
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "models").mkdir(exist_ok=True)
    (DATA_DIR / "findings").mkdir(exist_ok=True)

    # Load data
    print("\nLoading canonical v1.6 result files...")
    model_results = load_canonical_results()
    total = sum(len(v) for v in model_results.values())
    print(f"  Loaded {total} probe results across {len(model_results)} models")
    for mid, results in sorted(model_results.items()):
        print(f"    {get_model_label(mid)} ({mid}): {len(results)} probes")

    # Build summary
    print("\nBuilding summary.json...")
    summary = build_summary(model_results)
    size = write_json(DATA_DIR / "summary.json", summary)
    print(f"  summary.json: {size / 1024:.1f} KB")

    # Build per-model files
    print("\nBuilding per-model data...")
    for model_id, results in sorted(model_results.items()):
        slug = model_slug(model_id)
        model_data = build_model_data(model_id, results)
        size = write_json(DATA_DIR / "models" / f"{slug}.json", model_data)
        print(f"  {slug}.json: {size / 1024:.1f} KB ({len(results)} probes)")

    # Build cross-model comparison
    print("\nBuilding cross-model.json...")
    cross = build_cross_model(model_results)
    size = write_json(DATA_DIR / "cross-model.json", cross)
    print(f"  cross-model.json: {size / 1024:.1f} KB")

    # Build findings HTML
    print("\nConverting findings documents...")
    build_findings(BASE_DIR)

    # Report total size
    total_size = sum(
        f.stat().st_size
        for f in DATA_DIR.rglob("*")
        if f.is_file()
    )
    file_count = sum(1 for f in DATA_DIR.rglob("*") if f.is_file())
    print(f"\nData output: {file_count} files, {total_size / 1024 / 1024:.1f} MB")

    # Report full webapp size
    webapp_size = sum(
        f.stat().st_size
        for f in WEBAPP_DIR.rglob("*")
        if f.is_file()
    )
    webapp_files = sum(1 for f in WEBAPP_DIR.rglob("*") if f.is_file())
    print(f"Total webapp: {webapp_files} files, {webapp_size / 1024 / 1024:.1f} MB")
    print("\nBuild complete! Run 'python serve.py' to preview.")


if __name__ == "__main__":
    main()
