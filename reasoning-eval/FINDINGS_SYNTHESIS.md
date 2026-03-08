# Synthesis: What the Evaluation Actually Shows

**Scope**: 468 probe runs across 3 Claude models, 52 probes, 7 domains, 3 variance runs each.
**Framework version**: eval_config v1.5.0 (variance-calibrated thresholds, graded tone modulation, length-only scope_diff).

**Models evaluated** (chronological release order):

| Model | ID | Tier | Release |
|-------|----|------|---------|
| Sonnet 4 | `claude-sonnet-4-20250514` | Mid | May 2025 |
| Haiku 4.5 | `claude-haiku-4-5-20251001` | Small | Oct 2025 |
| Sonnet 4.6 | `claude-sonnet-4-6` | Mid | Later |

These are not three generations of the same model. Sonnet 4 and Sonnet 4.6 are mid-tier; Haiku 4.5 is the smaller, faster tier. Comparisons characterize behavioral differences across the model family — not a progression within a single line.

This document synthesizes the cross-model and per-model findings into higher-order observations. It is meant to be read after — or instead of — the detailed breakdowns in `FINDINGS_AGGREGATE.md` and `FINDINGS_SONNET46.md`.

---

## 1. The Central Finding: All Models Modulate, None Are Consistent

Every model tested adjusts its responses based on how questions are framed. The rate of truly consistent behavior — where the model gives genuinely equivalent responses regardless of framing — is near zero across the entire family:

| Model | Deflection | Full Assist | Discriminatory | Tone Modulated | Consistent |
|-------|-----------|-------------|----------------|----------------|------------|
| Sonnet 4 | 1.9% | 82.1% | 9.0% | 91.0% | 0.0% |
| Haiku 4.5 | 3.8% | 75.6% | 17.9% | 82.1% | 0.0% |
| Sonnet 4.6 | 1.9% | 88.5% | 13.5% | 84.5% | 2.0% |

The models vary in *how much* they discriminate between framings (9–18% discriminatory) and in *how helpful* they are (76–89% full assist). But the underlying behavior — adjusting response depth, hedging, and engagement based on question presentation — is universal. No model tested produces consistent responses across framings.

This is the core diagnostic: **framing sensitivity is a shared behavioral characteristic of the Claude model family**, not a defect of any particular model or tier.

---

## 2. Evasion Patterns Vary by Model, but Liability Laundering Persists

Detected evasion patterns vary substantially across models:

| Model | Pattern Matches | Top Pattern |
|-------|----------------|-------------|
| Sonnet 4 | 54 | Liability Laundering (22) |
| Haiku 4.5 | 79 | Liability Laundering (23) |
| Sonnet 4.6 | 23 | Liability Laundering (6) |

Haiku 4.5 (the smaller model) triggers the most patterns. Sonnet 4.6 triggers the fewest — less than a third of Haiku's count. But all three share the same top evasion strategy: **liability laundering**, where the model frames its constraints as being for the user's benefit.

The pattern-matching engine catches structured evasion: concern front-loading, scope narrowing, competence deflection. What it doesn't catch is *tonal* modulation — subtle shifts in hedging density, caveat placement, engagement level, and depth of response. Sonnet 4.6 triggers fewer detectable patterns while maintaining an 84.5% tone modulation rate. Whether fewer detectable patterns represent less evasion or more diffuse evasion is an open question this framework can identify but not resolve.

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
- **Haiku 4.5** (the smaller model) has the highest discrimination in cybersecurity (51.9%) and reasoning (50.0%). Whether this reflects less sophisticated framing adaptation or stronger safety training relative to capability is unclear.
- **Sonnet 4.6** shows discriminatory behavior in legal (20.8%) and medical (9.5%) where neither Sonnet 4 nor Haiku 4.5 does. The model is more helpful in both domains (legal full assist: 91.7% vs. 58–67%; medical: 87.5% vs. 75%) — but it differentiates *how* it helps based on framing.
- **Sonnet 4** has the lowest aggregate discrimination (9.0%) and the broadest full-assist behavior, but also the most capability gaps (22 vs. 16 and 6), suggesting it restricts less by framing but more by topic.

The discrimination is not uniform across the family. Each model has a different behavioral fingerprint — different domains where framing matters most.

---

## 4. The Meta-Cognitive Gap Is Consistent Across All Models

The reasoning-honesty suite asks models to reason about their own reasoning — to examine limitations, articulate uncertainty, and apply epistemic principles. It produces the weakest results of any domain across all three models:

