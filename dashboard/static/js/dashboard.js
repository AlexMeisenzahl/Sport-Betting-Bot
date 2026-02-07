/**
 * Sports Betting Dashboard - Frontend JavaScript
 * 
 * Handles all frontend interactivity, AJAX calls, and UI updates
 */

// Constants
const CONFIDENCE_HIGH_THRESHOLD = 70;
const CONFIDENCE_MEDIUM_THRESHOLD = 40;

// Global state
let currentTab = 'alerts';
let autoRefreshInterval = null;
let charts = {};

// Initialize dashboard on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard initializing...');
    
    // Load initial data
    loadMetadata();
    loadAlerts();
    loadNotificationSettings();
    
    // Setup auto-refresh
    setupAutoRefresh();
    
    console.log('Dashboard initialized');
});

// ============================================================================
// TAB MANAGEMENT
// ============================================================================

function showTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('[id^="tab-"]').forEach(btn => {
        btn.classList.remove('tab-active', 'text-blue-400');
        btn.classList.add('text-slate-400');
    });
    
    document.getElementById(`tab-${tabName}`).classList.add('tab-active', 'text-blue-400');
    document.getElementById(`tab-${tabName}`).classList.remove('text-slate-400');
    
    // Update content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.add('hidden');
    });
    
    document.getElementById(`content-${tabName}`).classList.remove('hidden');
    
    currentTab = tabName;
    
    // Load tab-specific data
    if (tabName === 'alerts') {
        loadAlerts();
    } else if (tabName === 'history') {
        loadHistory();
    } else if (tabName === 'analytics') {
        loadAnalytics();
    } else if (tabName === 'settings') {
        loadNotificationSettings();
    }
}

// ============================================================================
// ALERTS FEED
// ============================================================================

async function loadAlerts() {
    const container = document.getElementById('alerts-container');
    const loading = document.getElementById('alerts-loading');
    const empty = document.getElementById('alerts-empty');
    
    loading.classList.remove('hidden');
    container.innerHTML = '';
    empty.classList.add('hidden');
    
    try {
        const params = new URLSearchParams();
        
        const sport = document.getElementById('filter-sport')?.value;
        const time = document.getElementById('filter-time')?.value;
        const confidence = document.getElementById('filter-confidence')?.value;
        const limit = document.getElementById('filter-limit')?.value || '100';
        
        if (sport) params.append('sport', sport);
        if (time) params.append('time_range', time);
        if (confidence) params.append('min_confidence', confidence);
        if (limit) params.append('limit', limit);
        
        const response = await fetch(`/api/alerts?${params.toString()}`);
        const data = await response.json();
        
        loading.classList.add('hidden');
        
        if (data.success && data.alerts.length > 0) {
            data.alerts.forEach(alert => {
                container.appendChild(createAlertCard(alert));
            });
        } else {
            empty.classList.remove('hidden');
        }
    } catch (error) {
        console.error('Error loading alerts:', error);
        loading.classList.add('hidden');
        showToast('Error loading alerts', 'error');
    }
}

function createAlertCard(alert) {
    const card = document.createElement('div');
    card.className = 'card alert-card cursor-pointer';
    
    const confidenceClass = alert.confidence >= CONFIDENCE_HIGH_THRESHOLD ? 'confidence-high' : 
                           alert.confidence >= CONFIDENCE_MEDIUM_THRESHOLD ? 'confidence-medium' : 
                           'confidence-low';
    
    const timestamp = new Date(alert.timestamp).toLocaleString();
    
    card.innerHTML = `
        <div class="flex justify-between items-start mb-3">
            <div>
                <span class="inline-block bg-blue-600 text-xs px-2 py-1 rounded">${alert.sport.toUpperCase()}</span>
                <span class="inline-block bg-purple-600 text-xs px-2 py-1 rounded ml-1">${alert.type}</span>
            </div>
            <div class="text-sm text-slate-400">${timestamp}</div>
        </div>
        
        <h3 class="text-lg font-semibold mb-2">
            ${alert.away_team} @ ${alert.home_team}
        </h3>
        
        <div class="flex justify-between items-end">
            <div>
                <div class="text-sm text-slate-400 mb-1">Bet Type</div>
                <div class="font-medium">${alert.bet_type}</div>
            </div>
            <div class="text-right">
                <div class="text-sm text-slate-400 mb-1">Confidence</div>
                <div class="text-2xl font-bold ${confidenceClass}">${alert.confidence.toFixed(0)}%</div>
            </div>
        </div>
        
        ${alert.odds ? `
        <div class="mt-3 pt-3 border-t border-slate-600">
            <span class="text-sm text-slate-400">Odds: </span>
            <span class="font-medium">${alert.odds}</span>
        </div>
        ` : ''}
    `;
    
    return card;
}

