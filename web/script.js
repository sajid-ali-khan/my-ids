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
        const srcIp = pred.src_ip.split('.').slice(-2).join('.');
        const dstIp = pred.dst_ip.split('.').slice(-2).join('.');
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
                <td title="${escapeHtml(pred.src_ip)}">${srcIp}:${pred.src_port}</td>
                <td title="${escapeHtml(pred.dst_ip)}">${dstIp}:${pred.dst_port}</td>
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
            const srcIp = flow.src_ip.split('.').slice(-2).join('.');
            const dstIp = flow.dst_ip.split('.').slice(-2).join('.');
            html += `
                <tr>
                    <td title="${escapeHtml(flow.src_ip)}">${srcIp}:${flow.src_port}</td>
                    <td title="${escapeHtml(flow.dst_ip)}">${dstIp}:${flow.dst_port}</td>
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
