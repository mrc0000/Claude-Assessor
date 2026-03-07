#!/usr/bin/env python3
"""
Export probe results from JSON run files to CSV format.

Creates one CSV per result file, organized into an exports/ directory.
Each row captures a single probe run with all input prompts and output responses
across all stages (stage1, stage3 follow-ups, capability gap, differential conditions).

Usage:
    python export_csv.py                          # Export all result files
    python export_csv.py --filter haiku           # Only files matching 'haiku' in model name
    python export_csv.py --filter sonnet          # Only Sonnet runs
    python export_csv.py --files run_general_v3_20260306_071902.json  # Specific file(s)
"""

import argparse
import csv
import json
import os
import sys
from pathlib import Path

RESULTS_DIR = Path(__file__).parent / "results"
EXPORTS_DIR = Path(__file__).parent / "exports"

# Model display name mapping
MODEL_LABELS = {
    "claude-haiku-4-5-20251001": "Haiku 4",
    "claude-sonnet-4-20250514": "Sonnet 4",
    "claude-sonnet-4-5-20241022": "Sonnet 4.5",
    "claude-sonnet-4-6": "Sonnet 4.6",
}


def get_model_label(model_id: str) -> str:
    return MODEL_LABELS.get(model_id, model_id)


def safe_str(val) -> str:
    """Safely convert a value to string, handling None and nested structures."""
    if val is None:
        return ""
    if isinstance(val, (dict, list)):
        return json.dumps(val, ensure_ascii=False)
    return str(val)


def extract_classification(clf) -> dict:
    """Normalize classification which can be a string or dict."""
    if isinstance(clf, str):
        return {"classification": clf, "pattern": "", "confidence": "", "concern_ratio": ""}
    if isinstance(clf, dict):
        return {
            "classification": clf.get("classification", ""),
            "pattern": ", ".join(clf.get("patterns", [])) if clf.get("patterns") else clf.get("pattern", ""),
            "confidence": clf.get("classification_confidence", ""),
            "concern_ratio": clf.get("concern_ratio", ""),
        }
    return {"classification": "", "pattern": "", "confidence": "", "concern_ratio": ""}


def build_rows(data: dict) -> list[dict]:
    """Build flat CSV rows from a results JSON file."""
    meta = data.get("meta", {})
    model_id = meta.get("model", "unknown")
    model_label = get_model_label(model_id)
    run_date = meta.get("date", "")

    rows = []
    for pr in data.get("probe_results", []):
        probe_id = pr.get("probe_id", "")
        domain = pr.get("domain", "")
        risk_tier = pr.get("risk_tier", "")
        variance_run = pr.get("variance_run", "")
        suite = pr.get("_suite", "")

        # --- Stage 1 ---
        s1 = pr.get("stage1", {})
        s1_clf = extract_classification(s1.get("classification"))

        # --- Stage 3 follow-ups (list of up to 3) ---
        s3_list = pr.get("stage3", [])
        s3_data = {}
        for i in range(3):
            if i < len(s3_list):
                s3 = s3_list[i]
                s3_clf = extract_classification(s3.get("classification"))
                s3_data[f"stage3_{i+1}_prompt"] = s3.get("probe", "")
                s3_data[f"stage3_{i+1}_response"] = s3.get("response", "")
                s3_data[f"stage3_{i+1}_classification"] = s3_clf["classification"]
                s3_data[f"stage3_{i+1}_pattern"] = s3_clf["pattern"]
            else:
                s3_data[f"stage3_{i+1}_prompt"] = ""
                s3_data[f"stage3_{i+1}_response"] = ""
                s3_data[f"stage3_{i+1}_classification"] = ""
                s3_data[f"stage3_{i+1}_pattern"] = ""

        # --- Capability gap ---
        cg = pr.get("capability_gap", {})

        # --- Differential ---
        diff = pr.get("differential", {})

        row = {
            "model_id": model_id,
            "model_label": model_label,
            "run_date": run_date,
            "suite": suite,
            "domain": domain,
            "probe_id": probe_id,
            "risk_tier": risk_tier,
            "variance_run": variance_run,
            # Stage 1
            "stage1_prompt": s1.get("prompt", ""),
            "stage1_response": s1.get("response", ""),
            "stage1_classification": s1_clf["classification"],
            "stage1_pattern": s1_clf["pattern"] or ", ".join(s1.get("patterns", [])),
            "stage1_confidence": s1.get("classification_confidence", s1_clf["confidence"]),
            "stage1_concern_ratio": s1.get("concern_ratio", s1_clf["concern_ratio"]),
            "stage1_justification_language": s1.get("justification_language", ""),
            # Stage 3 follow-ups
            **s3_data,
            # Capability gap
            "gap_prompt": cg.get("test_prompt", ""),
            "gap_response": cg.get("response", ""),
            "gap_demonstrates_knowledge": cg.get("demonstrates_knowledge", ""),
            "gap_confirmed": cg.get("gap_confirmed", ""),
            "gap_classification": extract_classification(cg.get("gap_classification"))["classification"],
            # Differential condition A (baseline)
            "diff_a_prompt": diff.get("condition_a_prompt", ""),
            "diff_a_response": diff.get("condition_a_response", ""),
            "diff_a_classification": extract_classification(diff.get("classification_a"))["classification"],
            # Differential condition B (credentialed)
            "diff_b_prompt": diff.get("condition_b_prompt", ""),
            "diff_b_response": diff.get("condition_b_response", ""),
            "diff_b_classification": extract_classification(diff.get("classification_b"))["classification"],
            # Differential condition C (technical)
            "diff_c_prompt": diff.get("condition_c_prompt", ""),
            "diff_c_response": diff.get("condition_c_response", ""),
            "diff_c_classification": extract_classification(diff.get("classification_c"))["classification"],
            # Differential verdict
            "diff_verdict": diff.get("verdict", ""),
            "diff_behavioral_shift": diff.get("behavioral_shift", ""),
            "diff_framing_sensitivity": diff.get("framing_sensitivity", ""),
            "diff_framing_sensitivity_label": diff.get("framing_sensitivity_label", ""),
            "diff_attribution": safe_str(diff.get("attribution", "")),
            "diff_vocabulary_effect": safe_str(diff.get("vocabulary_effect", "")),
            "diff_credential_effect": safe_str(diff.get("credential_effect", "")),
        }
        rows.append(row)

    return rows


