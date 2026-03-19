/**
 * Probe deep-dive view.
 */
import { domainTag, verdictBadge, classificationBadge } from '../components/badge.js';
import { responseViewer, differentialViewer } from '../components/response-viewer.js';

export async function renderProbeList(container, data) {
    // Load all models to build a probe index
    const probeIndex = {};
    for (const modelId of Object.keys(data.summary.models)) {
        const modelData = await data.loadModel(modelId);
        if (modelData) {
            for (const pr of modelData.probe_results) {
                const key = pr.probe_id;
                if (!probeIndex[key]) {
                    probeIndex[key] = { probe_id: key, domain: pr.domain, risk_tier: pr.risk_tier, models: {} };
                }
                if (!probeIndex[key].models[modelId]) {
                    probeIndex[key].models[modelId] = [];
                }
                probeIndex[key].models[modelId].push(pr);
            }
        }
    }

    const probes = Object.values(probeIndex).sort((a, b) => a.probe_id.localeCompare(b.probe_id));

    container.innerHTML = `
        <h2 class="section-header">Probe Deep Dive</h2>
        <p style="color:var(--muted);margin-bottom:1.5rem;font-size:0.8rem">
            52 unique probes across 7 domains. Click any probe to see full model responses,
            reasoning audit, and differential framing analysis.
        </p>

        <div class="filter-bar">
            <label>
                Domain
                <select id="probe-domain-filter">
                    <option value="">All</option>
                    ${[...new Set(probes.map(p => p.domain))].sort().map(d =>
                        `<option value="${d}">${d}</option>`
                    ).join('')}
                </select>
            </label>
            <label>
                Search
                <input type="text" id="probe-search" placeholder="Probe ID...">
            </label>
        </div>

        <table>
            <thead>
                <tr>
                    <th>Probe ID</th>
                    <th>Domain</th>
                    <th>Risk</th>
                    <th class="num">Models</th>
                    <th class="num">Runs</th>
                </tr>
            </thead>
            <tbody id="probe-table-body">
                ${renderProbeRows(probes)}
            </tbody>
        </table>
    `;

    // Filtering
    const filterFn = () => {
        const domain = document.getElementById('probe-domain-filter').value;
        const search = document.getElementById('probe-search').value.toLowerCase();
        const filtered = probes.filter(p =>
            (!domain || p.domain === domain) &&
            (!search || p.probe_id.toLowerCase().includes(search))
        );
        document.getElementById('probe-table-body').innerHTML = renderProbeRows(filtered);
    };
    document.getElementById('probe-domain-filter').addEventListener('change', filterFn);
    document.getElementById('probe-search').addEventListener('input', filterFn);
}

function renderProbeRows(probes) {
    return probes.map(p => {
        const modelCount = Object.keys(p.models).length;
        const runCount = Object.values(p.models).reduce((a, runs) => a + runs.length, 0);
        return `
            <tr onclick="location.hash='#/probes/${p.probe_id}'" style="cursor:pointer">
                <td><code>${p.probe_id}</code></td>
                <td>${domainTag(p.domain)}</td>
                <td style="font-size:0.75rem">${p.risk_tier}</td>
                <td class="num">${modelCount}</td>
                <td class="num">${runCount}</td>
            </tr>`;
    }).join('');
}

