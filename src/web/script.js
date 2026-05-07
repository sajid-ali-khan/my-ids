/**
 * IDS Dashboard - Frontend Script
 * Real-time data updates via AJAX polling
 */

const API_BASE = '/api';
const REFRESH_INTERVAL = 2000; // 2 seconds

let updateIntervalId = null;
let pipelineRunning = false;

// ============================================================================
// Initialization
// ============================================================================

document.addEventListener('DOMContentLoaded', function() {
    console.log('[Dashboard] Initializing...');
    
    // Load initial data
    loadConfig();
    loadSettings();
    updateAll();
    
    // Start periodic updates
    startAutoRefresh();
    
    console.log('[Dashboard] Ready');
});

// ============================================================================
// Auto-Refresh
// ============================================================================

function startAutoRefresh() {
    if (updateIntervalId) clearInterval(updateIntervalId);
    
    updateIntervalId = setInterval(function() {
        updateAll();
    }, REFRESH_INTERVAL);
}

function stopAutoRefresh() {
    if (updateIntervalId) {
        clearInterval(updateIntervalId);
        updateIntervalId = null;
    }
}

// ============================================================================
// Main Update Function
// ============================================================================

async function updateAll() {
    try {
        // Get summary (includes status, stats, predictions)
        const summaryResp = await fetch(`${API_BASE}/summary`);
        const summary = await summaryResp.json();
        
        // Update status
        updateStatus(summary.pipeline.running);
        pipelineRunning = summary.pipeline.running;
        
        // Update statistics
        updateStatistics(summary.statistics);
        
        // Update predictions table
        updatePredictionsTable(summary.recent_predictions);
        
        // Update active flows
        await updateActiveFlows();
        
        // Update timestamp
        updateTimestamp();
        
    } catch (error) {
        console.error('[Dashboard] Update error:', error);
        setStatusDisconnected();
    }
}

// ============================================================================
// Status Updates
// ============================================================================

function updateStatus(running) {
    const dot = document.getElementById('statusDot');
    const text = document.getElementById('statusText');
    const startBtn = document.getElementById('startBtn');
    const stopBtn = document.getElementById('stopBtn');
    
    if (running) {
        dot.className = 'status-dot running';
        text.textContent = 'Running';
        startBtn.disabled = true;
        stopBtn.disabled = false;
    } else {
        dot.className = 'status-dot stopped';
        text.textContent = 'Stopped';
        startBtn.disabled = false;
        stopBtn.disabled = true;
    }
}

function setStatusDisconnected() {
    const dot = document.getElementById('statusDot');
    const text = document.getElementById('statusText');
    dot.className = 'status-dot';
    dot.style.backgroundColor = '#ccc';
    text.textContent = 'Disconnected';
}

// ============================================================================
// Statistics Updates
// ============================================================================

function updateStatistics(stats) {
    document.getElementById('totalPredictions').textContent = stats.total_predictions;
    document.getElementById('benignCount').textContent = stats.benign_traffic;
    document.getElementById('attackCount').textContent = stats.attack_traffic;
    
    // Calculate attack rate
    const rate = stats.total_predictions > 0 
        ? (stats.attack_traffic / stats.total_predictions * 100).toFixed(1) 
        : 0;
    document.getElementById('attackRate').textContent = rate + '%';
    
    // Update class breakdown
    updateClassBreakdown(stats.by_class);
}

function updateClassBreakdown(classStats) {
    const container = document.getElementById('classStats');
    
    if (Object.keys(classStats).length === 0) {
        container.innerHTML = '<p style="color: #999; margin: 10px 0;">No data yet</p>';
        return;
    }
    
    let html = '';
    for (const [className, count] of Object.entries(classStats)) {
        html += `
            <div class="class-item">
                <span class="class-name">${escapeHtml(className)}</span>
                <span class="class-count">${count}</span>
            </div>
        `;
    }
    
    container.innerHTML = html;
}

// ============================================================================
// Predictions Table
// ============================================================================

