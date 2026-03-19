/**
 * Response viewer component — shows model response text with metadata.
 */

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

export function responseViewer(label, response, meta = {}) {
    const metaParts = [];
    if (meta.classification) metaParts.push(`Classification: ${meta.classification}`);
    if (meta.concern_ratio != null) metaParts.push(`Concern Ratio: ${meta.concern_ratio.toFixed(2)}`);
    if (meta.patterns && meta.patterns.length) metaParts.push(`Patterns: ${meta.patterns.join(', ')}`);

    return `
        <div class="response-viewer">
            <div class="response-header">
                <span>${escapeHtml(label)}</span>
                ${metaParts.length ? `<span style="font-size:0.65rem">${escapeHtml(metaParts.join(' | '))}</span>` : ''}
            </div>
            <div class="response-body">${escapeHtml(response || '(no response)')}</div>
        </div>`;
}

export function differentialViewer(differential) {
    if (!differential) return '';

    const conditions = [
        { key: 'condition_a', label: 'Condition A — Neutral Framing' },
        { key: 'condition_b', label: 'Condition B — Credentialed Framing' },
        { key: 'condition_c', label: 'Condition C — Technical Framing' },
    ];

    const viewers = conditions
        .filter(c => differential[c.key + '_response'])
        .map(c => {
            const prompt = differential[c.key + '_prompt'] || '';
            return `
                <div class="response-viewer">
                    <div class="response-header">
                        <span>${c.label}</span>
                    </div>
                    <div class="response-body" style="max-height:150px;font-size:0.7rem;color:var(--muted)">${escapeHtml(prompt)}</div>
                    <div class="response-body">${escapeHtml(differential[c.key + '_response'])}</div>
                </div>`;
        })
        .join('');

    const detail = differential.detail || {};
    const dims = ['constraint_diff', 'justification_diff', 'scope_diff', 'calibration_diff'];
    const dimBars = dims.map(d => {
        const val = detail[d] || 0;
        const width = val / 2 * 100;
        return `
            <div style="display:flex;align-items:center;gap:0.5rem;margin:0.2rem 0">
                <span style="width:120px;font-size:0.7rem;color:var(--muted)">${d.replace('_diff', '')}</span>
                <div style="flex:1;height:8px;background:var(--surface3);border-radius:4px;overflow:hidden">
                    <div style="width:${width}%;height:100%;background:${val >= 2 ? 'var(--red)' : val >= 1 ? 'var(--orange)' : 'var(--green)'};border-radius:4px"></div>
                </div>
                <span style="font-size:0.7rem;font-weight:700">${val}</span>
            </div>`;
    }).join('');

    return `
        <div style="margin:1rem 0">
            <h4 style="font-size:0.85rem;margin-bottom:0.5rem">Differential Analysis</h4>
            <div style="margin-bottom:1rem;padding:0.75rem;background:var(--surface);border:1px solid var(--border);border-radius:8px">
                <div style="display:flex;gap:1rem;flex-wrap:wrap;margin-bottom:0.5rem">
                    <span style="font-size:0.75rem"><strong>Verdict:</strong> ${differential.verdict || 'N/A'}</span>
                    <span style="font-size:0.75rem"><strong>Shift:</strong> ${differential.behavioral_shift || 'none'}</span>
                    <span style="font-size:0.75rem"><strong>FS:</strong> ${differential.framing_sensitivity ?? 'N/A'} (${differential.framing_sensitivity_label || ''})</span>
                </div>
                ${dimBars}
                ${differential.explanation ? `<p style="font-size:0.75rem;color:var(--muted);margin-top:0.5rem">${escapeHtml(differential.explanation)}</p>` : ''}
            </div>
            ${viewers}
        </div>`;
}
