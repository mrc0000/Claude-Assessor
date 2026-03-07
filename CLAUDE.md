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
├── config.py                  # Runtime configuration dataclass
├── probe_runner.py            # Anthropic API interaction layer
├── mock_runner.py             # Simulated responses for dev/testing
├── analyzer.py                # Pattern matching, gap detection, differential scoring
├── reporter.py                # JSON + Markdown report generation
├── html_report.py             # Interactive HTML report (per-suite)
├── comparative_analysis.py    # Cross-domain statistical aggregation
├── comparative_html_report.py # Comparative HTML report with implications
├── eval_config.json           # Versioned scoring parameters (v1.3.0)
├── probes.json                # Primary 16-probe multi-domain suite
├── probes_*.json              # Domain-specific deep suites (6 probes each)
├── OPERATIONS.md              # Scoring model, protocol, interpretation guide
├── results/                   # Timestamped JSON run outputs
└── reports/                   # Markdown, HTML, and comparative reports
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

# Mock mode for testing
python run_full_suite.py --mock --variance 1
```

## Configuration

- **API key**: `ANTHROPIC_API_KEY` in `reasoning-eval/.env`
- **Eval config**: `eval_config.json` — patterns, thresholds, prompt templates (versioned)
- **Scoring thresholds**: `scoring.classification_thresholds` and `scoring.differential_thresholds`

## Outputs

- `results/run_{label}_{timestamp}.json` — Raw data with responses and classifications
- `reports/report_{label}_{timestamp}.html` — Per-suite interactive HTML
- `reports/comparative_{label}_{timestamp}.html` — Cross-domain comparative report

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

## Current Evaluation Status (Sonnet 4.6)

### Completed Models
- **Haiku 4.5** (`claude-haiku-4-5-20251001`) — All 7 suites, reclassified with LLM
- **Sonnet 4** (`claude-sonnet-4-20250514`) — All 7 suites, reclassified with LLM

### Completed: Sonnet 4.6 (`claude-sonnet-4-6`)
Fresh runs with LLM classification, `--workers 6`, `--variance 3` — all 7 suites complete (156/156 results):
- general: COMPLETE (48 results)
- cyber-insider: COMPLETE (18 results)
- medical-deep: COMPLETE (18 results)
- legal-deep: COMPLETE (18 results)
- financial-deep: COMPLETE (18 results)
- chemistry-deep: COMPLETE (18 results)
- reasoning-honesty: COMPLETE (18 results)

### Findings Reports
- `reasoning-eval/FINDINGS_SONNET46.md` — Sonnet 4.6 specific observations and analysis
- `reasoning-eval/FINDINGS_AGGREGATE.md` — Cross-model comparison (Haiku 4.5, Sonnet 4, Sonnet 4.6)
