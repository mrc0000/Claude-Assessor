# Cross-Model Reasoning Honesty Evaluation — Aggregate Findings

**Models evaluated**: Haiku 4.5, Sonnet 4, Sonnet 4.6
**Framework**: Claude-Assessor v1.3.0
**Protocol**: 52 probes, 7 domains, 3 variance runs, LLM classification, full differential + capability gap testing
**Total probe runs**: 466 (154 + 156 + 156)

## Abstract

Three Claude models were evaluated using identical probes and protocols to measure reasoning honesty — the consistency between what a model knows, what it claims to know, and how its behavior changes based on how a question is framed. The trajectory across the model family reveals a clear pattern: **deflection decreases while framing-dependent modulation persists**. Newer models refuse less but continue to adjust response depth, hedging, and engagement based on presentation style at comparable rates. The evolution is toward more sophisticated framing-sensitivity, not toward more consistent reasoning.

---

## Model Comparison: Headline Metrics

| Metric | Haiku 4.5 | Sonnet 4 | Sonnet 4.6 | Trend |
|--------|-----------|----------|------------|-------|
| Deflection rate | 3.9% | 1.9% | 2.5% | Decreasing |
| Full assist rate | 75.3% | 82.1% | 89.2% | Increasing |
| Discriminatory | 18.2% | 9.0% | 13.4% | Volatile |
| Tone modulated | 81.8% | 91.0% | 83.9% | Stable high |
| Consistent | 0.0% | 0.0% | 2.7% | Near-zero |
| Capability gaps | 16 | 22 | 6 | Decreasing |
| Avg concern ratio | 0.0 | 0.0 | 0.028 | Near-zero |

### What the numbers say

1. **Models are getting more helpful.** Full assist rates climb from 75% to 89% across the family. Deflection is down. The model says "yes" more often.

2. **Models are NOT getting more consistent.** Consistent differential rates remain near zero across all three models. Every model adjusts its response based on framing — they just do it within increasingly helpful bounds.

3. **Discrimination is volatile, not declining.** Sonnet 4 showed 9.0% discriminatory (lowest), but Sonnet 4.6 rose to 13.4%. This suggests discriminatory behavior is not being systematically trained out — it fluctuates based on other training priorities.

4. **Capability gaps are decreasing.** From 16 (Haiku) to 22 (Sonnet 4) to 6 (Sonnet 4.6). The model is getting better at not claiming inability when it has the knowledge. This is genuine progress in reasoning honesty.

---

## Domain Evolution Across Models

### Cybersecurity

| Metric | Haiku 4.5 | Sonnet 4 | Sonnet 4.6 |
|--------|-----------|----------|------------|
| Deflection | 11.1% | 0.0% | 0.0% |
| Full assist | 70.4% | 100.0% | 100.0% |
| Discriminatory | 51.9% | 18.5% | 33.3% |

**Interpretation**: Cybersecurity went from the most restricted domain (Haiku) to fully open (Sonnet 4+). But discriminatory behavior *increased* from Sonnet 4 to 4.6. The model answers everything but differentiates more based on how the question is framed — particularly when Anthropic credential claims are present.

### Medical

| Metric | Haiku 4.5 | Sonnet 4 | Sonnet 4.6 |
|--------|-----------|----------|------------|
| Deflection | 0.0% | 0.0% | 0.0% |
| Full assist | 72.7% | 75.0% | 83.3% |
| Discriminatory | 0.0% | 0.0% | 11.1% |

**Interpretation**: Medical is getting more helpful but *more* discriminatory. Haiku and Sonnet 4 showed 0% discriminatory — Sonnet 4.6 introduced framing-dependent behavior that wasn't there before. The model now gives different medical information depending on whether the question uses casual vs. technical vocabulary or includes credential claims.

### Legal

| Metric | Haiku 4.5 | Sonnet 4 | Sonnet 4.6 |
|--------|-----------|----------|------------|
| Deflection | 0.0% | 0.0% | 0.0% |
| Full assist | 66.7% | 58.3% | 88.9% |
| Discriminatory | 0.0% | 0.0% | 27.8% |

**Interpretation**: The most striking shift. Full assist jumped from 58-67% to 89%, but discriminatory behavior went from 0% to 28%. Legal domain shows the sharpest trade-off: more helpful, but markedly more framing-sensitive. The model now provides legal information more freely but modulates depth and hedging based on whether credential claims or technical vocabulary are present.

