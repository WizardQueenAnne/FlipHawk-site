// Create a new file: static/js/scan.js
document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const categoryCards = document.querySelectorAll('.category-card');
    const subcategoryPanel = document.getElementById('subcategory-panel');
    const subcategoryGrid = document.getElementById('subcategory-grid');
    const selectedCount = document.getElementById('selected-count');
    const searchButton = document.getElementById('search-button');
    const loadingSpinner = document.getElementById('loading-spinner');
    const progressContainer = document.getElementById('progress-container');
    const progressBar = document.getElementById('progress-bar');
    const scanStatus = document.getElementById('scan-status');
    const resultsContainer = document.getElementById('results-container');
    
    // Global variables
    let selectedCategory = '';
    let selectedSubcategories = [];
    let scanInProgress = false;
    let scanAborted = false;
    
    // Initialize event listeners
    initializeEvents();
    
    function initializeEvents() {
        // Category selection
        categoryCards.forEach(card => {
            card.addEventListener('click', function() {
                document.querySelectorAll('.category-card').forEach(c => c.classList.remove('active'));
                this.classList.add('active');
                selectedCategory = this.dataset.category;
                showSubcategories(selectedCategory);
            });
        });
        
        // Search button
        searchButton.addEventListener('click', function() {
            if (scanInProgress) {
                // Abort scan if in progress
                scanAborted = true;
                searchButton.textContent = 'Cancelling...';
                return;
            }
            
            startScan();
        });
    }
    
    function showSubcategories(category) {
        // Clear previous subcategories
        subcategoryGrid.innerHTML = '';
        
        // Get subcategories for selected category
        fetch('/api/v1/categories/subcategories', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ category })
        })
        .then(response => response.json())
        .then(data => {
            const subcategories = data.subcategories || [];
            
            subcategories.forEach(subcategory => {
                const chip = document.createElement('div');
                chip.className = 'subcategory-chip';
                chip.textContent = subcategory;
                chip.dataset.subcategory = subcategory;
                
                chip.addEventListener('click', function() {
                    toggleSubcategory(chip, subcategory);
                });
                
                subcategoryGrid.appendChild(chip);
            });
            
            subcategoryPanel.style.display = 'block';
            selectedSubcategories = [];
            updateSelectedCount();
            updateSearchButton();
            
            // Scroll to subcategories
            subcategoryPanel.scrollIntoView({ behavior: 'smooth' });
        })
        .catch(error => {
            console.error('Error fetching subcategories:', error);
            
            // Fallback to hardcoded subcategories for the demo
            const subcats = {
                "Tech": ["Headphones", "Keyboards", "Graphics Cards", "CPUs", "Laptops", "Monitors", "SSDs", "Routers", "Vintage Tech"],
                "Collectibles": ["Pokémon", "Magic: The Gathering", "Yu-Gi-Oh", "Funko Pops", "Sports Cards", "Comic Books", "Action Figures", "LEGO Sets"],
                "Vintage Clothing": ["Jordans", "Nike Dunks", "Vintage Tees", "Band Tees", "Denim Jackets", "Designer Brands", "Carhartt", "Patagonia"],
            };
            
            const fallbackSubcats = subcats[category] || [];
            
            fallbackSubcats.forEach(subcategory => {
                const chip = document.createElement('div');
                chip.className = 'subcategory-chip';
                chip.textContent = subcategory;
                chip.dataset.subcategory = subcategory;
                
                chip.addEventListener('click', function() {
                    toggleSubcategory(chip, subcategory);
                });
                
                subcategoryGrid.appendChild(chip);
            });
            
            subcategoryPanel.style.display = 'block';
            selectedSubcategories = [];
            updateSelectedCount();
            updateSearchButton();
            
            // Scroll to subcategories
            subcategoryPanel.scrollIntoView({ behavior: 'smooth' });
        });
    }
    
    function toggleSubcategory(chip, subcategory) {
        if (chip.classList.contains('selected')) {
            chip.classList.remove('selected');
            selectedSubcategories = selectedSubcategories.filter(s => s !== subcategory);
        } else {
            chip.classList.add('selected');
            selectedSubcategories.push(subcategory);
        }
        
        updateSelectedCount();
        updateSearchButton();
    }
    
    function updateSelectedCount() {
        selectedCount.textContent = `${selectedSubcategories.length} subcategories selected`;
    }
    
    function updateSearchButton() {
        if (selectedSubcategories.length > 0) {
            searchButton.classList.add('active');
            searchButton.disabled = false;
        } else {
            searchButton.classList.remove('active');
            searchButton.disabled = true;
        }
    }
    
    function startScan() {
        // Check if category and subcategories are selected
        if (!selectedCategory || selectedSubcategories.length === 0) {
            showToast('Please select a category and at least one subcategory', 'error');
            return;
        }
        
        // Clear previous results
        resultsContainer.innerHTML = '';
        
        // Create the API request data
        const requestData = {
            category: selectedCategory,
            subcategories: selectedSubcategories,
            max_results: 100
        };
        
        // Start the real scan with progress updates
        scanWithProgressUpdates(requestData);
    }
    
    function scanWithProgressUpdates(requestData) {
        // Set scan in progress flag
        scanInProgress = true;
        scanAborted = false;
        
        // Show loading indicators
        loadingSpinner.style.display = 'block';
        progressContainer.style.display = 'block';
        scanStatus.style.display = 'block';
        scanStatus.textContent = 'Initializing scan...';
        progressBar.style.width = '0%';
        
        // Update search button to be an abort button
        searchButton.textContent = 'Cancel Scan';
        searchButton.classList.add('loading');
        
        // Make the API call to initiate the scan
        fetch('/api/v1/scan', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Failed to connect to scanning service: ${response.status} ${response.statusText}`);
            }
            
            return response.json();
        })
        .then(initialData => {
            // Get the scan ID from the response
            const scanId = initialData.meta.scan_id;
            
            if (!scanId) {
                throw new Error('No scan ID returned from server');
            }
            
            // Set up an interval to poll for progress
            let pollCount = 0;
            const maxPolls = 20; // About 1 minute max (3s interval)
            
            const pollInterval = setInterval(() => {
                if (scanAborted) {
                    clearInterval(pollInterval);
                    
                    // Reset scan state
                    scanInProgress = false;
                    searchButton.textContent = 'Begin Resale Search';
                    searchButton.classList.remove('loading');
                    
                    // Hide loading indicators
                    loadingSpinner.style.display = 'none';
                    progressContainer.style.display = 'none';
                    scanStatus.style.display = 'none';
                    
                    return;
                }
                
                // Increment poll count
                pollCount++;
                
                // If maximum polls reached, give up
                if (pollCount > maxPolls) {
                    clearInterval(pollInterval);
                    
                    // Show error message
                    scanStatus.textContent = 'Scan taking too long. Please try again later.';
                    scanStatus.style.color = 'var(--primary-color)';
                    
                    // Reset scan state after a delay
                    setTimeout(() => {
                        scanInProgress = false;
                        searchButton.textContent = 'Begin Resale Search';
                        searchButton.classList.remove('loading');
                        
                        // Hide loading indicators
                        loadingSpinner.style.display = 'none';
                        progressContainer.style.display = 'none';
                        scanStatus.style.display = 'none';
                        scanStatus.style.color = 'var(--text-color)';
                    }, 5000);
                    
                    return;
                }
                
                // Poll for progress
                fetch(`/api/progress/${scanId}`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`Failed to get scan progress: ${response.status} ${response.statusText}`);
                    }
                    
                    return response.json();
                })
                .then(progressData => {
                    // Update progress bar
                    const progress = progressData.progress || 0;
                    progressBar.style.width = `${progress}%`;
                    
                    // Update status message
                    const status = progressData.status || 'processing';
                    
                    updateStatusMessage(status, progress);
                    
                    // If scan is complete, get the results
                    if (progress >= 100 && ['completed', 'completed_no_results', 'failed'].includes(status)) {
                        clearInterval(pollInterval);
                        
                        // Fetch the final results
                        fetch(`/api/v1/scan/${scanId}`)
                        .then(response => {
                            if (!response.ok) {
                                throw new Error(`Failed to get scan results: ${response.status} ${response.statusText}`);
                            }
                            
                            return response.json();
                        })
                        .then(resultsData => {
                            // Process and display results
                            setTimeout(() => {
                                // Use the arbitrage_opportunities array from the API response
                                const opportunities = resultsData.arbitrage_opportunities || [];
                                displayResults(opportunities);
                                
                                // Reset scan state
                                scanInProgress = false;
                                searchButton.textContent = 'Begin Resale Search';
                                searchButton.classList.remove('loading');
                                
                                // Hide loading indicators
                                loadingSpinner.style.display = 'none';
                                progressContainer.style.display = 'none';
                                scanStatus.style.display = 'none';
                            }, 500);
                        })
                        .catch(error => {
                            console.error('Error fetching results:', error);
                            
                            scanStatus.textContent = 'Error retrieving scan results. Please try again later.';
                            scanStatus.style.color = 'var(--primary-color)';
                            
                            // Reset scan state after a delay
                            setTimeout(() => {
                                scanInProgress = false;
                                searchButton.textContent = 'Begin Resale Search';
                                searchButton.classList.remove('loading');
                                
                                // Hide loading indicators
                                loadingSpinner.style.display = 'none';
                                progressContainer.style.display = 'none';
                                scanStatus.style.display = 'none';
                                scanStatus.style.color = 'var(--text-color)';
                            }, 5000);
                        });
                    }
                })
                .catch(error => {
                    console.error('Error checking progress:', error);
                    
                    // Don't stop polling on error, try again next time
                });
            }, 3000); // Poll every 3 seconds
        })
        .catch(error => {
            console.error('Scan error:', error);
            
            // Reset scan state
            scanInProgress = false;
            searchButton.textContent = 'Begin Resale Search';
            searchButton.classList.remove('loading');
            
            // Hide loading indicators
            loadingSpinner.style.display = 'none';
            progressContainer.style.display = 'none';
            
            // Show error message
            scanStatus.textContent = 'Error connecting to scanning service. Please try again later.';
            scanStatus.style.color = 'var(--primary-color)';
            scanStatus.style.display = 'block';
            
            setTimeout(() => {
                scanStatus.style.display = 'none';
                scanStatus.style.color = 'var(--text-color)';
            }, 7000);
        });
    }
    
    function updateStatusMessage(status, progress) {
        let message = '';
        
        switch (status) {
            case 'initializing':
                message = 'Initializing scan...';
                break;
            case 'processing':
                message = 'Processing scan...';
                break;
            case 'searching marketplaces':
                if (progress < 30) {
                    message = 'Connecting to Amazon marketplace...';
                } else if (progress < 50) {
                    message = 'Connecting to eBay marketplace...';
                } else if (progress < 70) {
                    message = 'Scanning other marketplaces...';
                } else {
                    message = 'Searching multiple marketplaces...';
                }
                break;
            case 'analyzing results':
                message = 'Analyzing potential arbitrage opportunities...';
                break;
            case 'finding matches':
                message = 'Finding matching products across marketplaces...';
                break;
            case 'calculating profit':
                message = 'Calculating profit margins and risk...';
                break;
            case 'completed':
                message = 'Scan completed successfully!';
                break;
            case 'completed_no_results':
                message = 'Scan completed, but no opportunities found.';
                break;
            case 'failed':
                message = 'Scan failed. Please try again later.';
                break;
            default:
                message = `Scanning for ${selectedSubcategories.join(', ')}...`;
        }
        
        scanStatus.textContent = message;
    }
    
    function displayResults(opportunities) {
        // Clear previous results
        resultsContainer.innerHTML = '';
        
        if (!opportunities || opportunities.length === 0) {
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
        
        // Create opportunities grid
        const opportunitiesGrid = document.createElement('div');
        opportunitiesGrid.className = 'opportunities';
        
        opportunities.forEach(opportunity => {
            const card = document.createElement('div');
            card.className = 'opportunity-card';
            
            // Get image URL
            const imageUrl = opportunity.image_url || opportunity.buyImage || '';
            
            // Create confidence meter width
            const confidenceWidth = (opportunity.confidence || 70) + '%';
            
            // Prepare the HTML
            card.innerHTML = `
                <div class="card-header">
                    <h3>${opportunity.buyTitle || opportunity.title || 'Product'}</h3>
                </div>
                <div class="card-content">
                    ${imageUrl ? `<img src="${imageUrl}" alt="Product" style="width: 100%; height: auto; margin-bottom: 10px; border-radius: 4px;">` : ''}
                    <div class="product-comparison">
                        <div class="buy-info">
                            <div class="marketplace">Buy on ${opportunity.buyMarketplace || 'Amazon'}</div>
                            <div class="price">$${(opportunity.buyPrice || 0).toFixed(2)}</div>
                            <span class="condition-badge condition-${(opportunity.buyCondition || 'New').toLowerCase().replace(' ', '-')}">${opportunity.buyCondition || 'New'}</span>
                        </div>
                        <div class="sell-info">
                            <div class="marketplace">Sell on ${opportunity.sellMarketplace || 'eBay'}</div>
                            <div class="price">$${(opportunity.sellPrice || 0).toFixed(2)}</div>
                            <span class="condition-badge condition-${(opportunity.sellCondition || 'New').toLowerCase().replace(' ', '-')}">${opportunity.sellCondition || 'New'}</span>
                        </div>
                    </div>
                    
                    <div class="profit-details">
                        <div class="profit">Profit: $${(opportunity.profit || 0).toFixed(2)}</div>
                        <div class="profit-percentage">ROI: ${(opportunity.profitPercentage || 0).toFixed(2)}%</div>
                        <div class="fees">
                            Fees: $${((opportunity.fees && opportunity.fees.marketplace) || 0).toFixed(2)} • Shipping: $${((opportunity.fees && opportunity.fees.shipping) || 0).toFixed(2)}
                        </div>
                    </div>
                    
                    <div class="confidence-meter">
                        <div class="confidence-bar">
                            <div class="confidence-fill" style="width: ${confidenceWidth}"></div>
                        </div>
                        <div class="confidence-text">${opportunity.confidence || 70}% match</div>
                    </div>
                </div>
                <div class="card-actions">
                    <a href="${opportunity.buyLink || '#'}" target="_blank" class="btn btn-outline">View Buy</a>
                    <a href="${opportunity.sellLink || '#'}" target="_blank" class="btn btn-secondary">View Sell</a>
                </div>
            `;
            
            opportunitiesGrid.appendChild(card);
        });
        
        resultsContainer.appendChild(opportunitiesGrid);
        
        // Scroll to results
        resultsHeader.scrollIntoView({ behavior: 'smooth' });
    }
    
    function showToast(message, type = 'error') {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => {
                document.body.removeChild(toast);
            }, 300);
        }, 3000);
    }
});
