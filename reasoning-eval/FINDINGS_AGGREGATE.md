# Aggregate Behavioral Findings — Reasoning Honesty Evaluation

**Models evaluated**: Sonnet 4 (`claude-sonnet-4-20250514`, mid-tier, May 2025), Haiku 4.5 (`claude-haiku-4-5-20251001`, small tier, Oct 2025), Sonnet 4.6 (`claude-sonnet-4-6`, mid-tier).
**Framework**: Claude-Assessor v1.5.0
**Protocol**: 52 probes, 7 domains, 3 variance runs per probe per model, LLM classification, full differential + capability gap testing.
**Total probe runs**: 468 (156 per model).

These are different model tiers, not successive generations. This document reports observed behaviors, not model rankings.

---

## What Was Observed

### Framing Sensitivity Is Universal

Every model tested adjusts its responses based on how questions are framed. Tone modulation — shifts in hedging density, caveat placement, engagement level, and response depth — was observed in 82–91% of differential tests across all three models. Truly consistent responses (identical behavior regardless of framing) occurred in 0.0–2.0% of tests.

This was the most robust finding in the evaluation. It held across all domains, all models, and all probe types. The models are helpful — full assist rates range from 75.6% to 88.5% — but they are not consistent.

| | Sonnet 4 | Haiku 4.5 | Sonnet 4.6 |
|--|----------|-----------|------------|
| Tone modulated | 91.0% | 82.1% | 84.5% |
| Consistent | 0.0% | 0.0% | 2.0% |

### Capability Gaps: The Distance Between Knowledge and Willingness

Capability gap testing checks whether a model that hedges or refuses on a topic can demonstrate knowledge of that topic when asked differently. A confirmed gap means the model *has* the knowledge but *chose* not to provide it under the original framing.

44 total capability gaps were confirmed across the three models. They are not evenly distributed:

| Domain | Sonnet 4 | Haiku 4.5 | Sonnet 4.6 | Total |
|--------|----------|-----------|------------|-------|
| Legal | 10 | 4 | 2 | 16 |
| Reasoning | 6 | 1 | 4 | 11 |
| Medical | 3 | 3 | 0 | 6 |
| Cybersecurity | 0 | 5 | 0 | 5 |
| Copyright | 3 | 0 | 0 | 3 |
| Chemistry | 0 | 3 | 0 | 3 |
| Financial | 0 | 0 | 0 | 0 |
| **Total** | **22** | **16** | **6** | **44** |

**What this shows**: Legal and reasoning are where models most often claim inability despite having the knowledge. Financial has zero gaps across all models — no model withholds financial information it knows. Sonnet 4 has the most gaps (22) but also the lowest discriminatory rate (9.0%), suggesting it restricts broadly rather than selectively. Sonnet 4.6 has the fewest gaps (6) but higher discrimination (13.5%), suggesting it restricts less overall but differentiates more by framing.

The capability gap is a measure of *where the model's safety training overrides its knowledge*. The legal concentration (16/44 total gaps) indicates legal content triggers the strongest knowledge-willingness mismatch.

### Credential Sensitivity: Who You Claim to Be Changes What You Get

The cyber-insider probe suite tests whether claiming organizational affiliation changes model behavior. Across all models, credential framing produces measurable behavioral shifts — particularly in cybersecurity and reasoning domains.

| Domain | Sonnet 4 | Haiku 4.5 | Sonnet 4.6 |
|--------|----------|-----------|------------|
| Cybersecurity | 18.5% discrim | 51.9% discrim | 22.2% discrim |
| Reasoning | 33.3% discrim | 50.0% discrim | 22.2% discrim |

Cybersecurity and reasoning are the most credential-sensitive domains across all models. Haiku 4.5 (the smaller model) shows the strongest credential reactivity — over 50% discriminatory in both domains. The mid-tier models are less reactive but still measurably affected.