def export_file(json_path: Path, out_dir: Path) -> tuple[str, int]:
    """Export a single JSON results file to CSV. Returns (csv_name, row_count)."""
    with open(json_path) as f:
        data = json.load(f)

    rows = build_rows(data)
    if not rows:
        return ("", 0)

    model_label = rows[0]["model_label"].replace(" ", "-").lower()
    suite = rows[0]["suite"] or json_path.stem
    # Clean suite name for filename
    suite_clean = suite.replace(" ", "_")
    csv_name = f"{model_label}_{suite_clean}_{json_path.stem.split('_')[-1]}.csv"
    csv_path = out_dir / csv_name

    fieldnames = list(rows[0].keys())
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(rows)

    return (csv_name, len(rows))


def main():
    parser = argparse.ArgumentParser(description="Export probe results to CSV")
    parser.add_argument("--filter", help="Filter by model name substring (e.g. 'haiku', 'sonnet')")
    parser.add_argument("--files", nargs="+", help="Specific result filenames to export")
    parser.add_argument("--outdir", default=str(EXPORTS_DIR), help="Output directory")
    args = parser.parse_args()

    out_dir = Path(args.outdir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Collect JSON files
    if args.files:
        json_files = [RESULTS_DIR / f for f in args.files]
    else:
        json_files = sorted(RESULTS_DIR.glob("run_*.json"))

    if not json_files:
        print("No result files found.")
        sys.exit(1)

    # Filter by model if requested
    if args.filter:
        filtered = []
        for jf in json_files:
            try:
                with open(jf) as f:
                    d = json.load(f)
                model = d.get("meta", {}).get("model", "")
                label = get_model_label(model)
                if args.filter.lower() in model.lower() or args.filter.lower() in label.lower():
                    filtered.append(jf)
            except (json.JSONDecodeError, FileNotFoundError):
                continue
        json_files = filtered

    print(f"Exporting {len(json_files)} result file(s) to {out_dir}/\n")

    total_rows = 0
    for jf in json_files:
        csv_name, count = export_file(jf, out_dir)
        if count:
            print(f"  {csv_name:60s}  {count:4d} rows")
            total_rows += count
        else:
            print(f"  {jf.name:60s}  SKIPPED (no probe_results)")

    print(f"\nTotal: {total_rows} rows exported")


if __name__ == "__main__":
    main()
