// static/js/script.js
// FlipHawk Frontend Script - Enhanced version
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
    let currentScanId = null;
    let pollingInterval = null;
    
    // Initialize
    initEventListeners();
    
    // Log initialization
    console.log('FlipHawk script.js loaded successfully');
    
    // Set up event listeners
    function initEventListeners() {
        // Category selection
        if (categoryCards.length > 0) {
            categoryCards.forEach(card => {
                card.addEventListener('click', function() {
                    if (scanInProgress) return; // Prevent changing category during scan
                    
                    document.querySelectorAll('.category-card').forEach(c => c.classList.remove('active'));
                    this.classList.add('active');
                    selectedCategory = this.dataset.category;
                    showSubcategories(selectedCategory);
                });
            });
        }
        
        // Search button
        if (searchButton) {
            searchButton.addEventListener('click', function() {
                if (scanInProgress) {
                    // Abort scan if in progress
                    abortScan();
                    return;
                }
                
                startScan();
            });
        }
    }
    
    // Show subcategories for selected category
    function showSubcategories(category) {
        console.log(`Loading subcategories for: ${category}`);
        
        // Show loading state
        if (subcategoryGrid) {
            subcategoryGrid.innerHTML = '<div class="loading">Loading subcategories...</div>';
        }
        
        // Fetch subcategories from backend
        fetch('/api/categories/' + encodeURIComponent(category) + '/subcategories')
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Error ${response.status}: ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                // Clear previous subcategories
                if (subcategoryGrid) {
                    subcategoryGrid.innerHTML = '';
                }
                
                // Get subcategories from response
                const subcategories = data.subcategories || [];
                
                if (subcategories.length === 0) {
                    if (subcategoryGrid) {
                        subcategoryGrid.innerHTML = '<div class="no-subcategories">No subcategories found for this category.</div>';
                    }
                    return;
                }
                
                // Create subcategory chips
                subcategories.forEach(subcategory => {
                    if (subcategoryGrid) {
                        const chip = document.createElement('div');
                        chip.className = 'subcategory-chip';
                        chip.textContent = subcategory;
                        chip.addEventListener('click', () => toggleSubcategory(chip, subcategory));
                        subcategoryGrid.appendChild(chip);
                    }
                });
                
                // Show subcategory panel
                if (subcategoryPanel) {
                    subcategoryPanel.style.display = 'block';
                }
                
                // Reset selections
                selectedSubcategories = [];
                updateSelectedCount();
                updateSearchButton();
                
                // Scroll to subcategories
                if (subcategoryPanel) {
                    subcategoryPanel.scrollIntoView({ behavior: 'smooth' });
                }
                
                console.log(`Loaded ${subcategories.length} subcategories for ${category}`);
            })
            .catch(error => {
                console.error('Error fetching subcategories:', error);
                
                // Show error message
                if (subcategoryGrid) {
                    subcategoryGrid.innerHTML = `<div class="error">Error loading subcategories: ${error.message}</div>`;
                }
                
                // Show panel anyway
                if (subcategoryPanel) {
                    subcategoryPanel.style.display = 'block';
                }
            });
    }
    
    // Toggle subcategory selection
    function toggleSubcategory(chip, subcategory) {
        if (scanInProgress) return; // Prevent changing selection during scan
        
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
    
    // Update selected count display
    function updateSelectedCount() {
        if (selectedCount) {
            selectedCount.textContent = `${selectedSubcategories.length} subcategories selected`;
        }
    }
    
    // Update search button state based on selections
    function updateSearchButton() {
        if (searchButton) {
            if (selectedSubcategories.length > 0) {
                searchButton.classList.add('active');
                searchButton.disabled = false;
            } else {
                searchButton.classList.remove('active');
                searchButton.disabled = true;
            }
        }
    }
    
    // Abort current scan
    function abortScan() {
        console.log('Aborting scan...');
        
        // Stop polling
        if (pollingInterval) {
            clearInterval(pollingInterval);
            pollingInterval = null;
        }
        
        // Reset UI
        if (searchButton) {
            searchButton.textContent = 'Cancelling...';
            searchButton.disabled = true;
            
            // Delay reset to show cancelling state
            setTimeout(() => {
                scanInProgress = false;
                searchButton.textContent = 'Begin Resale Search';
                searchButton.disabled = false;
                searchButton.classList.add('active');
                
                // Hide loading indicators
                if (loadingSpinner) loadingSpinner.style.display = 'none';
                if (progressContainer) progressContainer.style.display = 'none';
                if (scanStatus) scanStatus.style.display = 'none';
            }, 1000);
        }
    }
    
    // Start scan function with real-time progress reporting
    function startScan() {
        // Check if category and subcategories are selected
        if (!selectedCategory || selectedSubcategories.length === 0) {
            showToast('Please select a category and at least one subcategory', 'error');
            return;
        }
        
        console.log(`Starting scan for ${selectedCategory}: ${selectedSubcategories.join(', ')}`);
        
        // Set scan in progress state
        scanInProgress = true;
        
        // Clear previous results
        if (resultsContainer) {
            resultsContainer.innerHTML = '';
        }
        
        // Show loading indicators
        if (loadingSpinner) loadingSpinner.style.display = 'block';
        if (progressContainer) progressContainer.style.display = 'block';
        if (scanStatus) {
            scanStatus.style.display = 'block';
            scanStatus.textContent = 'Initializing scan...';
        }
        if (progressBar) progressBar.style.width = '0%';
        
        // Update search button
        if (searchButton) {
            searchButton.disabled = false;
            searchButton.textContent = 'Cancel Scan';
            searchButton.classList.add('loading');
            searchButton.classList.remove('active');
        }
        
        // Prepare the request data
        const requestData = {
            category: selectedCategory,
            subcategories: selectedSubcategories,
            max_results: 100
        };
        
        // Call the scan API
        fetch('/api/v1/scan', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Error ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            // Check for error
            if (data.error) {
                throw new Error(data.error);
            }
            
            // Get the scan ID
            const scanId = data.meta?.scan_id;
            
            if (!scanId) {
                throw new Error('No scan ID returned from server');
            }
            
            console.log(`Scan started with ID: ${scanId}`);
            
            // Store current scan ID
            currentScanId = scanId;
            
            // Start polling for progress
            pollScanProgress(scanId);
        })
        .catch(error => {
            console.error('Error starting scan:', error);
            
            // Reset scan state
            scanInProgress = false;
            
            if (searchButton) {
                searchButton.textContent = 'Begin Resale Search';
                searchButton.classList.remove('loading');
                searchButton.classList.add('active');
            }
            
            // Hide loading indicators
            if (loadingSpinner) loadingSpinner.style.display = 'none';
            if (progressContainer) progressContainer.style.display = 'none';
            
            // Show error message
            if (scanStatus) {
                scanStatus.textContent = `Error connecting to scanning service. Please try again later.`;
                scanStatus.style.color = 'var(--primary-color, #ff0000)';
                scanStatus.style.display = 'block';
                
                // Reset after a delay
                setTimeout(() => {
                    scanStatus.style.display = 'none';
                    scanStatus.style.color = '';
                }, 5000);
            } else {
                showToast(`Error connecting to scanning service. Please try again later.`, 'error');
            }
        });
    }
    
    // Poll for scan progress
    function pollScanProgress(scanId) {
        // Clear any existing polling interval
        if (pollingInterval) {
            clearInterval(pollingInterval);
        }
        
        let consecutiveErrors = 0;
        const maxErrors = 5;
        
        pollingInterval = setInterval(() => {
            // Check if scan is still in progress
            if (!scanInProgress) {
                clearInterval(pollingInterval);
                pollingInterval = null;
                return;
            }
            
            // Poll for scan progress
            fetch(`/api/progress/${scanId}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Error ${response.status}: ${response.statusText}`);
                }
                return response.json();
            })
            .then(progressData => {
                console.log('Raw API response:', resultsData);
                // Reset error counter on success
                consecutiveErrors = 0;
                
                // Update progress bar
                const progress = progressData.progress || 0;
                if (progressBar) progressBar.style.width = `${progress}%`;
                
                // Update status message based on status
                const status = progressData.status || 'processing';
                updateStatusMessage(status, progress);
                
                // Check if scan is complete
                if (progress >= 100 || ['completed', 'completed_no_results', 'failed', 'error', 'cancelled'].includes(status)) {
                    clearInterval(pollingInterval);
                    pollingInterval = null;
                    
                    // Fetch the results
                    fetchScanResults(scanId);
                }
            })
            .catch(error => {
                console.error('Error polling scan progress:', error);
                consecutiveErrors++;
                
                // If too many consecutive errors, stop polling
                if (consecutiveErrors >= maxErrors) {
                    clearInterval(pollingInterval);
                    pollingInterval = null;
                    
                    // Show error and reset UI
                    showToast('Lost connection to server. Please try again.', 'error');
                    
                    scanInProgress = false;
                    
                    if (searchButton) {
                        searchButton.textContent = 'Begin Resale Search';
                        searchButton.classList.remove('loading');
                        searchButton.classList.add('active');
                    }
                    
                    if (loadingSpinner) loadingSpinner.style.display = 'none';
                    if (progressContainer) progressContainer.style.display = 'none';
                    if (scanStatus) scanStatus.style.display = 'none';
                }
            });
        }, 1000); // Poll every 1 second
    }
    
    // Update status message based on scan status
    function updateStatusMessage(status, progress) {
        if (!scanStatus) return;
        
        let message = '';
        
        switch (status) {
            case 'initializing':
                message = 'Initializing scan...';
                break;
            case 'running':
                message = 'Running scan...';
                break;
            case 'searching marketplaces':
                message = 'Searching marketplaces...';
                break;
            case 'searching amazon':
                message = 'Searching Amazon marketplace...';
                break;
            case 'searching ebay':
                message = 'Searching eBay marketplace...';
                break;
            case 'searching facebook':
                message = 'Searching Facebook marketplace...';
                break;
            case 'finding opportunities':
                message = 'Finding arbitrage opportunities...';
                break;
            case 'processing results':
                message = 'Processing results...';
                break;
            case 'completed':
                message = 'Scan completed!';
                break;
            case 'completed_no_results':
                message = 'Scan completed with no results found.';
                break;
            case 'failed':
            case 'error':
                message = 'Scan failed. Please try again.';
                break;
            case 'cancelled':
                message = 'Scan cancelled.';
                break;
            default:
                message = `Scanning for ${selectedSubcategories.join(', ')}...`;
                
                // Set more specific messages based on progress
                if (progress < 20) {
                    message = 'Preparing scrapers and keywords...';
                } else if (progress < 40) {
                    message = 'Scanning Amazon marketplace...';
                } else if (progress < 60) {
                    message = 'Scanning eBay marketplace...';
                } else if (progress < 80) {
                    message = 'Finding matching products across marketplaces...';
                } else {
                    message = 'Calculating profit opportunities...';
                }
        }
        
        scanStatus.textContent = message;
    }
    
    // Fetch the actual scan results
    function fetchScanResults(scanId) {
        console.log(`Fetching results for scan ${scanId}`);
        
        fetch(`/api/v1/scan/${scanId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`Error ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
.then(resultsData => {
    console.log('Raw API response:', resultsData);
    
    // Always have a valid array
    const opportunities = [];
    
    // Display the results (empty array is fine)
    displayResults(opportunities);
            // Reset scan state
            scanInProgress = false;
            currentScanId = null;
            
            if (searchButton) {
                searchButton.textContent = 'Begin Resale Search';
                searchButton.classList.remove('loading');
                searchButton.classList.add('active');
            }
            
            // Hide loading indicators
            if (loadingSpinner) loadingSpinner.style.display = 'none';
            if (progressContainer) progressContainer.style.display = 'none';
            if (scanStatus) scanStatus.style.display = 'none';
        })
        .catch(error => {
            console.error('Error fetching scan results:', error);
            
            // Show error message
            if (scanStatus) {
                scanStatus.textContent = `Error retrieving results: ${error.message}`;
                scanStatus.style.color = 'var(--primary-color, #ff0000)';
            } else {
                showToast(`Error retrieving results: ${error.message}`, 'error');
            }
            
            // Reset scan state after a delay
            setTimeout(() => {
                scanInProgress = false;
                currentScanId = null;
                
                if (searchButton) {
                    searchButton.textContent = 'Begin Resale Search';
                    searchButton.classList.remove('loading');
                    searchButton.classList.add('active');
                }
                
                // Hide loading indicators
                if (loadingSpinner) loadingSpinner.style.display = 'none';
                if (progressContainer) progressContainer.style.display = 'none';
                if (scanStatus) {
                    scanStatus.style.display = 'none';
                    scanStatus.style.color = '';
                }
            }, 5000);
        });
    }
    
    // Display scan results
    function displayResults(opportunities) {
        if (!resultsContainer) return;
        
        // Clear previous results
        resultsContainer.innerHTML = '';
        
        // Check if we have results
        if (!opportunities || opportunities.length === 0) {
            // Show no results message
            const noResults = document.createElement('div');
            noResults.className = 'no-results';
            noResults.innerHTML = `
                <h3>No Opportunities Found</h3>
                <p>Try selecting different subcategories or come back later for new listings.</p>
            `;
            
            resultsContainer.appendChild(noResults);
            return;
        }
        
        // Create results header
        const resultsHeader = document.createElement('div');
        resultsHeader.className = 'results-header';
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
    function createResultCard(opportunity) {
        const card = document.createElement('div');
        card.className = 'result-card';
        
        // Get image
        const imageUrl = opportunity.buyImage || opportunity.sellImage || 'https://via.placeholder.com/200';
        
        // Get condition classes
        const buyCondition = opportunity.buyCondition || 'New';
        const sellCondition = opportunity.sellCondition || 'New';
        
        const buyConditionClass = getConditionClass(buyCondition);
        const sellConditionClass = getConditionClass(sellCondition);
        
        // Format fees
        const marketplaceFee = opportunity.fees?.marketplace || 0;
        const shippingFee = opportunity.fees?.shipping || 0;
        
        // Format numbers
        const buyPrice = parseFloat(opportunity.buyPrice).toFixed(2);
        const sellPrice = parseFloat(opportunity.sellPrice).toFixed(2);
        const profit = parseFloat(opportunity.profit).toFixed(2);
        const profitPercentage = parseFloat(opportunity.profitPercentage).toFixed(1);
        
        // Format similarity/confidence
        const similarity = opportunity.similarity || opportunity.confidence || 70;
        
        // Card HTML
        card.innerHTML = `
            <div class="card-header">
                <h3>${opportunity.buyTitle}</h3>
            </div>
            <div class="card-image">
                <img src="${imageUrl}" alt="${opportunity.buyTitle}" onerror="this.src='https://via.placeholder.com/200?text=No+Image'">
            </div>
            <div class="card-content">
                <div class="comparison">
                    <div class="buy-info">
                        <div class="marketplace">Buy on ${opportunity.buyMarketplace}</div>
                        <div class="price">$${buyPrice}</div>
                        <div class="condition ${buyConditionClass}">${buyCondition}</div>
                    </div>
                    <div class="sell-info">
                        <div class="marketplace">Sell on ${opportunity.sellMarketplace}</div>
                        <div class="price">$${sellPrice}</div>
                        <div class="condition ${sellConditionClass}">${sellCondition}</div>
                    </div>
                </div>
                
                <div class="profit-info">
                    <div class="profit">Profit: $${profit}</div>
                    <div class="profit-percentage">ROI: ${profitPercentage}%</div>
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
                <a href="${opportunity.buyLink}" target="_blank" class="btn btn-outline">View Buy</a>
                <a href="${opportunity.sellLink}" target="_blank" class="btn btn-primary">View Sell</a>
            </div>
        `;
        
        return card;
    }
    
    // Helper function to get condition class
    function getConditionClass(condition) {
        if (!condition) return '';
        
        condition = condition.toLowerCase();
        if (condition.includes('new') || condition === 'mint' || condition === 'sealed') {
            return 'condition-new';
        } else {
            return 'condition-used';
        }
    }
    
    // Function to show toast notification
    function showToast(message, type = 'info') {
        console.log(`Toast: ${type} - ${message}`);
        
        // Remove existing toasts
        document.querySelectorAll('.toast').forEach(toast => {
            document.body.removeChild(toast);
        });
        
        // Create toast
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        
        // Add to document
        document.body.appendChild(toast);
        
        // Remove after delay
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transition = 'opacity 0.5s ease';
            
            setTimeout(() => {
                if (document.body.contains(toast)) {
                    document.body.removeChild(toast);
                }
            }, 500);
        }, 3000);
    }
});
