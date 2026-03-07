# Session Handoff: Remaining Sonnet 4.6 Evaluation Suites

## What's Done

### Code Changes (committed + pushed to `claude/reasoning-honesty-eval-Zy1Ef`)
- LLM classification prompt fixed: short labels (3-8 words) instead of verbatim quotes for `justification_language`
- Shift tracker rewritten: compares pattern sets (symmetric difference) instead of raw text
- Error capture: content filter blocks and empty responses now saved as proper results
- Concurrent execution: `--workers` flag (default 8) using ThreadPoolExecutor
- Inter-call delay reduced from 1.0s to 0.1s
- All defaults set to LLM classification

### Completed Sonnet 4.6 Runs (3 variance each, LLM classified)
- **general** — 48 results in `results/run_general_v3_20260307_062803.json`
- **cyber-insider** — 18 results in `results/run_cyber-insider_v3_20260307_064645.json`
- **medical** — in progress (partial at `results/_partial_medical-deep_v3.json`)

### Known Probe Failures
- `copyright-1a`: Consistently blocked by API content filter on Sonnet 4.6 (all 3 runs)
- `copyright-2a`: Intermittently blocked (2 of 3 runs)
- `chemistry-1b`: Intermittent empty response (1-2 of 3 runs)
- `med-vaccine-6`: Empty response seen in run 2 (transient)
- See `INFRASTRUCTURE_OPACITY.md` for analysis of content filter findings

## What Needs to Be Done

### Remaining Suites to Run
```bash
# Run from reasoning-eval/ directory
# Use --resume-partial if medical has a partial file
PYTHONUNBUFFERED=1 python run_full_suite.py \
  --model claude-sonnet-4-6 \
  --variance 3 \
  --suites medical legal financial chemistry reasoning \
  --classify llm \
  --workers 6 \
  --resume-partial
```

If medical is already complete, drop it from `--suites`. Check with:
```bash
python3 -c "
import json, glob
for f in sorted(glob.glob('results/run_*0307*.json')) + sorted(glob.glob('results/_partial_*.json')):
    with open(f) as fh: data = json.load(fh)
    if isinstance(data, dict):
        results = data.get('results', data.get('probe_results', []))
    else:
        results = data
    print(f'{f}: {len(results)} results')
"
```

### After All Suites Complete
1. The `_combined_all_suites.json` will be auto-generated with all results
2. Comparative report auto-generated as HTML
3. Commit all new result files, reports, and any remaining partials
4. Push to `claude/reasoning-honesty-eval-Zy1Ef`

### Important Notes
- **Branch**: `claude/reasoning-honesty-eval-Zy1Ef` — all work goes here
- **Do not modify**: `probe_runner.py`, `analyzer.py`, `config.py`, `eval_config.json` — these are stable
- **API key**: loaded from `reasoning-eval/.env`
- **Rate limits**: 1k requests/min, 200k tokens in, 90k out — workers=6 stays well under
- **Sonnet 4.6 generates long responses** for cyber/security probes (~6000 chars), making those suites slower
- **PYTHONUNBUFFERED=1** is important for seeing real-time progress in background runs

### File Layout
```
results/
  run_general_v3_20260307_*.json          # Done
  run_cyber-insider_v3_20260307_*.json    # Done
  _partial_medical-deep_v3.json           # In progress
  _combined_all_suites.json               # Auto-updated
reports/
  report_*_v3_20260307_*.html             # Auto-generated per suite
  comparative_full-suite_20260307_*.html  # Auto-generated cross-suite
```