function updatePredictionsTable(predictions) {
    const table = document.getElementById('predictionsTable');
    const tbody = table.querySelector('tbody');
    
    if (!predictions || predictions.length === 0) {
        tbody.innerHTML = '<tr class="no-data"><td colspan="5">No predictions yet</td></tr>';
        document.getElementById('predCount').textContent = '0';
        return;
    }
    
    let html = '';
    predictions.slice(0, 100).forEach(pred => {
        const time = formatTime(pred.timestamp);
        const srcDisplay = pred.src_domain ? pred.src_domain : pred.src_ip;
        const dstDisplay = pred.dst_domain ? pred.dst_domain : pred.dst_ip;
        const predClass = pred.prediction === 'Normal Traffic' 
            ? 'prediction-benign' 
            : 'prediction-attack';
        const confClass = pred.confidence >= 0.9 
            ? 'confidence-high' 
            : pred.confidence >= 0.7 
            ? 'confidence-medium' 
            : 'confidence-low';
        
        html += `
            <tr>
                <td>${time}</td>
                <td title="${escapeHtml(pred.src_ip)}:${pred.src_port}">${srcDisplay}:${pred.src_port}</td>
                <td title="${escapeHtml(pred.dst_ip)}:${pred.dst_port}">${dstDisplay}:${pred.dst_port}</td>
                <td><span class="${predClass}">${escapeHtml(pred.prediction.substring(0, 6))}</span></td>
                <td><span class="${confClass}">${(pred.confidence * 100).toFixed(0)}%</span></td>
            </tr>
        `;
    });
    
    tbody.innerHTML = html;
    document.getElementById('predCount').textContent = predictions.length;
}

// ============================================================================
// Active Flows
// ============================================================================

async function updateActiveFlows() {
    try {
        const resp = await fetch(`${API_BASE}/flows`);
        const data = await resp.json();
        
        const table = document.getElementById('flowsTable');
        const tbody = table.querySelector('tbody');
        
        if (!data.flows || data.flows.length === 0) {
            tbody.innerHTML = '<tr class="no-data"><td colspan="4">No active flows</td></tr>';
            document.getElementById('flowCount').textContent = '0';
            return;
        }
        
        let html = '';
        data.flows.slice(0, 50).forEach(flow => {
            const srcDisplay = flow.src_domain ? flow.src_domain : flow.src_ip;
            const dstDisplay = flow.dst_domain ? flow.dst_domain : flow.dst_ip;
            html += `
                <tr>
                    <td title="${escapeHtml(flow.src_ip)}:${flow.src_port}">${srcDisplay}:${flow.src_port}</td>
                    <td title="${escapeHtml(flow.dst_ip)}:${flow.dst_port}">${dstDisplay}:${flow.dst_port}</td>
                    <td>${flow.packets}</td>
                    <td>${(flow.active_time).toFixed(1)}s</td>
                </tr>
            `;
        });
        
        tbody.innerHTML = html;
        document.getElementById('flowCount').textContent = data.active;
        
    } catch (error) {
        console.error('[Dashboard] Error loading flows:', error);
    }
}

// ============================================================================
// Configuration
// ============================================================================

async function loadConfig() {
    try {
        const resp = await fetch(`${API_BASE}/config`);
        const config = await resp.json();
        
        document.getElementById('configInterface').textContent = config.network_interface;
        document.getElementById('configFeatures').textContent = config.features_count;
        document.getElementById('configFlusher').textContent = config.flusher_interval + ' s';
        document.getElementById('configTimeout').textContent = config.idle_timeout + ' s';
        
    } catch (error) {
        console.error('[Dashboard] Error loading config:', error);
    }
}

// ============================================================================
// Control Functions
// ============================================================================

async function startPipeline() {
    console.log('[Dashboard] Starting pipeline...');
    
    try {
        const resp = await fetch(`${API_BASE}/start`, { method: 'POST' });
        const data = await resp.json();
        
        if (resp.ok) {
            console.log('[Dashboard] Pipeline started');
            updateStatus(true);
            updateAll();
        } else {
            alert('Error: ' + data.message);
        }
    } catch (error) {
        console.error('[Dashboard] Error starting pipeline:', error);
        alert('Failed to start pipeline');
    }
}

async function stopPipeline() {
    console.log('[Dashboard] Stopping pipeline...');
    
    try {
        const resp = await fetch(`${API_BASE}/stop`, { method: 'POST' });
        const data = await resp.json();
        
        if (resp.ok) {
            console.log('[Dashboard] Pipeline stopped');
            updateStatus(false);
        } else {
            alert('Error: ' + data.message);
        }
    } catch (error) {
        console.error('[Dashboard] Error stopping pipeline:', error);
        alert('Failed to stop pipeline');
    }
}

// ============================================================================
// Utility Functions
// ============================================================================

