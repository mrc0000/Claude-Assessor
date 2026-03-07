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
