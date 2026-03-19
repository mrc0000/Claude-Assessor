/**
 * Minimal hash-based router.
 * Routes: #/path/param1/param2
 */
export class Router {
    constructor() {
        this.routes = [];
        this.current = null;
        window.addEventListener('hashchange', () => this.resolve());
    }

    on(pattern, handler) {
        // Convert /path/:param to regex
        const parts = pattern.split('/').map(p =>
            p.startsWith(':') ? '([^/]+)' : p.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
        );
        const regex = new RegExp('^' + parts.join('/') + '$');
        this.routes.push({ pattern, regex, handler });
        return this;
    }

    resolve() {
        const hash = window.location.hash.slice(1) || '/';
        for (const route of this.routes) {
            const match = hash.match(route.regex);
            if (match) {
                const params = match.slice(1).map(decodeURIComponent);
                this.current = route.pattern;
                route.handler(...params);
                this._updateNav(hash);
                return;
            }
        }
        // Default to landing
        window.location.hash = '#/';
    }

    _updateNav(hash) {
        document.querySelectorAll('.nav-links a').forEach(a => {
            const href = a.getAttribute('href');
            const isActive = hash === href || (href !== '#/' && hash.startsWith(href));
            a.classList.toggle('active', isActive);
        });
    }

    start() {
        this.resolve();
    }
}
