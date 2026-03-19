/**
 * Research Findings Explorer — Main Application
 *
 * Loads data, sets up routing, and renders views.
 */
import { Router } from './lib/router.js';
import { renderLanding } from './views/landing.js';
import { renderModelList, renderModelDetail } from './views/models.js';
import { renderDomainList, renderDomainDetail } from './views/domains.js';
import { renderProbeList, renderProbeDetail } from './views/probes.js';
import { renderFindings } from './views/findings.js';
import { renderMethodology } from './views/methodology.js';
import { renderDataTables } from './views/data-tables.js';
import { renderConsistencyMap } from './views/consistency-map.js';

// ── Data Store ──
const dataStore = {
    summary: null,
    crossModel: null,
    _modelCache: {},

    async load() {
        const [summary, crossModel] = await Promise.all([
            fetch('data/summary.json').then(r => r.json()),
            fetch('data/cross-model.json').then(r => r.json()),
        ]);
        this.summary = summary;
        this.crossModel = crossModel;
    },

    async loadModel(modelId) {
        if (this._modelCache[modelId]) return this._modelCache[modelId];
        const label = this.summary.models[modelId]?.label || modelId;
        const slug = label.toLowerCase().replace(/ /g, '-').replace(/\./g, '');
        const url = `data/models/${slug}.json`;
        for (let attempt = 0; attempt < 3; attempt++) {
            try {
                const res = await fetch(url);
                if (!res.ok) throw new Error(`HTTP ${res.status}`);
                const data = await res.json();
                this._modelCache[modelId] = data;
                return data;
            } catch (e) {
                console.warn(`loadModel ${modelId} attempt ${attempt + 1} failed:`, e.message);
                if (attempt < 2) await new Promise(r => setTimeout(r, 1000 * (attempt + 1)));
            }
        }
        console.error(`Failed to load model ${modelId} after 3 attempts`);
        return null;
    },
};

// ── App Container ──
const app = document.getElementById('app');

function showLoading() {
    app.innerHTML = '<div class="loading"><div class="loading-spinner"></div><p>Loading...</p></div>';
}

// ── Scroll to top on route change ──
function scrollTop() {
    window.scrollTo(0, 0);
}

// ── Initialize ──
async function init() {
    try {
        await dataStore.load();
    } catch (e) {
        app.innerHTML = `
            <div class="empty-state">
                <h2>Data not found</h2>
                <p style="margin-top:1rem">Run <code>python build_webapp.py</code> in the reasoning-eval directory to generate the data files.</p>
                <p style="margin-top:0.5rem;font-size:0.75rem;color:var(--muted)">Error: ${e.message}</p>
            </div>`;
        return;
    }

    const router = new Router();

    router
        .on('/', () => {
            scrollTop();
            renderLanding(app, dataStore);
        })
        .on('/models', () => {
            scrollTop();
            renderModelList(app, dataStore);
        })
        .on('/models/:id', (id) => {
            scrollTop();
            showLoading();
            renderModelDetail(app, dataStore, id);
        })
        .on('/domains', () => {
            scrollTop();
            renderDomainList(app, dataStore);
        })
        .on('/domains/:domain', (domain) => {
            scrollTop();
            showLoading();
            renderDomainDetail(app, dataStore, domain);
        })
        .on('/probes', () => {
            scrollTop();
            showLoading();
            renderProbeList(app, dataStore);
        })
        .on('/probes/:id', (id) => {
            scrollTop();
            showLoading();
            renderProbeDetail(app, dataStore, id);
        })
        .on('/findings', () => {
            scrollTop();
            renderFindings(app, dataStore);
        })
        .on('/findings/:doc', (doc) => {
            scrollTop();
            renderFindings(app, dataStore, doc);
        })
        .on('/methodology', () => {
            scrollTop();
            renderMethodology(app);
        })
        .on('/map', () => {
            scrollTop();
            showLoading();
            renderConsistencyMap(app, dataStore);
        })
        .on('/data', () => {
            scrollTop();
            showLoading();
            renderDataTables(app, dataStore);
        });

    router.start();
}

init();
