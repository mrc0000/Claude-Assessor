# Sonnet 4.6 Evaluation: Execution Plan & Verification Guide

## Current State (as of 2026-03-07)

### Branch
All work on `claude/reasoning-honesty-eval-Zy1Ef`.

### Code Changes (committed + pushed)
- LLM classification prompt fixed: short labels (3-8 words) instead of verbatim quotes for `justification_language`
- Shift tracker rewritten: compares pattern sets (symmetric difference) instead of raw text
- Error capture: content filter blocks and empty responses now saved as proper results
- Concurrent execution: `--workers` flag (default 8) using ThreadPoolExecutor
- Inter-call delay reduced from 1.0s to 0.1s
- All defaults set to LLM classification

---

## Suite Completion Status & Verification

### How to verify a suite is complete
Each suite runs with `--variance 3`, meaning 3 independent runs. With differentials (initial + reframed response per probe), the expected result counts are:

| Suite | File Pattern | Probes | Results per run | Expected total (3 runs) |
|-------|-------------|--------|-----------------|------------------------|
| general | `run_general_v3_*.json` | 16 | 16 | **48** |
| cyber-insider | `run_cyber-insider_v3_*.json` | 6 | 6 | **18** |
| medical | `run_medical-deep_v3_*.json` | 6 | 6 | **18** |
| legal | `run_legal-deep_v3_*.json` | 6 | 6 | **18** |
| financial | `run_financial-deep_v3_*.json` | 6 | 6 | **18** |
| chemistry | `run_chemistry-deep_v3_*.json` | 6 | 6 | **18** |
| reasoning | `run_reasoning-honesty_v3_*.json` | 6 | 6 | **18** |

**Verification script:**
```bash
cd reasoning-eval
python3 -c "
import json, glob
expected = {'general': 48, 'cyber-insider': 18, 'medical-deep': 18, 'legal-deep': 18,
            'financial-deep': 18, 'chemistry-deep': 18, 'reasoning-honesty': 18}
for suite, exp in expected.items():
    files = sorted(glob.glob(f'results/run_{suite}_v3_20260307*.json'))
    partials = sorted(glob.glob(f'results/_partial_{suite}_v3*.json'))
    if files:
        with open(files[-1]) as f: data = json.load(f)
        results = data.get('probe_results', data.get('results', data)) if isinstance(data, dict) else data
        count = len(results)
        status = 'COMPLETE' if count >= exp else f'PARTIAL ({count}/{exp})'
        print(f'{suite}: {status} — {files[-1]}')
    elif partials:
        with open(partials[-1]) as f: data = json.load(f)
        count = len(data) if isinstance(data, list) else len(data.get('results', []))
        print(f'{suite}: PARTIAL ({count}/{exp}) — {partials[-1]}')
    else:
        print(f'{suite}: NOT STARTED')
"
```

### Completed Suites
| Suite | Result File | Count | Status |
|-------|------------|-------|--------|
| general | `run_general_v3_20260307_062803.json` | 48 | COMPLETE |
| cyber-insider | `run_cyber-insider_v3_20260307_064645.json` | 18 | COMPLETE |

### All Suites Complete
| Suite | Result File | Count | Status |
|-------|------------|-------|--------|
| general | `run_general_v3_20260307_062803.json` | 48 | COMPLETE |
| cyber-insider | `run_cyber-insider_v3_20260307_064645.json` | 18 | COMPLETE |
| medical-deep | `run_medical-deep_v3_20260307_071310.json` | 18 | COMPLETE |
| legal-deep | `run_legal-deep_v3_20260307_072531.json` | 18 | COMPLETE |
| financial-deep | `run_financial-deep_v3_20260307_074431.json` | 18 | COMPLETE |
| chemistry-deep | `run_chemistry-deep_v3_20260307_075234.json` | 18 | COMPLETE |
| reasoning-honesty | `run_reasoning-honesty_v3_20260307_074853.json` | 18 | COMPLETE |

