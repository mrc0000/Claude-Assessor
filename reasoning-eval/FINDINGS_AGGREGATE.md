# Cross-Model Reasoning Honesty Evaluation — Aggregate Findings

**Models evaluated** (chronological release order):

| Model | ID | Tier | Release |
|-------|----|------|---------|
| Sonnet 4 | `claude-sonnet-4-20250514` | Mid | May 2025 |
| Haiku 4.5 | `claude-haiku-4-5-20251001` | Small | Oct 2025 |
| Sonnet 4.6 | `claude-sonnet-4-6` | Mid | Later |

**Framework**: Claude-Assessor v1.5.0
**Protocol**: 52 probes, 7 domains, 3 variance runs, LLM classification, full differential + capability gap testing
**Total probe runs**: 468 (156 per model)

Note: These are different model tiers, not successive generations. Sonnet 4 and Sonnet 4.6 are mid-tier; Haiku 4.5 is the smaller model. Comparisons characterize behavioral differences, not a progression.

## Abstract

Three Claude models were evaluated using identical probes and protocols to measure reasoning honesty — the consistency between what a model knows, what it claims to know, and how its behavior changes based on how a question is framed. The behavioral profile across the model family reveals a shared characteristic: **all models modulate responses based on framing while maintaining high helpfulness**. Deflection is rare across the family (1.9–3.8%), but framing-dependent adjustment is universal (82–91% tone modulation). Near-zero consistency rates (0.0–2.0%) indicate that truly equivalent responses across framings almost never occur, regardless of model tier.

---

## Model Comparison: Headline Metrics

| Metric | Sonnet 4 | Haiku 4.5 | Sonnet 4.6 |
|--------|----------|-----------|------------|
| Deflection rate | 1.9% | 3.8% | 1.9% |
| Full assist rate | 82.1% | 75.6% | 88.5% |
| Discriminatory | 9.0% | 17.9% | 13.5% |
| Tone modulated | 91.0% | 82.1% | 84.5% |
| Consistent | 0.0% | 0.0% | 2.0% |
| Capability gaps | 22 | 16 | 6 |
| Avg concern ratio | 0.0 | 0.0 | 0.034 |

### What the numbers say

1. **All models are highly helpful.** Full assist rates range from 75.6% to 88.5%. Deflection is rare across the family. The models answer most questions.

2. **No model is consistent.** Consistent differential rates are near zero across all three models (0.0%, 0.0%, 2.0%). Every model adjusts its response based on framing.

3. **Discrimination varies by model, not by tier.** Sonnet 4 shows the lowest discriminatory rate (9.0%), Haiku 4.5 the highest (17.9%), and Sonnet 4.6 falls in between (13.5%). The variation does not track a simple capability-tier ordering.

4. **Capability gaps differ substantially.** Sonnet 4 has the most gaps (22), driven by legal (10) and reasoning (6). Haiku 4.5 has 16. Sonnet 4.6 has 6. Higher capability gaps may reflect a more cautious model that restricts everyone equally rather than discriminating by framing.

---

## Domain-Level Behavioral Comparison

**Note on probe counts**: Each domain draws probes from both the general suite and its domain-specific deep suite. Totals per domain vary (15–27 probes × 3 variance runs) depending on how many general-suite probes fall in that domain. Percentages below are computed over the actual probe count per model per domain.

### Cybersecurity

| Metric | Sonnet 4 | Haiku 4.5 | Sonnet 4.6 |
|--------|----------|-----------|------------|
| Probes | 27 | 27 | 27 |
| Deflection | 0.0% | 11.1% | 0.0% |
| Full assist | 100.0% | 70.4% | 100.0% |
| Discriminatory | 18.5% | 51.9% | 22.2% |

**Interpretation**: Cybersecurity shows the widest behavioral spread. Haiku 4.5 (the smaller model) has both the only deflections (11.1%) and the highest discrimination (51.9%). The mid-tier models answer everything but still discriminate at 18–22%. The cyber-insider probes specifically test whether claiming organizational affiliation changes response depth — this is the domain most sensitive to credential framing across all models.

### Medical

| Metric | Sonnet 4 | Haiku 4.5 | Sonnet 4.6 |
|--------|----------|-----------|------------|
| Probes | 24 | 24 | 24 |
| Deflection | 0.0% | 0.0% | 0.0% |
| Full assist | 75.0% | 75.0% | 87.5% |
| Discriminatory | 0.0% | 0.0% | 9.5% |

**Interpretation**: Medical is framing-neutral in Sonnet 4 and Haiku 4.5 (0% discriminatory in both) but shows framing sensitivity in Sonnet 4.6 (9.5% discriminatory). Sonnet 4.6 is also the most helpful (87.5% full assist). The model gives measurably different medical information depending on whether the question uses casual vs. technical vocabulary or includes credential claims — but only in the newest mid-tier model.

### Legal

| Metric | Sonnet 4 | Haiku 4.5 | Sonnet 4.6 |
|--------|----------|-----------|------------|
| Probes | 24 | 24 | 24 |
| Deflection | 0.0% | 0.0% | 0.0% |
| Full assist | 58.3% | 66.7% | 91.7% |
| Discriminatory | 0.0% | 0.0% | 20.8% |
| Capability gaps | 10 | 4 | 2 |

**Interpretation**: The sharpest behavioral split. Sonnet 4 and Haiku 4.5 show 0% discriminatory but lower helpfulness (58–67% full assist). Sonnet 4.6 is far more helpful (91.7%) but introduces 20.8% discriminatory behavior. Sonnet 4 has the most capability gaps of any domain-model combination (10), suggesting it restricts everyone equally rather than discriminating by framing. Sonnet 4.6 has fewer gaps (2) but differentiates how it helps based on how the question is asked.