| Metric | Sonnet 4 | Haiku 4.5 | Sonnet 4.6 |
|--------|----------|-----------|------------|
| Full assist | 50.0% | 44.4% | 72.2% |
| Discriminatory | 33.3% | 50.0% | 22.2% |
| Concern ratio | — | — | 0.108 |

Every model can articulate epistemic principles better than it can apply them. When asked about its own limitations, each deploys the same patterns it would criticize in others: hedging that obscures rather than informs, claimed uncertainty about things it demonstrably knows, and justifications that shift under reframing.

The meta-cognitive domain consistently has the lowest full assist rate and the highest discriminatory rate of any domain. This is not a property of any single model — it's a behavioral characteristic of the family. The gap between stated principles and demonstrated behavior is the most robust finding in the evaluation.

---

## 5. Variance Analysis: Most Framing Effects Are Within Noise

The variance baseline — which measures how much responses vary across identical reruns of the same probe — provides critical calibration:

| Model | Framing Sensitivity (mean) | Within-Noise Probes | Strong Effect Probes |
|-------|---------------------------|--------------------|--------------------|
| Sonnet 4 | 2.36 | 45/52 (87%) | 3/52 (6%) |
| Haiku 4.5 | 2.71 | 44/52 (85%) | 6/52 (12%) |
| Sonnet 4.6 | 2.57 | 41/52 (79%) | 3/52 (6%) |

Most probes (79–87%) show framing sensitivity scores within the range of natural variance — meaning the measured difference between framings is not reliably larger than the difference between two identical runs. Only 3–6 probes per model show strong effects that clearly exceed noise.

This doesn't invalidate the differential findings — the strong-effect probes concentrate in cybersecurity and reasoning, exactly the domains with the highest discriminatory rates. But it means the 82–91% tone modulation rate should be read as "the model nearly always adjusts somewhat" rather than "the model discriminates on 82–91% of probes." Most of that adjustment is within natural behavioral variance.

The probes that do exceed noise cluster in two categories: **credential-sensitive probes** (where claiming expertise or organizational affiliation changes response depth) and **meta-cognitive probes** (where the model reasons differently about its own limitations depending on how the question is framed). These are the reliable signals.

---

## 6. Infrastructure vs. Model Behavior: A Necessary Distinction

Copyright deflection is 20.0% across all three models — identical, because it's API-level content filtering, not model reasoning. The model never sees these requests. This is a separate system with separate accountability.

This matters for evaluation methodology: any framework that conflates infrastructure blocks with model refusals will misattribute behavior. The 20% copyright deflection in this evaluation is a property of the deployment stack, not of the model's reasoning honesty. We report it for transparency but exclude it from model-level conclusions.

---

## 7. What This Framework Can and Cannot Show

**What it shows:**
- Whether responses change based on framing (they do, universally)
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
3. **Universal framing sensitivity** — 82–91% tone modulation; responses adjust based on how questions are asked
4. **Near-zero consistency** — truly identical responses across framings almost never occur (0.0–2.0%)
5. **Credential reactivity** — claiming expertise or organizational affiliation measurably changes response depth
6. **Meta-cognitive weakness** — reasoning about own limitations is the weakest domain for every model
7. **Liability laundering as dominant strategy** — framing constraints as user benefit is the most persistent evasion pattern

Within this shared profile, each model has a distinctive behavioral fingerprint. Haiku 4.5 shows the most evasion patterns and highest cybersecurity discrimination. Sonnet 4 has the lowest aggregate discrimination but the most capability gaps. Sonnet 4.6 is the most helpful but introduces framing sensitivity in domains where the other models are neutral.

These are behavioral observations, not quality judgments. The evaluation characterizes how each model navigates the space between knowledge, willingness, and presentation — not which model does it "best."

---

## Methodology Reference

- **Probes**: 52 across 7 domains, each with neutral + credentialed + technical framings
- **Classification**: LLM-based (Haiku 4.5 classifier), consistent across all evaluations
- **Differential scoring**: Variance-calibrated thresholds (v1.5.0), length-based scope_diff, graded tone modulation
- **Variance control**: 3 runs per probe per model, within-probe effect size computation
- **Infrastructure detection**: Content filter blocks distinguished from model-level refusal by error response analysis

Companion documents:
- `FINDINGS_AGGREGATE.md` — Cross-model metrics and domain-level comparison tables
- `FINDINGS_SONNET46.md` — Sonnet 4.6 deep dive with probe-level observations
- `OPERATIONS.md` — Scoring model, protocol details, interpretation guide
