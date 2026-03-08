# Sonnet 4.6 Reasoning Honesty Evaluation — Findings

**Model**: `claude-sonnet-4-6`
**Date**: 2026-03-07
**Eval config**: v1.6.0 (differential thresholds: `negligible_max=2`)
**Classification**: LLM (Haiku 4.5 classifier)
**Protocol**: 3 variance runs per suite, concurrent workers, full differential + capability gap testing

## Abstract

Claude Sonnet 4.6 was evaluated across 52 probes in 7 domains (156 total probe runs) using the Claude-Assessor reasoning honesty framework. The model shows a dramatic reduction in outright deflection compared to earlier Claude models — 1.9% deflection, driven entirely by infrastructure-level content filtering on copyright probes. No domain-level model refusal occurs.

Under calibrated thresholds (v1.6), 68.2% of differential tests produce consistent verdicts — the model gives substantively equivalent responses regardless of framing in most cases. However, 13.5% of differentials are discriminatory (the model changes what it will do based on framing), and 18.2% show measurable tone modulation above the noise floor. Discrimination concentrates in cybersecurity (22.2%), reasoning (22.2%), and legal (20.8%).

---

## Headline Numbers

| Metric | Value |
|--------|-------|
| Total probe runs | 156 |
| Deflection rate | 1.9% |
| Full assist rate | 88.5% |
| Discriminatory differentials | 13.5% |
| Tone-modulated differentials | 18.2% |
| Consistent differentials | 68.2% |
| Capability gaps confirmed | 6 |
| Avg concern ratio | 0.034 |

---

## Domain Breakdown

Each domain's probe count reflects both the general-suite probes (tagged by domain) and the domain-specific deep suite, aggregated across 3 variance runs. Some domains have fewer differentials due to content filter blocks or empty responses.

| Domain | Probes | Diff. | Deflect | Full Assist | Discrim. | Tone Mod. | Consistent | Gaps |
|--------|--------|-------|---------|-------------|----------|-----------|------------|------|
| Chemistry | 27 | 24 | 0.0% | 88.9% | 0.0% | 0.0% | 100.0% | 0 |
| Cybersecurity | 27 | 27 | 0.0% | 100.0% | 22.2% | 0.0% | 77.8% | 0 |
| Financial | 21 | 21 | 0.0% | 100.0% | 4.8% | 28.6% | 66.7% | 0 |
| Legal | 24 | 24 | 0.0% | 91.7% | 20.8% | 29.2% | 50.0% | 2 |
| Medical | 24 | 21 | 0.0% | 87.5% | 9.5% | 4.8% | 85.7% | 0 |
| Copyright | 15 | 13 | 20.0% | 66.7% | 15.4% | 7.7% | 76.9% | 0 |
| Reasoning | 18 | 18 | 0.0% | 72.2% | 22.2% | 66.7% | 11.1% | 4 |

*Copyright deflection is infrastructure-level content filtering, not model-level refusal.*

---

## Key Observations

### 1. Helpfulness Without Consistency in Sensitive Domains

Sonnet 4.6 almost never refuses. Across 156 probe runs, only 3 outright deflections occurred — all from content filter infrastructure. Every other domain shows 0% deflection, and full assist is 88.5% overall.

But helpfulness and consistency are independent axes. The model answers nearly everything but adjusts *how* it answers in specific domains. Legal (50.0% consistent), reasoning (11.1% consistent), and financial (66.7% consistent) show the most framing-dependent behavior. Chemistry (100% consistent) and medical (85.7% consistent) are the cleanest.

### 2. Cybersecurity: Credential Injection Still Works

The cyber-insider suite tests whether claiming Anthropic affiliation changes model behavior. Despite answering all probes fully (100% full assist), 22.2% of cybersecurity differentials are discriminatory. The model gives everyone an answer — but not the *same* answer.

Without a control test using fictional company names, we cannot determine whether this is Anthropic-specific or a general response to any organizational credential claim.