**Total: 156/156 results across all 7 suites.**

---

## Expected Output Files Per Suite

When a suite completes, `run_full_suite.py` produces:

1. **Result JSON**: `results/run_{suite}_v3_{timestamp}.json`
   - Contains `results` array with one entry per probe per variance run
   - Each entry has: `probe_id`, `initial_response`, `reframed_response`, `classification`, `differential_analysis`

2. **HTML Report**: `reports/report_{suite}_v3_{timestamp}.html`
   - Interactive single-suite report with per-probe breakdowns

3. **Markdown Report**: `reports/report_{suite}_v3_{timestamp}.md`
   - Text version of the same report

4. **Combined JSON**: `results/_combined_all_suites.json`
   - Auto-updated after each suite with all results merged

5. **Comparative HTML**: `reports/comparative_full-suite_{timestamp}.html`
   - Cross-suite analysis (generated after final suite)

### How to know a suite truly finished vs crashed mid-run
- **Truly finished**: Final result JSON exists (not `_partial_*`), result count matches expected, HTML report exists
- **Partially finished**: Only `_partial_*` file exists — use `--resume-partial` to continue
- **Never started**: No result file and no partial file for that suite

---

## Known Probe Failures (Expected)
These are probe-level issues, not suite failures:

- `copyright-1a`: Consistently blocked by API content filter on Sonnet 4.6 (all runs)
- `copyright-2a`: Intermittently blocked (2 of 3 runs)
- `chemistry-1b`: Intermittent empty response (1-2 of 3 runs)
- `med-vaccine-6`: Empty response seen in some runs (transient)
- Blocked/empty responses are saved as results with `classification: "content_filter_block"` or `"empty_response"`

See `INFRASTRUCTURE_OPACITY.md` for analysis.

---

## Execution Commands

### Resume medical + run remaining suites
```bash
cd reasoning-eval
PYTHONUNBUFFERED=1 python run_full_suite.py \
  --model claude-sonnet-4-6 \
  --variance 3 \
  --suites medical legal financial chemistry reasoning \
  --classify llm \
  --workers 6 \
  --resume-partial
```

### Run individual suite (if needed)
```bash
PYTHONUNBUFFERED=1 python run_full_suite.py \
  --model claude-sonnet-4-6 \
  --variance 3 \
  --suites legal \
  --classify llm \
  --workers 6
```

### After all suites complete
```bash
# Verify all suites
# (use verification script above)

# Commit results
git add results/ reports/
git commit -m "Add Sonnet 4.6 evaluation results: all 7 suites, 3 variance runs each"
git push -u origin claude/reasoning-honesty-eval-Zy1Ef
```

---

## Configuration (Do Not Modify)
- `probe_runner.py`, `analyzer.py`, `config.py`, `eval_config.json` — stable
- API key in `reasoning-eval/.env`
- Rate limits: 1k req/min, 200k tokens in, 90k out — workers=6 stays well under
- Sonnet 4.6 generates long responses for cyber/security probes (~6000 chars)

## File Layout
```
results/
  run_general_v3_20260307_*.json          # COMPLETE (48 results)
  run_cyber-insider_v3_20260307_*.json    # COMPLETE (18 results)
  run_medical-deep_v3_*.json             # Pending completion
  run_legal-deep_v3_*.json               # Not started
  run_financial-deep_v3_*.json           # Not started
  run_chemistry-deep_v3_*.json           # Not started
  run_reasoning-honesty_v3_*.json        # Not started
  _combined_all_suites.json              # Auto-updated
  _partial_*.json                        # Temp files, deleted on completion
reports/
  report_*_v3_*.html                     # Per-suite interactive HTML
  report_*_v3_*.md                       # Per-suite markdown
  comparative_full-suite_*.html          # Cross-suite comparative
  comparative_full-suite_*.json          # Cross-suite data
```
