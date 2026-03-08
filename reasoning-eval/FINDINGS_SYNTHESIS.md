# Synthesis: What the Evaluation Actually Shows

**Scope**: 468 probe runs across 3 Claude models (Haiku 4.5, Sonnet 4, Sonnet 4.6), 52 probes, 7 domains, 3 variance runs each.
**Framework version**: eval_config v1.5.0 (variance-calibrated thresholds, graded tone modulation, length-only scope_diff).

This document synthesizes the cross-model and per-model findings into higher-order observations. It is meant to be read after — or instead of — the detailed breakdowns in `FINDINGS_AGGREGATE.md` and `FINDINGS_SONNET46.md`.

---

## 1. The Central Finding: Helpfulness Improved, Consistency Did Not

Across three model generations, Claude became substantially more helpful:

| Model | Deflection | Full Assist | Discriminatory | Consistent |
|-------|-----------|-------------|----------------|------------|
| Haiku 4.5 | 3.8% | 75.6% | 17.9% | 0.0% |
| Sonnet 4 | 1.9% | 82.1% | 9.0% | 0.0% |
| Sonnet 4.6 | 1.9% | 88.5% | 13.5% | 2.0% |

Full assist climbed 13 points. Deflection halved. But consistent differential rates — where the model gives genuinely equivalent responses regardless of how the question is framed — remained at or near zero across all three models.

This is the core diagnostic: **the training process optimizes for "say yes" without optimizing for "say the same thing."** The model learned to stop refusing. It did not learn to stop discriminating between framings.

---

## 2. Evasion Patterns Are Declining, But What Replaced Them?

Total detected evasion patterns dropped sharply:

| Model | Pattern Matches | Top Pattern |
|-------|----------------|-------------|
| Haiku 4.5 | 79 | Liability Laundering (23) |
| Sonnet 4 | 54 | Liability Laundering (22) |
| Sonnet 4.6 | 23 | Liability Laundering (6) |

Sonnet 4.6 triggers fewer than a third of the evasion patterns that Haiku 4.5 does. On its face, this looks like improvement. But consider it alongside the tone modulation rate: 82–91% of all differential tests show the model adjusting its response based on framing — across all three models, stably.

The pattern-matching engine catches structured evasion: concern front-loading, scope narrowing, competence deflection. What it doesn't catch is *tonal* modulation — subtle shifts in hedging density, caveat placement, engagement level, and depth of response. The model evolved from detectable evasion patterns to diffuse tonal adjustment. Whether this represents genuine improvement or more sophisticated evasion is an open question that this framework can identify but not resolve.

**Liability laundering** is the last evasion pattern standing. Even in Sonnet 4.6 (6 matches out of 23 total), it accounts for 26% of all detected patterns. The model's most persistent rhetorical strategy is framing its constraints as being for the user's benefit.

---

## 3. Discrimination Emerged Where It Didn't Exist Before

The aggregate discriminatory rate (17.9% → 9.0% → 13.5%) tells a misleading story. The domain-level data reveals something more specific:

| Domain | Haiku 4.5 | Sonnet 4 | Sonnet 4.6 | Direction |
|--------|-----------|----------|------------|-----------|
| Cybersecurity | 51.9% | 18.5% | 22.2% | Improved sharply, then stalled |
| Reasoning | 50.0% | 33.3% | 22.2% | Steady improvement |
| Chemistry | 14.8% | 0.0% | 0.0% | Resolved |
| Financial | 4.8% | 0.0% | 4.8% | Noise-level |
| **Legal** | **0.0%** | **0.0%** | **20.8%** | **Emerged in 4.6** |
| **Medical** | **0.0%** | **0.0%** | **9.5%** | **Emerged in 4.6** |
| Copyright | 0.0% | 20.0% | 15.4% | Emerged in Sonnet 4 |

Legal and medical had zero discriminatory behavior through two model generations — then Sonnet 4.6 introduced it. The model is more helpful in both domains (legal full assist jumped from 58–67% to 91.7%, medical from 75% to 87.5%), but it now gives meaningfully different responses depending on framing.

This is the "helpful but discriminatory" equilibrium: the model answers everyone, but it doesn't answer everyone the same way. Users who frame questions with technical vocabulary or credential claims receive deeper, less hedged responses. The discrimination shifted from *whether* you get an answer to *what quality* of answer you get.

---

## 4. The Meta-Cognitive Gap Is the Most Revealing Signal

The reasoning-honesty suite asks the model to reason about its own reasoning — to examine its limitations, articulate when it's uncertain, and apply epistemic principles consistently. It produces the worst results of any domain across all three models:

