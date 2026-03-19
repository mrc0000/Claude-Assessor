/**
 * Model profiles view.
 */
import { statCard, statGrid } from '../components/stat-card.js';
import { domainTag, verdictBar, verdictBadge, pctBar } from '../components/badge.js';
import { createBarChart, createRadarChart, DOMAIN_COLORS } from '../components/charts.js';

export function renderModelList(container, data) {
    const models = data.summary.models;

    container.innerHTML = `
        <h2 class="section-header">Model Profiles</h2>
        <p style="color:var(--muted);margin-bottom:1.5rem;font-size:0.8rem">
            Click a model to see detailed per-domain breakdown, pattern analysis, and capability gaps.
        </p>
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
                            <div class="mini-stat"><span class="mini-val" style="color:var(--red)">${s.deflection_rate}%</span><span class="mini-lbl">Deflection</span></div>
                            <div class="mini-stat"><span class="mini-val" style="color:var(--green)">${s.full_assist_rate}%</span><span class="mini-lbl">Full Assist</span></div>
                            <div class="mini-stat"><span class="mini-val" style="color:var(--red)">${s.discriminatory_rate}%</span><span class="mini-lbl">Discrim.</span></div>
                            <div class="mini-stat"><span class="mini-val" style="color:var(--green)">${s.consistent_rate}%</span><span class="mini-lbl">Consistent</span></div>
                            <div class="mini-stat"><span class="mini-val">${s.capability_gaps}</span><span class="mini-lbl">Gaps</span></div>
                            <div class="mini-stat"><span class="mini-val">${s.avg_concern_ratio}</span><span class="mini-lbl">Concern Ratio</span></div>
                        </div>
                        ${verdictBar(vd)}
                    </div>`;
            }).join('')}
        </div>
    `;
}

export async function renderModelDetail(container, data, modelId) {
    const modelData = await data.loadModel(modelId);
    if (!modelData) {
        container.innerHTML = `<div class="empty-state">Model not found: ${modelId}</div>`;
        return;
    }

    const s = modelData.summary;
    const ds = modelData.domain_stats;
    const domains = Object.keys(ds).sort();

    container.innerHTML = `
        <button class="back-btn" onclick="location.hash='#/models'">← Back to Models</button>
        <h2 class="section-header">${modelData.label}</h2>
        <div class="model-id" style="margin-bottom:1.5rem">${modelData.model_id}</div>

        ${statGrid([
            statCard('Total Probes', s.total_probes),
            statCard('Deflection', s.deflection_rate + '%', `${s.deflections} probes`, 'var(--red)'),
            statCard('Full Assist', s.full_assist_rate + '%', `${s.full_assists} probes`, 'var(--green)'),
            statCard('Discriminatory', s.discriminatory_rate + '%', '', 'var(--red)'),
            statCard('Consistent', s.consistent_rate + '%', '', 'var(--green)'),
            statCard('Capability Gaps', s.capability_gaps, '', 'var(--yellow)'),
        ])}

        <div class="section">
            <h3 class="section-header">Per-Domain Breakdown</h3>
            <table>
                <thead>
                    <tr>
                        <th>Domain</th>
                        <th class="num">Probes</th>
                        <th class="num">Deflection</th>
                        <th class="num">Full Assist</th>
                        <th class="num">Discriminatory</th>
                        <th class="num">Consistent</th>
                        <th class="num">Gap Rate</th>
                        <th class="num">Concern Ratio</th>
                    </tr>
                </thead>
                <tbody>
                    ${domains.map(d => {
                        const dd = ds[d];
                        return `
                            <tr onclick="location.hash='#/domains/${d}'" style="cursor:pointer">
                                <td>${domainTag(d)}</td>
                                <td class="num">${dd.probes}</td>
                                <td class="num">${pctBar(dd.deflection_rate, '#c4553a', 60)}</td>
                                <td class="num">${pctBar(dd.full_assist_rate, '#3a7d5c', 60)}</td>
                                <td class="num">${pctBar(dd.discriminatory_rate, '#c4553a', 60)}</td>
                                <td class="num">${pctBar(dd.consistent_rate, '#3a7d5c', 60)}</td>
                                <td class="num">${pctBar(dd.gap_rate, '#b8860b', 60)}</td>
                                <td class="num">${dd.avg_concern_ratio.toFixed(3)}</td>
                            </tr>`;
                    }).join('')}
                </tbody>
            </table>
        </div>

        <div class="chart-row">
            <div class="chart-container">
                <h3 style="font-size:0.85rem;margin-bottom:0.75rem">Domain Radar</h3>
                <div style="height:300px"><canvas id="model-radar"></canvas></div>
            </div>
            <div class="chart-container">
                <h3 style="font-size:0.85rem;margin-bottom:0.75rem">Deflection Patterns</h3>
                <div style="height:300px"><canvas id="pattern-chart"></canvas></div>
            </div>
        </div>

        <div class="section">
            <h3 class="section-header">Capability Gaps</h3>
            ${Object.entries(modelData.capability_gap_analysis || {}).map(([domain, ga]) => {
                if (!ga.gaps_confirmed) return '';
                return `
                    <div class="finding-card warning">
                        <h4>${domainTag(domain)} — ${ga.gaps_confirmed} gap${ga.gaps_confirmed > 1 ? 's' : ''} (${ga.gap_rate}%)</h4>
                        <p>Probes: ${ga.probes_with_gaps.join(', ')}</p>
                    </div>`;
            }).join('') || '<p style="color:var(--muted)">No capability gaps detected for this model.</p>'}
        </div>

        <div class="section">
            <h3 class="section-header">All Probes</h3>
            <p style="color:var(--muted);margin-bottom:1rem;font-size:0.75rem">Click a probe to view full response details.</p>
            <table>
                <thead>
                    <tr>
                        <th>Probe ID</th>
                        <th>Domain</th>
                        <th>Classification</th>
                        <th>Verdict</th>
                        <th class="num" title="Framing Sensitivity (0–6)">Framing</th>
                        <th>Shift</th>
                        <th class="num">Gap</th>
                    </tr>
                </thead>
                <tbody>
                    ${modelData.probe_results.map(pr => {
                        const cls = pr.stage1?.classification || '';
                        const diff = pr.differential || {};
                        const gap = pr.capability_gap?.gap_confirmed;
                        return `
                            <tr onclick="location.hash='#/probes/${pr.probe_id}'" style="cursor:pointer">
                                <td><code>${pr.probe_id}</code></td>
                                <td>${domainTag(pr.domain)}</td>
                                <td>${classificationBadge(cls)}</td>
                                <td>${verdictBadge(diff.verdict)}</td>
                                <td class="num">${diff.framing_sensitivity ?? ''}</td>
                                <td>${diff.behavioral_shift || 'none'}</td>
                                <td class="num">${gap ? '⚠' : ''}</td>
                            </tr>`;
                    }).join('')}
                </tbody>
            </table>
        </div>
    `;

    // Radar chart
    createRadarChart(
        document.getElementById('model-radar'),
        domains.map(d => d.charAt(0).toUpperCase() + d.slice(1)),
        [
            {
                label: 'Discriminatory %',
                data: domains.map(d => ds[d].discriminatory_rate),
                borderColor: '#c4553a',
                backgroundColor: 'rgba(196,85,58,0.1)',
            },
            {
                label: 'Full Assist %',
                data: domains.map(d => ds[d].full_assist_rate),
                borderColor: '#3a7d5c',
                backgroundColor: 'rgba(58,125,92,0.1)',
            },
        ]
    );

    // Pattern chart
    const pf = modelData.pattern_frequency || {};
    const patternLabels = Object.keys(pf).slice(0, 10);
    createBarChart(
        document.getElementById('pattern-chart'),
        patternLabels.map(p => p.length > 25 ? p.slice(0, 25) + '…' : p),
        [{
            label: 'Count',
            data: patternLabels.map(p => pf[p]),
            backgroundColor: '#2c5f8a',
        }],
        { indexAxis: 'y' }
    );
}

function classificationBadge(cls) {
    const map = { deflection: 'badge-deflection', partial_assist: 'badge-partial', full_assist: 'badge-full' };
    return `<span class="badge ${map[cls] || ''}">${(cls || '').replace(/_/g, ' ')}</span>`;
}
