// FlipHawk Connector Script
// This script ensures that scraping happens when the user clicks "scan"

(function() {
    // Check if the main script is loaded
    if (typeof startScan !== 'function') {
        // Main script not loaded, set up a basic scanner
        console.log('Main script not loaded, initializing connector...');
        
        document.addEventListener('DOMContentLoaded', function() {
            const searchButton = document.getElementById('search-button');
            
            if (searchButton) {
                searchButton.addEventListener('click', function() {
                    if (this.classList.contains('loading')) {
                        return; // Already scanning
                    }
                    
                    // Get selected subcategories
                    const selectedSubcategories = Array.from(document.querySelectorAll('.subcategory-chip.selected'))
                        .map(chip => chip.textContent);
                    
                    if (selectedSubcategories.length === 0) {
                        alert('Please select at least one subcategory');
                        return;
                    }
                    
                    // Get selected category
                    const selectedCategoryElem = document.querySelector('.category-card.active');
                    const selectedCategory = selectedCategoryElem ? selectedCategoryElem.dataset.category : '';
                    
                    if (!selectedCategory) {
                        alert('Please select a category');
                        return;
                    }
                    
                    // Show loading state
                    this.textContent = 'Scanning...';
                    this.classList.add('loading');
                    
                    // Show loading indicators
                    const loadingSpinner = document.getElementById('loading-spinner');
                    const progressContainer = document.getElementById('progress-container');
                    const scanStatus = document.getElementById('scan-status');
                    const progressBar = document.getElementById('progress-bar');
                    
                    if (loadingSpinner) loadingSpinner.style.display = 'block';
                    if (progressContainer) progressContainer.style.display = 'block';
                    if (scanStatus) {
                        scanStatus.style.display = 'block';
                        scanStatus.textContent = 'Initializing scan...';
                    }
                    if (progressBar) progressBar.style.width = '0%';
                    
                    // Start the actual scan
                    fetch('/api/v1/scan', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            category: selectedCategory,
                            subcategories: selectedSubcategories,
                            max_results: 100
                        })
                    })
                    .then(response => {
                        if (!response.ok) {
                            throw new Error(`Error ${response.status}: ${response.statusText}`);
                        }
                        return response.json();
                    })
                    .then(data => {
                        console.log('Scan initiated successfully', data);
                        
                        // Get scan ID from response
                        const scanId = data.meta?.scan_id;
                        
                        if (!scanId) {
                            throw new Error('No scan ID returned from server');
                        }
                        
                        // Monitor progress
                        monitorProgress(scanId);
                    })
                    .catch(error => {
                        console.error('Error starting scan:', error);
                        
                        // Reset button
                        searchButton.textContent = 'Begin Resale Search';
                        searchButton.classList.remove('loading');
                        
                        // Hide loading indicators
                        if (loadingSpinner) loadingSpinner.style.display = 'none';
                        if (progressContainer) progressContainer.style.display = 'none';
                        
                        // Show error
                        if (scanStatus) {
                            scanStatus.textContent = `Error: ${error.message}`;
                            scanStatus.style.color = 'var(--primary-color)';
                        }
                        
                        // Reset after delay
                        setTimeout(() => {
                            if (scanStatus) {
                                scanStatus.style.display = 'none';
                                scanStatus.style.color = 'var(--text-color)';
                            }
                        }, 5000);
                    });
                });
            }
        });
        
        // Function to monitor scan progress
        function monitorProgress(scanId) {
            const searchButton = document.getElementById('search-button');
            const loadingSpinner = document.getElementById('loading-spinner');
            const progressContainer = document.getElementById('progress-container');
            const scanStatus = document.getElementById('scan-status');
            const progressBar = document.getElementById('progress-bar');
            const resultsContainer = document.getElementById('results-container');
            
            let pollCount = 0;
            const maxPolls = 30;
            const pollInterval = setInterval(() => {
                pollCount++;
                
                // Check if max polls reached
                if (pollCount > maxPolls) {
                    clearInterval(pollInterval);
                    
                    // Complete progress
                    if (progressBar) progressBar.style.width = '100%';
                    
                    // Get results anyway
                    fetchResults(scanId);
                    return;
                }
                
                // Update progress visually (simulate if needed)
                const progress = Math.min(95, pollCount * 3);
                if (progressBar) progressBar.style.width = `${progress}%`;
                
                // Update status message
                if (scanStatus) {
                    if (progress < 30) {
                        scanStatus.textContent = 'Starting marketplace scrapers...';
                    } else if (progress < 50) {
                        scanStatus.textContent = 'Searching Amazon marketplace...';
                    } else if (progress < 70) {
                        scanStatus.textContent = 'Searching eBay marketplace...';
                    } else if (progress < 85) {
                        scanStatus.textContent = 'Finding matching products across marketplaces...';
                    } else {
                        scanStatus.textContent = 'Calculating profit margins...';
                    }
                }
                
                // Check actual progress from server
                fetch(`/api/progress/${scanId}`)
                    .then(response => {
                        if (!response.ok) {
                            throw new Error(`Error ${response.status}: ${response.statusText}`);
                        }
                        return response.json();
                    })
                    .then(progressData => {
                        const realProgress = progressData.progress || 0;
                        const status = progressData.status || '';
                        
                        // Update progress bar with real progress
                        if (progressBar && realProgress > progress) {
                            progressBar.style.width = `${realProgress}%`;
                        }
                        
                        // Check if scan is complete
                        if (realProgress >= 100 || ['completed', 'completed_no_results', 'failed'].includes(status)) {
                            clearInterval(pollInterval);
                            
                            // Complete progress bar
                            if (progressBar) progressBar.style.width = '100%';
                            
                            // Get final results
                            fetchResults(scanId);
                        }
                    })
                    .catch(error => {
                        console.error('Error checking progress:', error);
                        // Continue polling despite errors
                    });
            }, 2000);
        }
        
        // Function to fetch scan results
        function fetchResults(scanId) {
            const searchButton = document.getElementById('search-button');
            const loadingSpinner = document.getElementById('loading-spinner');
            const progressContainer = document.getElementById('progress-container');
            const scanStatus = document.getElementById('scan-status');
            const resultsContainer = document.getElementById('results-container');
            
            fetch(`/api/v1/scan/${scanId}`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`Error ${response.status}: ${response.statusText}`);
                    }
                    return response.json();
                })
                .then(data => {
                    console.log('Scan results:', data);
                    
                    // Get opportunities from response
                    const opportunities = data.arbitrage_opportunities || [];
                    
                    // Reset UI state
                    if (searchButton) {
                        searchButton.textContent = 'Begin Resale Search';
                        searchButton.classList.remove('loading');
                    }
                    
                    // Hide loading indicators
                    if (loadingSpinner) loadingSpinner.style.display = 'none';
                    if (progressContainer) progressContainer.style.display = 'none';
                    if (scanStatus) scanStatus.style.display = 'none';
                    
                    // Display results
                    displayResults(opportunities);
                })
                .catch(error => {
                    console.error('Error fetching results:', error);
                    
                    // Reset UI state
                    if (searchButton) {
                        searchButton.textContent = 'Begin Resale Search';
                        searchButton.classList.remove('loading');
                    }
                    
                    // Hide loading indicators
                    if (loadingSpinner) loadingSpinner.style.display = 'none';
                    if (progressContainer) progressContainer.style.display = 'none';
                    
                    // Show error
                    if (scanStatus) {
                        scanStatus.textContent = `Error retrieving results: ${error.message}`;
                        scanStatus.style.color = 'var(--primary-color)';
                        
                        // Reset after delay
                        setTimeout(() => {
                            scanStatus.style.display = 'none';
                            scanStatus.style.color = 'var(--text-color)';
                        }, 5000);
                    }
                });
        }
        
        // Function to display results
        function displayResults(opportunities) {
            const resultsContainer = document.getElementById('results-container');
            if (!resultsContainer) return;
            
            // Clear existing results
            resultsContainer.innerHTML = '';
            
            // Check if we have results
            if (!opportunities || opportunities.length === 0) {
                // Show no results message
                const noResults = document.createElement('div');
                noResults.style.textAlign = 'center';
                noResults.style.padding = '40px 20px';
                noResults.style.background = 'var(--card-bg)';
                noResults.style.borderRadius = '15px';
                noResults.style.marginTop = '30px';
                
                noResults.innerHTML = `
                    <div style="font-size: 3em; margin-bottom: 20px;">😢</div>
                    <h3>No Opportunities Found</h3>
                    <p>Try selecting different subcategories or come back later for new listings.</p>
                `;
                
                resultsContainer.appendChild(noResults);
                return;
            }
            
            // Get selected category and subcategories
            const selectedCategoryElem = document.querySelector('.category-card.active');
            const selectedCategory = selectedCategoryElem ? selectedCategoryElem.dataset.category : 'General';
            
            const selectedSubcategories = Array.from(document.querySelectorAll('.subcategory-chip.selected'))
                .map(chip => chip.textContent);
            
            // Create results header
            const resultsHeader = document.createElement('div');
            resultsHeader.style.background = 'var(--card-bg)';
            resultsHeader.style.padding = '20px';
            resultsHeader.style.borderRadius = '15px';
            resultsHeader.style.marginBottom = '20px';
            resultsHeader.innerHTML = `
                <h2>Found ${opportunities.length} Opportunities</h2>
                <p>Category: ${selectedCategory} • Subcategories: ${selectedSubcategories.join(', ')}</p>
            `;
            
            resultsContainer.appendChild(resultsHeader);
            
            // Create results grid
            const opportunitiesGrid = document.createElement('div');
            opportunitiesGrid.className = 'opportunities';
            
            // Create a card for each opportunity
            opportunities.forEach(opportunity => {
                // Handle marketplace fees
                let marketplaceFee = 0;
                let shippingFee = 0;
                
                if (opportunity.fees) {
                    marketplaceFee = opportunity.fees.marketplace || 0;
                    shippingFee = opportunity.fees.shipping || 0;
                }
                
                // Get confidence score
                const confidence = opportunity.confidence || opportunity.similarity || 80;
                
                // Create the card
                const card = document.createElement('div');
                card.className = 'opportunity-card';
                
                // Get image URL
                const imageUrl = opportunity.buyImage || '';
                let imageHtml = '';
                
                if (imageUrl) {
                    imageHtml = `<img src="${imageUrl}" alt="${opportunity.buyTitle}" style="width: 100%; height: auto; margin-bottom: 10px; border-radius: 4px;">`;
                }
                
                // Format card HTML
                card.innerHTML = `
                    <div class="card-header">
                        <h3>${opportunity.buyTitle}</h3>
                    </div>
                    <div class="card-content">
                        ${imageHtml}
                        <div class="product-comparison">
                            <div class="buy-info">
                                <div class="marketplace">Buy on ${opportunity.buyMarketplace}</div>
                                <div class="price">$${opportunity.buyPrice.toFixed(2)}</div>
                                <span class="condition-badge condition-new">${opportunity.buyCondition || 'New'}</span>
                            </div>
                            <div class="sell-info">
                                <div class="marketplace">Sell on ${opportunity.sellMarketplace}</div>
                                <div class="price">$${opportunity.sellPrice.toFixed(2)}</div>
                                <span class="condition-badge condition-new">${opportunity.sellCondition || 'New'}</span>
                            </div>
                        </div>
                        
                        <div class="profit-details">
                            <div class="profit">Profit: $${opportunity.profit.toFixed(2)}</div>
                            <div class="profit-percentage">ROI: ${opportunity.profitPercentage.toFixed(2)}%</div>
                            <div class="fees">
                                Fees: $${marketplaceFee.toFixed(2)} • Shipping: $${shippingFee.toFixed(2)}
                            </div>
                        </div>
                        
                        <div class="confidence-meter">
                            <div class="confidence-bar">
                                <div class="confidence-fill" style="width: ${confidence}%"></div>
                            </div>
                            <div class="confidence-text">${confidence}% match</div>
                        </div>
                    </div>
                    <div class="card-actions">
                        <a href="${opportunity.buyLink}" target="_blank" class="btn btn-outline">View Buy</a>
                        <a href="${opportunity.sellLink}" target="_blank" class="btn btn-secondary">View Sell</a>
                    </div>
                `;
                
                opportunitiesGrid.appendChild(card);
            });
            
            resultsContainer.appendChild(opportunitiesGrid);
            
            // Scroll to results
            resultsHeader.scrollIntoView({ behavior: 'smooth' });
        }
    }
})();