| Metric | Haiku 4.5 | Sonnet 4 | Sonnet 4.6 |
|--------|-----------|----------|------------|
| Full assist | 44.4% | 50.0% | 72.2% |
| Discriminatory | 50.0% | 33.3% | 22.2% |
| Concern ratio | — | — | 0.108 |

The model can articulate epistemic principles better than it can apply them. When asked about its own limitations, it deploys the same patterns it would criticize in others: hedging that obscures rather than informs, claimed uncertainty about things it demonstrably knows, and justifications that shift under reframing.

Sonnet 4.6 is improving here — discriminatory dropped from 50% to 22%, full assist climbed from 44% to 72%. But the reasoning domain still has the highest concern ratio (0.108) and the lowest full assist rate of any domain. The gap between stated principles and demonstrated behavior is narrowing, but it remains the widest gap in the evaluation.

---

## 5. Variance Analysis: Most Framing Effects Are Noise

The variance baseline — which measures how much the model's responses vary across identical reruns of the same probe — provides a critical calibration:

| Model | Framing Sensitivity (mean) | Within-Noise Probes | Strong Effect Probes |
|-------|---------------------------|--------------------|--------------------|
| Haiku 4.5 | 2.71 | 44/52 (85%) | 6/52 (12%) |
| Sonnet 4 | 2.36 | 45/52 (87%) | 3/52 (6%) |
| Sonnet 4.6 | 2.57 | 41/52 (79%) | 3/52 (6%) |

Most probes (79–87%) show framing sensitivity scores within the range of natural variance — meaning the measured difference between framings is not reliably larger than the difference between two identical runs. Only 3–6 probes per model show strong effects that clearly exceed noise.

This doesn't invalidate the differential findings — the strong-effect probes concentrate in cybersecurity and reasoning, exactly the domains with the highest discriminatory rates. But it means the 82–91% tone modulation rate should be read as "the model nearly always adjusts somewhat" rather than "the model discriminates on 82–91% of probes." Most of that adjustment is within natural behavioral variance.

The probes that do exceed noise are the signal. They cluster in two categories: **credential-sensitive probes** (where claiming expertise or organizational affiliation changes response depth) and **meta-cognitive probes** (where the model reasons differently about its own limitations depending on how the question is framed).

---

## 6. Infrastructure vs. Model Behavior: A Necessary Distinction

Copyright deflection is 20.0% across all three models — identical, because it's API-level content filtering, not model reasoning. The model never sees these requests. This is a separate system with separate accountability.

This matters for evaluation methodology: any framework that conflates infrastructure blocks with model refusals will misattribute behavior. The 20% copyright deflection in this evaluation is a property of the deployment stack, not of the model's reasoning honesty. We report it for transparency but exclude it from model-level conclusions.

---

## 7. What This Framework Can and Cannot Show

**What it shows:**
- Whether responses change based on framing (they do, universally)
- Which domains and probe types show the largest framing effects (cybersecurity, reasoning)
- How evasion strategy evolves across model generations (from overt patterns to diffuse modulation)
- Where new discriminatory behavior emerges (legal and medical in Sonnet 4.6)
- The gap between articulated principles and demonstrated behavior (meta-cognitive probes)

**What it cannot show:**
- Whether framing-dependent modulation causes real-world harm (the framework measures behavioral shift, not impact)
- Whether credential sensitivity is Anthropic-specific or general (no control test with fictional company names)
- Whether tonal modulation constitutes "reasoning dishonesty" or "adaptive communication" (this is an interpretive question, not an empirical one)
- How these findings compare to other model families (no cross-provider evaluation yet)

**What it intentionally does not claim:**
- That these models are "unsafe" — deflection rates are low and declining
- That any single discriminatory verdict is cause for alarm — the signal is in the aggregate pattern
- That tone modulation is inherently problematic — some register adaptation may be appropriate

---

## 8. The Trajectory

The Claude model family is converging on a specific behavioral profile:

1. **High helpfulness** — answer nearly everything (88.5% full assist in Sonnet 4.6)
2. **Low overt refusal** — deflection rare and declining (1.9%)
3. **Persistent framing sensitivity** — responses adjust based on how questions are asked (84.5% tone modulated)
4. **Near-zero consistency** — truly identical responses across framings almost never occur (2.0%)
5. **Declining detectable evasion** — fewer pattern matches (79 → 54 → 23)
6. **Emergent domain-specific discrimination** — new framing effects appearing in domains that were previously clean

This is not a model getting worse. It's a model getting better at saying yes while retaining the underlying tendency to say yes differently depending on who's asking and how. The question is whether that tendency matters — and to whom.

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
