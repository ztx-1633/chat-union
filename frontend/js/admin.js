const API_BASE = 'http://localhost:8000/api/admin';
let performanceChart = null;
let requestsChart = null;

$(document).ready(function() {
    initMenu();
    refreshDashboard();
    refreshGateways();
    refreshVersions();
    refreshAuditLogs();
    refreshRevenue();
    refreshEcosystemPool();
    setInterval(refreshDashboard, 30000);
});

function initMenu() {
    $('.menu-item').on('click', function() {
        const section = $(this).data('section');
        $('.menu-item').removeClass('active');
        $(this).addClass('active');
        $('.content-section').removeClass('active');
        $(`#${section}-section`).addClass('active');
    });
}

async function fetchAPI(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        return { success: false, error: error.message };
    }
}

async function refreshDashboard() {
    const data = await fetchAPI('/monitoring/dashboard');
    if (data.success) {
        $('#total-gateways').text(data.summary.total_gateways);
        $('#online-gateways').text(data.summary.online_gateways);
        $('#total-requests').text(data.summary.total_requests.toLocaleString());
        $('#error-rate').text(data.summary.error_rate + '%');
    }

    const alertsData = await fetchAPI('/monitoring/alerts');
    if (alertsData.success) {
        renderAlerts(alertsData.alerts);
    }

    const gatewaysData = await fetchAPI('/monitoring/gateways');
    if (gatewaysData.success) {
        renderCharts(gatewaysData.gateways);
    }
}

function renderAlerts(alerts) {
    const container = $('#alerts-list');
    if (!alerts || alerts.length === 0) {
        container.html('<p class="empty-state">暂无告警</p>');
        return;
    }

    container.html(alerts.map(alert => `
        <div class="alert-item ${alert.severity}">
            <div class="alert-message">
                <strong>${alert.gateway_name}</strong>: ${alert.message}
            </div>
            <div style="font-size: 12px; color: #64748b; margin-top: 4px;">
                ${alert.timestamp}
            </div>
        </div>
    `).join(''));
}

