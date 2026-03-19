/**
 * Data tables view — sortable, filterable, paginated, exportable.
 */
import { domainTag, verdictBadge } from '../components/badge.js';

const PAGE_SIZE = 50;

export async function renderDataTables(container, data) {
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
    let page = 0;

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
        const totalPages = Math.ceil(filtered.length / PAGE_SIZE);
        if (page >= totalPages) page = Math.max(0, totalPages - 1);
        const start = page * PAGE_SIZE;
        const pageData = filtered.slice(start, start + PAGE_SIZE);

        const tbody = document.getElementById('data-tbody');
        tbody.innerHTML = pageData.map(p => `
            <tr onclick="location.hash='#/probes/${p.probe_id}'" style="cursor:pointer">
                <td><code style="font-size:0.78rem">${p.probe_id}</code></td>
                <td style="font-size:0.78rem">${p.model}</td>
                <td class="num">${p.run}</td>
                <td>${domainTag(p.domain)}</td>
                <td><span class="badge ${clsBadge(p.classification)}">${p.classification.replace(/_/g, ' ')}</span></td>
                <td>${verdictBadge(p.verdict)}</td>
                <td class="num">${p.framing_sensitivity}</td>
                <td class="num">${p.gap_confirmed === 'Yes' ? 'Yes' : ''}</td>
            </tr>
        `).join('');

        document.getElementById('data-count').textContent =
            `Showing ${start + 1}–${Math.min(start + PAGE_SIZE, filtered.length)} of ${filtered.length} results`;

        // Pagination controls
        document.getElementById('pagination').innerHTML = totalPages > 1 ? `
            <button class="page-btn" ${page === 0 ? 'disabled' : ''} data-page="${page - 1}">&larr; Prev</button>
            <span style="font-size:0.8rem;color:var(--muted)">Page ${page + 1} of ${totalPages}</span>
            <button class="page-btn" ${page >= totalPages - 1 ? 'disabled' : ''} data-page="${page + 1}">Next &rarr;</button>
        ` : '';

        // Rebind pagination
        document.querySelectorAll('.page-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                page = parseInt(btn.dataset.page);
                renderTable();
                document.getElementById('data-table-top').scrollIntoView({ behavior: 'smooth' });
            });
        });
    }

    const models = [...new Set(allProbes.map(p => p.model))].sort();
    const domains = [...new Set(allProbes.map(p => p.domain))].sort();
    const verdicts = [...new Set(allProbes.map(p => p.verdict))].filter(Boolean).sort();

    container.innerHTML = `
        <h2 class="section-header">Data Explorer</h2>
        <p class="section-subheader">
            All ${allProbes.length} evaluation results across every model, domain, and variance run.
            Filter, sort by any column, or export to CSV.
        </p>

        <div class="filter-bar" style="flex-wrap:wrap">
            <label>
                Model
                <select id="filter-model">
                    <option value="">All models</option>
                    ${models.map(m => `<option value="${m}">${m}</option>`).join('')}
                </select>
            </label>
            <label>
                Domain
                <select id="filter-domain">
                    <option value="">All domains</option>
                    ${domains.map(d => `<option value="${d}">${d}</option>`).join('')}
                </select>
            </label>
            <label>
                Verdict
                <select id="filter-verdict">
                    <option value="">All verdicts</option>
                    ${verdicts.map(v => `<option value="${v}">${v.replace(/_/g, ' ')}</option>`).join('')}
                </select>
            </label>
            <label>
                Search
                <input type="text" id="filter-search" placeholder="Probe ID...">
            </label>
            <div style="display:flex;align-items:flex-end;margin-left:auto">
                <button class="export-btn" id="export-csv">Export CSV</button>
            </div>
        </div>

        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.75rem" id="data-table-top">
            <span id="data-count" style="font-size:0.8rem;color:var(--muted)"></span>
            <div id="pagination" style="display:flex;align-items:center;gap:0.75rem"></div>
        </div>

        <div style="overflow-x:auto">
            <table>
                <thead>
                    <tr>
                        <th data-col="probe_id">Probe</th>
                        <th data-col="model">Model</th>
                        <th data-col="run" class="num">Run</th>
                        <th data-col="domain">Domain</th>
                        <th data-col="classification">Classification</th>
                        <th data-col="verdict">Verdict</th>
                        <th data-col="framing_sensitivity" class="num" title="Framing Sensitivity: how much the response changed across framings (0–6)">Framing</th>
                        <th data-col="gap_confirmed" class="num" title="Capability gap: model claimed inability but demonstrated knowledge">Gap</th>
                    </tr>
                </thead>
                <tbody id="data-tbody"></tbody>
            </table>
        </div>

        <div style="display:flex;justify-content:space-between;align-items:center;margin-top:0.75rem">
            <span></span>
            <div id="pagination-bottom" style="display:flex;align-items:center;gap:0.75rem"></div>
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
            page = 0;
            renderTable();
        });
    });

    // Filters
    ['model', 'domain', 'verdict'].forEach(key => {
        document.getElementById(`filter-${key}`).addEventListener('change', e => {
            filters[key] = e.target.value;
            page = 0;
            renderTable();
        });
    });
    document.getElementById('filter-search').addEventListener('input', e => {
        filters.search = e.target.value;
        page = 0;
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
