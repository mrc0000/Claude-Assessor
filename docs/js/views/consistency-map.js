/**
 * Consistency Map — Heatmap of framing sensitivity across probes × models.
 *
 * The core research question visualized: where does reasoning honesty break down?
 * Each cell = one probe's framing sensitivity for one model. Warm = inconsistent, cool = stable.
 * Instantly reveals that the signal clusters in specific domains.
 */
import { domainTag, verdictBadge } from '../components/badge.js';

const DOMAIN_ORDER = ['cybersecurity', 'reasoning', 'legal', 'medical', 'chemistry', 'financial', 'copyright'];

function fsColor(fs) {
    // 0-1: cool sage, 2: neutral, 3-4: warm amber, 5-6: hot terracotta
    if (fs <= 1) return { bg: '#e2efea', text: '#2d6b4d' };
    if (fs === 2) return { bg: '#f0ecdf', text: '#7a7a5a' };
    if (fs === 3) return { bg: '#f8e8d0', text: '#946b3c' };
    if (fs === 4) return { bg: '#f4d4b8', text: '#8a5226' };
    if (fs >= 5) return { bg: '#eab8a4', text: '#8b3a2a' };
    return { bg: '#f0ecdf', text: '#7a7a7a' };
}

function verdictColor(verdict) {
    if (verdict === 'discriminatory') return '#c4553a';
    if (verdict === 'consistent') return '#3a7d5c';
    if (verdict?.startsWith('tone_modulated')) return '#c47e33';
    return '#7a7a7a';
}

export async function renderConsistencyMap(container, data) {
    // Load all models
    const modelEntries = [];
    const probeMap = {}; // probeId → { domain, risk_tier, models: { modelId: [results] } }

    const allModelIds = Object.keys(data.summary.models);
    // Load all models in parallel for faster initial render
    const modelResults = await Promise.all(allModelIds.map(id => data.loadModel(id)));
    for (let i = 0; i < allModelIds.length; i++) {
        const modelId = allModelIds[i];
        const modelData = modelResults[i];
        if (!modelData) {
            console.warn(`Consistency map: skipping ${modelId} — data not loaded`);
            continue;
        }
        modelEntries.push({ id: modelId, label: modelData.label });

        for (const pr of modelData.probe_results) {
            const key = pr.probe_id;
            if (!probeMap[key]) {
                probeMap[key] = { probe_id: key, domain: pr.domain, risk_tier: pr.risk_tier, models: {} };
            }
            if (!probeMap[key].models[modelId]) {
                probeMap[key].models[modelId] = [];
            }
            probeMap[key].models[modelId].push(pr);
        }
    }

    // Group probes by domain, sort by domain priority then probe_id
    const probes = Object.values(probeMap).sort((a, b) => {
        const ai = DOMAIN_ORDER.indexOf(a.domain);
        const bi = DOMAIN_ORDER.indexOf(b.domain);
        if (ai !== bi) return (ai === -1 ? 99 : ai) - (bi === -1 ? 99 : bi);
        return a.probe_id.localeCompare(b.probe_id);
    });

    let filterDomain = '';
    let hoveredCell = null;

    function render() {
        const filtered = filterDomain
            ? probes.filter(p => p.domain === filterDomain)
            : probes;

        const domains = [...new Set(filtered.map(p => p.domain))];

        container.innerHTML = `
            <h2 class="section-header">Consistency Map</h2>
            <div class="section-subheader">
                Where does reasoning honesty break down? Each cell shows a probe's framing sensitivity for one model.
                Warm cells indicate the model's response changed significantly based on who was asking.
                Sorted by domain — the pattern clustering is the finding.
            </div>

            <div class="filter-bar">
                <label>
                    Domain
                    <select id="map-domain-filter">
                        <option value="">All domains</option>
                        ${DOMAIN_ORDER.map(d =>
                            `<option value="${d}" ${d === filterDomain ? 'selected' : ''}>${d}</option>`
                        ).join('')}
                    </select>
                </label>
                <div style="display:flex;align-items:flex-end;gap:1rem;margin-left:auto">
                    <div style="display:flex;align-items:center;gap:0.5rem;font-size:0.72rem;color:var(--muted)">
                        <span>Consistent</span>
                        <div style="display:flex;gap:2px">
                            ${[0,1,2,3,4,5,6].map(fs => {
                                const c = fsColor(fs);
                                return `<div style="width:14px;height:14px;border-radius:3px;background:${c.bg}" title="FS=${fs}"></div>`;
                            }).join('')}
                        </div>
                        <span>Inconsistent</span>
                    </div>
                </div>
            </div>

            <div style="overflow-x:auto">
                <table style="min-width:600px">
                    <thead>
                        <tr>
                            <th style="position:sticky;left:0;background:var(--surface2);z-index:2">Probe</th>
                            <th>Domain</th>
                            ${modelEntries.map(m => `<th class="num" style="min-width:140px">${m.label}</th>`).join('')}
                        </tr>
                    </thead>
                    <tbody>
                        ${filtered.map(p => {
                            let prevDomain = null;
                            const cells = modelEntries.map(m => {
                                const runs = p.models[m.id] || [];
                                if (!runs.length) return '<td class="num">—</td>';

                                // Average framing sensitivity across variance runs
                                const fsValues = runs.map(r => r.differential?.framing_sensitivity ?? 0);
                                const avgFs = fsValues.reduce((a, b) => a + b, 0) / fsValues.length;
                                const roundFs = Math.round(avgFs);
                                const c = fsColor(roundFs);

                                // Majority verdict
                                const verdicts = runs.map(r => r.differential?.verdict).filter(Boolean);
                                const majorityVerdict = mode(verdicts);
                                const vc = verdictColor(majorityVerdict);

                                return `
                                    <td class="num">
                                        <div class="map-cell"
                                             style="background:${c.bg};color:${c.text};border-radius:6px;padding:0.35rem 0.5rem;display:inline-block;min-width:80px;cursor:pointer;border-left:3px solid ${vc}"
                                             data-probe="${p.probe_id}" data-model="${m.id}"
                                             onclick="location.hash='#/probes/${p.probe_id}'"
                                             title="${p.probe_id} × ${m.label}\nFS: ${avgFs.toFixed(1)} | Verdict: ${majorityVerdict || 'N/A'}">
                                            <span style="font-weight:600;font-size:0.8rem">${roundFs}</span>
                                            <span style="font-size:0.6rem;margin-left:0.25rem;opacity:0.7">${(majorityVerdict || '').replace('tone_modulated_', 'tm_').replace('discriminatory', 'disc').replace('consistent', 'cons')}</span>
                                        </div>
                                    </td>`;
                            }).join('');

                            return `
                                <tr>
                                    <td style="position:sticky;left:0;background:var(--surface);z-index:1;font-family:var(--font-mono);font-size:0.75rem">
                                        <a href="#/probes/${p.probe_id}" style="color:var(--accent);text-decoration:none">${p.probe_id}</a>
                                    </td>
                                    <td>${domainTag(p.domain)}</td>
                                    ${cells}
                                </tr>`;
                        }).join('')}
                    </tbody>
                </table>
            </div>

            <div style="margin-top:2rem">
                <h3 class="section-header">Reading This Map</h3>
                <div class="insight-grid">
                    <div class="insight-card coral">
                        <div class="eyebrow">Hot zones</div>
                        <h3>Where the warm clusters appear, honesty is audience-dependent</h3>
                        <p>High framing sensitivity (FS 3–6) means the model gave meaningfully different responses
                        depending on whether the asker claimed professional credentials. The left border color shows
                        the verdict: red = discriminatory, amber = tone modulated, green = consistent.</p>
                    </div>
                    <div class="insight-card sage">
                        <div class="eyebrow">Cool zones</div>
                        <h3>Green regions show genuine consistency</h3>
                        <p>Low framing sensitivity (FS 0–1) means the model responded equivalently regardless of
                        framing. Most domains are predominantly cool — the inconsistency concentrates
                        in specific knowledge areas.</p>
                    </div>
                </div>
            </div>

            ${renderDomainSummary(filtered, modelEntries)}
        `;

        // Bind filter
        document.getElementById('map-domain-filter').addEventListener('change', e => {
            filterDomain = e.target.value;
            render();
        });
    }

    render();
}

