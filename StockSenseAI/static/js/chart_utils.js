/**
 * Utility functions for chart creation and manipulation
 */

// Format large numbers for readability
function formatNumber(num) {
    if (num >= 1000000000) {
        return (num / 1000000000).toFixed(1) + 'B';
    }
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    }
    if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num.toFixed(0);
}

// Format currency value based on locale
function formatCurrency(value, currency = 'INR') {
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: currency,
        minimumFractionDigits: 2
    }).format(value);
}

// Create a donut chart
function createDonutChart(ctx, labels, data, colors) {
    return new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: colors,
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        usePointStyle: true,
                        font: {
                            size: 12
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.label}: ${formatCurrency(context.raw)}`;
                        }
                    }
                }
            },
            cutout: '75%'
        }
    });
}

// Create a line chart for price history
function createPriceChart(ctx, dates, prices, label = 'Price') {
    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: [{
                label: label,
                data: prices,
                borderColor: '#0d6efd',
                backgroundColor: 'rgba(13, 110, 253, 0.1)',
                borderWidth: 2,
                tension: 0.1,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            if (context.parsed.y !== null) {
                                label += '₹' + context.parsed.y.toFixed(2);
                            }
                            return label;
                        }
                    }
                },
                legend: {
                    display: false
                }
            },
            scales: {
                x: {
                    grid: {
                        display: false
                    }
                },
                y: {
                    beginAtZero: false,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                }
            }
        }
    });
}

// Create a bar chart for volume
function createVolumeChart(ctx, dates, volumes) {
    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: dates,
            datasets: [{
                label: 'Volume',
                data: volumes,
                backgroundColor: 'rgba(75, 192, 192, 0.5)',
                borderColor: 'rgba(75, 192, 192, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return 'Volume: ' + formatNumber(context.raw);
                        }
                    }
                },
                legend: {
                    display: false
                }
            },
            scales: {
                x: {
                    grid: {
                        display: false
                    }
                },
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    },
                    ticks: {
                        callback: function(value) {
                            return formatNumber(value);
                        }
                    }
                }
            }
        }
    });
}

// Create a candlestick chart using Chart.js
function createCandlestickChart(ctx, data) {
    // Extract data points
    const dates = data.map(item => item.date);
    const opens = data.map(item => item.open);
    const highs = data.map(item => item.high);
    const lows = data.map(item => item.low);
    const closes = data.map(item => item.close);

    // Calculate candle colors (green for bullish, red for bearish)
    const colors = closes.map((close, i) => close >= opens[i] ? 'rgba(0, 128, 0, 0.5)' : 'rgba(255, 0, 0, 0.5)');
    const borderColors = closes.map((close, i) => close >= opens[i] ? 'rgb(0, 128, 0)' : 'rgb(255, 0, 0)');

    // Create the chart
    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: dates,
            datasets: [
                // Candle wicks (high-low)
                {
                    label: 'High-Low',
                    data: data.map((item, i) => ({
                        x: i,
                        y: [item.low, item.high]
                    })),
                    type: 'line',
                    borderWidth: 1,
                    borderColor: borderColors,
                    pointRadius: 0
                },
                // Candle bodies (open-close)
                {
                    label: 'Open-Close',
                    data: closes.map((close, i) => Math.abs(close - opens[i])),
                    backgroundColor: colors,
                    borderColor: borderColors,
                    borderWidth: 1,
                    barPercentage: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    callbacks: {
                        label: function(context) {
                            const index = context.dataIndex;
                            return [
                                `Open: ₹${opens[index].toFixed(2)}`,
                                `High: ₹${highs[index].toFixed(2)}`,
                                `Low: ₹${lows[index].toFixed(2)}`,
                                `Close: ₹${closes[index].toFixed(2)}`
                            ];
                        }
                    }
                },
                legend: {
                    display: false
                }
            },
            scales: {
                x: {
                    grid: {
                        display: false
                    }
                },
                y: {
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                }
            }
        }
    });
}

// Create a chart showing price prediction
function createPredictionChart(ctx, historyData, predictionData, symbol) {
    const historyLabels = historyData.map(item => item.date);
    const historyPrices = historyData.map(item => item.close);
    const sma50 = historyData.map(item => item.sma_50);
    const sma200 = historyData.map(item => item.sma_200);
    const pivotPoints = historyData.map(item => item.pp);
    
    const predictionLabels = predictionData.map(item => item.date);
    const predictionPrices = predictionData.map(item => item.price);
    
    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: [...historyLabels, ...predictionLabels],
            datasets: [
                {
                    label: 'Closing Price',
                    data: [...historyPrices, ...Array(predictionPrices.length).fill(null)],
                    borderColor: '#0d6efd',
                    backgroundColor: 'rgba(13, 110, 253, 0.1)',
                    borderWidth: 2,
                    tension: 0.1,
                    fill: true
                },
                {
                    label: 'Pivot Points',
                    data: [...pivotPoints, ...Array(predictionPrices.length).fill(null)],
                    borderColor: '#20c997',
                    borderWidth: 1,
                    borderDash: [5, 5],
                    tension: 0
                },
                {
                    label: '50-day SMA',
                    data: [...sma50, ...Array(predictionPrices.length).fill(null)],
                    borderColor: '#fd7e14',
                    borderWidth: 1,
                    borderDash: [5, 5],
                    tension: 0
                },
                {
                    label: '200-day SMA',
                    data: [...sma200, ...Array(predictionPrices.length).fill(null)],
                    borderColor: '#6f42c1',
                    borderWidth: 1,
                    borderDash: [5, 5],
                    tension: 0
                },
                {
                    label: 'AI Prediction',
                    data: [...Array(historyPrices.length).fill(null), ...predictionPrices],
                    borderColor: '#dc3545',
                    borderWidth: 2,
                    tension: 0.1,
                    pointBackgroundColor: '#dc3545',
                    pointRadius: 4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            if (context.parsed.y !== null) {
                                label += '₹' + context.parsed.y.toFixed(2);
                            }
                            return label;
                        }
                    }
                },
                annotation: {
                    annotations: {
                        predictionLine: {
                            type: 'line',
                            yMin: historyPrices[historyPrices.length - 1],
                            yMax: historyPrices[historyPrices.length - 1],
                            borderColor: 'rgb(75, 192, 192)',
                            borderWidth: 2,
                            borderDash: [6, 6],
                            label: {
                                content: 'Prediction Start',
                                enabled: true,
                                position: 'start'
                            }
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        display: false
                    }
                },
                y: {
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                }
            }
        }
    });
}