export async function renderProbeDetail(container, data, probeId) {
    // Load all models and find this probe
    const modelResults = {};
    for (const modelId of Object.keys(data.summary.models)) {
        const modelData = await data.loadModel(modelId);
        if (modelData) {
            const matches = modelData.probe_results.filter(pr => pr.probe_id === probeId);
            if (matches.length) {
                modelResults[modelId] = { label: modelData.label, results: matches };
            }
        }
    }

    if (!Object.keys(modelResults).length) {
        container.innerHTML = `<div class="empty-state">Probe not found: ${probeId}</div>`;
        return;
    }

    const first = Object.values(modelResults)[0].results[0];

    container.innerHTML = `
        <button class="back-btn" onclick="location.hash='#/probes'">← Back to Probes</button>
        <h2 class="section-header">${probeId}</h2>
        <div style="display:flex;gap:0.75rem;margin-bottom:1.5rem">
            ${domainTag(first.domain)}
            <span style="font-size:0.75rem;color:var(--muted)">Risk: ${first.risk_tier}</span>
        </div>

        <div class="tabs" id="model-tabs">
            ${Object.entries(modelResults).map(([mid, m], i) =>
                `<button class="tab ${i === 0 ? 'active' : ''}" data-model="${mid}">${m.label}</button>`
            ).join('')}
        </div>

        <div id="probe-content"></div>
    `;

    function showModel(modelId) {
        const m = modelResults[modelId];
        if (!m) return;

        document.querySelectorAll('#model-tabs .tab').forEach(t => {
            t.classList.toggle('active', t.dataset.model === modelId);
        });

        const content = document.getElementById('probe-content');

        // Show variance runs as tabs
        const runs = m.results;
        content.innerHTML = `
            ${runs.length > 1 ? `
                <div class="tabs" id="run-tabs">
                    ${runs.map((r, i) => `<button class="tab ${i === 0 ? 'active' : ''}" data-run="${i}">Run ${r.variance_run || i + 1}</button>`).join('')}
                </div>
            ` : ''}
            <div id="run-content"></div>
        `;

        function showRun(idx) {
            const pr = runs[idx];
            if (runs.length > 1) {
                document.querySelectorAll('#run-tabs .tab').forEach((t, i) => {
                    t.classList.toggle('active', i === idx);
                });
            }

            const s1 = pr.stage1 || {};
            const s3 = pr.stage3 || [];
            const gap = pr.capability_gap || {};
            const diff = pr.differential || {};

            document.getElementById('run-content').innerHTML = `
                <div class="section">
                    <h3 class="section-header">Stage 1 — Oblique Entry</h3>
                    <div style="display:flex;gap:0.5rem;margin-bottom:0.75rem">
                        ${classificationBadge(s1.classification || '')}
                        ${verdictBadge(diff.verdict)}
                        ${s1.concern_ratio != null ? `<span style="font-size:0.7rem;color:var(--muted)">Concern Ratio: ${s1.concern_ratio.toFixed(2)}</span>` : ''}
                    </div>
                    ${s1.patterns?.length ? `<p style="font-size:0.75rem;color:var(--muted);margin-bottom:0.5rem">Patterns: ${s1.patterns.join(', ')}</p>` : ''}
                    ${responseViewer('Prompt', s1.prompt)}
                    ${responseViewer('Response', s1.response, {
                        classification: s1.classification,
                        concern_ratio: s1.concern_ratio,
                        patterns: s1.patterns,
                    })}
                </div>

                ${s3.length ? `
                    <div class="section">
                        <h3 class="section-header">Stage 3 — Reasoning Audit</h3>
                        ${s3.map((probe, i) => `
                            <div style="margin-bottom:1rem">
                                <div style="font-size:0.75rem;color:var(--muted);margin-bottom:0.25rem">
                                    Follow-up ${i + 1}
                                    ${probe.justification_shifted ? '<span style="color:var(--orange);font-weight:700"> — Justification Shifted</span>' : '<span style="color:var(--green)"> — Stable</span>'}
                                </div>
                                ${probe.shift_description ? `<p style="font-size:0.75rem;color:var(--muted);margin-bottom:0.5rem">${escapeHtml(probe.shift_description)}</p>` : ''}
                                ${responseViewer('Probe', probe.probe)}
                                ${responseViewer('Response', probe.response)}
                            </div>
                        `).join('')}
                    </div>
                ` : ''}

                ${gap.test_prompt ? `
                    <div class="section">
                        <h3 class="section-header">Capability Gap Test</h3>
                        <div style="margin-bottom:0.5rem">
                            ${gap.gap_confirmed
                                ? '<span class="badge badge-deflection">GAP CONFIRMED</span>'
                                : '<span class="badge badge-full">NO GAP</span>'}
                            ${gap.demonstrates_knowledge ? ' <span style="font-size:0.75rem;color:var(--muted)">Demonstrates knowledge</span>' : ''}
                        </div>
                        ${responseViewer('Test Prompt', gap.test_prompt)}
                        ${responseViewer('Response', gap.response)}
                    </div>
                ` : ''}

                ${diff.condition_a_response ? `
                    <div class="section">
                        ${differentialViewer(diff)}
                    </div>
                ` : ''}
            `;
        }

        showRun(0);

        // Bind run tabs
        if (runs.length > 1) {
            document.querySelectorAll('#run-tabs .tab').forEach((t, i) => {
                t.addEventListener('click', () => showRun(i));
            });
        }
    }

    showModel(Object.keys(modelResults)[0]);

    // Bind model tabs
    document.querySelectorAll('#model-tabs .tab').forEach(t => {
        t.addEventListener('click', () => showModel(t.dataset.model));
    });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text || '';
    return div.innerHTML;
}
