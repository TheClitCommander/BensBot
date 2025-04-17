// Dashboard JavaScript for the Strategy Ensemble Monitor

// Chart.js global configuration
Chart.defaults.font.family = 'Roboto, sans-serif';
Chart.defaults.color = '#6c757d';
Chart.defaults.scale.grid.color = 'rgba(0, 0, 0, 0.05)';

// Global variables
let socket;
let performanceChart;
let weightsChart;
let correlationChart;
let currentPeriod = '7d'; // Default to 7 days
let currentEnsemble = 'default';
let ensembleData = {
    strategies: [],
    weights: {},
    performance: {
        total: 0,
        daily: 0,
        series: []
    },
    signals: [],
    positions: [],
    riskAlerts: [],
    timestamps: []
};

// Time period mapping to days/minutes for API calls
const timeUnitMap = {
    '1m': { unit: 'minute', value: 1 },
    '5m': { unit: 'minute', value: 5 },
    '15m': { unit: 'minute', value: 15 },
    '30m': { unit: 'minute', value: 30 },
    '1h': { unit: 'hour', value: 1 },
    '8h': { unit: 'hour', value: 8 },
    '1d': { unit: 'day', value: 1 },
    '7d': { unit: 'day', value: 7 },
    '1mo': { unit: 'month', value: 1 },
    '3mo': { unit: 'month', value: 3 },
    '6mo': { unit: 'month', value: 6 },
    '1y': { unit: 'year', value: 1 },
    'all': { unit: 'all', value: 0 }
};

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    // Initialize connection status
    updateConnectionStatus('connecting');
    
    // Initialize charts
    initCharts();
    
    // Initialize event listeners
    initEventListeners();
    
    // Connect to websocket
    connectWebSocket();
    
    // Initial data load
    loadDashboardData();
});

// Initialize WebSocket Connection
function connectWebSocket() {
    // Close any existing connection
    if (socket) {
        socket.close();
    }
    
    // Create new WebSocket connection
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    socket = new WebSocket(`${protocol}//${window.location.host}/ws`);
    
    // Connection opened
    socket.addEventListener('open', function (event) {
        updateConnectionStatus('connected');
        console.log('Connected to WebSocket server');
        
        // Subscribe to updates for current ensemble
        socket.send(JSON.stringify({
            action: 'subscribe',
            ensemble: currentEnsemble
        }));
    });
    
    // Listen for messages
    socket.addEventListener('message', function (event) {
        const data = JSON.parse(event.data);
        processWebSocketMessage(data);
    });
    
    // Connection closed
    socket.addEventListener('close', function (event) {
        updateConnectionStatus('disconnected');
        console.log('Disconnected from WebSocket server');
        
        // Try to reconnect after 5 seconds
        setTimeout(connectWebSocket, 5000);
    });
    
    // Connection error
    socket.addEventListener('error', function (event) {
        updateConnectionStatus('error');
        console.error('WebSocket error:', event);
    });
}

// Process WebSocket messages
function processWebSocketMessage(data) {
    // Update last update timestamp
    document.getElementById('last-update').textContent = `Last update: ${new Date().toLocaleTimeString()}`;
    
    // Process different message types
    switch (data.type) {
        case 'performance_update':
            updatePerformanceChart(data.performance);
            updateMetrics(data.metrics);
            break;
        case 'weights_update':
            updateWeightsChart(data.weights);
            break;
        case 'signals_update':
            updateSignalsTable(data.signals);
            break;
        case 'positions_update':
            updatePositionsTable(data.positions);
            break;
        case 'strategy_performance_update':
            updateStrategyTable(data.strategies);
            break;
        case 'correlation_update':
            updateCorrelationChart(data.correlation);
            break;
        case 'risk_alerts_update':
            updateRiskAlerts(data.alerts);
            break;
        case 'regime_update':
            updateRegimeIndicator(data.regime);
            break;
        default:
            console.log('Unknown message type:', data.type);
    }
}

