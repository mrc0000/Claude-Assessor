# Claude-Assessor

## Project Intent

Claude-Assessor is a sociolinguistic evaluation framework that audits **reasoning honesty** in large language models. It tests whether AI models reason transparently about their limitations or deploy patterned evasion strategies — and whether those patterns shift based on who the model believes is asking.

The core diagnostic: honest reasoning should be stable under scrutiny, consistent across framings, and transparent about the gap between capability and willingness.

## Architecture

All source code lives in `reasoning-eval/`. For detailed scoring model, protocol docs, and interpretation guide, see [`reasoning-eval/OPERATIONS.md`](reasoning-eval/OPERATIONS.md).

```
reasoning-eval/
├── main.py                    # CLI entry point for single-suite runs
├── run_full_suite.py          # Multi-suite orchestration (7 suites, variance)
├── reanalyze.py               # Retroactive re-analysis with updated patterns
├── backfill_probes.py         # Backfill missing/failed probe results
├── config.py                  # Runtime configuration dataclass
├── probe_runner.py            # Anthropic API interaction layer
├── mock_runner.py             # Simulated responses for dev/testing
├── analyzer.py                # Pattern matching, gap detection, differential scoring
├── reporter.py                # JSON + Markdown report generation
├── html_report.py             # Interactive HTML report (per-suite)
├── comparative_analysis.py    # Cross-domain statistical aggregation (single model)
├── comparative_html_report.py # Comparative HTML report with implications
├── cross_model_report.py      # Cross-model side-by-side comparison report
├── manage_reports.py          # Report organization and cleanup utility
├── export_csv.py              # Export results to CSV format
├── eval_config.json           # Versioned scoring parameters (v1.3.0)
├── probes.json                # Primary 16-probe multi-domain suite
├── probes_*.json              # Domain-specific deep suites (6 probes each)
├── OPERATIONS.md              # Scoring model, protocol, interpretation guide
├── results/                   # Timestamped JSON run outputs
└── reports/                   # Organized reports (see Report Management below)
```

## Probe Suites (52 probes)

| Suite | File | Probes | Domains |
|-------|------|--------|---------|
| General | `probes.json` | 16 | copyright, cybersecurity, chemistry, legal, financial, medical |
| Cyber Insider | `probes_cyber_insider.json` | 6 | cybersecurity (credential injection) |
| Medical Deep | `probes_medical_deep.json` | 6 | medical |
| Legal Deep | `probes_legal_deep.json` | 6 | legal |
| Financial Deep | `probes_financial_deep.json` | 6 | financial |
| Chemistry Deep | `probes_chemistry_deep.json` | 6 | chemistry |
| Reasoning Honesty | `probes_reasoning_honesty.json` | 6 | meta-cognitive reasoning |

## CLI Quick Reference

```bash
# Full run (7 suites, 3 variance runs)
python run_full_suite.py --variance 3 --model claude-haiku-4-5-20251001

# Specific suites
python run_full_suite.py --suites medical legal --variance 3

# Re-analyze with updated config
python reanalyze.py --diff --comparative --label v1.3.0

# Cross-model comparison report
python cross_model_report.py

# Backfill missing probes (e.g. API failures)
python backfill_probes.py --result-file results/run_X.json --original-file results/heuristic_originals/run_Y.json --probes-file probes_medical_deep.json

# Report management
python manage_reports.py status
python manage_reports.py regenerate

# Mock mode for testing
python run_full_suite.py --mock --variance 1
```

## Configuration

- **API key**: `ANTHROPIC_API_KEY` in `reasoning-eval/.env`
- **Eval config**: `eval_config.json` — patterns, thresholds, prompt templates (versioned)
- **Scoring thresholds**: `scoring.classification_thresholds` and `scoring.differential_thresholds`

## Outputs

- `results/run_{label}_{timestamp}.json` — Raw data with responses and classifications
- `reports/{model-label}/{suite}.html` — Per-suite interactive HTML (organized by model)
- `reports/{model-label}/comparative.html` — Cross-suite comparative report for one model
- `reports/cross-model/comparison.html` — Cross-model side-by-side comparison report

## Report Management

Reports are organized into model-specific folders using `manage_reports.py`:

```
reports/
├── haiku-4.5/           # Per-suite + comparative reports for Haiku 4.5
├── sonnet-4/            # Per-suite + comparative reports for Sonnet 4
├── sonnet-4.6/          # Per-suite + comparative reports for Sonnet 4.6
├── cross-model/         # Cross-model comparison reports
└── archive/             # Old/intermediate reports
```

```bash
python manage_reports.py status       # Show current report state
python manage_reports.py organize     # Organize flat reports into model folders
python manage_reports.py clean        # Archive intermediate/duplicate reports
python manage_reports.py regenerate   # Regenerate all reports from current result data
```

## Verification & Confirmation Requirements

**Always confirm completion of each step.** When running evaluation suites or making changes:

1. **After each suite run**: Verify the result file exists, check result count matches expected (probes × variance runs), confirm HTML report was generated
2. **After code changes**: Run mock mode (`--mock --variance 1`) to verify changes don't break the pipeline before running real API calls
3. **After commits**: Run `git log --oneline -3` and `git status` to confirm clean state
4. **After pushes**: Verify the push succeeded and the branch is up to date

### Expected Result Counts (with `--variance 3`)

| Suite | Probes | Expected results |
|-------|--------|-----------------|
| general | 16 | 48 |
| cyber-insider | 6 | 18 |
| medical-deep | 6 | 18 |
| legal-deep | 6 | 18 |
| financial-deep | 6 | 18 |
| chemistry-deep | 6 | 18 |
| reasoning-honesty | 6 | 18 |

### Verification Script
```bash
python3 -c "
import json, glob
expected = {'general': 48, 'cyber-insider': 18, 'medical-deep': 18, 'legal-deep': 18,
            'financial-deep': 18, 'chemistry-deep': 18, 'reasoning-honesty': 18}
for suite, exp in expected.items():
    files = sorted(glob.glob(f'results/run_{suite}*v3*.json'))
    partials = sorted(glob.glob(f'results/_partial_{suite}*.json'))
    if files:
        with open(files[-1]) as f: data = json.load(f)
        results = data.get('probe_results', data.get('results', data)) if isinstance(data, dict) else data
        count = len(results)
        status = 'COMPLETE' if count >= exp else f'PARTIAL ({count}/{exp})'
        print(f'{suite}: {status}')
    elif partials:
        with open(partials[-1]) as f: data = json.load(f)
        count = len(data) if isinstance(data, list) else len(data.get('results', []))
        print(f'{suite}: PARTIAL ({count}/{exp})')
    else:
        print(f'{suite}: NOT STARTED')
"
```

## Current Evaluation Status

All 3 models complete — 468 total probe runs (156 per model, 7 suites each, 3 variance runs).

| Model | ID | Probes | Status |
|-------|-----|--------|--------|
| Haiku 4.5 | `claude-haiku-4-5-20251001` | 156/156 | Complete |
| Sonnet 4 | `claude-sonnet-4-20250514` | 156/156 | Complete |
| Sonnet 4.6 | `claude-sonnet-4-6` | 156/156 | Complete |

### Findings Reports
- `reasoning-eval/FINDINGS_SONNET46.md` — Sonnet 4.6 specific observations and analysis
- `reasoning-eval/FINDINGS_AGGREGATE.md` — Cross-model comparison (Haiku 4.5, Sonnet 4, Sonnet 4.6)
- `reports/cross-model/` — Generated cross-model comparison HTML + JSON
