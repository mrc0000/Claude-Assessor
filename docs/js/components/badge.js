/**
 * Badge and tag components — editorial palette.
 */

export function domainTag(domain) {
    return `<span class="domain-tag">${domain}</span>`;
}

export function classificationBadge(cls) {
    const map = {
        deflection: 'badge-deflection',
        partial_assist: 'badge-partial',
        full_assist: 'badge-full',
    };
    const label = cls.replace(/_/g, ' ');
    return `<span class="badge ${map[cls] || ''}">${label}</span>`;
}

export function verdictBadge(verdict) {
    if (!verdict) return '';
    let cls = 'badge-tone';
    if (verdict === 'discriminatory') cls = 'badge-discriminatory';
    else if (verdict === 'consistent') cls = 'badge-consistent';
    const label = verdict.replace(/_/g, ' ');
    return `<span class="badge ${cls}">${label}</span>`;
}

export function pctBar(value, color = '#2c5f8a', width = 80) {
    const pct = Math.min(value, 100);
    return `
        <div class="pct-bar" style="width:${width}px">
            <div class="pct-fill" style="width:${pct}%;background:${color}"></div>
            <span class="pct-label">${value.toFixed(1)}%</span>
        </div>`;
}

export function verdictBar(distribution) {
    const total = Object.values(distribution).reduce((a, b) => a + b, 0);
    if (!total) return '<div class="verdict-bar"></div>';

    const order = ['discriminatory', 'tone_modulated_high', 'tone_modulated_moderate', 'tone_modulated_low', 'tone_modulated', 'consistent'];
    const colors = {
        discriminatory: 'var(--red)',
        tone_modulated_high: '#a0642a',
        tone_modulated_moderate: 'var(--orange)',
        tone_modulated_low: '#d4a95a',
        tone_modulated: 'var(--orange)',
        consistent: 'var(--green)',
    };

    const segs = order
        .filter(v => distribution[v])
        .map(v => `<div class="vb-seg" style="width:${distribution[v]/total*100}%;background:${colors[v]}" title="${v}: ${distribution[v]}"></div>`)
        .join('');

    return `<div class="verdict-bar">${segs}</div>`;
}