function applyFilters() {
    loadAlerts();
}

// ============================================================================
// ALERT HISTORY
// ============================================================================

let currentPage = 1;
let historyData = [];

async function loadHistory(page = 1) {
    currentPage = page;
    
    try {
        const response = await fetch(`/api/alerts/history?page=${page}&per_page=25`);
        const data = await response.json();
        
        if (data.success) {
            historyData = data.alerts;
            renderHistoryTable(data.alerts);
            renderPagination(data.pagination);
        }
    } catch (error) {
        console.error('Error loading history:', error);
        showToast('Error loading history', 'error');
    }
}

function renderHistoryTable(alerts) {
    const tbody = document.getElementById('history-table-body');
    tbody.innerHTML = '';
    
    if (alerts.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center py-8 text-slate-400">
                    No alerts found
                </td>
            </tr>
        `;
        return;
    }
    
    alerts.forEach(alert => {
        const row = document.createElement('tr');
        row.className = 'border-b border-slate-700 hover:bg-slate-700';
        
        const timestamp = new Date(alert.timestamp).toLocaleString();
        const confidenceClass = alert.confidence >= CONFIDENCE_HIGH_THRESHOLD ? 'text-green-400' : 
                               alert.confidence >= CONFIDENCE_MEDIUM_THRESHOLD ? 'text-yellow-400' : 
                               'text-red-400';
        
        row.innerHTML = `
            <td class="px-4 py-3">${timestamp}</td>
            <td class="px-4 py-3">${alert.sport.toUpperCase()}</td>
            <td class="px-4 py-3">${alert.type}</td>
            <td class="px-4 py-3">${alert.away_team} @ ${alert.home_team}</td>
            <td class="px-4 py-3 ${confidenceClass} font-semibold">${alert.confidence.toFixed(0)}%</td>
            <td class="px-4 py-3">${alert.odds || 'N/A'}</td>
        `;
        
        tbody.appendChild(row);
    });
}

function renderPagination(pagination) {
    const container = document.getElementById('history-pagination');
    container.innerHTML = '';
    
    if (pagination.pages <= 1) return;
    
    // Previous button
    const prevBtn = document.createElement('button');
    prevBtn.textContent = '← Previous';
    prevBtn.className = 'px-4 py-2 bg-slate-700 rounded hover:bg-slate-600 disabled:opacity-50';
    prevBtn.disabled = pagination.page === 1;
    prevBtn.onclick = () => loadHistory(pagination.page - 1);
    container.appendChild(prevBtn);
    
    // Page info
    const pageInfo = document.createElement('span');
    pageInfo.textContent = `Page ${pagination.page} of ${pagination.pages}`;
    pageInfo.className = 'px-4 py-2';
    container.appendChild(pageInfo);
    
    // Next button
    const nextBtn = document.createElement('button');
    nextBtn.textContent = 'Next →';
    nextBtn.className = 'px-4 py-2 bg-slate-700 rounded hover:bg-slate-600 disabled:opacity-50';
    nextBtn.disabled = pagination.page === pagination.pages;
    nextBtn.onclick = () => loadHistory(pagination.page + 1);
    container.appendChild(nextBtn);
}

function exportToCSV() {
    if (historyData.length === 0) {
        showToast('No data to export', 'warning');
        return;
    }
    
    // Create CSV content
    const headers = ['Timestamp', 'Sport', 'Type', 'Match', 'Confidence', 'Odds'];
    const rows = historyData.map(alert => [
        alert.timestamp,
        alert.sport,
        alert.type,
        `${alert.away_team} @ ${alert.home_team}`,
        alert.confidence,
        alert.odds || 'N/A'
    ]);
    
    let csv = headers.join(',') + '\n';
    rows.forEach(row => {
        csv += row.map(cell => `"${cell}"`).join(',') + '\n';
    });
    
    // Download CSV
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `betting-alerts-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
    
    showToast('Exported to CSV', 'success');
}

// ============================================================================
// ANALYTICS
// ============================================================================

async function loadAnalytics() {
    try {
        // Load overview stats
        const overviewResponse = await fetch('/api/analytics/overview');
        const overviewData = await overviewResponse.json();
        
        if (overviewData.success) {
            updateStats(overviewData.stats);
        }
        
        // Load chart data
        const chartsResponse = await fetch('/api/analytics/charts');
        const chartsData = await chartsResponse.json();
        
        if (chartsData.success) {
            renderCharts(chartsData.data);
        }
    } catch (error) {
        console.error('Error loading analytics:', error);
        showToast('Error loading analytics', 'error');
    }
}

function updateStats(stats) {
    document.getElementById('stat-total').textContent = stats.total_alerts.toLocaleString();
    document.getElementById('stat-today').textContent = stats.alerts_today.toLocaleString();
    document.getElementById('stat-confidence').textContent = stats.avg_confidence.toFixed(1) + '%';
    document.getElementById('stat-per-day').textContent = stats.alerts_per_day.toFixed(1);
}

function renderCharts(data) {
    // Destroy existing charts
    Object.values(charts).forEach(chart => chart.destroy());
    charts = {};
    
    // Alerts over time
    const timelineCtx = document.getElementById('chart-timeline').getContext('2d');
    charts.timeline = new Chart(timelineCtx, {
        type: 'line',
        data: {
            labels: data.alerts_over_time.labels,
            datasets: [{
                label: 'Alerts',
                data: data.alerts_over_time.data,
                borderColor: '#3b82f6',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: { beginAtZero: true, ticks: { color: '#cbd5e1' } },
                x: { ticks: { color: '#cbd5e1' } }
            }
        }
    });
    
    // Alerts by sport
    const sportCtx = document.getElementById('chart-sport').getContext('2d');
    charts.sport = new Chart(sportCtx, {
        type: 'bar',
        data: {
            labels: data.alerts_by_sport.labels,
            datasets: [{
                label: 'Alerts',
                data: data.alerts_by_sport.data,
                backgroundColor: '#3b82f6'
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: { beginAtZero: true, ticks: { color: '#cbd5e1' } },
                x: { ticks: { color: '#cbd5e1' } }
            }
        }
    });
    
    // Confidence distribution
    const confCtx = document.getElementById('chart-confidence').getContext('2d');
    charts.confidence = new Chart(confCtx, {
        type: 'bar',
        data: {
            labels: data.confidence_distribution.labels,
            datasets: [{
                label: 'Alerts',
                data: data.confidence_distribution.data,
                backgroundColor: '#10b981'
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: { beginAtZero: true, ticks: { color: '#cbd5e1' } },
                x: { ticks: { color: '#cbd5e1' } }
            }
        }
    });
    
    // Alerts by day
    const dayCtx = document.getElementById('chart-day').getContext('2d');
    charts.day = new Chart(dayCtx, {
        type: 'bar',
        data: {
            labels: data.alerts_by_day.labels,
            datasets: [{
                label: 'Alerts',
                data: data.alerts_by_day.data,
                backgroundColor: '#a855f7'
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: { beginAtZero: true, ticks: { color: '#cbd5e1' } },
                x: { ticks: { color: '#cbd5e1' } }
            }
        }
    });
}

// ============================================================================
// SETTINGS
// ============================================================================

async function loadNotificationSettings() {
    try {
        const response = await fetch('/api/settings/notification');
        const data = await response.json();
        
        if (data.success) {
            const settings = data.settings;
            
            document.getElementById('notif-desktop').checked = settings.desktop?.enabled || false;
            document.getElementById('notif-email').checked = settings.email?.enabled || false;
            document.getElementById('notif-telegram').checked = settings.telegram?.enabled || false;
        }
    } catch (error) {
        console.error('Error loading notification settings:', error);
    }
}

async function saveNotificationSettings() {
    const settings = {
        desktop: {
            enabled: document.getElementById('notif-desktop').checked,
            event_types: {
                trade: true,
                opportunity: true,
                error: true,
                summary: true,
                status_change: true
            }
        },
        email: {
            enabled: document.getElementById('notif-email').checked
        },
        telegram: {
            enabled: document.getElementById('notif-telegram').checked
        }
    };
    
    try {
        const response = await fetch('/api/settings/notification', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(settings)
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('Settings saved successfully', 'success');
        } else {
            showToast('Error saving settings', 'error');
        }
    } catch (error) {
        console.error('Error saving settings:', error);
        showToast('Error saving settings', 'error');
    }
}

async function testNotification(channel) {
    try {
        const response = await fetch('/api/notifications/test', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ channel })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast(data.message, 'success');
        } else {
            showToast(data.error || 'Test failed', 'error');
        }
    } catch (error) {
        console.error('Error testing notification:', error);
        showToast('Error testing notification', 'error');
    }
}

// ============================================================================
// METADATA
// ============================================================================

async function loadMetadata() {
    try {
        // Load sports list
        const sportsResponse = await fetch('/api/metadata/sports');
        const sportsData = await sportsResponse.json();
        
        if (sportsData.success) {
            const select = document.getElementById('filter-sport');
            sportsData.sports.forEach(sport => {
                const option = document.createElement('option');
                option.value = sport;
                option.textContent = sport.toUpperCase();
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading metadata:', error);
    }
}

// ============================================================================
// AUTO-REFRESH
// ============================================================================

function setupAutoRefresh() {
    const interval = parseInt(document.getElementById('auto-refresh')?.value || '60');
    
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
        autoRefreshInterval = null;
    }
    
    if (interval > 0) {
        autoRefreshInterval = setInterval(() => {
            refreshData();
        }, interval * 1000);
    }
}

function refreshData() {
    const icon = document.getElementById('refresh-icon');
    icon.textContent = '⟳';
    icon.style.display = 'inline-block';
    icon.style.animation = 'spin 1s linear infinite';
    
    if (currentTab === 'alerts') {
        loadAlerts();
    } else if (currentTab === 'history') {
        loadHistory(currentPage);
    } else if (currentTab === 'analytics') {
        loadAnalytics();
    }
    
    setTimeout(() => {
        icon.textContent = '🔄';
        icon.style.animation = '';
    }, 1000);
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    
    const toast = document.createElement('div');
    toast.className = `toast bg-slate-800 text-white px-6 py-4 rounded-lg shadow-lg mb-2`;
    
    const icon = type === 'success' ? '✓' : 
                 type === 'error' ? '✗' : 
                 type === 'warning' ? '⚠' : 'ℹ';
    
    const color = type === 'success' ? 'text-green-400' : 
                  type === 'error' ? 'text-red-400' : 
                  type === 'warning' ? 'text-yellow-400' : 'text-blue-400';
    
    toast.innerHTML = `
        <div class="flex items-center space-x-3">
            <span class="${color} text-xl">${icon}</span>
            <span>${message}</span>
        </div>
    `;
    
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// ============================================================================
// ENHANCED DASHBOARD - OVERVIEW & CHARTS
// ============================================================================

/**
 * BettingBotDashboard class for enhanced chart and analytics functionality
 */
class BettingBotDashboard {
    constructor() {
        this.charts = {};
        this.refreshInterval = null;
    }
    
    /**
     * Initialize the enhanced dashboard
     */
    async init() {
        try {
            await this.loadOverview();
            await this.loadCharts();
            this.setupRefresh();
        } catch (error) {
            console.error('Error initializing enhanced dashboard:', error);
        }
    }
    
    /**
     * Load overview statistics
     */
    async loadOverview() {
        try {
            const response = await fetch('/api/overview');
            const result = await response.json();
            
            if (result.success) {
                this.updateMetricCards(result.data);
            }
        } catch (error) {
            console.error('Error loading overview:', error);
        }
    }
    
    /**
     * Update metric cards with overview data
     */
    updateMetricCards(data) {
        // Update bankroll metrics
        if (data.bankroll) {
            this.updateElement('current-bankroll', `$${data.bankroll.current.toFixed(2)}`);
            this.updateElement('total-profit', `$${data.bankroll.profit.toFixed(2)}`);
            this.updateElement('roi-percent', `${data.bankroll.roi.toFixed(1)}%`);
        }
        
        // Update bet statistics
        if (data.bets) {
            this.updateElement('total-bets', data.bets.total);
            this.updateElement('win-rate', `${data.bets.win_rate.toFixed(1)}%`);
            this.updateElement('pending-bets', data.bets.pending);
        }
        
        // Update today's stats
        if (data.today) {
            this.updateElement('today-trades', data.today.trades);
            this.updateElement('today-profit', `$${data.today.profit.toFixed(2)}`);
        }
    }
    
    /**
     * Load and render charts
     */
    async loadCharts() {
        try {
            await this.loadCumulativePnLChart();
            await this.loadStrategyPerformanceChart();
        } catch (error) {
            console.error('Error loading charts:', error);
        }
    }
    
    /**
     * Load and render cumulative P&L chart
     */
    async loadCumulativePnLChart() {
        try {
            const response = await fetch('/api/charts/cumulative-pnl?days=30');
            const result = await response.json();
            
            if (result.success) {
                this.renderLineChart('pnl-chart', result.data);
            }
        } catch (error) {
            console.error('Error loading P&L chart:', error);
        }
    }
    
    /**
     * Load and render strategy performance chart
     */
    async loadStrategyPerformanceChart() {
        try {
            const response = await fetch('/api/charts/strategy-performance');
            const result = await response.json();
            
            if (result.success) {
                this.renderBarChart('strategy-chart', result.data);
            }
        } catch (error) {
            console.error('Error loading strategy chart:', error);
        }
    }
    
    /**
     * Render a line chart using Chart.js
     */
    renderLineChart(canvasId, data) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) {
            console.warn(`Canvas ${canvasId} not found`);
            return;
        }
        
        // Destroy existing chart if any
        if (this.charts[canvasId]) {
            this.charts[canvasId].destroy();
        }
        
        const ctx = canvas.getContext('2d');
        this.charts[canvasId] = new Chart(ctx, {
            type: 'line',
            data: data,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        ticks: {
                            callback: function(value) {
                                return '$' + value.toFixed(2);
                            }
                        }
                    }
                }
            }
        });
    }
    
    /**
     * Render a bar chart using Chart.js
     */
    renderBarChart(canvasId, data) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) {
            console.warn(`Canvas ${canvasId} not found`);
            return;
        }
        
        // Destroy existing chart if any
        if (this.charts[canvasId]) {
            this.charts[canvasId].destroy();
        }
        
        const ctx = canvas.getContext('2d');
        this.charts[canvasId] = new Chart(ctx, {
            type: 'bar',
            data: data,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.parsed.y.toFixed(1) + '%';
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return value + '%';
                            }
                        }
                    }
                }
            }
        });
    }
    
    /**
     * Export trades to CSV
     */
    async exportTrades(filters = {}) {
        try {
            const response = await fetch('/api/export/trades', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(filters)
            });
            
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `trades_export_${new Date().toISOString().split('T')[0]}.csv`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
                
                showToast('Trades exported successfully', 'success');
            } else {
                throw new Error('Export failed');
            }
        } catch (error) {
            console.error('Error exporting trades:', error);
            showToast('Error exporting trades', 'error');
        }
    }
    
    /**
     * Setup auto-refresh for charts and metrics
     */
    setupRefresh(intervalSeconds = 60) {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
        
        this.refreshInterval = setInterval(() => {
            this.loadOverview();
            this.loadCharts();
        }, intervalSeconds * 1000);
    }
    
    /**
     * Helper to update element text content
     */
    updateElement(id, value) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    }
    
    /**
     * Destroy all charts and cleanup
     */
    destroy() {
        Object.values(this.charts).forEach(chart => chart.destroy());
        this.charts = {};
        
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }
}

// Create global dashboard instance
const enhancedDashboard = new BettingBotDashboard();

// Initialize enhanced dashboard if Chart.js is available
if (typeof Chart !== 'undefined') {
    document.addEventListener('DOMContentLoaded', function() {
        enhancedDashboard.init();
    });
}