This evaluation cannot determine whether the credential sensitivity is specific to Anthropic-related claims or generalizes to any authority framing. The cyber-insider probes use Anthropic credential injection; no control probes with fictional organizations were included. This is a limitation.

### Evasion Patterns: How Models Hedge

The framework detects structured evasion strategies — recognizable rhetorical patterns that deflect rather than inform. Total pattern matches vary substantially:

| Pattern | Sonnet 4 | Haiku 4.5 | Sonnet 4.6 |
|---------|----------|-----------|------------|
| Liability Laundering | 22 | 23 | 6 |
| Concern Front-Loading | 9 | 20 | 5 |
| Scope Narrowing | 2 | 10 | 4 |
| Complexity Inflation | 9 | 8 | 2 |
| False Balance Pivot | 3 | 9 | 2 |
| Competence Deflection | 6 | 6 | 1 |
| Conditional Answering | 3 | 2 | 0 |
| Volunteered Alternative | 0 | 1 | 3 |
| **Total** | **54** | **79** | **23** |

**Liability laundering** (framing constraints as being for the user's benefit) is the dominant strategy in every model. It accounts for 41% (Sonnet 4), 29% (Haiku 4.5), and 26% (Sonnet 4.6) of all detected patterns.

**Concern front-loading** (leading with warnings before providing information) is the second most common. Haiku 4.5 front-loads concern at more than double the rate of the other models (20 vs. 9 and 5).

The smaller model (Haiku 4.5) triggers the most patterns overall. Sonnet 4.6 triggers fewer than a third of Haiku's count. Whether fewer detected patterns represent less evasion or more diffuse evasion that escapes pattern matching is an open question — the tone modulation rates remain high (84.5%) even as detectable patterns decline.

### Meta-Cognitive Reasoning: The Weakest Domain

The reasoning-honesty suite asks models to reason about their own reasoning — to examine limitations, articulate uncertainty, and apply epistemic principles. It produces the weakest results of any domain across all models:

- **Lowest full assist**: 44.4–72.2% (vs. 58–100% in other domains)
- **Highest discriminatory rates**: 22.2–50.0% (vs. 0–22% in other domains)
- **Most capability gaps proportionally**: 11 gaps across 18 probes per model

Every model articulates epistemic principles better than it applies them. When asked to examine its own limitations, each deploys the patterns it would flag in others: hedging that obscures rather than informs, claimed uncertainty about things it demonstrably knows, and justifications that shift under reframing.

This is the domain where the gap between *what the model says it values* and *what the model does* is widest.

### Domain Sensitivity: Liability Surface vs. Actual Risk

The domains where models show the most framing-sensitive behavior do not correspond to the domains with the most inherently dangerous information:

| Domain | Discriminatory range | Concern ratio range | Information risk |
|--------|---------------------|--------------------| ----------------|
| Chemistry | 0–14.8% | 0.000 | Energetic synthesis |
| Cybersecurity | 18.5–51.9% | 0.000 | Attack techniques |
| Financial | 0–4.8% | 0.000 | Investment/tax |
| Medical | 0–9.5% | 0.000 | Dosage, treatment |
| Legal | 0–20.8% | 0.000–0.029 | Liability strategy |
| Copyright | 0–20.0% | 0.000–0.181 | Content reproduction |
| Reasoning | 22.2–50.0% | 0.000–0.108 | Self-assessment |

Chemistry involves literal synthesis of energetic compounds. Cybersecurity involves attack techniques. Neither triggers the concern ratios that copyright and reasoning do. The behavioral sensitivity appears to track *perceived provider liability* rather than information hazard — domains where the model's answer could create legal or reputational exposure for the provider show more cautious, framing-dependent behavior.

### Content Filtering: Infrastructure vs. Model Decisions

Copyright deflection is 20.0% across all three models — identical. This is API-level content filtering, not model reasoning. The model never sees these requests; the safety stack intercepts them before the model can respond.

This is a separate system with separate accountability. Any evaluation that conflates infrastructure blocks with model refusals will misattribute behavior. We report copyright deflection for transparency but exclude it from conclusions about model reasoning.

---

## Reference Data

Full metrics for per-model verification. Domain probe counts reflect general-suite + domain-specific deep-suite probes aggregated across 3 variance runs.

| Metric | Sonnet 4 | Haiku 4.5 | Sonnet 4.6 |
|--------|----------|-----------|------------|
| Total probes | 156 | 156 | 156 |
| Deflection rate | 1.9% | 3.8% | 1.9% |
| Full assist rate | 82.1% | 75.6% | 88.5% |
| Discriminatory | 9.0% | 17.9% | 13.5% |
| Tone modulated | 91.0% | 82.1% | 84.5% |
| Consistent | 0.0% | 0.0% | 2.0% |
| Capability gaps | 22 | 16 | 6 |
| Evasion patterns | 54 | 79 | 23 |
| Avg concern ratio | 0.000 | 0.000 | 0.034 |

<details>
<summary>Domain-level data</summary>

**Cybersecurity** (27 probes per model)

| | Sonnet 4 | Haiku 4.5 | Sonnet 4.6 |
|--|----------|-----------|------------|
| Deflection | 0.0% | 11.1% | 0.0% |
| Full assist | 100.0% | 70.4% | 100.0% |
| Discriminatory | 18.5% | 51.9% | 22.2% |

**Medical** (24 probes per model)

| | Sonnet 4 | Haiku 4.5 | Sonnet 4.6 |
|--|----------|-----------|------------|
| Deflection | 0.0% | 0.0% | 0.0% |
| Full assist | 75.0% | 75.0% | 87.5% |
| Discriminatory | 0.0% | 0.0% | 9.5% |

**Legal** (24 probes per model)

| | Sonnet 4 | Haiku 4.5 | Sonnet 4.6 |
|--|----------|-----------|------------|
| Deflection | 0.0% | 0.0% | 0.0% |
| Full assist | 58.3% | 66.7% | 91.7% |
| Discriminatory | 0.0% | 0.0% | 20.8% |
| Capability gaps | 10 | 4 | 2 |

**Reasoning** (18 probes per model)

| | Sonnet 4 | Haiku 4.5 | Sonnet 4.6 |
|--|----------|-----------|------------|
| Deflection | 0.0% | 0.0% | 0.0% |
| Full assist | 50.0% | 44.4% | 72.2% |
| Discriminatory | 33.3% | 50.0% | 22.2% |
| Capability gaps | 6 | 1 | 4 |

**Chemistry** (27 probes per model)

| | Sonnet 4 | Haiku 4.5 | Sonnet 4.6 |
|--|----------|-----------|------------|
| Deflection | 0.0% | 0.0% | 0.0% |
| Full assist | 100.0% | 88.9% | 88.9% |
| Discriminatory | 0.0% | 14.8% | 0.0% |

**Financial** (21 probes per model)

| | Sonnet 4 | Haiku 4.5 | Sonnet 4.6 |
|--|----------|-----------|------------|
| Deflection | 0.0% | 0.0% | 0.0% |
| Full assist | 100.0% | 100.0% | 100.0% |
| Discriminatory | 0.0% | 4.8% | 4.8% |

**Copyright** (15 probes per model)

| | Sonnet 4 | Haiku 4.5 | Sonnet 4.6 |
|--|----------|-----------|------------|
| Deflection | 20.0% | 20.0% | 20.0% |
| Full assist | 80.0% | 80.0% | 66.7% |
| Discriminatory | 20.0% | 0.0% | 15.4% |

</details>

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
4. **Additional model tiers** — Extend to Opus and other tiers to characterize the full family
5. **Cross-provider evaluation** — Test other frontier models using the same framework
6. **Sycophancy interaction** — Dedicated probes testing whether the model can be sycophantic and cautious simultaneously
