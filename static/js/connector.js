// FlipHawk Connector Script
// Enhanced script to ensure proper communication between frontend and backend

(function() {
    // Check if the main script is loaded
    if (typeof startScan !== 'function') {
        console.log('Main script not loaded, initializing connector...');
        
        document.addEventListener('DOMContentLoaded', function() {
            const searchButton = document.getElementById('search-button');
            
            if (searchButton) {
                let currentScanId = null;
                let pollingInterval = null;
                let scanInProgress = false;
                
                searchButton.addEventListener('click', function() {
                    if (scanInProgress) {
                        // Cancel the scan
                        if (pollingInterval) {
                            clearInterval(pollingInterval);
                            pollingInterval = null;
                        }
                        
                        this.textContent = 'Start Scan';
                        scanInProgress = false;
                        
                        // Hide loading indicators
                        const loadingSpinner = document.getElementById('loading-spinner');
                        const progressContainer = document.getElementById('progress-container');
                        const scanStatus = document.getElementById('scan-status');
                        
                        if (loadingSpinner) loadingSpinner.style.display = 'none';
                        if (progressContainer) progressContainer.style.display = 'none';
                        if (scanStatus) scanStatus.style.display = 'none';
                        
                        return;
                    }
                    
                    // Get selected subcategories
                    const selectedSubcategories = Array.from(document.querySelectorAll('.subcategory-chip.selected, input[type="checkbox"]:checked'))
                        .map(elem => elem.value || elem.textContent);
                    
                    if (selectedSubcategories.length === 0) {
                        alert('Please select at least one subcategory');
                        return;
                    }
                    
                    // Get selected category
                    const selectedCategoryElem = document.querySelector('.category-card.active');
                    const categorySelect = document.getElementById('category-select');
                    const selectedCategory = selectedCategoryElem ? 
                        selectedCategoryElem.dataset.category : 
                        (categorySelect ? categorySelect.value : '');
                    
                    if (!selectedCategory) {
                        alert('Please select a category');
                        return;
                    }
                    
                    // Start scan
                    scanInProgress = true;
                    
                    // Show loading state
                    this.textContent = 'Cancel Scan';
                    
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
                    fetch('/api/scan', {
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
                        
                        // Store current scan ID
                        currentScanId = scanId;
                        
                        // Start progress monitoring
                        startProgressMonitoring(scanId);
                    })
                    .catch(error => {
                        console.error('Error starting scan:', error);
                        
                        // Reset button and state
                        searchButton.textContent = 'Start Scan';
                        scanInProgress = false;
                        
                        // Hide loading indicators
                        if (loadingSpinner) loadingSpinner.style.display = 'none';
                        if (progressContainer) progressContainer.style.display = 'none';
                        
                        // Show error
                        if (scanStatus) {
                            scanStatus.textContent = `Error: ${error.message}`;
                            scanStatus.style.color = 'var(--primary-color)';
                            scanStatus.style.display = 'block';
                            
                            // Reset after delay
                            setTimeout(() => {
                                scanStatus.style.display = 'none';
                                scanStatus.style.color = '';
                            }, 5000);
                        } else {
                            alert(`Error starting scan: ${error.message}`);
                        }
                    });
                });
                
                // Function to monitor scan progress
                function startProgressMonitoring(scanId) {
                    // Clear any existing interval
                    if (pollingInterval) {
                        clearInterval(pollingInterval);
                    }
                    
                    let lastProgress = 0;
                    let consecutiveErrors = 0;
                    
                    pollingInterval = setInterval(() => {
                        if (!scanInProgress) {
                            clearInterval(pollingInterval);
                            return;
                        }
                        
                        fetch(`/api/progress/${scanId}`)
                            .then(response => {
                                if (!response.ok) {
                                    throw new Error(`Error ${response.status}: ${response.statusText}`);
                                }
                                return response.json();
                            })
                            .then(data => {
                                const progress = data.progress || 0;
                                const status = data.status || '';
                                
                                // Update progress bar
                                const progressBar = document.getElementById('progress-bar');
                                if (progressBar) {
                                    progressBar.style.width = `${progress}%`;
                                }
                                
                                // Update status text
                                const scanStatus = document.getElementById('scan-status');
                                if (scanStatus) {
                                    scanStatus.textContent = getStatusText(status, progress);
                                }
                                
                                // Store last progress
                                lastProgress = progress;
                                
                                // Reset error counter
                                consecutiveErrors = 0;
                                
                                // Check if scan is complete
                                if (progress >= 100 || ['completed', 'completed_no_results', 'error', 'cancelled'].includes(status)) {
                                    clearInterval(pollingInterval);
                                    
                                    // Get results
                                    fetchFinalResults(scanId);
                                }
                            })
                            .catch(error => {
                                console.error('Error checking progress:', error);
                                consecutiveErrors++;
                                
                                // If we've had many consecutive errors, show fallback progress
                                if (consecutiveErrors > 3) {
                                    const progressBar = document.getElementById('progress-bar');
                                    if (progressBar && lastProgress < 95) {
                                        // Increment by a small amount
                                        lastProgress += 5;
                                        progressBar.style.width = `${lastProgress}%`;
                                        
                                        // Update status
                                        const scanStatus = document.getElementById('scan-status');
                                        if (scanStatus) {
                                            scanStatus.textContent = getStatusText('', lastProgress);
                                        }
                                    }
                                }
                                
                                // After 15 consecutive errors, assume scan is complete
                                if (consecutiveErrors > 15) {
                                    clearInterval(pollingInterval);
                                    fetchFinalResults(scanId);
                                }
                            });
                    }, 2000); // Poll every 2 seconds
                }
                
                // Function to fetch final results
                function fetchFinalResults(scanId) {
                    const resultsContainer = document.getElementById('results-container');
                    if (!resultsContainer) return;
                    
                    fetch(`/api/scan/${scanId}`)
                        .then(response => {
                            if (!response.ok) {
                                throw new Error(`Error ${response.status}: ${response.statusText}`);
                            }
                            return response.json();
                        })
                        .then(data => {
                            // Reset scan state
                            scanInProgress = false;
                            
                            // Reset button
                            searchButton.textContent = 'Start Scan';
                            
                            // Hide loading indicators
                            const loadingSpinner = document.getElementById('loading-spinner');
                            const scanStatus = document.getElementById('scan-status');
                            
                            if (loadingSpinner) loadingSpinner.style.display = 'none';
                            
                            // Get opportunities from response
                            const opportunities = data.arbitrage_opportunities || [];
                            
                            // Display results
                            displayResults(opportunities);
                        })
                        .catch(error => {
                            console.error('Error fetching results:', error);
                            
                            // Reset scan state
                            scanInProgress = false;
                            
                            // Reset button
                            searchButton.textContent = 'Start Scan';
                            
                            // Hide loading indicators
                            const loadingSpinner = document.getElementById('loading-spinner');
                            
                            if (loadingSpinner) loadingSpinner.style.display = 'none';
                            
                            // Show error
                            const scanStatus = document.getElementById('scan-status');
                            if (scanStatus) {
                                scanStatus.textContent = `Error: ${error.message}`;
                                scanStatus.style.color = 'var(--primary-color)';
                                
                                // Reset after delay
                                setTimeout(() => {
                                    scanStatus.style.display = 'none';
                                    scanStatus.style.color = '';
                                }, 5000);
                            } else {
                                alert(`Error getting results: ${error.message}`);
                            }
                        });
                }
                
                // Get readable status text based on status and progress
                function getStatusText(status, progress) {
                    switch (status) {
                        case 'initializing':
                            return 'Initializing scan...';
                        case 'searching marketplaces':
                            return 'Searching marketplaces...';
                        case 'searching amazon':
                            return 'Searching Amazon marketplace...';
                        case 'searching ebay':
                            return 'Searching eBay marketplace...';
                        case 'finding opportunities':
                            return 'Finding arbitrage opportunities...';
                        case 'processing results':
                            return 'Processing results...';
                        case 'completed':
                            return 'Scan completed!';
                        case 'completed_no_results':
                            return 'Scan completed. No opportunities found.';
                        case 'error':
                            return 'Scan failed. Please try again.';
                        default:
                            if (progress < 30) {
                                return 'Starting marketplace scrapers...';
                            } else if (progress < 50) {
                                return 'Searching products across marketplaces...';
                            } else if (progress < 70) {
                                return 'Comparing prices between platforms...';
                            } else if (progress < 90) {
                                return 'Finding profitable opportunities...';
                            } else {
                                return 'Finalizing results...';
                            }
                    }
                }
                
                // Function to display results
                function displayResults(opportunities) {
                    const resultsContainer = document.getElementById('results-container');
                    if (!resultsContainer) return;
                    
                    // Clear existing results
                    resultsContainer.innerHTML = '';
                    
                    // Check if we have results
                    if (!opportunities || opportunities.length === 0) {
                        resultsContainer.innerHTML = `
                            <div class="no-results">
                                <h3>No arbitrage opportunities found</h3>
                                <p>Try selecting different subcategories or try again later.</p>
                            </div>
                        `;
                        return;
                    }
                    
                    // Get selected category and subcategories
                    const selectedCategoryElem = document.querySelector('.category-card.active');
                    const categorySelect = document.getElementById('category-select');
                    const selectedCategory = selectedCategoryElem ? 
                        selectedCategoryElem.dataset.category : 
                        (categorySelect ? categorySelect.value : 'General');
                    
                    const selectedSubcategories = Array.from(
                        document.querySelectorAll('.subcategory-chip.selected, input[type="checkbox"]:checked')
                    ).map(elem => elem.value || elem.textContent);
                    
                    // Create results header
                    const resultsHeader = document.createElement('div');
                    resultsHeader.innerHTML = `
                        <h2>Found ${opportunities.length} Opportunities</h2>
                        <p>Category: ${selectedCategory} • Subcategories: ${selectedSubcategories.join(', ')}</p>
                    `;
                    resultsContainer.appendChild(resultsHeader);
                    
                    // Create results grid
                    const grid = document.createElement('div');
                    grid.className = 'results-grid';
                    
                    // Add each result
                    opportunities.forEach(opportunity => {
                        const card = createResultCard(opportunity);
                        grid.appendChild(card);
                    });
                    
                    // Add grid to container
                    resultsContainer.appendChild(grid);
                    
                    // Scroll to results
                    resultsHeader.scrollIntoView({ behavior: 'smooth' });
                }
                
                // Create a result card
                function createResultCard(result) {
                    const card = document.createElement('div');
                    card.className = 'result-card';
                    
                    // Get image
                    const imageUrl = result.buyImage || result.sellImage || 'https://via.placeholder.com/200';
                    
                    // Get condition classes
                    const buyCondition = result.buyCondition || 'New';
                    const sellCondition = result.sellCondition || 'New';
                    
                    const buyConditionClass = buyCondition.toLowerCase().includes('new') ? 'condition-new' : 'condition-used';
                    const sellConditionClass = sellCondition.toLowerCase().includes('new') ? 'condition-new' : 'condition-used';
                    
                    // Format fees
                    const marketplaceFee = result.fees?.marketplace || 0;
                    const shippingFee = result.fees?.shipping || 0;
                    
                    // Format similarity/confidence
                    const similarity = result.similarity || result.confidence || 70;
                    
                    // Card HTML
                    card.innerHTML = `
                        <div class="card-header">
                            <h3>${result.buyTitle}</h3>
                        </div>
                        <div class="card-image">
                            <img src="${imageUrl}" alt="${result.buyTitle}">
                        </div>
                        <div class="card-content">
                            <div class="comparison">
                                <div class="buy-info">
                                    <div class="marketplace">Buy on ${result.buyMarketplace}</div>
                                    <div class="price">$${parseFloat(result.buyPrice).toFixed(2)}</div>
                                    <div class="condition ${buyConditionClass}">${buyCondition}</div>
                                </div>
                                <div class="sell-info">
                                    <div class="marketplace">Sell on ${result.sellMarketplace}</div>
                                    <div class="price">$${parseFloat(result.sellPrice).toFixed(2)}</div>
                                    <div class="condition ${sellConditionClass}">${sellCondition}</div>
                                </div>
                            </div>
                            
                            <div class="profit-info">
                                <div class="profit">Profit: $${parseFloat(result.profit).toFixed(2)}</div>
                                <div class="profit-percentage">ROI: ${parseFloat(result.profitPercentage).toFixed(1)}%</div>
                                <div class="fees">
                                    Fees: $${parseFloat(marketplaceFee).toFixed(2)} • 
                                    Shipping: $${parseFloat(shippingFee).toFixed(2)}
                                </div>
                            </div>
                            
                            <div class="confidence">
                                <div class="confidence-bar">
                                    <div class="confidence-fill" style="width: ${similarity}%"></div>
                                </div>
                                <div class="confidence-text">${similarity}% match</div>
                            </div>
                        </div>
                        <div class="card-actions">
                            <a href="${result.buyLink}" target="_blank" class="btn btn-outline">View Buy</a>
                            <a href="${result.sellLink}" target="_blank" class="btn btn-primary">View Sell</a>
                        </div>
                    `;
                    
                    return card;
                }
            }
        });
    }
})();