function renderCharts(gateways) {
    const ctx1 = document.getElementById('performanceChart');
    const ctx2 = document.getElementById('requestsChart');

    if (performanceChart) performanceChart.destroy();
    if (requestsChart) requestsChart.destroy();

    performanceChart = new Chart(ctx1, {
        type: 'line',
        data: {
            labels: gateways.map(g => g.name),
            datasets: [{
                label: 'CPU 使用率 (%)',
                data: gateways.map(g => g.current_cpu || 0),
                borderColor: '#667eea',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                tension: 0.4
            }, {
                label: '内存使用率 (%)',
                data: gateways.map(g => g.current_memory || 0),
                borderColor: '#10b981',
                backgroundColor: 'rgba(16, 185, 129, 0.1)',
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { position: 'top' } }
        }
    });

    requestsChart = new Chart(ctx2, {
        type: 'bar',
        data: {
            labels: gateways.map(g => g.name),
            datasets: [{
                label: '请求数',
                data: gateways.map(g => g.recent_requests || 0),
                backgroundColor: '#667eea'
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { position: 'top' } }
        }
    });
}

async function refreshGateways() {
    const data = await fetchAPI('/gateways');
    if (data.success) {
        renderGatewaysTable(data.gateways);
    }
}

function renderGatewaysTable(gateways) {
    const tbody = $('#gateways-table-body');
    if (!gateways || gateways.length === 0) {
        tbody.html('<tr><td colspan="7" class="empty-state">暂无网关数据</td></tr>');
        return;
    }

    tbody.html(gateways.map(gateway => `
        <tr>
            <td>${gateway.gateway_id.substring(0, 8)}...</td>
            <td>${gateway.name}</td>
            <td>${gateway.version}</td>
            <td><span class="status-badge ${gateway.status}">${gateway.status}</span></td>
            <td>${gateway.endpoint}</td>
            <td>${gateway.last_heartbeat || '-'}</td>
            <td>
                <button class="btn btn-secondary btn-table" onclick="sendHeartbeat('${gateway.gateway_id}')">心跳</button>
            </td>
        </tr>
    `).join(''));
}

async function sendHeartbeat(gatewayId) {
    await fetchAPI(`/gateways/${gatewayId}/heartbeat`, { method: 'POST' });
    refreshGateways();
}

async function refreshVersions() {
    const data = await fetchAPI('/gateways/versions');
    if (data.success) {
        renderVersionsTable(data.versions);
    }
}

function renderVersionsTable(versions) {
    const tbody = $('#versions-table-body');
    if (!versions || Object.keys(versions).length === 0) {
        tbody.html('<tr><td colspan="5" class="empty-state">暂无版本数据</td></tr>');
        return;
    }

    tbody.html(Object.entries(versions).map(([id, gateway]) => `
        <tr>
            <td>${gateway.name}</td>
            <td>${gateway.current_version}</td>
            <td><span class="status-badge ${gateway.status}">${gateway.status}</span></td>
            <td>${gateway.last_heartbeat || '-'}</td>
            <td>
                <button class="btn btn-secondary btn-table">部署版本</button>
            </td>
        </tr>
    `).join(''));
}

async function refreshAuditLogs() {
    const data = await fetchAPI('/audit/logs');
    if (data.success) {
        renderAuditTable(data.logs);
    }
}

function renderAuditTable(logs) {
    const tbody = $('#audit-table-body');
    if (!logs || logs.length === 0) {
        tbody.html('<tr><td colspan="7" class="empty-state">暂无审计日志</td></tr>');
        return;
    }

    tbody.html(logs.map(log => `
        <tr>
            <td>${log.created_at}</td>
            <td>${log.user_id || '-'}</td>
            <td>${log.action}</td>
            <td>${log.resource_type || '-'}</td>
            <td>${log.resource_id || '-'}</td>
            <td>${log.details || '-'}</td>
            <td><span class="status-badge ${log.status}">${log.status}</span></td>
        </tr>
    `).join(''));
}

async function refreshRevenue() {
    const statsData = await fetchAPI('/revenue/statistics');
    if (statsData.success) {
        $('#total-revenue').text(statsData.statistics.total_amount.toLocaleString());
        $('#source-gateway-fee').text(statsData.statistics.total_source_gateway_fee.toLocaleString());
        $('#ecosystem-fee').text(statsData.statistics.total_ecosystem_pool_fee.toLocaleString());
    }

    const txData = await fetchAPI('/revenue/transactions');
    if (txData.success) {
        renderRevenueTable(txData.transactions);
    }
}

function renderRevenueTable(transactions) {
    const tbody = $('#revenue-table-body');
    if (!transactions || transactions.length === 0) {
        tbody.html('<tr><td colspan="9" class="empty-state">暂无交易记录</td></tr>');
        return;
    }

    tbody.html(transactions.map(tx => `
        <tr>
            <td>${tx.transaction_id.substring(0, 8)}...</td>
            <td>${tx.source_gateway_id.substring(0, 8)}...</td>
            <td>${tx.target_gateway_id ? tx.target_gateway_id.substring(0, 8) + '...' : '-'}</td>
            <td>${tx.amount}</td>
            <td>${tx.source_gateway_fee}</td>
            <td>${tx.ecosystem_pool_fee}</td>
            <td>${tx.net_amount}</td>
            <td>${tx.transaction_type}</td>
            <td>${tx.created_at}</td>
        </tr>
    `).join(''));
}

async function updateFeeRates() {
    const sourceRate = parseFloat($('#source-gateway-rate').val()) / 100;
    const ecosystemRate = parseFloat($('#ecosystem-pool-rate').val()) / 100;

    await fetchAPI('/revenue/fee-rates', {
        method: 'PUT',
        body: JSON.stringify({
            source_gateway_rate: sourceRate,
            ecosystem_pool_rate: ecosystemRate
        })
    });

    alert('分成比例已更新');
}

async function refreshEcosystemPool() {
    const balanceData = await fetchAPI('/ecosystem-pool/balance');
    if (balanceData.success) {
        $('#pool-balance').text(balanceData.balance.toLocaleString());
    }

    const statsData = await fetchAPI('/ecosystem-pool/statistics');
    if (statsData.success) {
        $('#pool-deposits').text(statsData.statistics.total_deposits.toLocaleString());
        $('#pool-withdrawals').text(statsData.statistics.total_withdrawals.toLocaleString());
    }

    const historyData = await fetchAPI('/ecosystem-pool/history');
    if (historyData.success) {
        renderPoolTable(historyData.history);
    }
}

function renderPoolTable(history) {
    const tbody = $('#pool-table-body');
    if (!history || history.length === 0) {
        tbody.html('<tr><td colspan="6" class="empty-state">暂无历史记录</td></tr>');
        return;
    }

    tbody.html(history.map(entry => `
        <tr>
            <td>${entry.created_at}</td>
            <td>${entry.transaction_id.substring(0, 8)}...</td>
            <td>${entry.transaction_type}</td>
            <td style="color: ${entry.amount > 0 ? '#10b981' : '#ef4444'}">${entry.amount > 0 ? '+' : ''}${entry.amount}</td>
            <td>${entry.balance}</td>
            <td>${entry.description || '-'}</td>
        </tr>
    `).join(''));
}

function openRegisterGatewayModal() {
    $('#registerGatewayModal').addClass('active');
}

async function registerGateway() {
    const name = $('#gateway-name').val();
    const version = $('#gateway-version').val();
    const endpoint = $('#gateway-endpoint').val();

    if (!name || !version || !endpoint) {
        alert('请填写完整信息');
        return;
    }

    await fetchAPI('/gateways', {
        method: 'POST',
        body: JSON.stringify({ name, version, endpoint })
    });

    closeModal('registerGatewayModal');
    refreshGateways();
    refreshVersions();
}

function openTransactionModal() {
    $('#transactionModal').addClass('active');
}

async function createTransaction() {
    const sourceGatewayId = $('#tx-source-gateway').val();
    const targetGatewayId = $('#tx-target-gateway').val() || null;
    const amount = parseFloat($('#tx-amount').val());
    const transactionType = $('#tx-type').val();
    const details = $('#tx-details').val();

    if (!sourceGatewayId || !amount) {
        alert('请填写必要信息');
        return;
    }

    await fetchAPI('/revenue/transactions', {
        method: 'POST',
        body: JSON.stringify({
            source_gateway_id: sourceGatewayId,
            target_gateway_id: targetGatewayId,
            amount,
            transaction_type: transactionType,
            details
        })
    });

    closeModal('transactionModal');
    refreshRevenue();
    refreshEcosystemPool();
}

function openWithdrawalModal() {
    $('#withdrawalModal').addClass('active');
}

async function withdrawFromPool() {
    const amount = parseFloat($('#wd-amount').val());
    const description = $('#wd-description').val();
    const approvedBy = $('#wd-approved-by').val();

    if (!amount || !description || !approvedBy) {
        alert('请填写完整信息');
        return;
    }

    const result = await fetchAPI('/ecosystem-pool/withdraw', {
        method: 'POST',
        body: JSON.stringify({ amount, description, approved_by: approvedBy })
    });

    if (result.success) {
        closeModal('withdrawalModal');
        refreshEcosystemPool();
    } else {
        alert('提取失败: ' + (result.error || '余额不足'));
    }
}

function closeModal(modalId) {
    $(`#${modalId}`).removeClass('active');
}

$('.modal .btn-secondary').on('click', function() {
    $(this).closest('.modal').removeClass('active');
});