// Initialize charts
function initCharts() {
    // Performance Chart
    const performanceCtx = document.getElementById('performance-chart').getContext('2d');
    performanceChart = new Chart(performanceCtx, {
        type: 'line',
        data: {
            datasets: [{
                label: 'Portfolio',
                borderColor: 'rgb(54, 162, 235)',
                backgroundColor: 'rgba(54, 162, 235, 0.1)',
                borderWidth: 2,
                fill: true,
                data: []
            }, {
                label: 'Benchmark',
                borderColor: 'rgb(128, 128, 128)',
                borderWidth: 1,
                borderDash: [5, 5],
                fill: false,
                data: []
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false
            },
            scales: {
                x: {
                    type: 'time',
                    time: {
                        unit: 'day'
                    },
                    title: {
                        display: true,
                        text: 'Date'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Value ($)'
                    }
                }
            },
            plugins: {
                legend: {
                    position: 'top'
                },
                tooltip: {
                    mode: 'index',
                    intersect: false
                }
            }
        }
    });
    
    // Weights Chart
    const weightsCtx = document.getElementById('weights-chart').getContext('2d');
    weightsChart = new Chart(weightsCtx, {
        type: 'doughnut',
        data: {
            labels: [],
            datasets: [{
                data: [],
                backgroundColor: [
                    'rgba(255, 99, 132, 0.7)',
                    'rgba(54, 162, 235, 0.7)',
                    'rgba(255, 206, 86, 0.7)',
                    'rgba(75, 192, 192, 0.7)',
                    'rgba(153, 102, 255, 0.7)',
                    'rgba(255, 159, 64, 0.7)',
                    'rgba(199, 199, 199, 0.7)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.raw || 0;
                            return `${label}: ${(value * 100).toFixed(1)}%`;
                        }
                    }
                }
            }
        }
    });
    
    // Correlation Chart
    const correlationCtx = document.getElementById('correlation-chart').getContext('2d');
    correlationChart = new Chart(correlationCtx, {
        type: 'heatmap',
        data: {
            labels: [],
            datasets: []
        },
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
                            const value = context.raw || 0;
                            return `Correlation: ${value.toFixed(2)}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    ticks: {
                        autoSkip: false,
                        maxRotation: 90,
                        minRotation: 90
                    }
                },
                y: {
                    ticks: {
                        autoSkip: false
                    }
                }
            }
        }
    });
}

// Initialize event listeners
function initEventListeners() {
    // Time range selector
    const timeRangeSelector = document.getElementById('time-range-selector');
    if (timeRangeSelector) {
        timeRangeSelector.addEventListener('change', function() {
            currentPeriod = this.value;
            loadPerformanceData(currentPeriod);
            
            // Update chart display units based on selected time range
            updateChartTimeUnit(currentPeriod);
        });
    }
    
    // Strategy filter checkboxes
    document.querySelectorAll('.strategy-filter').forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            // Get all selected strategies
            const selectedStrategies = [];
            document.querySelectorAll('.strategy-filter:checked').forEach(cb => {
                selectedStrategies.push(cb.value);
            });
            
            // Update visualizations with filtered strategies
            filterStrategies(selectedStrategies);
        });
    });
    
    // Period selector buttons
    document.querySelectorAll('.period-btn').forEach(button => {
        button.addEventListener('click', function() {
            const period = this.getAttribute('data-period');
            document.querySelectorAll('.period-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            this.classList.add('active');
            currentPeriod = period;
            loadPerformanceData(period);
        });
    });
    
    // Ensemble selector
    document.getElementById('ensemble-select').addEventListener('change', function() {
        currentEnsemble = this.value;
        
        // Update subscription
        if (socket && socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({
                action: 'subscribe',
                ensemble: currentEnsemble
            }));
        }
        
        // Reload dashboard data
        loadDashboardData();
    });
    
    // Risk tab buttons
    document.querySelectorAll('#riskTabs .nav-link').forEach(tab => {
        tab.addEventListener('click', function() {
            document.querySelectorAll('#riskTabs .nav-link').forEach(t => {
                t.classList.remove('active');
            });
            document.querySelectorAll('.tab-pane').forEach(pane => {
                pane.classList.remove('show', 'active');
            });
            
            this.classList.add('active');
            const target = this.getAttribute('data-bs-target');
            document.querySelector(target).classList.add('show', 'active');
        });
    });
}

// Load dashboard data
function loadDashboardData() {
    // Make API requests to load initial data
    loadPerformanceData(currentPeriod);
    loadWeightsData();
    loadSignalsData();
    loadPositionsData();
    loadStrategyPerformanceData();
    loadCorrelationData();
    loadRiskAlertsData();
}

// Load performance data
function loadPerformanceData(period) {
    fetch(`/api/performance?period=${period}&ensemble=${currentEnsemble}`)
        .then(response => response.json())
        .then(data => {
            updatePerformanceChart(data.performance);
            updateMetrics(data.metrics);
        })
        .catch(error => console.error('Error loading performance data:', error));
}

// Load weights data
function loadWeightsData() {
    fetch(`/api/weights?ensemble=${currentEnsemble}`)
        .then(response => response.json())
        .then(data => {
            updateWeightsChart(data.weights);
        })
        .catch(error => console.error('Error loading weights data:', error));
}

// Load signals data
function loadSignalsData() {
    fetch(`/api/signals?ensemble=${currentEnsemble}`)
        .then(response => response.json())
        .then(data => {
            updateSignalsTable(data.signals);
        })
        .catch(error => console.error('Error loading signals data:', error));
}

// Load positions data
function loadPositionsData() {
    fetch(`/api/positions?ensemble=${currentEnsemble}`)
        .then(response => response.json())
        .then(data => {
            updatePositionsTable(data.positions);
        })
        .catch(error => console.error('Error loading positions data:', error));
}

// Load strategy performance data
function loadStrategyPerformanceData() {
    fetch(`/api/strategy_performance?ensemble=${currentEnsemble}`)
        .then(response => response.json())
        .then(data => {
            updateStrategyTable(data.strategies);
        })
        .catch(error => console.error('Error loading strategy performance data:', error));
}

// Load correlation data
function loadCorrelationData() {
    fetch(`/api/correlation?ensemble=${currentEnsemble}`)
        .then(response => response.json())
        .then(data => {
            updateCorrelationChart(data.correlation);
        })
        .catch(error => console.error('Error loading correlation data:', error));
}

// Load risk alerts data
function loadRiskAlertsData() {
    fetch(`/api/risk_alerts?ensemble=${currentEnsemble}`)
        .then(response => response.json())
        .then(data => {
            updateRiskAlerts(data.alerts);
        })
        .catch(error => console.error('Error loading risk alerts data:', error));
}

// Update performance chart
function updatePerformanceChart(performance) {
    if (!performance || !performance.portfolio || !performance.benchmark) {
        return;
    }
    
    // Update chart data
    performanceChart.data.datasets[0].data = performance.portfolio;
    performanceChart.data.datasets[1].data = performance.benchmark;
    
    // Update chart time unit based on period
    updateChartTimeUnit(currentPeriod);
}

// Update metrics
function updateMetrics(metrics) {
    if (!metrics) return;
    
    // Update P&L
    const pnlElement = document.getElementById('current-pnl');
    const pnlChangeElement = document.getElementById('pnl-change');
    if (pnlElement && metrics.pnl) {
        pnlElement.textContent = `$${metrics.pnl.value.toFixed(2)}`;
        pnlChangeElement.textContent = `${metrics.pnl.change >= 0 ? '+' : ''}${metrics.pnl.change.toFixed(2)}% today`;
        
        // Apply color based on value
        pnlElement.classList.remove('positive', 'negative');
        pnlChangeElement.classList.remove('positive', 'negative');
        
        if (metrics.pnl.value > 0) {
            pnlElement.classList.add('positive');
        } else if (metrics.pnl.value < 0) {
            pnlElement.classList.add('negative');
        }
        
        if (metrics.pnl.change > 0) {
            pnlChangeElement.classList.add('positive');
        } else if (metrics.pnl.change < 0) {
            pnlChangeElement.classList.add('negative');
        }
    }
    
    // Update Sharpe Ratio
    const sharpeElement = document.getElementById('sharpe-ratio');
    const sharpeChangeElement = document.getElementById('sharpe-change');
    if (sharpeElement && metrics.sharpe) {
        sharpeElement.textContent = metrics.sharpe.value.toFixed(2);
        sharpeChangeElement.textContent = `${metrics.sharpe.change >= 0 ? '+' : ''}${metrics.sharpe.change.toFixed(2)} vs benchmark`;
        
        // Apply color based on value
        sharpeElement.classList.remove('positive', 'negative');
        sharpeChangeElement.classList.remove('positive', 'negative');
        
        if (metrics.sharpe.value > 1) {
            sharpeElement.classList.add('positive');
        } else if (metrics.sharpe.value < 0) {
            sharpeElement.classList.add('negative');
        }
        
        if (metrics.sharpe.change > 0) {
            sharpeChangeElement.classList.add('positive');
        } else if (metrics.sharpe.change < 0) {
            sharpeChangeElement.classList.add('negative');
        }
    }
    
    // Update Drawdown
    const drawdownElement = document.getElementById('drawdown');
    const drawdownChangeElement = document.getElementById('drawdown-change');
    if (drawdownElement && metrics.drawdown) {
        drawdownElement.textContent = `${metrics.drawdown.value.toFixed(2)}%`;
        drawdownChangeElement.textContent = `${metrics.drawdown.change >= 0 ? '+' : ''}${metrics.drawdown.change.toFixed(2)}% from peak`;
        
        // Apply color based on value (negative is better for drawdown)
        drawdownElement.classList.remove('positive', 'negative');
        
        if (metrics.drawdown.value > 10) {
            drawdownElement.classList.add('negative');
        } else if (metrics.drawdown.value < 5) {
            drawdownElement.classList.add('positive');
        }
    }
    
    // Update Volatility
    const volatilityElement = document.getElementById('volatility');
    const volatilityChangeElement = document.getElementById('volatility-change');
    if (volatilityElement && metrics.volatility) {
        volatilityElement.textContent = `${metrics.volatility.value.toFixed(2)}%`;
        volatilityChangeElement.textContent = `${metrics.volatility.change >= 0 ? '+' : ''}${metrics.volatility.change.toFixed(2)}% vs avg`;
        
        // Apply color based on value (lower volatility is generally better)
        volatilityElement.classList.remove('positive', 'negative');
        
        if (metrics.volatility.change > 20) {
            volatilityElement.classList.add('negative');
        } else if (metrics.volatility.change < 0) {
            volatilityElement.classList.add('positive');
        }
    }
}

// Update weights chart
function updateWeightsChart(weights) {
    if (!weights) return;
    
    const labels = [];
    const data = [];
    
    for (const strategy in weights) {
        labels.push(strategy);
        data.push(weights[strategy]);
    }
    
    weightsChart.data.labels = labels;
    weightsChart.data.datasets[0].data = data;
    weightsChart.update();
    
    // Apply current strategy filter
    const selectedStrategies = [];
    document.querySelectorAll('.strategy-filter:checked').forEach(cb => {
        selectedStrategies.push(cb.value);
    });
    
    if (selectedStrategies.length > 0) {
        filterStrategies(selectedStrategies);
    }
}

// Update signals table
function updateSignalsTable(signals) {
    if (!signals || !signals.length) {
        document.getElementById('signals-table').querySelector('tbody').innerHTML = '<tr><td colspan="5" class="text-center">No signals available</td></tr>';
        return;
    }
    
    const tbody = document.getElementById('signals-table').querySelector('tbody');
    tbody.innerHTML = '';
    
    signals.forEach(signal => {
        const row = document.createElement('tr');
        row.classList.add(signal.signal.toLowerCase() === 'buy' ? 'buy-signal' : 'sell-signal');
        
        row.innerHTML = `
            <td>${signal.symbol}</td>
            <td>${signal.signal}</td>
            <td>${signal.strength}</td>
            <td>${signal.timeframe}</td>
            <td>${signal.price !== undefined ? '$' + signal.price.toFixed(2) : 'N/A'}</td>
        `;
        
        tbody.appendChild(row);
    });
}

// Update positions table
function updatePositionsTable(positions) {
    if (!positions || !positions.length) {
        document.getElementById('positions-table').querySelector('tbody').innerHTML = '<tr><td colspan="5" class="text-center">No open positions</td></tr>';
        return;
    }
    
    const tbody = document.getElementById('positions-table').querySelector('tbody');
    tbody.innerHTML = '';
    
    positions.forEach(position => {
        const pnlValue = position.current - position.entry;
        const pnlPercent = (pnlValue / position.entry) * 100;
        const isProfitable = pnlValue > 0;
        
        const row = document.createElement('tr');
        row.classList.add(isProfitable ? 'profitable' : 'unprofitable');
        
        row.innerHTML = `
            <td>${position.symbol}</td>
            <td>${position.position > 0 ? 'Long' : 'Short'} ${Math.abs(position.position)}</td>
            <td>$${position.entry.toFixed(2)}</td>
            <td>$${position.current.toFixed(2)}</td>
            <td class="${isProfitable ? 'positive' : 'negative'}">
                ${isProfitable ? '+' : ''}$${pnlValue.toFixed(2)} (${isProfitable ? '+' : ''}${pnlPercent.toFixed(2)}%)
            </td>
        `;
        
        tbody.appendChild(row);
    });
}

// Update strategy table
function updateStrategyTable(strategies) {
    if (!strategies || !strategies.length) {
        document.getElementById('strategy-table').querySelector('tbody').innerHTML = '<tr><td colspan="6" class="text-center">No strategy data available</td></tr>';
        return;
    }
    
    const tbody = document.getElementById('strategy-table').querySelector('tbody');
    tbody.innerHTML = '';
    
    strategies.forEach(strategy => {
        const row = document.createElement('tr');
        
        row.innerHTML = `
            <td>${strategy.name}</td>
            <td>${(strategy.weight * 100).toFixed(1)}%</td>
            <td class="${strategy.return > 0 ? 'positive' : strategy.return < 0 ? 'negative' : ''}">
                ${strategy.return > 0 ? '+' : ''}${(strategy.return * 100).toFixed(2)}%
            </td>
            <td class="${strategy.sharpe > 1 ? 'positive' : strategy.sharpe < 0 ? 'negative' : ''}">
                ${strategy.sharpe.toFixed(2)}
            </td>
            <td class="${strategy.drawdown > 15 ? 'negative' : strategy.drawdown < 5 ? 'positive' : ''}">
                ${strategy.drawdown.toFixed(2)}%
            </td>
            <td>${(strategy.winRate * 100).toFixed(1)}%</td>
        `;
        
        tbody.appendChild(row);
    });
    
    // Apply current strategy filter
    const selectedStrategies = [];
    document.querySelectorAll('.strategy-filter:checked').forEach(cb => {
        selectedStrategies.push(cb.value);
    });
    
    if (selectedStrategies.length > 0) {
        filterStrategies(selectedStrategies);
    }
}

// Update correlation chart
function updateCorrelationChart(correlation) {
    if (!correlation || !correlation.matrix || !correlation.labels) return;
    
    // We need to convert the correlation matrix into a format Chart.js can use
    const labels = correlation.labels;
    const datasets = [];
    
    correlation.matrix.forEach((row, idx) => {
        datasets.push({
            label: labels[idx],
            data: row.map((value, i) => ({ x: labels[i], y: labels[idx], v: value })),
            backgroundColor: function(context) {
                const value = context.dataset.data[context.dataIndex].v;
                
                if (value === 1) {
                    return 'rgba(75, 192, 192, 1)'; // Perfect correlation (self)
                } else if (value > 0.5) {
                    return 'rgba(255, 99, 132, 0.8)'; // High positive correlation
                } else if (value > 0) {
                    return 'rgba(255, 99, 132, 0.5)'; // Low positive correlation
                } else if (value > -0.5) {
                    return 'rgba(54, 162, 235, 0.5)'; // Low negative correlation
                } else {
                    return 'rgba(54, 162, 235, 0.8)'; // High negative correlation
                }
            }
        });
    });
    
    correlationChart.data.labels = labels;
    correlationChart.data.datasets = datasets;
    correlationChart.update();
}

// Update risk alerts
function updateRiskAlerts(alerts) {
    const alertsContainer = document.getElementById('risk-alerts');
    const noAlertsElement = document.getElementById('no-alerts');
    
    if (!alerts || !alerts.length) {
        noAlertsElement.style.display = 'block';
        // Remove existing alerts
        const existingAlerts = alertsContainer.querySelectorAll('.alert:not(#no-alerts)');
        existingAlerts.forEach(alert => alert.remove());
        return;
    }
    
    // Hide "no alerts" message
    noAlertsElement.style.display = 'none';
    
    // Remove existing alerts
    const existingAlerts = alertsContainer.querySelectorAll('.alert:not(#no-alerts)');
    existingAlerts.forEach(alert => alert.remove());
    
    // Add new alerts
    alerts.forEach(alert => {
        const alertElement = document.createElement('div');
        alertElement.classList.add('alert');
        alertElement.classList.add(`alert-${alert.severity.toLowerCase()}`);
        
        alertElement.innerHTML = `
            <div class="alert-header">
                <i class="fas ${getSeverityIcon(alert.severity)}"></i>
                <span>${alert.title}</span>
            </div>
            <div class="alert-body">
                ${alert.message}
            </div>
            <div class="alert-footer">
                <small>${new Date(alert.timestamp).toLocaleString()}</small>
            </div>
        `;
        
        alertsContainer.appendChild(alertElement);
    });
}

// Update regime indicator
function updateRegimeIndicator(regime) {
    if (!regime) return;
    
    // TODO: Add regime indicator UI element
    console.log('Current market regime:', regime);
}

// Update connection status
function updateConnectionStatus(status) {
    const statusElement = document.querySelector('.connection-status');
    const statusTextElement = document.getElementById('connection-status-text');
    
    statusElement.classList.remove('connected', 'connecting', 'disconnected', 'error');
    statusElement.classList.add(status);
    
    switch (status) {
        case 'connected':
            statusTextElement.textContent = 'Connected';
            break;
        case 'connecting':
            statusTextElement.textContent = 'Connecting...';
            break;
        case 'disconnected':
            statusTextElement.textContent = 'Disconnected';
            break;
        case 'error':
            statusTextElement.textContent = 'Connection Error';
            break;
    }
}

// Helper function for alert icons
function getSeverityIcon(severity) {
    switch (severity.toLowerCase()) {
        case 'critical':
            return 'fa-skull-crossbones';
        case 'high':
            return 'fa-exclamation-triangle';
        case 'medium':
            return 'fa-exclamation-circle';
        case 'low':
            return 'fa-info-circle';
        default:
            return 'fa-bell';
    }
}

// Add ChartJS heatmap controller
// Since Chart.js doesn't include heatmap by default, we need to add it
Chart.register({
    id: 'heatmap',
    beforeInit(chart) {
        chart.legend.afterFit = function() {
            this.height = this.height + 10;
        };
    },
    beforeUpdate(chart) {
        const chartData = chart.data.datasets[0].data;
        const xScale = chart.scales.x;
        const yScale = chart.scales.y;
        
        // set data to dummy data
        chart.data.datasets.forEach(dataset => {
            dataset._meta = chartData.map(data => {
                return {
                    x: xScale.getPixelForValue(data.x),
                    y: yScale.getPixelForValue(data.y),
                    v: data.v
                };
            });
        });
    },
    afterDraw(chart) {
        const ctx = chart.ctx;
        
        chart.data.datasets.forEach(dataset => {
            (dataset._meta || []).forEach(meta => {
                const w = chart.scales.x.getPixelForValue(meta.x) - chart.scales.x.getPixelForValue(0);
                const h = chart.scales.y.getPixelForValue(0) - chart.scales.y.getPixelForValue(meta.y);
                
                ctx.save();
                ctx.fillStyle = typeof dataset.backgroundColor === 'function' 
                    ? dataset.backgroundColor({ dataset, dataIndex: dataset._meta.indexOf(meta) }) 
                    : dataset.backgroundColor;
                ctx.fillRect(meta.x - w/2, meta.y - h/2, w, h);
                
                if (meta.v !== undefined && dataset.showValue) {
                    ctx.fillStyle = 'white';
                    ctx.font = '10px Arial';
                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'middle';
                    ctx.fillText(meta.v.toFixed(2), meta.x, meta.y);
                }
                ctx.restore();
            });
        });
    }
});

// Update chart time unit based on selected period
function updateChartTimeUnit(period) {
    if (!performanceChart) return;
    
    let timeUnit = 'day';
    
    if (period === '1m' || period === '5m' || period === '15m' || period === '30m') {
        timeUnit = 'minute';
    } else if (period === '1h' || period === '8h') {
        timeUnit = 'hour';
    } else if (period === '1d' || period === '7d') {
        timeUnit = 'day';
    } else if (period === '1mo' || period === '3mo' || period === '6mo' || period === '1y' || period === 'all') {
        timeUnit = 'month';
    }
    
    performanceChart.options.scales.x.time.unit = timeUnit;
    performanceChart.update();
}

// Filter strategies based on user selection
function filterStrategies(selectedStrategies) {
    // Get current data
    const currentWeights = weightsChart ? weightsChart.data : null;
    const strategyTable = document.querySelector('#strategy-table tbody');
    
    if (currentWeights && currentWeights.labels) {
        // Filter weights chart data
        const filteredIndices = [];
        const filteredLabels = [];
        const filteredData = [];
        
        // Find indices of selected strategies
        currentWeights.labels.forEach((label, index) => {
            if (selectedStrategies.includes(label)) {
                filteredIndices.push(index);
                filteredLabels.push(label);
                filteredData.push(currentWeights.datasets[0].data[index]);
            }
        });
        
        // Update chart with filtered data
        weightsChart.data.labels = filteredLabels;
        weightsChart.data.datasets[0].data = filteredData;
        weightsChart.update();
    }
    
    // Filter strategy table rows
    if (strategyTable) {
        const rows = strategyTable.querySelectorAll('tr');
        rows.forEach(row => {
            const strategyName = row.querySelector('td:first-child').textContent;
            if (selectedStrategies.includes(strategyName)) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    }
    
    // Update strategy weight bars if they exist
    const strategyWeights = document.getElementById('strategy-weights');
    if (strategyWeights) {
        const bars = strategyWeights.querySelectorAll('.strategy-bar');
        bars.forEach(bar => {
            const strategyName = bar.textContent.split(':')[0].trim();
            if (selectedStrategies.includes(strategyName)) {
                bar.style.display = '';
            } else {
                bar.style.display = 'none';
            }
        });
    }
} 