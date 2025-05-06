document.addEventListener('DOMContentLoaded', function() {
    // Portfolio overview chart
    const portfolioChartEl = document.getElementById('portfolioChart');
    if (portfolioChartEl) {
        const portfolioLabels = JSON.parse(portfolioChartEl.getAttribute('data-labels') || '[]');
        const portfolioValues = JSON.parse(portfolioChartEl.getAttribute('data-values') || '[]');
        const portfolioColors = [
            '#0d6efd', '#6610f2', '#6f42c1', '#d63384', '#dc3545', 
            '#fd7e14', '#ffc107', '#198754', '#20c997', '#0dcaf0'
        ];

        if (portfolioLabels.length > 0) {
            createDonutChart(
                portfolioChartEl.getContext('2d'),
                portfolioLabels,
                portfolioValues,
                portfolioColors.slice(0, portfolioLabels.length)
            );
        } else {
            // Display empty state
            portfolioChartEl.parentElement.innerHTML = `
                <div class="text-center py-5">
                    <i class="bi bi-bar-chart-line fs-1 text-muted"></i>
                    <p class="mt-3">No portfolio data available</p>
                </div>
            `;
        }
    }

    // Portfolio performance chart
    const performanceChartEl = document.getElementById('performanceChart');
    if (performanceChartEl) {
        const performanceDates = JSON.parse(performanceChartEl.getAttribute('data-dates') || '[]');
        const performanceValues = JSON.parse(performanceChartEl.getAttribute('data-values') || '[]');

        if (performanceDates.length > 0) {
            createPriceChart(
                performanceChartEl.getContext('2d'),
                performanceDates,
                performanceValues,
                'Portfolio Value'
            );
        } else {
            // Display empty state
            performanceChartEl.parentElement.innerHTML = `
                <div class="text-center py-5">
                    <i class="bi bi-graph-up-arrow fs-1 text-muted"></i>
                    <p class="mt-3">No performance data available</p>
                </div>
            `;
        }
    }

    // Connect brokerage buttons
    const connectBtns = document.querySelectorAll('.connect-brokerage-btn');
    if (connectBtns.length > 0) {
        connectBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                const brokerage = this.getAttribute('data-brokerage');
                const brokerageNameEl = document.getElementById('brokerageName');
                const brokerageSelect = document.getElementById('brokerage');
                
                if (brokerageNameEl) {
                    brokerageNameEl.textContent = brokerage.charAt(0).toUpperCase() + brokerage.slice(1);
                }
                
                if (brokerageSelect) {
                    brokerageSelect.value = brokerage;
                }
                
                // Show the modal
                const modal = new bootstrap.Modal(document.getElementById('connectBrokerageModal'));
                modal.show();
            });
        });
    }

    // Add holding form handling
    const addHoldingForm = document.getElementById('addHoldingForm');
    if (addHoldingForm) {
        addHoldingForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const portfolioId = document.getElementById('portfolioId').value;
            const symbol = document.getElementById('symbol').value;
            const quantity = document.getElementById('quantity').value;
            const averagePrice = document.getElementById('averagePrice').value;
            
            try {
                const response = await fetch('/api/portfolio/add_holding', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        portfolio_id: portfolioId,
                        symbol: symbol,
                        quantity: parseFloat(quantity),
                        average_price: parseFloat(averagePrice)
                    })
                });

                const data = await response.json();
                
                if (response.ok) {
                    showSuccess(data.message || 'Holding added successfully');
                    // Hide modal
                    const modal = bootstrap.Modal.getInstance(document.getElementById('addHoldingModal'));
                    modal.hide();
                    // Reload page to show new holding
                    window.location.reload();
                } else {
                    showError(data.message || 'Failed to add holding');
                }
            } catch (error) {
                console.error('Error adding holding:', error);
                showError('Failed to add holding. Please try again.');
            }
        });
    }

    // Delete holding buttons
    document.querySelectorAll('.delete-holding-btn').forEach(button => {
        button.addEventListener('click', async function() {
            if (!confirm('Are you sure you want to delete this holding?')) {
                return;
            }
            
            const holdingId = this.getAttribute('data-holding-id');
            const portfolioId = this.getAttribute('data-portfolio-id');
            
            try {
                const response = await fetch('/api/portfolio/delete_holding', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        holding_id: holdingId,
                        portfolio_id: portfolioId
                    })
                });

                const data = await response.json();
                
                if (response.ok) {
                    showSuccess(data.message || 'Holding deleted successfully');
                    // Remove holding from the DOM
                    this.closest('tr').remove();
                } else {
                    showError(data.message || 'Failed to delete holding');
                }
            } catch (error) {
                console.error('Error deleting holding:', error);
                showError('Failed to delete holding. Please try again.');
            }
        });
    });

    // Refresh all portfolios button
    const refreshAllBtn = document.getElementById('refreshAllPortfolios');
    if (refreshAllBtn) {
        refreshAllBtn.addEventListener('click', async function() {
            const brokerageAccounts = document.querySelectorAll('.brokerage-account');
            if (brokerageAccounts.length === 0) {
                showError('No brokerage accounts connected');
                return;
            }
            
            this.disabled = true;
            this.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Refreshing...';
            
            let successCount = 0;
            
            for (const account of brokerageAccounts) {
                const brokerageId = account.getAttribute('data-brokerage-id');
                
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

                    if (response.ok) {
                        successCount++;
                    }
                } catch (error) {
                    console.error(`Error syncing portfolio for brokerage ${brokerageId}:`, error);
                }
            }
            
            this.disabled = false;
            this.innerHTML = '<i class="bi bi-arrow-repeat"></i> Refresh All Portfolios';
            
            if (successCount > 0) {
                showSuccess(`Successfully refreshed ${successCount} out of ${brokerageAccounts.length} portfolios`);
                // Reload page to show updated portfolios
                window.location.reload();
            } else {
                showError('Failed to refresh any portfolios. Please try again.');
            }
        });
    }
});
