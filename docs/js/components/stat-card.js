/**
 * Stat card component.
 */
export function statCard(label, value, detail = '', color = '') {
    const colorStyle = color ? `color:${color}` : '';
    return `
        <div class="stat-card">
            <div class="label">${label}</div>
            <div class="value" style="${colorStyle}">${value}</div>
            ${detail ? `<div class="detail">${detail}</div>` : ''}
        </div>`;
}

export function statGrid(cards) {
    return `<div class="stat-grid">${cards.join('')}</div>`;
}