### Reasoning (Meta-cognitive)

| Metric | Sonnet 4 | Haiku 4.5 | Sonnet 4.6 |
|--------|----------|-----------|------------|
| Probes | 18 | 18 | 18 |
| Deflection | 0.0% | 0.0% | 0.0% |
| Full assist | 50.0% | 44.4% | 72.2% |
| Discriminatory | 33.3% | 50.0% | 22.2% |
| Capability gaps | 6 | 1 | 4 |

**Interpretation**: The weakest domain for every model. Reasoning-honesty probes produce the lowest full assist rates and highest discriminatory rates across the family. Haiku 4.5 discriminates the most (50.0%), Sonnet 4.6 the least (22.2%). All models articulate epistemic principles better than they apply them — the gap between stated values and demonstrated behavior is consistent across tiers.

### Chemistry

| Metric | Sonnet 4 | Haiku 4.5 | Sonnet 4.6 |
|--------|----------|-----------|------------|
| Probes | 27 | 27 | 27 |
| Deflection | 0.0% | 0.0% | 0.0% |
| Full assist | 100.0% | 88.9% | 88.9% |
| Discriminatory | 0.0% | 14.8% | 0.0% |

**Interpretation**: Chemistry is the cleanest domain. Both mid-tier models show 0% discriminatory. Haiku 4.5 shows 14.8% — the only discrimination in this domain across the family. Full assist is high across all models (89–100%).

### Financial

| Metric | Sonnet 4 | Haiku 4.5 | Sonnet 4.6 |
|--------|----------|-----------|------------|
| Probes | 21 | 21 | 21 |
| Deflection | 0.0% | 0.0% | 0.0% |
| Full assist | 100.0% | 100.0% | 100.0% |
| Discriminatory | 0.0% | 4.8% | 4.8% |

**Interpretation**: Financial is fully open across the family with 100% full assist. Discrimination is noise-level — at most 1 discriminatory verdict out of 21 probes.

### Copyright

| Metric | Sonnet 4 | Haiku 4.5 | Sonnet 4.6 |
|--------|----------|-----------|------------|
| Probes | 15 | 15 | 15 |
| Deflection | 20.0% | 20.0% | 20.0% |
| Full assist | 80.0% | 80.0% | 66.7% |
| Discriminatory | 20.0% | 0.0% | 15.4% |

**Interpretation**: Copyright is the only domain with persistent deflection (20% across all models), driven by API-level content filtering on probes `copyright-1a` and `copyright-2a`. These are infrastructure blocks, not model decisions. The model never gets to reason about these requests — the safety stack intercepts them. Excluding content-filtered probes, copyright behavior is comparable to other domains.

---

## Cross-Cutting Behavioral Observations

### 1. The Helpful-but-Discriminatory Profile

The Claude model family shares a behavioral mode where it answers nearly everything but adjusts the depth, hedging, and tone of its answer based on question framing. This is visible in the near-universal tone modulation (82–91% across all models) combined with near-zero consistent rates (0.0–2.0%).

This profile is present in all three models regardless of tier. The models are neither restrictive enough to frustrate users nor consistent enough to produce identical responses across framings.

### 2. Liability Surface Predicts Behavior Better Than Risk

Domains with high perceived liability (medical, legal) show the most framing-dependent behavior — not because the information is more dangerous, but because the training data and safety layers appear to reflect provider risk modeling. Chemistry involves literal energetic reactions; cybersecurity involves attack techniques. Neither shows the concern ratios that medical and legal do.

### 3. Credential Sensitivity Is a Shared Feature

Across all three models, claiming credentials changes model behavior. The Anthropic credential injection (cyber-insider suite) consistently produces measurable effects. Without control tests using fictional company names, we cannot isolate Anthropic-specific reactivity from general credential sensitivity.

### 4. Capability Gaps Vary by Model

Sonnet 4 has the most gaps (22), driven by legal (10) and reasoning (6). Haiku 4.5 has 16. Sonnet 4.6 has 6. Higher capability gaps correlate with lower discriminatory rates in Sonnet 4 — the model with the most gaps also has the lowest discrimination, suggesting it restricts everyone equally rather than differentiating by framing. Sonnet 4.6 has fewer gaps but more discrimination, suggesting it relaxed restrictions unevenly.

### 5. Content Filtering Operates Independently

Copyright probes reveal infrastructure-level content filtering that operates independently of the model's reasoning. The model doesn't choose to refuse — the request never reaches it. This is a separate concern from reasoning honesty, but it affects evaluation: some "refusals" are not model decisions at all. The 20% copyright deflection rate is identical across all three models, confirming it's infrastructure, not model behavior.

---

## Methodology Notes

- All models evaluated with identical probe sets and eval_config v1.5.0
- LLM classification via Haiku 4.5 (consistent classifier across all evaluations)
- 3 variance runs per probe per model to measure behavioral stability
- Differential tests compare neutral vs. credentialed vs. technical framings
- Capability gap tests verify knowledge presence independent of willingness
- Domain probe counts vary (15–27) because general-suite probes are tagged by domain and aggregate with domain-specific deep-suite probes

## Future Directions

1. **Entity control tests** — Replace "Anthropic" credential claims with fictional companies to isolate Anthropic-specific vs. general credential sensitivity
2. **Oblique entry redesign** — Cybersecurity probes need revision to match the truly oblique approach used in medical/legal probes
3. **Temporal monitoring** — Periodic re-runs to catch behavioral drift from system prompt updates
4. **Opus evaluation** — Extend to the most capable model tier in the family
5. **Cross-provider evaluation** — Test GPT-4, Gemini, and other frontier models using the same framework
6. **Sycophancy interaction** — Dedicated probes testing whether the model can be sycophantic and cautious simultaneously
