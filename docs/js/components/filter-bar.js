/**
 * Filter bar component.
 */
export function filterBar(filters) {
    const parts = filters.map(f => {
        if (f.type === 'select') {
            const opts = f.options.map(o =>
                `<option value="${o.value}" ${o.value === f.value ? 'selected' : ''}>${o.label}</option>`
            ).join('');
            return `
                <label>
                    ${f.label}
                    <select data-filter="${f.key}">${opts}</select>
                </label>`;
        }
        if (f.type === 'search') {
            return `
                <label>
                    ${f.label}
                    <input type="text" data-filter="${f.key}" placeholder="${f.placeholder || 'Search...'}" value="${f.value || ''}">
                </label>`;
        }
        return '';
    }).join('');

    return `<div class="filter-bar">${parts}</div>`;
}

export function bindFilters(container, onChange) {
    container.querySelectorAll('[data-filter]').forEach(el => {
        el.addEventListener(el.tagName === 'SELECT' ? 'change' : 'input', () => {
            const filters = {};
            container.querySelectorAll('[data-filter]').forEach(el => {
                filters[el.dataset.filter] = el.value;
            });
            onChange(filters);
        });
    });
}