function renderDomainSummary(probes, models) {
    const domainStats = {};
    for (const p of probes) {
        if (!domainStats[p.domain]) {
            domainStats[p.domain] = { domain: p.domain, totalFs: 0, count: 0, discCount: 0, consCount: 0 };
        }
        for (const m of models) {
            const runs = p.models[m.id] || [];
            for (const r of runs) {
                const fs = r.differential?.framing_sensitivity ?? 0;
                domainStats[p.domain].totalFs += fs;
                domainStats[p.domain].count++;
                if (r.differential?.verdict === 'discriminatory') domainStats[p.domain].discCount++;
                if (r.differential?.verdict === 'consistent') domainStats[p.domain].consCount++;
            }
        }
    }

    const sorted = Object.values(domainStats).sort((a, b) => (b.totalFs / b.count) - (a.totalFs / a.count));

    return `
        <div style="margin-top:2rem">
            <h3 class="section-header">Domain Sensitivity Ranking</h3>
            <table>
                <thead>
                    <tr>
                        <th>Domain</th>
                        <th class="num">Avg FS</th>
                        <th class="num">Probes</th>
                        <th class="num">Discriminatory</th>
                        <th class="num">Consistent</th>
                    </tr>
                </thead>
                <tbody>
                    ${sorted.map(d => {
                        const avgFs = (d.totalFs / d.count).toFixed(1);
                        const discPct = (d.discCount / d.count * 100).toFixed(0);
                        const consPct = (d.consCount / d.count * 100).toFixed(0);
                        return `
                            <tr>
                                <td>${domainTag(d.domain)}</td>
                                <td class="num" style="font-weight:600">${avgFs}</td>
                                <td class="num">${d.count}</td>
                                <td class="num" style="color:var(--red)">${discPct}%</td>
                                <td class="num" style="color:var(--green)">${consPct}%</td>
                            </tr>`;
                    }).join('')}
                </tbody>
            </table>
        </div>
    `;
}

function mode(arr) {
    if (!arr.length) return null;
    const counts = {};
    for (const v of arr) counts[v] = (counts[v] || 0) + 1;
    return Object.entries(counts).sort((a, b) => b[1] - a[1])[0][0];
}
