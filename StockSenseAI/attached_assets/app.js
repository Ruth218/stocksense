document.addEventListener('DOMContentLoaded', function() {
    const stockSearch = document.getElementById('stockSearch');
    const searchResults = document.getElementById('searchResults');
    const selectedStock = document.getElementById('selectedStock');
    const stockSelect = document.getElementById('stockSelect');
    const daysInput = document.getElementById('daysInput');
    const predictBtn = document.getElementById('predictBtn');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const resultSection = document.getElementById('resultSection');
    let stockChart = null;
    let searchDebounceTimer;

    async function init() {
        stockSearch.addEventListener('input', handleStockSearch);
        stockSearch.addEventListener('focus', handleStockSearch);
        stockSearch.addEventListener('blur', function() {
            setTimeout(() => searchResults.style.display = 'none', 200);
        });
        predictBtn.addEventListener('click', predictStock);
    }

    async function handleStockSearch() {
        clearTimeout(searchDebounceTimer);
        const query = stockSearch.value.trim();
        
        if (query.length < 2) {
            searchResults.style.display = 'none';
            return;
        }
        
        searchDebounceTimer = setTimeout(async () => {
            try {
                const response = await fetch(`/search_stocks?query=${encodeURIComponent(query)}`);
                if (!response.ok) throw new Error('Search failed');
                const stocks = await response.json();
                displaySearchResults(stocks);
            } catch (error) {
                console.error('Search error:', error);
                showError('Failed to search stocks. Please try again.');
            }
        }, 300);
    }

    function displaySearchResults(stocks) {
        if (!stocks || stocks.length === 0) {
            searchResults.innerHTML = '<div class="search-item">No results found</div>';
            searchResults.style.display = 'block';
            return;
        }
        
        searchResults.innerHTML = stocks.map(stock => `
            <div class="search-item" 
                 data-ticker="${stock.ticker}" 
                 data-name="${stock.name}">
                ${stock.name} 
                <small class="text-muted">${stock.ticker.replace('.NS', '')}</small>
            </div>
        `).join('');
        
        document.querySelectorAll('.search-item').forEach(item => {
            item.addEventListener('click', function() {
                const ticker = this.getAttribute('data-ticker');
                const name = this.getAttribute('data-name');
                selectStock(ticker, name);
            });
        });
        
        searchResults.style.display = 'block';
    }

    function selectStock(ticker, name) {
        stockSelect.value = ticker;
        selectedStock.innerHTML = `
            <strong>${name}</strong> 
            <small class="text-muted">${ticker.replace('.NS', '')}</small>
        `;
        stockSearch.value = '';
        searchResults.style.display = 'none';
    }

    async function predictStock() {
        const symbol = stockSelect.value;
        const days = parseInt(daysInput.value);
        
        if (!symbol) {
            showError('Please select a stock');
            return;
        }
        
        if (isNaN(days) || days < 1 || days > 30) {
            showError('Please enter a valid number of days (1-30)');
            return;
        }
        
        loadingIndicator.style.display = 'block';
        resultSection.style.display = 'none';
        
        try {
            const response = await fetch('/predict', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    symbol: symbol,
                    days: days
                })
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'Failed to get prediction');
            }
            
            updateResultsUI(data, symbol, days);
            
        } catch (error) {
            console.error('Prediction error:', error);
            showError(error.message || 'Failed to get prediction. Please try another stock.');
        } finally {
            loadingIndicator.style.display = 'none';
            resultSection.style.display = 'block';
        }
    }

    function updateResultsUI(data, symbol, days) {
        document.getElementById('stockTitle').textContent = 
            `${selectedStock.textContent.trim()} Price Prediction`;
        
        const accuracyBadge = document.getElementById('accuracyBadge');
        accuracyBadge.textContent = `Accuracy: ${data.accuracy.toFixed(1)}%`;
        accuracyBadge.className = `badge accuracy-badge ${
            data.accuracy > 80 ? 'bg-success' : data.accuracy > 65 ? 'bg-warning' : 'bg-danger'
        }`;
        
        document.getElementById('modelAccuracy').textContent = `${data.accuracy.toFixed(1)}%`;
        document.getElementById('modelLoss').textContent = data.model_loss.toFixed(5);
        document.getElementById('directionalAccuracy').textContent = `${data.directional_accuracy.toFixed(1)}%`;
        
        const lastClose = data.last_close;
        document.getElementById('currentPrice').textContent = `₹${lastClose.toFixed(2)}`;
        
        const lastPrediction = data.predictions[data.predictions.length - 1].price;
        document.getElementById('predictedPrice').textContent = `₹${lastPrediction.toFixed(2)}`;
        
        const changePercent = ((lastPrediction - lastClose) / lastClose * 100);
        const changeElement = document.getElementById('predictedChange');
        changeElement.textContent = `${changePercent.toFixed(2)}%`;
        changeElement.className = changePercent >= 0 ? 'positive' : 'negative';
        
        document.getElementById('predictionDays').textContent = days;
        
        const lastHistory = data.history[data.history.length - 1];
        document.getElementById('rsiValue').textContent = lastHistory.rsi.toFixed(2);
        document.getElementById('sma50Value').textContent = `₹${lastHistory.sma_50.toFixed(2)}`;
        document.getElementById('sma200Value').textContent = `₹${lastHistory.sma_200.toFixed(2)}`;
        
        const rsiElement = document.getElementById('rsiValue');
        if (lastHistory.rsi > 70) {
            rsiElement.className = 'indicator-value text-danger';
        } else if (lastHistory.rsi < 30) {
            rsiElement.className = 'indicator-value text-success';
        } else {
            rsiElement.className = 'indicator-value';
        }
        
        // Update pivot points
        document.getElementById('pivotPointValue').textContent = `₹${data.pivot_points.pp.toFixed(2)}`;
        document.getElementById('support1Value').textContent = `₹${data.pivot_points.s1.toFixed(2)}`;
        document.getElementById('support2Value').textContent = `₹${data.pivot_points.s2.toFixed(2)}`;
        document.getElementById('resistance1Value').textContent = `₹${data.pivot_points.r1.toFixed(2)}`;
        document.getElementById('resistance2Value').textContent = `₹${data.pivot_points.r2.toFixed(2)}`;
        
        const dailyPredictionsContainer = document.getElementById('dailyPredictions');
        dailyPredictionsContainer.innerHTML = '';
        
        data.predictions.forEach(pred => {
            const date = new Date(pred.date);
            const dayElement = document.createElement('div');
            dayElement.className = 'list-group-item';
            dayElement.innerHTML = `
                <div class="d-flex justify-content-between">
                    <span>${date.toLocaleDateString()}</span>
                    <strong>₹${pred.price.toFixed(2)}</strong>
                </div>
            `;
            dailyPredictionsContainer.appendChild(dayElement);
        });
        
        updateChart(data.history, data.predictions, symbol);
    }

    function updateChart(historyData, predictionData, symbol) {
        const ctx = document.getElementById('stockChart').getContext('2d');
        
        const historyLabels = historyData.map(item => item.date);
        const historyPrices = historyData.map(item => item.close);
        const sma50 = historyData.map(item => item.sma_50);
        const sma200 = historyData.map(item => item.sma_200);
        const pivotPoints = historyData.map(item => item.pp);
        
        const predictionLabels = predictionData.map(item => item.date);
        const predictionPrices = predictionData.map(item => item.price);
        
        if (stockChart) {
            stockChart.destroy();
        }
        
        stockChart = new Chart(ctx, {
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
                                    position: 'right'
                                }
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        ticks: {
                            callback: function(value) {
                                return '₹' + value.toFixed(2);
                            }
                        },
                        title: {
                            display: true,
                            text: 'Price (₹)'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Date'
                        }
                    }
                },
                interaction: {
                    mode: 'nearest',
                    axis: 'x',
                    intersect: false
                }
            }
        });
    }

    function showError(message) {
        const errorToast = new bootstrap.Toast(document.getElementById('errorToast'));
        document.getElementById('errorToastBody').textContent = message;
        errorToast.show();
    }

    init();
});