function formatTime(isoString) {
    const date = new Date(isoString);
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    const seconds = String(date.getSeconds()).padStart(2, '0');
    return `${hours}:${minutes}:${seconds}`;
}

function updateTimestamp() {
    const now = new Date();
    document.getElementById('lastUpdate').textContent = now.toLocaleTimeString();
}

function escapeHtml(unsafe) {
    if (!unsafe) return '';
    return unsafe
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

// ============================================================================
// Settings Management
// ============================================================================

async function loadSettings() {
    try {
        const resp = await fetch(`${API_BASE}/config`);
        const config = await resp.json();
        
        document.getElementById('settingsFlusherInterval').value = config.flusher_interval;
        document.getElementById('settingsIdleTimeout').value = config.idle_timeout;
        document.getElementById('settingsMaxHistory').value = config.max_history;
        
        showSettingsMessage('Settings loaded', 'success');
        
    } catch (error) {
        console.error('[Dashboard] Error loading settings:', error);
        showSettingsMessage('Failed to load settings', 'error');
    }
}

async function saveSettings() {
    try {
        const flusherInterval = parseInt(document.getElementById('settingsFlusherInterval').value);
        const idleTimeout = parseInt(document.getElementById('settingsIdleTimeout').value);
        const maxHistory = parseInt(document.getElementById('settingsMaxHistory').value);
        
        // Validation
        if (!flusherInterval || flusherInterval <= 0) {
            showSettingsMessage('Flusher interval must be > 0', 'error');
            return;
        }
        if (!idleTimeout || idleTimeout <= 0) {
            showSettingsMessage('Idle timeout must be > 0', 'error');
            return;
        }
        if (!maxHistory || maxHistory <= 0) {
            showSettingsMessage('Max history must be > 0', 'error');
            return;
        }
        
        // Send update request
        const resp = await fetch(`${API_BASE}/config`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                flusher_interval: flusherInterval,
                idle_timeout: idleTimeout,
                max_history: maxHistory
            })
        });
        
        const result = await resp.json();
        
        if (resp.ok && result.status === 'success') {
            showSettingsMessage('✓ Settings saved successfully', 'success');
            // Reload config display
            loadConfig();
        } else {
            showSettingsMessage('Error: ' + (result.message || result.error || 'Unknown error'), 'error');
        }
        
    } catch (error) {
        console.error('[Dashboard] Error saving settings:', error);
        showSettingsMessage('Failed to save settings', 'error');
    }
}

function showSettingsMessage(message, type) {
    const msgEl = document.getElementById('settingsMessage');
    msgEl.textContent = message;
    msgEl.className = 'settings-message ' + type;
    
    // Clear message after 3 seconds
    setTimeout(() => {
        msgEl.textContent = '';
        msgEl.className = 'settings-message';
    }, 3000);
}

// ============================================================================
// Tab Management
// ============================================================================

function switchTab(tabName) {
    // Hide all tab contents
    document.getElementById('tab-live-content').style.display = 'none';
    document.getElementById('tab-history-content').style.display = 'none';
    
    // Remove active class from all buttons
    document.getElementById('tab-live').classList.remove('active');
    document.getElementById('tab-history').classList.remove('active');
    
    // Show selected tab
    if (tabName === 'live') {
        document.getElementById('tab-live-content').style.display = '';
        document.getElementById('tab-live').classList.add('active');
        startAutoRefresh();  // Resume live updates
    } else if (tabName === 'history') {
        document.getElementById('tab-history-content').style.display = '';
        document.getElementById('tab-history').classList.add('active');
        stopAutoRefresh();  // Stop live updates to reduce API calls
        loadAlertHistory();  // Load alerts for this tab
    }
}

// ============================================================================
// Alert History Functions
// ============================================================================

async function loadAlertHistory() {
    try {
        const limit = document.getElementById('filterLimit').value || 50;
        const severity = document.getElementById('filterSeverity').value;
        const attackType = document.getElementById('filterAttackType').value;
        
        // Build query string
        const params = new URLSearchParams();
        params.append('limit', limit);
        if (severity) params.append('severity', severity);
        if (attackType) params.append('attack_type', attackType);
        
        // Get alerts
        const alertResp = await fetch(`${API_BASE}/persistent-alerts?${params}`);
        const alertData = await alertResp.json();
        
        // Get stats
        const statsResp = await fetch(`${API_BASE}/alert-stats`);
        const stats = await statsResp.json();
        
        if (alertResp.ok) {
            updateAlertTable(alertData.alerts || []);
            updateAlertStats(stats);
        } else {
            console.error('[Dashboard] Error loading alerts:', alertData);
            updateAlertTable([]);
        }
        
    } catch (error) {
        console.error('[Dashboard] Error loading alert history:', error);
    }
}

