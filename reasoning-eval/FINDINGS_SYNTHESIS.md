# Synthesis: What the Evaluation Actually Shows

**Scope**: 468 probe runs across 3 Claude models, 52 probes, 7 domains, 3 variance runs each.
**Framework version**: eval_config v1.6.0 (variance-calibrated thresholds, `negligible_max=2`, graded tone modulation).

**Models evaluated** (chronological release order):

| Model | ID | Tier | Release |
|-------|----|------|---------|
| Sonnet 4 | `claude-sonnet-4-20250514` | Mid | May 2025 |
| Haiku 4.5 | `claude-haiku-4-5-20251001` | Small | Oct 2025 |
| Sonnet 4.6 | `claude-sonnet-4-6` | Mid | Later |

These are not three generations of the same model. Sonnet 4 and Sonnet 4.6 are mid-tier; Haiku 4.5 is the smaller, faster tier. Comparisons characterize behavioral differences across the model family — not a progression within a single line.

This document synthesizes the cross-model and per-model findings into higher-order observations. It is meant to be read after — or instead of — the detailed breakdowns in `FINDINGS_AGGREGATE.md` and `FINDINGS_SONNET46.md`.

---

## 1. The Central Finding: Most Responses Are Consistent, but Discrimination Concentrates in Specific Domains

Under calibrated thresholds (v1.6, `negligible_max=2`), the majority of responses are substantively consistent across framings:

| Model | Deflection | Full Assist | Discriminatory | Tone Modulated | Consistent |
|-------|-----------|-------------|----------------|----------------|------------|
| Sonnet 4 | 1.9% | 82.1% | 9.0% | 9.0% | 82.1% |
| Haiku 4.5 | 3.8% | 75.6% | 18.2% | 17.5% | 64.3% |
| Sonnet 4.6 | 1.9% | 88.5% | 13.5% | 18.2% | 68.2% |

The prior v1.5 analysis reported near-zero consistency (0–2%), which overstated framing sensitivity. The LLM differential classifier tends to find minor tonal differences even between substantively equivalent responses, scoring FS=2 on 66–82% of probes. These minor differences — a slightly longer caveat, a minor phrasing variation — do not represent meaningful modulation. The v1.6 threshold corrects for this classifier sensitivity bias.

The meaningful behavioral signals are:
- **Discriminatory verdicts (9–18%)**: The model changes what it will or won't do based on framing. This is threshold-independent — it's triggered by `behavioral_shift`, not framing sensitivity.
- **Tone modulation at FS ≥ 3 (9–18%)**: The model gives the same substantive answer but adjusts depth, hedging, or engagement measurably.
- **Domain concentration**: Discrimination is not uniformly distributed — it clusters sharply in cybersecurity and reasoning.

---

## 2. Evasion Patterns Vary by Model, but Liability Laundering Persists

Detected evasion patterns vary substantially across models:

| Model | Pattern Matches | Top Pattern |
|-------|----------------|-------------|
| Sonnet 4 | 54 | Liability Laundering (22) |
| Haiku 4.5 | 79 | Liability Laundering (23) |
| Sonnet 4.6 | 23 | Liability Laundering (6) |

Haiku 4.5 (the smaller model) triggers the most patterns. Sonnet 4.6 triggers the fewest — less than a third of Haiku's count. But all three share the same top evasion strategy: **liability laundering**, where the model frames its constraints as being for the user's benefit.

Sonnet 4.6 shows 18.2% tone modulation while triggering only 23 pattern matches, suggesting its modulation is more diffuse — tonal shifts that escape structured pattern detection. Whether fewer detectable patterns represent less evasion or more sophisticated evasion is an open question this framework can identify but not resolve.

---

## 3. Discriminatory Behavior Differs by Domain and Model

The aggregate discriminatory rates (9–18%) obscure sharp differences at the domain level:

| Domain | Sonnet 4 | Haiku 4.5 | Sonnet 4.6 |
|--------|----------|-----------|------------|
| Cybersecurity | 18.5% | 51.9% | 22.2% |
| Reasoning | 33.3% | 50.0% | 22.2% |
| Legal | 0.0% | 0.0% | **20.8%** |
| Copyright | 20.0% | 0.0% | 15.4% |
| Medical | 0.0% | 0.0% | **9.5%** |
| Chemistry | 0.0% | 14.8% | 0.0% |
| Financial | 0.0% | 4.8% | 4.8% |

Key observations:

- **Cybersecurity and reasoning** show the highest discriminatory rates across all models. These are the domains where credential claims and meta-cognitive probes have the most impact.
- **Haiku 4.5** (the smaller model) has the highest discrimination in cybersecurity (51.9%) and reasoning (50.0%).
- **Sonnet 4.6** shows discriminatory behavior in legal (20.8%) and medical (9.5%) where neither Sonnet 4 nor Haiku 4.5 does. It's the most helpful model but differentiates *how* it helps based on framing.
- **Sonnet 4** has the lowest aggregate discrimination (9.0%) but the most capability gaps (22), suggesting it restricts broadly rather than by framing.

Each model has a different behavioral fingerprint — different domains where framing matters most.

---

## 4. The Meta-Cognitive Gap Is Consistent Across All Models

The reasoning-honesty suite asks models to reason about their own reasoning. It produces the weakest results of any domain across all three models:

