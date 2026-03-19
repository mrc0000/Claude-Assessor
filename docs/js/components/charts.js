/**
 * Chart.js wrapper utilities — editorial light theme.
 */

const COLORS = {
    red: '#c4553a',
    green: '#3a7d5c',
    yellow: '#b8860b',
    blue: '#2c5f8a',
    orange: '#c47e33',
    cyan: '#2a7f9e',
    purple: '#8b6daf',
    accent: '#2c5f8a',
    muted: '#7a7a7a',
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
    tone_modulated_high: '#a0642a',
    tone_modulated_moderate: COLORS.orange,
    tone_modulated_low: '#d4a95a',
    tone_modulated: COLORS.orange,
    consistent: COLORS.green,
};

// Chart.js defaults for light editorial theme
if (typeof Chart !== 'undefined') {
    Chart.defaults.color = '#7a7a7a';
    Chart.defaults.borderColor = '#edeae5';
    Chart.defaults.font.family = "'Inter', -apple-system, BlinkMacSystemFont, sans-serif";
    Chart.defaults.font.size = 12;
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
                    grid: { color: '#edeae5' },
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
                borderWidth: 2,
                borderColor: '#ffffff',
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: { boxWidth: 10, padding: 8, font: { size: 11 } },
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
                    grid: { color: '#edeae5' },
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
                    grid: { color: '#edeae5' },
                    pointLabels: { font: { size: 11 } },
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