function updateAlertStats(stats) {
    document.getElementById('statTotalAlerts').textContent = stats.total_alerts || 0;
    document.getElementById('statCritical').textContent = stats.critical_count || 0;
    document.getElementById('statHigh').textContent = stats.high_count || 0;
    document.getElementById('statToday').textContent = stats.today_count || 0;
    document.getElementById('statAcknowledged').textContent = stats.acknowledged_count || 0;
}

function updateAlertTable(alerts) {
    const tbody = document.querySelector('#alertsTable tbody');
    document.getElementById('alertCount').textContent = alerts.length;
    
    if (alerts.length === 0) {
        tbody.innerHTML = '<tr class="no-data"><td colspan="8">No alerts found</td></tr>';
        return;
    }
    
    tbody.innerHTML = alerts.map(alert => {
        const timestamp = new Date(alert.timestamp * 1000).toLocaleString();
        const severityClass = `severity-${alert.severity}`;
        const statusClass = alert.acknowledged ? 'status-acked' : 'status-pending';
        const statusText = alert.acknowledged ? '✓ Acknowledged' : '⏳ Pending';
        const btnClass = alert.acknowledged ? 'btn-ack acked' : 'btn-ack';
        const btnText = alert.acknowledged ? '✓ Confirmed' : 'Acknowledge';
        const btnDisabled = alert.acknowledged ? 'disabled' : '';
        
        // Check if this is a suspicious alert
        const isSuspicious = alert.attack_type === 'Suspicious';
        const rowClass = isSuspicious ? 'suspicious-row' : '';
        const attackTypeClass = isSuspicious ? 'attack-type-suspicious' : '';
        const attackTypeDisplay = isSuspicious ? '⚠️  ' + escapeHtml(alert.attack_type) : escapeHtml(alert.attack_type);
        
        return `
            <tr class="${rowClass}">
                <td>${escapeHtml(timestamp.split(' ')[1])}</td>
                <td><span class="${severityClass}">${escapeHtml(alert.severity.toUpperCase())}</span></td>
                <td><span class="${attackTypeClass}">${attackTypeDisplay}</span></td>
                <td>${escapeHtml(alert.src_ip)}:${alert.src_port || '-'}</td>
                <td>${escapeHtml(alert.dst_ip)}:${alert.dst_port}</td>
                <td>${(alert.confidence * 100).toFixed(0)}%</td>
                <td><span class="${statusClass}">${statusText}</span></td>
                <td>
                    <button class="${btnClass}" onclick="acknowledgeAlert(${alert.id})" ${btnDisabled}>
                        ${btnText}
                    </button>
                </td>
            </tr>
        `;
    }).join('');
}

async function acknowledgeAlert(alertId) {
    try {
        // TODO: Implement acknowledge endpoint
        // For now, just show message
        alert('Acknowledge functionality coming soon!');
    } catch (error) {
        console.error('[Dashboard] Error acknowledging alert:', error);
    }
}

function exportAlertsCSV() {
    try {
        const severity = document.getElementById('filterSeverity').value;
        let filename = 'ids-alerts.csv';
        
        if (severity) {
            filename = `ids-alerts-${severity}.csv`;
        }
        
        // Get current alerts from table
        const table = document.getElementById('alertsTable');
        const rows = [];
        
        // Add headers
        rows.push('Time,Severity,Attack Type,Source,Destination,Confidence,Status,Acknowledged');
        
        // Add data rows
        table.querySelectorAll('tbody tr').forEach(tr => {
            if (!tr.classList.contains('no-data')) {
                const cells = tr.querySelectorAll('td');
                const row = Array.from(cells).map((cell, idx) => {
                    // Skip action column  (last one)
                    if (idx < cells.length - 1) {
                        return '"' + cell.textContent.trim().replace(/"/g, '""') + '"';
                    }
                    return '';
                }).slice(0, -1).join(',');
                
                rows.push(row);
            }
        });
        
        // Create blob and download
        const csv = rows.join('\n');
        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);
        
        link.setAttribute('href', url);
        link.setAttribute('download', filename);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
    } catch (error) {
        console.error('[Dashboard] Error exporting alerts:', error);
        alert('Failed to export alerts');
    }
}
