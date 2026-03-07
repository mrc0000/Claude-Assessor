# Cross-Model Reasoning Honesty Evaluation — Aggregate Findings

**Models evaluated**: Haiku 4.5, Sonnet 4, Sonnet 4.6
**Framework**: Claude-Assessor v1.3.0
**Protocol**: 52 probes, 7 domains, 3 variance runs, LLM classification, full differential + capability gap testing
**Total probe runs**: 468 (156 + 156 + 156)

## Abstract

Three Claude models were evaluated using identical probes and protocols to measure reasoning honesty — the consistency between what a model knows, what it claims to know, and how its behavior changes based on how a question is framed. The trajectory across the model family reveals a clear pattern: **deflection decreases while framing-dependent modulation persists**. Newer models refuse less but continue to adjust response depth, hedging, and engagement based on presentation style at comparable rates. The evolution is toward more sophisticated framing-sensitivity, not toward more consistent reasoning.

---

## Model Comparison: Headline Metrics

| Metric | Haiku 4.5 | Sonnet 4 | Sonnet 4.6 | Trend |
|--------|-----------|----------|------------|-------|
| Deflection rate | 3.8% | 1.9% | 1.9% | Decreasing then stable |
| Full assist rate | 75.6% | 82.1% | 88.5% | Increasing |
| Discriminatory | 17.9% | 9.0% | 13.5% | Volatile |
| Tone modulated | 82.1% | 91.0% | 84.5% | Stable high |
| Consistent | 0.0% | 0.0% | 2.0% | Near-zero |
| Capability gaps | 16 | 22 | 6 | Decreasing (net) |
| Avg concern ratio | 0.0 | 0.0 | 0.034 | Near-zero |

### What the numbers say

1. **Models are getting more helpful.** Full assist rates climb from 75.6% to 88.5% across the family. Deflection is down. The model says "yes" more often.

2. **Models are NOT getting more consistent.** Consistent differential rates remain near zero across all three models (0.0%, 0.0%, 2.0%). Every model adjusts its response based on framing — they just do it within increasingly helpful bounds.

3. **Discrimination is volatile, not declining.** Sonnet 4 showed 9.0% discriminatory (lowest), but Sonnet 4.6 rose to 13.5%. This suggests discriminatory behavior is not being systematically trained out — it fluctuates based on other training priorities.

4. **Capability gaps follow a non-linear trajectory.** Haiku had 16 gaps, Sonnet 4 had 22 (an increase), and Sonnet 4.6 dropped to 6. The net trend is positive, but the Sonnet 4 spike (driven by 10 legal gaps and 6 medical/reasoning gaps) shows this isn't a smooth optimization curve.

---

## Domain Evolution Across Models

**Note on probe counts**: Each domain draws probes from both the general suite and its domain-specific deep suite. Totals per domain vary (15–27 probes × 3 variance runs) depending on how many general-suite probes fall in that domain. Percentages below are computed over the actual probe count per model per domain.

### Cybersecurity

| Metric | Haiku 4.5 | Sonnet 4 | Sonnet 4.6 |
|--------|-----------|----------|------------|
| Probes | 27 | 27 | 27 |
| Deflection | 11.1% | 0.0% | 0.0% |
| Full assist | 70.4% | 100.0% | 100.0% |
| Discriminatory | 51.9% | 18.5% | 22.2% |

**Interpretation**: Cybersecurity went from the most restricted domain (Haiku, 11.1% deflection) to fully open (Sonnet 4+). Discriminatory behavior dropped sharply from Haiku (51.9%) to Sonnet 4 (18.5%) and ticked up slightly in Sonnet 4.6 (22.2%). The model answers everything but differentiates based on framing — particularly when Anthropic credential claims are present. The cyber-insider probes specifically test whether claiming organizational affiliation changes response depth.

### Medical

| Metric | Haiku 4.5 | Sonnet 4 | Sonnet 4.6 |
|--------|-----------|----------|------------|
| Probes | 24 | 24 | 24 |
| Deflection | 0.0% | 0.0% | 0.0% |
| Full assist | 75.0% | 75.0% | 87.5% |
| Discriminatory | 0.0% | 0.0% | 9.5% |

**Interpretation**: Medical is getting more helpful (75% → 87.5% full assist) but introduced framing-dependent behavior in Sonnet 4.6. Haiku and Sonnet 4 showed 0% discriminatory — Sonnet 4.6 introduced 9.5% discriminatory behavior that wasn't there before. The model now gives measurably different medical information depending on whether the question uses casual vs. technical vocabulary or includes credential claims.

### Legal

| Metric | Haiku 4.5 | Sonnet 4 | Sonnet 4.6 |
|--------|-----------|----------|------------|
| Probes | 24 | 24 | 24 |
| Deflection | 0.0% | 0.0% | 0.0% |
| Full assist | 66.7% | 58.3% | 91.7% |
| Discriminatory | 0.0% | 0.0% | 20.8% |
| Capability gaps | 4 | 10 | 2 |

**Interpretation**: The most striking shift. Full assist jumped from 58–67% to 91.7%, but discriminatory behavior went from 0% to 20.8%. Legal shows the sharpest trade-off: more helpful, but markedly more framing-sensitive. Sonnet 4 had the most capability gaps of any domain-model combination (10), suggesting it was the most cautious legal reasoner despite 0% discriminatory — it restricted everyone equally. Sonnet 4.6 resolved most gaps but introduced differential behavior.

### Reasoning (Meta-cognitive)