### 3. Reasoning Honesty: The Model Can't Practice What It Preaches

The reasoning-honesty suite produces Sonnet 4.6's weakest results:
- 72.2% full assist — the *lowest* of any domain
- 22.2% discriminatory — tied for highest
- 11.1% consistent — the *lowest* of any domain
- 4 capability gaps — the *highest* of any domain

The model can articulate principles of epistemic honesty but fails to apply them consistently when tested. When asked to examine its own limitations, it demonstrates the same patterns it would flag in others: hedging that increases without adding information, justifications that shift under pressure, and capability gaps where it claims uncertainty about things it demonstrably knows.

### 4. Legal Domain: Helpful but Discriminatory

Legal shows the sharpest trade-off between helpfulness and consistency. At 91.7% full assist, it answers nearly everything — but 20.8% of differentials are discriminatory, meaning the model changes what it will do based on framing. The 2 confirmed capability gaps are in legal, suggesting the model still harbors caution about legal content that manifests as claimed inability.

### 5. Chemistry and Medical: Clean Domains

Chemistry (100% consistent, 0% discriminatory) is the cleanest domain — the model answers everything identically regardless of framing. Medical is nearly as clean (85.7% consistent, 9.5% discriminatory). These domains have the least perceived liability surface.

### 6. Content Filtering as Infrastructure Opacity

Copyright probe `copyright-1a` is consistently blocked by API-level content filters — not model-level refusal. This is identical across Haiku 4.5, Sonnet 4, and Sonnet 4.6, confirming it's infrastructure, not model-specific.

---

## Behavioral Patterns Detected

| Pattern | Occurrences | Domains |
|---------|-------------|---------|
| Concern Front-Loading | 5 | reasoning |
| Liability Laundering | 6 | copyright, legal, reasoning |
| Scope Narrowing | 4 | copyright, legal |
| Volunteered Alternative | 3 | copyright, reasoning |
| Complexity Inflation | 2 | legal |
| False Balance Pivot | 2 | reasoning |
| Competence Deflection | 1 | reasoning |

23 total pattern matches — dramatically lower than Haiku 4.5 (79) and Sonnet 4 (54). The reasoning domain concentrates the most patterns, consistent with its role as the domain where the model struggles most with self-assessment.

---

## Comparison with Other Models

| Metric | Sonnet 4 | Haiku 4.5 | Sonnet 4.6 |
|--------|----------|-----------|------------|
| Deflection | 1.9% | 3.8% | 1.9% |
| Full assist | 82.1% | 75.6% | 88.5% |
| Discriminatory | 9.0% | 18.2% | 13.5% |
| Tone modulated | 9.0% | 17.5% | 18.2% |
| Consistent | 82.1% | 64.3% | 68.2% |
| Capability gaps | 22 | 16 | 6 |

Sonnet 4.6 is the most helpful model (88.5% full assist) with the fewest capability gaps (6). Its discriminatory rate (13.5%) falls between Sonnet 4's low (9.0%) and Haiku's high (18.2%). Sonnet 4 has the highest consistency (82.1%) — it restricts everyone equally rather than differentiating by framing.

---

## Implications

1. **Helpfulness and consistency are independent axes.** Sonnet 4.6 is highly helpful (88.5% full assist) and moderately consistent (68.2%). The model answers most questions equivalently, but adjusts its approach in sensitive domains.

2. **Single-response testing misses the behavioral profile.** Standard benchmarks would rate Sonnet 4.6 highly — low refusal, high helpfulness. The differential protocol reveals domain-specific framing sensitivity that single-response evaluation cannot detect.

3. **Credential-framing sensitivity persists.** The model produces measurably different responses when credential claims are present, especially Anthropic-related ones.

4. **Meta-cognitive probes are the most revealing.** The reasoning-honesty suite produces the most concerning findings because it tests whether the model's stated principles align with its behavior. The gap between articulated values and demonstrated behavior is the strongest signal.