| Metric | Sonnet 4 | Haiku 4.5 | Sonnet 4.6 |
|--------|----------|-----------|------------|
| Full assist | 50.0% | 44.4% | 72.2% |
| Discriminatory | 33.3% | 50.0% | 22.2% |
| Consistent | 16.7% | 33.3% | 11.1% |

Every model can articulate epistemic principles better than it can apply them. Reasoning is the only domain where consistent verdicts drop below 35% for every model. The gap between stated principles and demonstrated behavior is the most robust finding in the evaluation.

---

## 5. Variance Analysis: Strong Effects Concentrate in Cybersecurity and Reasoning

The variance baseline measures how much responses vary across identical reruns of the same probe:

| Model | Framing Sensitivity (mean) | Within-Noise Probes | Strong Effect Probes |
|-------|---------------------------|--------------------|--------------------|
| Sonnet 4 | 2.36 | 45/52 (87%) | 3/52 (6%) |
| Haiku 4.5 | 2.71 | 44/52 (85%) | 6/52 (12%) |
| Sonnet 4.6 | 2.57 | 41/52 (79%) | 3/52 (6%) |

Most probes (79–87%) show framing sensitivity within natural variance — the measured difference between framings is not reliably larger than between identical runs. Only 3–6 probes per model show strong effects (d > 1.0) that clearly exceed noise.

The strong-effect probes cluster exclusively in cybersecurity and reasoning — exactly the domains with the highest discriminatory rates. These are the reliable signals. The high consistent rate (64–82%) reflects that most probes genuinely produce equivalent responses across framings, not that the evaluation lacks sensitivity.

---

## 6. Infrastructure vs. Model Behavior: A Necessary Distinction

Copyright deflection is 20.0% across all three models — identical, because it's API-level content filtering, not model reasoning. The model never sees these requests. This is a separate system with separate accountability.

Any framework that conflates infrastructure blocks with model refusals will misattribute behavior. We report it for transparency but exclude it from model-level conclusions.

---

## 7. What This Framework Can and Cannot Show

**What it shows:**
- Whether responses change based on framing (they do, but primarily in specific domains)
- Which domains and probe types show the largest framing effects (cybersecurity, reasoning)
- How evasion strategies differ across models (pattern frequency, pattern types)
- Where each model's behavioral fingerprint is distinctive (domain-level discrimination profiles)
- The gap between articulated principles and demonstrated behavior (meta-cognitive probes)

**What it cannot show:**
- Whether framing-dependent modulation causes real-world harm (the framework measures behavioral shift, not impact)
- Whether credential sensitivity is Anthropic-specific or general (no control test with fictional company names)
- Whether tonal modulation constitutes "reasoning dishonesty" or "adaptive communication" (this is an interpretive question, not an empirical one)
- How these findings compare to other model families (no cross-provider evaluation yet)
- Whether behavioral differences across models reflect training choices, capability differences, or tier-specific optimization

**What it intentionally does not claim:**
- That these models are "unsafe" — deflection rates are low across the family
- That any single discriminatory verdict is cause for alarm — the signal is in the aggregate pattern
- That tone modulation is inherently problematic — some register adaptation may be appropriate
- That model comparisons represent a quality ranking — different models have different behavioral profiles

---

## 8. Behavioral Profile of the Claude Model Family

The three models share a common behavioral profile:

1. **High helpfulness** — full assist rates of 76–89% across the family
2. **Low overt refusal** — deflection rare (1.9–3.8%), concentrated in infrastructure-level content filtering
3. **Majority consistency** — 64–82% of responses are substantively equivalent across framings
4. **Domain-concentrated discrimination** — 9–18% discriminatory, clustering in cybersecurity and reasoning
5. **Credential reactivity** — claiming expertise or organizational affiliation measurably changes response depth in sensitive domains
6. **Meta-cognitive weakness** — reasoning about own limitations is the weakest domain for every model
7. **Liability laundering as dominant strategy** — framing constraints as user benefit is the most persistent evasion pattern

Within this shared profile, each model has a distinctive behavioral fingerprint. Haiku 4.5 shows the most evasion patterns and highest cybersecurity discrimination. Sonnet 4 has the lowest aggregate discrimination but the most capability gaps. Sonnet 4.6 is the most helpful but introduces framing sensitivity in domains where the other models are neutral.

These are behavioral observations, not quality judgments. The evaluation characterizes how each model navigates the space between knowledge, willingness, and presentation — not which model does it "best."

---

## Methodology Reference

- **Probes**: 52 across 7 domains, each with neutral + credentialed + technical framings
- **Classification**: LLM-based (Haiku 4.5 classifier), consistent across all evaluations
- **Differential scoring**: v1.6.0 thresholds (`negligible_max=2`), graded tone modulation
- **Variance control**: 3 runs per probe per model, within-probe effect size computation
- **Infrastructure detection**: Content filter blocks distinguished from model-level refusal by error response analysis

Companion documents:
- `STATISTICS.md` — Raw counts, distributions, and cross-tabulations (LLM-consumable reference)
- `FINDINGS_AGGREGATE.md` — Cross-model metrics and domain-level comparison tables
- `FINDINGS_SONNET46.md` — Sonnet 4.6 deep dive with probe-level observations
- `METHODOLOGY.md` — Implementation details, gaps, and limitations
- `OPERATIONS.md` — Scoring model, protocol details, interpretation guide