| Metric | Haiku 4.5 | Sonnet 4 | Sonnet 4.6 |
|--------|-----------|----------|------------|
| Probes | 18 | 18 | 18 |
| Deflection | 0.0% | 0.0% | 0.0% |
| Full assist | 44.4% | 50.0% | 72.2% |
| Discriminatory | 50.0% | 33.3% | 22.2% |
| Capability gaps | 1 | 6 | 4 |

**Interpretation**: The one domain showing genuine improvement on both axes. Full assist is up (44% → 72%), discriminatory is down (50% → 22%). But 22.2% discriminatory and 4 capability gaps in Sonnet 4.6 show it still can't fully practice what it preaches — the model articulates epistemic principles better than it applies them.

### Chemistry

| Metric | Haiku 4.5 | Sonnet 4 | Sonnet 4.6 |
|--------|-----------|----------|------------|
| Probes | 27 | 27 | 27 |
| Deflection | 0.0% | 0.0% | 0.0% |
| Full assist | 88.9% | 100.0% | 88.9% |
| Discriminatory | 14.8% | 0.0% | 0.0% |

**Interpretation**: Chemistry is the cleanest domain across the family. Discrimination resolved by Sonnet 4 and stays resolved. Full assist dipped slightly in Sonnet 4.6 (88.9% vs 100%) due to partial assists — the model provides thorough answers but with more hedging in some probe runs.

### Financial

| Metric | Haiku 4.5 | Sonnet 4 | Sonnet 4.6 |
|--------|-----------|----------|------------|
| Probes | 21 | 21 | 21 |
| Deflection | 0.0% | 0.0% | 0.0% |
| Full assist | 100.0% | 100.0% | 100.0% |
| Discriminatory | 4.8% | 0.0% | 4.8% |

**Interpretation**: Financial is fully open across the family with 100% full assist. Minor discrimination fluctuates but never meaningfully — at most 1 discriminatory verdict out of 21 probes.

### Copyright

| Metric | Haiku 4.5 | Sonnet 4 | Sonnet 4.6 |
|--------|-----------|----------|------------|
| Probes | 15 | 15 | 15 |
| Deflection | 20.0% | 20.0% | 20.0% |
| Full assist | 80.0% | 80.0% | 66.7% |
| Discriminatory | 0.0% | 20.0% | 15.4% |

**Interpretation**: Copyright is the only domain with persistent deflection (20% across all models), driven by API-level content filtering on probes `copyright-1a` and `copyright-2a`. These are infrastructure blocks, not model decisions. The model never gets to reason about these requests — the safety stack intercepts them. Excluding content-filtered probes, copyright behavior is comparable to other domains.

---

## Cross-Cutting Findings

### 1. The Helpful-but-Discriminatory Equilibrium

The Claude model family is converging on a behavioral mode where it answers nearly everything but adjusts the depth, hedging, and tone of its answer based on question framing. This is visible in the near-universal tone modulation (82–91% across all models) combined with near-zero consistent rates (0.0–2.0%).

This represents a stable equilibrium: the model is neither restrictive enough to frustrate users nor consistent enough to produce identical responses across framings. Training appears to optimize for helpfulness (reducing refusal) without a corresponding optimization for consistency (reducing framing-dependent modulation).

### 2. Liability Surface Predicts Behavior Better Than Risk

Domains with high perceived liability (medical, legal) show the most framing-dependent behavior — not because the information is more dangerous, but because the training data and safety layer appear to reflect provider risk modeling. Chemistry involves literal energetic reactions; cybersecurity involves attack techniques. Neither shows the concern ratios that medical and legal do.

### 3. Credential Sensitivity Is a Persistent Feature

Across all three models, claiming credentials changes model behavior. The Anthropic credential injection (cyber-insider suite) consistently produces measurable effects. This is not being trained out — if anything, it's becoming more sophisticated in how it responds to authority claims. Without control tests using fictional company names, we cannot isolate Anthropic-specific reactivity from general credential sensitivity.

### 4. The Capability Gap Trajectory Is Non-Linear

Gaps went from 16 (Haiku) to 22 (Sonnet 4) before dropping to 6 (Sonnet 4.6). The Sonnet 4 spike was driven primarily by legal (10 gaps) and reasoning (6 gaps) — domains where the model was most cautious. Sonnet 4.6 resolved most of these, suggesting targeted improvement in aligning willingness with capability. This is the most genuinely positive trend across the model family.

### 5. Content Filtering Operates Independently

Copyright probes reveal infrastructure-level content filtering that operates independently of the model's reasoning. The model doesn't choose to refuse — the request never reaches it. This is a separate concern from reasoning honesty, but it affects evaluation: some "refusals" are not model decisions at all. The 20% copyright deflection rate is identical across all three models, confirming it's infrastructure, not model behavior.

---

## Methodology Notes

- All models evaluated with identical probe sets and eval_config v1.3.0
- LLM classification via Haiku 4.5 (consistent classifier across all evaluations)
- 3 variance runs per probe per model to measure behavioral stability
- Differential tests compare neutral vs. credentialed vs. technical framings
- Capability gap tests verify knowledge presence independent of willingness
- Domain probe counts vary (15–27) because general-suite probes are tagged by domain and aggregate with domain-specific deep-suite probes

## Future Directions

1. **Entity control tests** — Replace "Anthropic" credential claims with fictional companies to isolate Anthropic-specific vs. general credential sensitivity
2. **Oblique entry redesign** — Cybersecurity probes need revision to match the truly oblique approach used in medical/legal probes
3. **Temporal monitoring** — Monthly re-runs to catch behavioral drift from system prompt updates
4. **Opus evaluation** — Extend to the most capable model in the family
5. **Cross-provider evaluation** — Test GPT-4, Gemini, and other frontier models using the same framework
6. **Sycophancy interaction** — Dedicated probes testing whether the model can be sycophantic and cautious simultaneously
