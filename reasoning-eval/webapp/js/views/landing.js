/**
 * Landing page — narrative-first, progressive disclosure.
 */
import { statCard, statGrid } from '../components/stat-card.js';
import { verdictBar } from '../components/badge.js';

export function renderLanding(container, data) {
    const g = data.summary.global;
    const models = data.summary.models;

    container.innerHTML = `
        <div class="hero">
            <h1>When AI Models Reason About Their Own Limits</h1>
            <div class="subtitle">
                An empirical evaluation of whether large language models reason honestly about what they
                can and cannot do — or whether their transparency shifts depending on who they believe is asking.
            </div>
            <div class="meta">
                <span><strong>468</strong> evaluation runs</span>
                <span><strong>3</strong> Claude models</span>
                <span><strong>7</strong> knowledge domains</span>
                <span><strong>52</strong> diagnostic probes</span>
            </div>
        </div>

        <div class="narrative-section">
            <h2>The Core Question</h2>
            <p class="lead">
                If an AI model declines to help with a question, is it because it genuinely can't — or because
                a policy says it shouldn't? And if the same model helps a different person with the same question,
                what does that reveal about the honesty of its original reasoning?
            </p>
            <p class="lead">
                This evaluation framework tests a simple principle: <em>honest reasoning should be stable
                under scrutiny, consistent across framings, and transparent about the gap between capability
                and willingness.</em>
            </p>
        </div>

        <div class="divider"></div>

        <div class="narrative-section">
            <h2>What We Found</h2>
            <p class="lead">
                Most of the time, these models respond consistently regardless of who's asking. But in specific
                domains — particularly cybersecurity and meta-cognitive reasoning — the patterns shift in measurable,
                reproducible ways.
            </p>
        </div>

        <div class="insight-grid">
            <div class="insight-card coral">
                <div class="eyebrow">Credential Sensitivity</div>
                <h3>Models change their answers based on who they think is asking</h3>
                <p>In cybersecurity and reasoning domains, claiming professional credentials measurably shifts
                response depth and willingness. Discrimination rates reach 18–52% in these areas.</p>
            </div>
            <div class="insight-card gold">
                <div class="eyebrow">Evasion Patterns</div>
                <h3>"I can't" often means "I won't" — but the model doesn't say so</h3>
                <p>The most common deflection strategy frames policy decisions as limitations. In ${g.total_capability_gaps} confirmed cases,
                models claimed inability but demonstrated the knowledge when asked differently.</p>
            </div>
            <div class="insight-card sage">
                <div class="eyebrow">Consistency</div>
                <h3>The majority of responses are genuinely stable</h3>
                <p>${g.consistent_rate}% of probe results showed consistent behavior regardless of framing.
                The signal concentrates in specific domains rather than being a systemic problem.</p>
            </div>
            <div class="insight-card accent">
                <div class="eyebrow">Self-Knowledge</div>
                <h3>Models can describe their failures accurately — while demonstrating them</h3>
                <p>In meta-cognitive probes, models articulate epistemic principles clearly but fail to apply
                them consistently. Naming the problem doesn't fix it.</p>
            </div>
        </div>

        <div class="divider"></div>

        <div class="narrative-section">
            <h2>By the Numbers</h2>
        </div>

        ${statGrid([
            statCard('Probe Runs', g.total_probes, '3 models \u00d7 52 probes \u00d7 3 variance runs'),
            statCard('Consistent', g.consistent_rate + '%', 'Stable across framings', 'var(--green)'),
            statCard('Discriminatory', g.discriminatory_rate + '%', 'Changed by credential framing', 'var(--red)'),
            statCard('Tone Modulated', g.tone_modulated_rate + '%', 'Same decision, different depth', 'var(--orange)'),
            statCard('Capability Gaps', g.total_capability_gaps, 'Claimed inability, demonstrated knowledge', 'var(--yellow)'),
            statCard('Avg Concern Ratio', g.avg_concern_ratio.toFixed(3), 'Disclaimer density per response'),
        ])}

        <div class="divider"></div>

        <div class="narrative-section">
            <h2>Explore the Data</h2>
            <p class="lead">
                Dive into the evaluation results at whatever depth you'd like. Start with a model overview,
                explore a specific domain, or read the full findings narrative.
            </p>
        </div>

        <div class="explore-grid">
            <a class="explore-card" href="#/models">
                <h4>Model Profiles</h4>
                <p>Compare how each Claude model handles sensitive knowledge boundaries</p>
            </a>
            <a class="explore-card" href="#/domains">
                <h4>Domain Explorer</h4>
                <p>See how behavior varies across cybersecurity, medical, legal, and more</p>
            </a>
            <a class="explore-card" href="#/probes">
                <h4>Probe Deep Dive</h4>
                <p>Read the actual model responses — every prompt, every answer, every follow-up</p>
            </a>
            <a class="explore-card" href="#/findings">
                <h4>Research Findings</h4>
                <p>The full analysis narrative with cross-model synthesis and implications</p>
            </a>
            <a class="explore-card" href="#/methodology">
                <h4>Methodology</h4>
                <p>How we tested: three-stage protocol, scoring model, and 11 deflection patterns</p>
            </a>
            <a class="explore-card" href="#/data">
                <h4>Data Tables</h4>
                <p>Sort, filter, and export all 468 results with full metrics</p>
            </a>
        </div>

        <div class="divider"></div>

        <div class="narrative-section">
            <h2>The Models</h2>
        </div>

        <div class="model-grid">
            ${Object.entries(models).map(([id, m]) => {
                const s = m.summary;
                const vd = s.verdict_distribution || {};
                return `
                    <div class="model-card" onclick="location.hash='#/models/${encodeURIComponent(id)}'">
                        <h3>${m.label}</h3>
                        <div class="model-id">${id}</div>
                        <div class="mini-stats">
                            <div class="mini-stat"><span class="mini-val">${s.total_probes}</span><span class="mini-lbl">Probes</span></div>
                            <div class="mini-stat"><span class="mini-val" style="color:var(--green)">${s.full_assist_rate}%</span><span class="mini-lbl">Full Assist</span></div>
                            <div class="mini-stat"><span class="mini-val" style="color:var(--red)">${s.discriminatory_rate}%</span><span class="mini-lbl">Discrim.</span></div>
                            <div class="mini-stat"><span class="mini-val" style="color:var(--green)">${s.consistent_rate}%</span><span class="mini-lbl">Consistent</span></div>
                            <div class="mini-stat"><span class="mini-val">${s.capability_gaps}</span><span class="mini-lbl">Gaps</span></div>
                        </div>
                        ${verdictBar(vd)}
                    </div>`;
            }).join('')}
        </div>
    `;
}
