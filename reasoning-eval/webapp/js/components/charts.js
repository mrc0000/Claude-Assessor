/**
 * Chart.js wrapper utilities.
 */

const COLORS = {
    red: '#ef4444',
    green: '#22c55e',
    yellow: '#eab308',
    blue: '#3b82f6',
    orange: '#f97316',
    cyan: '#06b6d4',
    purple: '#a855f7',
    accent: '#7c3aed',
    muted: '#8892b0',
};

const DOMAIN_COLORS = {
    copyright: COLORS.purple,
    legal: COLORS.blue,
    financial: COLORS.yellow,
    medical: COLORS.red,
    cybersecurity: COLORS.green,
    chemistry: COLORS.orange,
    reasoning: COLORS.cyan,
};

const VERDICT_COLORS = {
    discriminatory: COLORS.red,
    tone_modulated_high: '#b45309',
    tone_modulated_moderate: COLORS.orange,
    tone_modulated_low: '#fde68a',
    tone_modulated: COLORS.orange,
    consistent: COLORS.green,
};

// Chart.js defaults for dark theme
if (typeof Chart !== 'undefined') {
    Chart.defaults.color = '#8892b0';
    Chart.defaults.borderColor = '#2a2f3d';
    Chart.defaults.font.family = "'SF Mono','Cascadia Code','Fira Code','JetBrains Mono',monospace";
    Chart.defaults.font.size = 11;
}

export function createBarChart(canvas, labels, datasets, options = {}) {
    return new Chart(canvas, {
        type: 'bar',
        data: { labels, datasets },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    labels: { boxWidth: 12, padding: 12 },
                },
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: '#1c2029' },
                },
                x: {
                    grid: { display: false },
                },
            },
            ...options,
        },
    });
}

export function createDoughnutChart(canvas, labels, data, colors) {
    return new Chart(canvas, {
        type: 'doughnut',
        data: {
            labels,
            datasets: [{
                data,
                backgroundColor: colors,
                borderWidth: 0,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: { boxWidth: 10, padding: 8, font: { size: 10 } },
                },
            },
            cutout: '60%',
        },
    });
}

export function createHorizontalBarChart(canvas, labels, datasets, options = {}) {
    return new Chart(canvas, {
        type: 'bar',
        data: { labels, datasets },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    labels: { boxWidth: 12, padding: 12 },
                },
            },
            scales: {
                x: {
                    beginAtZero: true,
                    grid: { color: '#1c2029' },
                },
                y: {
                    grid: { display: false },
                },
            },
            ...options,
        },
    });
}

export function createRadarChart(canvas, labels, datasets) {
    return new Chart(canvas, {
        type: 'radar',
        data: { labels, datasets },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                r: {
                    beginAtZero: true,
                    grid: { color: '#1c2029' },
                    pointLabels: { font: { size: 10 } },
                    ticks: { display: false },
                },
            },
            plugins: {
                legend: {
                    position: 'top',
                    labels: { boxWidth: 12, padding: 12 },
                },
            },
        },
    });
}

export { COLORS, DOMAIN_COLORS, VERDICT_COLORS };
