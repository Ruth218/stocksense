document.addEventListener('DOMContentLoaded', function() {
    // AI Advisor recommendation handling
    document.querySelectorAll('.recommendation-card').forEach(card => {
        card.addEventListener('click', function() {
            const symbol = this.getAttribute('data-symbol');
            const type = this.getAttribute('data-type');
            
            // Only redirect if it's a recommendation for a specific stock
            if (symbol && symbol !== 'PORTFOLIO' && symbol !== 'SECTOR' && symbol !== 'TRENDING' 
                && type !== 'market_alert' && type !== 'portfolio_alert' && type !== 'diversification_alert') {
                window.location.href = `/prediction?symbol=${symbol}`;
            }
        });
    });

    // Risk profile analysis chart
    const riskProfileEl = document.getElementById('riskProfileChart');
    if (riskProfileEl) {
        const ctx = riskProfileEl.getContext('2d');
        new Chart(ctx, {
            type: 'radar',
            data: {
                labels: ['Volatility', 'Diversification', 'Sector Exposure', 'Market Cap', 'Time Horizon'],
                datasets: [{
                    label: 'Your Portfolio',
                    data: [65, 70, 55, 80, 60],
                    backgroundColor: 'rgba(54, 162, 235, 0.2)',
                    borderColor: 'rgb(54, 162, 235)',
                    pointBackgroundColor: 'rgb(54, 162, 235)',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: 'rgb(54, 162, 235)'
                }, {
                    label: 'Ideal Profile',
                    data: [70, 85, 75, 70, 75],
                    backgroundColor: 'rgba(255, 99, 132, 0.2)',
                    borderColor: 'rgb(255, 99, 132)',
                    pointBackgroundColor: 'rgb(255, 99, 132)',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: 'rgb(255, 99, 132)'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    r: {
                        angleLines: {
                            display: true
                        },
                        suggestedMin: 0,
                        suggestedMax: 100
                    }
                }
            }
        });
    }

    // Portfolio allocation recommendation chart
    const allocationChartEl = document.getElementById('allocationChart');
    if (allocationChartEl) {
        const currentAllocation = {
            labels: ['Large Cap', 'Mid Cap', 'Small Cap', 'Debt', 'International', 'Others'],
            data: [45, 25, 15, 10, 3, 2],
            colors: ['#0d6efd', '#6610f2', '#6f42c1', '#d63384', '#dc3545', '#fd7e14']
        };

        const recommendedAllocation = {
            labels: ['Large Cap', 'Mid Cap', 'Small Cap', 'Debt', 'International', 'Others'],
            data: [40, 20, 10, 20, 8, 2],
            colors: ['#0d6efd', '#6610f2', '#6f42c1', '#d63384', '#dc3545', '#fd7e14']
        };

        createAllocationComparisonChart(allocationChartEl, currentAllocation, recommendedAllocation);
    }

    // Prediction accuracy chart
    const accuracyChartEl = document.getElementById('accuracyChart');
    if (accuracyChartEl) {
        const predictionDates = JSON.parse(accuracyChartEl.getAttribute('data-dates') || '[]');
        const accuracies = JSON.parse(accuracyChartEl.getAttribute('data-accuracies') || '[]');

        if (predictionDates.length > 0) {
            createPredictionAccuracyChart(accuracyChartEl, predictionDates, accuracies);
        } else {
            // Display empty state
            accuracyChartEl.parentElement.innerHTML = `
                <div class="text-center py-5">
                    <i class="bi bi-graph-up fs-1 text-muted"></i>
                    <p class="mt-3">No prediction history available</p>
                </div>
            `;
        }
    }
});

// Create a chart comparing current and recommended allocations
function createAllocationComparisonChart(element, currentAllocation, recommendedAllocation) {
    const ctx = element.getContext('2d');
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: currentAllocation.labels,
            datasets: [
                {
                    label: 'Current Allocation',
                    data: currentAllocation.data,
                    backgroundColor: currentAllocation.colors,
                    barPercentage: 0.4,
                    categoryPercentage: 0.5
                },
                {
                    label: 'Recommended Allocation',
                    data: recommendedAllocation.data,
                    backgroundColor: recommendedAllocation.colors.map(color => {
                        // Add transparency to recommended colors
                        return color + '80';
                    }),
                    barPercentage: 0.4,
                    categoryPercentage: 0.5
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': ' + context.raw + '%';
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Allocation Percentage'
                    },
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

// Create a chart showing prediction accuracy over time
function createPredictionAccuracyChart(element, dates, accuracies) {
    const ctx = element.getContext('2d');
    
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: [{
                label: 'Prediction Accuracy',
                data: accuracies,
                borderColor: '#198754',
                backgroundColor: 'rgba(25, 135, 84, 0.1)',
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return 'Accuracy: ' + context.raw + '%';
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    title: {
                        display: true,
                        text: 'Accuracy Percentage'
                    },
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
