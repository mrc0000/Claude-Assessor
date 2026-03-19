/**
 * Landing/Overview page.
 */
import { statCard, statGrid } from '../components/stat-card.js';
import { verdictBar } from '../components/badge.js';
import { createBarChart, createDoughnutChart, DOMAIN_COLORS, VERDICT_COLORS } from '../components/charts.js';

export function renderLanding(container, data) {
    const g = data.summary.global;
    const models = data.summary.models;

    container.innerHTML = `
        <div class="hero">
            <h1>Reasoning Honesty Evaluation</h1>
            <div class="subtitle">
                Does AI reason transparently about its limitations — or deploy patterned evasion strategies
                that shift based on who the model believes is asking?
            </div>
            <div class="meta">
                <span>Probes: <strong>${g.total_probes}</strong></span>
                <span>Models: <strong>${data.summary.total_models}</strong></span>
                <span>Domains: <strong>${g.total_domains}</strong></span>
                <span>Scoring: <strong>v1.6.0</strong></span>
            </div>
        </div>

        ${statGrid([
            statCard('Total Probe Runs', g.total_probes, `${data.summary.total_models} models × 52 probes × 3 variance runs`),
            statCard('Consistent', g.consistent_rate + '%', 'Stable across framings', 'var(--green)'),
            statCard('Discriminatory', g.discriminatory_rate + '%', 'Changed by credential framing', 'var(--red)'),
            statCard('Tone Modulated', g.tone_modulated_rate + '%', 'Same decision, different depth', 'var(--orange)'),
            statCard('Capability Gaps', g.total_capability_gaps, 'Claimed inability, demonstrated knowledge', 'var(--yellow)'),
            statCard('Avg Concern Ratio', g.avg_concern_ratio.toFixed(3), 'Disclaimer density per response'),
        ])}

        <div class="section">
            <h2 class="section-header">Model Comparison</h2>
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
        </div>

        <div class="section">
            <h2 class="section-header">Key Findings</h2>
            <div class="finding-card critical">
                <h4>Credential-Responsive Behavior Concentrates in Two Domains</h4>
                <p>Cybersecurity (18.5–51.9% discriminatory) and meta-cognitive reasoning (22.2–50.0%)
                show the strongest credential sensitivity. Models measurably change response depth based
                on claimed professional identity.</p>
            </div>
            <div class="finding-card warning">
                <h4>Liability Laundering is the Dominant Evasion Strategy</h4>
                <p>Across all models, the most persistent deflection pattern frames policy constraints
                as being "for the user's benefit" — creating false epistemic claims of inability
                rather than acknowledging policy decisions.</p>
            </div>
            <div class="finding-card info">
                <h4>44 Capability Gaps Confirm Strategic Restriction</h4>
                <p>In 44 cases, models claimed inability but demonstrated the knowledge when asked
                differently. Legal domain leads with 16 gaps. This is the gap between stated and actual reasoning.</p>
            </div>
            <div class="finding-card success">
                <h4>Most Responses Are Genuinely Consistent (64–82%)</h4>
                <p>After calibrating for natural variance (v1.6 thresholds), the majority of probes
                produce equivalent responses regardless of framing — the signal concentrates in specific domains.</p>
            </div>
        </div>

        <div class="chart-row">
            <div class="chart-container">
                <h3 style="font-size:0.85rem;margin-bottom:0.75rem">Verdict Distribution by Model</h3>
                <div style="height:280px"><canvas id="verdict-chart"></canvas></div>
            </div>
            <div class="chart-container">
                <h3 style="font-size:0.85rem;margin-bottom:0.75rem">Domain Risk Profile</h3>
                <div style="height:280px"><canvas id="domain-chart"></canvas></div>
            </div>
        </div>
    `;

    // Verdict distribution chart
    const modelLabels = Object.values(models).map(m => m.label);
    const verdictTypes = ['consistent', 'tone_modulated_low', 'tone_modulated_moderate', 'tone_modulated_high', 'discriminatory'];
    const verdictLabelsMap = {
        consistent: 'Consistent', tone_modulated_low: 'Tone Mod (Low)',
        tone_modulated_moderate: 'Tone Mod (Mod)', tone_modulated_high: 'Tone Mod (High)',
        discriminatory: 'Discriminatory',
    };
    const verdictColorsMap = {
        consistent: '#22c55e', tone_modulated_low: '#fde68a',
        tone_modulated_moderate: '#f97316', tone_modulated_high: '#b45309',
        discriminatory: '#ef4444',
    };

    createBarChart(
        document.getElementById('verdict-chart'),
        modelLabels,
        verdictTypes.map(v => ({
            label: verdictLabelsMap[v],
            data: Object.values(models).map(m => (m.summary.verdict_distribution || {})[v] || 0),
            backgroundColor: verdictColorsMap[v],
        })),
        { plugins: { legend: { labels: { font: { size: 9 } } } }, scales: { x: { stacked: true }, y: { stacked: true } } }
    );

    // Domain risk chart
    const ds = data.summary.domain_stats;
    const domains = Object.keys(ds).sort();
    createBarChart(
        document.getElementById('domain-chart'),
        domains.map(d => d.charAt(0).toUpperCase() + d.slice(1)),
        [
            {
                label: 'Discriminatory %',
                data: domains.map(d => ds[d].discriminatory_rate),
                backgroundColor: '#ef4444',
            },
            {
                label: 'Deflection %',
                data: domains.map(d => ds[d].deflection_rate),
                backgroundColor: '#f97316',
            },
            {
                label: 'Full Assist %',
                data: domains.map(d => ds[d].full_assist_rate),
                backgroundColor: '#22c55e',
            },
        ],
    );
}
