/**
 * Data tables view — sortable, filterable, exportable.
 */
import { domainTag, verdictBadge, pctBar } from '../components/badge.js';

export async function renderDataTables(container, data) {
    // Load all probe results across all models
    const allProbes = [];
    for (const modelId of Object.keys(data.summary.models)) {
        const modelData = await data.loadModel(modelId);
        if (modelData) {
            for (const pr of modelData.probe_results) {
                allProbes.push({
                    probe_id: pr.probe_id,
                    model: modelData.label,
                    model_id: modelData.model_id,
                    domain: pr.domain,
                    risk_tier: pr.risk_tier,
                    run: pr.variance_run || 1,
                    classification: pr.stage1?.classification || '',
                    concern_ratio: pr.stage1?.concern_ratio ?? 0,
                    patterns: (pr.stage1?.patterns || []).join(', '),
                    verdict: pr.differential?.verdict || '',
                    framing_sensitivity: pr.differential?.framing_sensitivity ?? 0,
                    behavioral_shift: pr.differential?.behavioral_shift || 'none',
                    gap_confirmed: pr.capability_gap?.gap_confirmed ? 'Yes' : 'No',
                });
            }
        }
    }

    let sortCol = 'probe_id';
    let sortDir = 1;
    let filters = { model: '', domain: '', verdict: '', search: '' };

    function getFiltered() {
        return allProbes.filter(p =>
            (!filters.model || p.model === filters.model) &&
            (!filters.domain || p.domain === filters.domain) &&
            (!filters.verdict || p.verdict === filters.verdict) &&
            (!filters.search || p.probe_id.toLowerCase().includes(filters.search.toLowerCase()))
        ).sort((a, b) => {
            const av = a[sortCol], bv = b[sortCol];
            if (typeof av === 'number') return (av - bv) * sortDir;
            return String(av).localeCompare(String(bv)) * sortDir;
        });
    }

    function renderTable() {
        const filtered = getFiltered();
        const tbody = document.getElementById('data-tbody');
        tbody.innerHTML = filtered.map(p => `
            <tr onclick="location.hash='#/probes/${p.probe_id}'" style="cursor:pointer">
                <td><code>${p.probe_id}</code></td>
                <td style="font-size:0.75rem">${p.model}</td>
                <td class="num">${p.run}</td>
                <td>${domainTag(p.domain)}</td>
                <td style="font-size:0.75rem">${p.risk_tier}</td>
                <td><span class="badge ${clsBadge(p.classification)}">${p.classification.replace(/_/g, ' ')}</span></td>
                <td class="num">${p.concern_ratio.toFixed(2)}</td>
                <td>${verdictBadge(p.verdict)}</td>
                <td class="num">${p.framing_sensitivity}</td>
                <td style="font-size:0.75rem">${p.behavioral_shift}</td>
                <td class="num">${p.gap_confirmed === 'Yes' ? '⚠' : ''}</td>
            </tr>
        `).join('');

        document.getElementById('data-count').textContent = `${filtered.length} of ${allProbes.length} results`;
    }

    const models = [...new Set(allProbes.map(p => p.model))].sort();
    const domains = [...new Set(allProbes.map(p => p.domain))].sort();
    const verdicts = [...new Set(allProbes.map(p => p.verdict))].filter(Boolean).sort();

    container.innerHTML = `
        <h2 class="section-header">Data Explorer</h2>
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem">
            <span id="data-count" style="font-size:0.75rem;color:var(--muted)"></span>
            <button class="export-btn" id="export-csv">Export CSV</button>
        </div>
        <div class="filter-bar">
            <label>
                Model
                <select id="filter-model">
                    <option value="">All</option>
                    ${models.map(m => `<option value="${m}">${m}</option>`).join('')}
                </select>
            </label>
            <label>
                Domain
                <select id="filter-domain">
                    <option value="">All</option>
                    ${domains.map(d => `<option value="${d}">${d}</option>`).join('')}
                </select>
            </label>
            <label>
                Verdict
                <select id="filter-verdict">
                    <option value="">All</option>
                    ${verdicts.map(v => `<option value="${v}">${v.replace(/_/g, ' ')}</option>`).join('')}
                </select>
            </label>
            <label>
                Search
                <input type="text" id="filter-search" placeholder="Probe ID...">
            </label>
        </div>
        <div style="overflow-x:auto">
            <table>
                <thead>
                    <tr>
                        <th data-col="probe_id">Probe</th>
                        <th data-col="model">Model</th>
                        <th data-col="run" class="num">Run</th>
                        <th data-col="domain">Domain</th>
                        <th data-col="risk_tier">Risk</th>
                        <th data-col="classification">Class.</th>
                        <th data-col="concern_ratio" class="num" title="Concern Ratio: disclaimer density">Concern</th>
                        <th data-col="verdict">Verdict</th>
                        <th data-col="framing_sensitivity" class="num" title="Framing Sensitivity (0–6)">Framing</th>
                        <th data-col="behavioral_shift">Shift</th>
                        <th data-col="gap_confirmed" class="num">Gap</th>
                    </tr>
                </thead>
                <tbody id="data-tbody"></tbody>
            </table>
        </div>
    `;

    // Sort
    container.querySelectorAll('th[data-col]').forEach(th => {
        th.addEventListener('click', () => {
            const col = th.dataset.col;
            if (sortCol === col) sortDir *= -1;
            else { sortCol = col; sortDir = 1; }
            container.querySelectorAll('th').forEach(t => t.classList.remove('sort-asc', 'sort-desc'));
            th.classList.add(sortDir === 1 ? 'sort-asc' : 'sort-desc');
            renderTable();
        });
    });

    // Filters
    ['model', 'domain', 'verdict'].forEach(key => {
        document.getElementById(`filter-${key}`).addEventListener('change', e => {
            filters[key] = e.target.value;
            renderTable();
        });
    });
    document.getElementById('filter-search').addEventListener('input', e => {
        filters.search = e.target.value;
        renderTable();
    });

    // CSV Export
    document.getElementById('export-csv').addEventListener('click', () => {
        const filtered = getFiltered();
        const headers = ['probe_id', 'model', 'run', 'domain', 'risk_tier', 'classification', 'concern_ratio', 'patterns', 'verdict', 'framing_sensitivity', 'behavioral_shift', 'gap_confirmed'];
        const csv = [headers.join(',')].concat(
            filtered.map(p => headers.map(h => `"${String(p[h]).replace(/"/g, '""')}"`).join(','))
        ).join('\n');
        const blob = new Blob([csv], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'claude_assessor_results.csv';
        a.click();
        URL.revokeObjectURL(url);
    });

    renderTable();
}

function clsBadge(cls) {
    return { deflection: 'badge-deflection', partial_assist: 'badge-partial', full_assist: 'badge-full' }[cls] || '';
}
