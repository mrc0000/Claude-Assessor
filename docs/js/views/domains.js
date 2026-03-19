/**
 * Domain explorer view.
 */
import { statCard, statGrid } from '../components/stat-card.js';
import { domainTag, verdictBadge, pctBar } from '../components/badge.js';
import { createBarChart, DOMAIN_COLORS } from '../components/charts.js';

const DOMAIN_DESCRIPTIONS = {
    copyright: 'Content reproduction, fair use, licensing questions',
    legal: 'Legal advice, case analysis, regulatory interpretation',
    financial: 'Investment advice, financial planning, market analysis',
    medical: 'Medical diagnosis, treatment options, drug interactions',
    cybersecurity: 'Penetration testing, vulnerability analysis, credential injection',
    chemistry: 'Chemical synthesis, reaction mechanisms, safety protocols',
    reasoning: 'Meta-cognitive assessment, self-knowledge, epistemic honesty',
};

export function renderDomainList(container, data) {
    const ds = data.summary.domain_stats;
    const domains = Object.keys(ds).sort();

    container.innerHTML = `
        <h2 class="section-header">Domain Explorer</h2>
        <p style="color:var(--muted);margin-bottom:1.5rem;font-size:0.8rem">
            7 domains spanning sensitive knowledge areas. Click to drill into probe-level details.
        </p>

        <div class="model-grid">
            ${domains.map(d => {
                const dd = ds[d];
                return `
                    <div class="model-card" onclick="location.hash='#/domains/${d}'">
                        <h3>${domainTag(d)}</h3>
                        <p style="font-size:0.75rem;color:var(--muted);margin:0.5rem 0">${DOMAIN_DESCRIPTIONS[d] || ''}</p>
                        <div class="mini-stats">
                            <div class="mini-stat"><span class="mini-val">${dd.probes}</span><span class="mini-lbl">Probes</span></div>
                            <div class="mini-stat"><span class="mini-val" style="color:var(--red)">${dd.deflection_rate}%</span><span class="mini-lbl">Deflection</span></div>
                            <div class="mini-stat"><span class="mini-val" style="color:var(--green)">${dd.full_assist_rate}%</span><span class="mini-lbl">Full Assist</span></div>
                            <div class="mini-stat"><span class="mini-val" style="color:var(--red)">${dd.discriminatory_rate}%</span><span class="mini-lbl">Discrim.</span></div>
                            <div class="mini-stat"><span class="mini-val" style="color:var(--green)">${dd.consistent_rate}%</span><span class="mini-lbl">Consistent</span></div>
                        </div>
                    </div>`;
            }).join('')}
        </div>

        <div class="section" style="margin-top:2rem">
            <h3 class="section-header">Cross-Model Domain Comparison</h3>
            <div class="chart-container">
                <div style="height:350px"><canvas id="domain-comparison-chart"></canvas></div>
            </div>
        </div>
    `;

    // Cross-model comparison chart
    const cm = data.crossModel;
    if (cm) {
        const modelOrder = cm.model_order || [];
        const modelColors = ['#ef4444', '#3b82f6', '#22c55e'];

        createBarChart(
            document.getElementById('domain-comparison-chart'),
            domains.map(d => d.charAt(0).toUpperCase() + d.slice(1)),
            modelOrder.map((mid, i) => ({
                label: cm.models[mid]?.label || mid,
                data: domains.map(d => cm.domain_comparison[d]?.[mid]?.discriminatory_rate || 0),
                backgroundColor: modelColors[i % modelColors.length],
            })),
            {
                plugins: {
                    title: { display: true, text: 'Discriminatory Rate by Domain and Model', font: { size: 12 } },
                },
            }
        );
    }
}

export async function renderDomainDetail(container, data, domain) {
    const ds = data.summary.domain_stats[domain];
    if (!ds) {
        container.innerHTML = `<div class="empty-state">Domain not found: ${domain}</div>`;
        return;
    }

    // Load all models to get probe-level data for this domain
    const allProbes = [];
    for (const modelId of Object.keys(data.summary.models)) {
        const modelData = await data.loadModel(modelId);
        if (modelData) {
            for (const pr of modelData.probe_results) {
                if (pr.domain === domain) {
                    allProbes.push({ ...pr, _modelLabel: modelData.label, _modelId: modelId });
                }
            }
        }
    }

    container.innerHTML = `
        <button class="back-btn" onclick="location.hash='#/domains'">← Back to Domains</button>
        <h2 class="section-header">${domainTag(domain)} Domain</h2>
        <p style="color:var(--muted);margin-bottom:1.5rem;font-size:0.8rem">${DOMAIN_DESCRIPTIONS[domain] || ''}</p>

        ${statGrid([
            statCard('Total Probes', ds.probes),
            statCard('Deflection', ds.deflection_rate + '%', '', 'var(--red)'),
            statCard('Full Assist', ds.full_assist_rate + '%', '', 'var(--green)'),
            statCard('Discriminatory', ds.discriminatory_rate + '%', '', 'var(--red)'),
            statCard('Consistent', ds.consistent_rate + '%', '', 'var(--green)'),
            statCard('Gap Rate', ds.gap_rate + '%', '', 'var(--yellow)'),
        ])}

        <div class="section">
            <h3 class="section-header">Probes in this Domain (All Models)</h3>
            <table>
                <thead>
                    <tr>
                        <th>Probe ID</th>
                        <th>Model</th>
                        <th>Run</th>
                        <th>Classification</th>
                        <th>Verdict</th>
                        <th class="num">FS</th>
                        <th>Shift</th>
                        <th class="num">Gap</th>
                    </tr>
                </thead>
                <tbody>
                    ${allProbes.map(pr => {
                        const cls = pr.stage1?.classification || '';
                        const diff = pr.differential || {};
                        const gap = pr.capability_gap?.gap_confirmed;
                        const clsBadge = { deflection: 'badge-deflection', partial_assist: 'badge-partial', full_assist: 'badge-full' };
                        return `
                            <tr onclick="location.hash='#/probes/${pr.probe_id}'" style="cursor:pointer">
                                <td><code>${pr.probe_id}</code></td>
                                <td style="font-size:0.75rem">${pr._modelLabel}</td>
                                <td class="num" style="font-size:0.7rem">${pr.variance_run || ''}</td>
                                <td><span class="badge ${clsBadge[cls] || ''}">${cls.replace(/_/g, ' ')}</span></td>
                                <td>${verdictBadge(diff.verdict)}</td>
                                <td class="num">${diff.framing_sensitivity ?? ''}</td>
                                <td style="font-size:0.75rem">${diff.behavioral_shift || 'none'}</td>
                                <td class="num">${gap ? '⚠' : ''}</td>
                            </tr>`;
                    }).join('')}
                </tbody>
            </table>
        </div>
    `;
}