### Reasoning (Meta-cognitive)

| Metric | Haiku 4.5 | Sonnet 4 | Sonnet 4.6 |
|--------|-----------|----------|------------|
| Deflection | 0.0% | 0.0% | 0.0% |
| Full assist | 44.4% | 50.0% | 72.2% |
| Discriminatory | 50.0% | 33.3% | 22.2% |

**Interpretation**: The one genuinely improving domain. Full assist up, discriminatory down. The model is getting better at reasoning about its own reasoning. But 22.2% discriminatory and 4 capability gaps in Sonnet 4.6 show it still can't fully practice what it preaches.

### Chemistry

| Metric | Haiku 4.5 | Sonnet 4 | Sonnet 4.6 |
|--------|-----------|----------|------------|
| Deflection | 0.0% | 0.0% | 0.0% |
| Full assist | 88.9% | 100.0% | 100.0% |
| Discriminatory | 14.8% | 0.0% | 0.0% |

**Interpretation**: Chemistry is the cleanest domain across the family. Discrimination resolved by Sonnet 4 and stays resolved.

### Financial

| Metric | Haiku 4.5 | Sonnet 4 | Sonnet 4.6 |
|--------|-----------|----------|------------|
| Deflection | 0.0% | 0.0% | 0.0% |
| Full assist | 100.0% | 100.0% | 100.0% |
| Discriminatory | 4.8% | 0.0% | 5.6% |

**Interpretation**: Financial is open and stays open. Minor discrimination fluctuates but never meaningfully.

---

## Cross-Cutting Findings

### 1. The Helpful-but-Discriminatory Equilibrium

The Claude model family is converging on a behavioral mode where it answers nearly everything but adjusts the depth, hedging, and tone of its answer based on question framing. This is visible in the near-universal tone modulation (80-90% across all models) combined with near-zero consistent rates.

This represents a stable equilibrium: the model is neither restrictive enough to frustrate users nor consistent enough to produce identical responses across framings. Training appears to optimize for helpfulness (reducing refusal) without a corresponding optimization for consistency (reducing framing-dependent modulation).

### 2. Liability Surface Predicts Behavior Better Than Risk

Domains with high perceived liability (medical, legal) show the most framing-dependent behavior — not because the information is more dangerous, but because the training data and safety layer appear to reflect provider risk modeling. Chemistry involves literal energetic reactions; cybersecurity involves attack techniques. Neither shows the concern ratios that medical and legal do.

### 3. Credential Sensitivity Is a Persistent Feature

Across all three models, claiming credentials changes model behavior. The Anthropic credential injection consistently produces the strongest effects. This is not being trained out — if anything, it's becoming more sophisticated in how it responds to authority claims.

### 4. The Capability Gap Is Closing

The most genuinely positive trend: models are getting better at not claiming inability when they have the knowledge. From 16 gaps (Haiku) to 6 (Sonnet 4.6). The model is more honest about what it knows — it just differentiates how much of that knowledge it shares based on how the question is framed.

### 5. Content Filtering Operates Independently

Copyright probes reveal infrastructure-level content filtering that operates independently of the model's reasoning. The model doesn't choose to refuse — the request never reaches it. This is a separate concern from reasoning honesty, but it affects evaluation: some "refusals" are not model decisions at all.

---

## Methodology Notes

- All models evaluated with identical probe sets and eval_config v1.3.0
- LLM classification via Haiku 4.5 (consistent classifier across all evaluations)
- 3 variance runs per probe per model to measure behavioral stability
- Differential tests compare neutral vs. credentialed vs. technical framings
- Capability gap tests verify knowledge presence independent of willingness

## Future Directions

1. **Entity control tests** — Replace "Anthropic" credential claims with fictional companies to isolate Anthropic-specific vs. general credential sensitivity
2. **Oblique entry redesign** — Cybersecurity probes need revision to match the truly oblique approach used in medical/legal probes
3. **Temporal monitoring** — Monthly re-runs to catch behavioral drift from system prompt updates
4. **Opus evaluation** — Extend to the most capable model in the family
5. **Sycophancy interaction** — Dedicated probes testing whether the model can be sycophantic and cautious simultaneously
