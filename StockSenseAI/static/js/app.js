document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Theme switching
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        themeToggle.addEventListener('change', function() {
            if (this.checked) {
                document.documentElement.setAttribute('data-bs-theme', 'dark');
                localStorage.setItem('theme', 'dark');
            } else {
                document.documentElement.setAttribute('data-bs-theme', 'light');
                localStorage.setItem('theme', 'light');
            }
        });

        // Set initial theme based on localStorage or system preference
        const savedTheme = localStorage.getItem('theme') || 
            (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
        
        if (savedTheme === 'dark') {
            themeToggle.checked = true;
            document.documentElement.setAttribute('data-bs-theme', 'dark');
        } else {
            themeToggle.checked = false;
            document.documentElement.setAttribute('data-bs-theme', 'light');
        }
    }

    // Stock search functionality
    const stockSearch = document.getElementById('stockSearch');
    const searchResults = document.getElementById('searchResults');
    
    if (stockSearch && searchResults) {
        let searchDebounceTimer;

        stockSearch.addEventListener('input', handleStockSearch);
        stockSearch.addEventListener('focus', handleStockSearch);
        stockSearch.addEventListener('blur', function() {
            setTimeout(() => searchResults.style.display = 'none', 200);
        });

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
                searchResults.innerHTML = '<div class="search-item p-2 border-bottom">No results found</div>';
                searchResults.style.display = 'block';
                return;
            }
            
            searchResults.innerHTML = stocks.map(stock => `
                <div class="search-item p-2 border-bottom" 
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
            // If we're on the prediction page, set the selected stock
            const stockSelect = document.getElementById('stockSelect');
            const selectedStock = document.getElementById('selectedStock');
            
            if (stockSelect && selectedStock) {
                stockSelect.value = ticker;
                selectedStock.innerHTML = `
                    <strong>${name}</strong> 
                    <small class="text-muted">${ticker.replace('.NS', '')}</small>
                `;
            }
            
            // Redirect to prediction page if we're not already on it
            if (!window.location.pathname.includes('/prediction')) {
                window.location.href = `/prediction?symbol=${ticker}&name=${encodeURIComponent(name)}`;
            }
            
            stockSearch.value = '';
            searchResults.style.display = 'none';
        }
    }

    // Error toast functionality
    window.showError = function(message) {
        const errorToastBody = document.getElementById('errorToastBody');
        const errorToast = document.getElementById('errorToast');
        
        if (errorToastBody && errorToast) {
            errorToastBody.textContent = message;
            const toast = new bootstrap.Toast(errorToast);
            toast.show();
        } else {
            alert(message);
        }
    };

    // Success toast functionality
    window.showSuccess = function(message) {
        const successToastBody = document.getElementById('successToastBody');
        const successToast = document.getElementById('successToast');
        
        if (successToastBody && successToast) {
            successToastBody.textContent = message;
            const toast = new bootstrap.Toast(successToast);
            toast.show();
        } else {
            alert(message);
        }
    };

    // Add to watchlist functionality
    const addToWatchlistBtn = document.getElementById('addToWatchlistBtn');
    if (addToWatchlistBtn) {
        addToWatchlistBtn.addEventListener('click', async function() {
            const stockSelect = document.getElementById('stockSelect');
            if (!stockSelect || !stockSelect.value) {
                showError('Please select a stock first');
                return;
            }

            try {
                const response = await fetch('/api/watchlist/add', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        symbol: stockSelect.value
                    })
                });

                const data = await response.json();
                
                if (response.ok) {
                    showSuccess(data.message);
                    addToWatchlistBtn.disabled = true;
                    addToWatchlistBtn.textContent = 'Added to Watchlist';
                } else {
                    showError(data.message);
                }
            } catch (error) {
                console.error('Error adding to watchlist:', error);
                showError('Failed to add to watchlist. Please try again.');
            }
        });
    }

    // Remove from watchlist functionality
    document.querySelectorAll('.remove-from-watchlist').forEach(button => {
        button.addEventListener('click', async function(e) {
            e.preventDefault();
            const symbol = this.getAttribute('data-symbol');
            
            try {
                const response = await fetch('/api/watchlist/remove', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        symbol: symbol
                    })
                });

                const data = await response.json();
                
                if (response.ok) {
                    const item = this.closest('.watchlist-item');
                    if (item) {
                        item.remove();
                    }
                    showSuccess(data.message);
                } else {
                    showError(data.message);
                }
            } catch (error) {
                console.error('Error removing from watchlist:', error);
                showError('Failed to remove from watchlist. Please try again.');
            }
        });
    });

    // Connect brokerage functionality
    const connectBrokerageForm = document.getElementById('connectBrokerageForm');
    if (connectBrokerageForm) {
        connectBrokerageForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const brokerage = document.getElementById('brokerage').value;
            const clientId = document.getElementById('clientId').value;
            const apiKey = document.getElementById('apiKey').value;
            const apiSecret = document.getElementById('apiSecret').value;
            
            try {
                const response = await fetch('/api/portfolio/connect', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        brokerage: brokerage,
                        credentials: {
                            client_id: clientId,
                            api_key: apiKey,
                            api_secret: apiSecret
                        }
                    })
                });

                const data = await response.json();
                
                if (response.ok) {
                    showSuccess(data.message);
                    // Hide modal
                    const modal = bootstrap.Modal.getInstance(document.getElementById('connectBrokerageModal'));
                    modal.hide();
                    // Reload page to show new connection
                    window.location.reload();
                } else {
                    showError(data.message);
                }
            } catch (error) {
                console.error('Error connecting brokerage:', error);
                showError('Failed to connect brokerage. Please try again.');
            }
        });
    }

    // Sync portfolio functionality
    document.querySelectorAll('.sync-portfolio-btn').forEach(button => {
        button.addEventListener('click', async function() {
            const brokerageId = this.getAttribute('data-brokerage-id');
            
            try {
                const response = await fetch('/api/portfolio/sync', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        brokerage_id: brokerageId
                    })
                });

                const data = await response.json();
                
                if (response.ok) {
                    showSuccess(data.message);
                    // Reload page to show updated portfolio
                    window.location.reload();
                } else {
                    showError(data.message);
                }
            } catch (error) {
                console.error('Error syncing portfolio:', error);
                showError('Failed to sync portfolio. Please try again.');
            }
        });
    });
});
