/**
 * Findings narrative view — renders the markdown findings documents.
 */

const FINDINGS_DOCS = [
    { id: 'synthesis', label: 'Synthesis', file: 'data/findings/synthesis.html' },
    { id: 'aggregate', label: 'Aggregate Findings', file: 'data/findings/aggregate.html' },
    { id: 'sonnet46', label: 'Sonnet 4.6 Deep Dive', file: 'data/findings/sonnet46.html' },
    { id: 'meta-reasoning', label: 'Meta-Reasoning', file: 'data/findings/meta-reasoning.html' },
    { id: 'statistics', label: 'Statistics', file: 'data/findings/statistics.html' },
];

const cache = {};

async function loadFinding(file) {
    if (cache[file]) return cache[file];
    try {
        const res = await fetch(file);
        if (!res.ok) return '<p style="color:var(--muted)">Document not available.</p>';
        cache[file] = await res.text();
        return cache[file];
    } catch {
        return '<p style="color:var(--muted)">Failed to load document.</p>';
    }
}

export async function renderFindings(container, data, docId) {
    const activeDoc = docId || 'synthesis';

    container.innerHTML = `
        <h2 class="section-header">Research Findings</h2>
        <p style="color:var(--muted);margin-bottom:1.5rem;font-size:0.8rem">
            Detailed analysis documents generated from the evaluation data.
        </p>
        <div class="tabs" id="findings-tabs">
            ${FINDINGS_DOCS.map(d =>
                `<button class="tab ${d.id === activeDoc ? 'active' : ''}" data-doc="${d.id}">${d.label}</button>`
            ).join('')}
        </div>
        <div id="findings-content" class="findings-content" style="padding:1rem 0">
            <div class="loading"><div class="loading-spinner"></div></div>
        </div>
    `;

    async function showDoc(id) {
        const doc = FINDINGS_DOCS.find(d => d.id === id);
        if (!doc) return;

        document.querySelectorAll('#findings-tabs .tab').forEach(t => {
            t.classList.toggle('active', t.dataset.doc === id);
        });

        const contentEl = document.getElementById('findings-content');
        contentEl.innerHTML = '<div class="loading"><div class="loading-spinner"></div></div>';

        const html = await loadFinding(doc.file);
        contentEl.innerHTML = html;

        // Update hash without re-rendering
        history.replaceState(null, '', `#/findings/${id}`);
    }

    // Bind tabs
    document.querySelectorAll('#findings-tabs .tab').forEach(t => {
        t.addEventListener('click', () => showDoc(t.dataset.doc));
    });

    await showDoc(activeDoc);
}
