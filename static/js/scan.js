// FlipHawk Scan Page JavaScript
// Enhanced implementation for marketplace scanning with real-time feedback

document.addEventListener('DOMContentLoaded', function() {
    // UI Elements
    const categorySelect = document.getElementById('category-select');
    const subcategoryContainer = document.getElementById('subcategory-container');
    const startScanButton = document.getElementById('start-scan');
    const scanStatusContainer = document.getElementById('scan-status-container');
    const progressBar = document.getElementById('progress-bar');
    const statusText = document.getElementById('status-text');
    const resultsContainer = document.getElementById('results-container');
    const loadingSpinner = document.getElementById('loading-spinner');

    // State
    let selectedSubcategories = [];
    let currentScanId = null;
    let scanInterval = null;
    let scanAborted = false;

    // Initialize
    init();

    // Main initialization function
    function init() {
        // Load categories
        loadCategories();
        
        // Set up event listeners
        setupEventListeners();
    }

    // Load available categories
    function loadCategories() {
        fetch('/api/categories')
            .then(response => response.json())
            .then(data => {
                // Clear select
                categorySelect.innerHTML = '';
                
                // Add placeholder
                const placeholder = document.createElement('option');
                placeholder.value = '';
                placeholder.textContent = 'Select a category';
                placeholder.disabled = true;
                placeholder.selected = true;
                categorySelect.appendChild(placeholder);
                
                // Add categories
                data.categories.forEach(category => {
                    const option = document.createElement('option');
                    option.value = category;
                    option.textContent = category;
                    categorySelect.appendChild(option);
                });
            })
            .catch(error => {
                console.error('Error loading categories:', error);
                showError('Failed to load categories. Please refresh the page.');
            });
    }

    // Load subcategories for a category
    function loadSubcategories(category) {
        fetch(`/api/categories/${category}/subcategories`)
            .then(response => response.json())
            .then(data => {
                // Clear container
                subcategoryContainer.innerHTML = '';
                
                // Add subcategories
                data.subcategories.forEach(subcategory => {
                    const checkbox = createSubcategoryCheckbox(subcategory);
                    subcategoryContainer.appendChild(checkbox);
                });
                
                // Show container
                subcategoryContainer.style.display = 'grid';
            })
            .catch(error => {
                console.error('Error loading subcategories:', error);
                showError('Failed to load subcategories. Please try a different category.');
            });
    }

    // Create a subcategory checkbox
    function createSubcategoryCheckbox(subcategory) {
        const container = document.createElement('div');
        container.className = 'subcategory-checkbox';
        
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.id = `subcategory-${subcategory.toLowerCase().replace(/\s+/g, '-')}`;
        checkbox.value = subcategory;
        checkbox.addEventListener('change', updateSelectedSubcategories);
        
        const label = document.createElement('label');
        label.htmlFor = checkbox.id;
        label.textContent = subcategory;
        
        container.appendChild(checkbox);
        container.appendChild(label);
        
        return container;
    }

    // Update the selected subcategories list
    function updateSelectedSubcategories() {
        selectedSubcategories = Array.from(
            document.querySelectorAll('#subcategory-container input[type="checkbox"]:checked')
        ).map(checkbox => checkbox.value);
        
        // Enable/disable scan button
        startScanButton.disabled = selectedSubcategories.length === 0;
    }

    // Set up all event listeners
    function setupEventListeners() {
        // Category selection change
        categorySelect.addEventListener('change', function() {
            const category = this.value;
            if (category) {
                loadSubcategories(category);
            } else {
                subcategoryContainer.style.display = 'none';
            }
        });
        
        // Start scan button
        startScanButton.addEventListener('click', function() {
            if (this.textContent === 'Cancel Scan') {
                // Cancel the scan
                cancelScan();
                return;
            }
            
            startScan();
        });
    }

    // Cancel the current scan
    function cancelScan() {
        scanAborted = true;
        startScanButton.disabled = true;
        startScanButton.textContent = 'Cancelling...';
        
        // Stop polling
        if (scanInterval) {
            clearInterval(scanInterval);
            scanInterval = null;
        }
        
        // Reset UI after a delay
        setTimeout(() => {
            startScanButton.disabled = false;
            startScanButton.textContent = 'Start Scan';
            scanStatusContainer.style.display = 'none';
            scanAborted = false;
        }, 1000);
    }

    // Start the scan process
    function startScan() {
        // Check if subcategories selected
        if (selectedSubcategories.length === 0) {
            showError('Please select at least one subcategory.');
            return;
        }
        
        // Get selected category
        const category = categorySelect.value;
        if (!category) {
            showError('Please select a category.');
            return;
        }
        
        // Clear previous results
        resultsContainer.innerHTML = '';
        
        // Show scan status
        scanStatusContainer.style.display = 'block';
        progressBar.style.width = '0%';
        statusText.textContent = 'Initializing scan...';
        loadingSpinner.style.display = 'inline-block';
        
        // Update button to cancel
        startScanButton.textContent = 'Cancel Scan';
        
        // Reset scan state
        scanAborted = false;
        
        // Send scan request
        fetch('/api/scan', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                category: category,
                subcategories: selectedSubcategories,
                max_results: 100
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            
            // Store scan ID
            currentScanId = data.meta.scan_id;
            
            // Start polling for progress
            startProgressPolling();
        })
        .catch(error => {
            console.error('Error starting scan:', error);
            showError('Failed to start scan: ' + error.message);
            
            // Reset button
            startScanButton.textContent = 'Start Scan';
            
            // Hide scan status
            scanStatusContainer.style.display = 'none';
        });
    }

    // Start polling for scan progress
    function startProgressPolling() {
        // Clear any existing interval
        if (scanInterval) {
            clearInterval(scanInterval);
        }
        
        // Set up polling interval (every 1 second)
        scanInterval = setInterval(checkScanProgress, 1000);
    }

    // Check scan progress
    function checkScanProgress() {
        if (!currentScanId || scanAborted) {
            clearInterval(scanInterval);
            return;
        }
        
        fetch(`/api/progress/${currentScanId}`)
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    throw new Error(data.error);
                }
                
                // Update progress bar
                progressBar.style.width = `${data.progress}%`;
                
                // Update status text
                statusText.textContent = getStatusText(data.status, data.progress);
                
                // Check if scan is complete
                if (data.status === 'completed' || data.status === 'completed_no_results' || 
                    data.status === 'error' || data.status === 'cancelled' || data.progress >= 100) {
                    clearInterval(scanInterval);
                    
                    // If not cancelled, get results
                    if (!scanAborted && data.status !== 'cancelled') {
                        getResults();
                    } else {
                        // Reset UI
                        startScanButton.textContent = 'Start Scan';
                        loadingSpinner.style.display = 'none';
                    }
                }
            })
            .catch(error => {
                console.error('Error checking progress:', error);
                
                // Don't stop polling on error, just continue
                // If we've had many errors, simulate progress
                const currentWidth = parseInt(progressBar.style.width) || 0;
                if (currentWidth < 95) {
                    progressBar.style.width = `${currentWidth + 2}%`;
                }
            });
    }

    // Get human-readable status text
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
            case 'searching facebook':
                return 'Searching Facebook marketplace...';
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
            case 'cancelled':
                return 'Scan cancelled.';
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

    // Get scan results
    function getResults() {
        fetch(`/api/scan/${currentScanId}`)
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    throw new Error(data.error);
                }
                
                // Hide loading spinner
                loadingSpinner.style.display = 'none';
                
                // Display results
                displayResults(data.arbitrage_opportunities || []);
                
                // Reset button
                startScanButton.textContent = 'Start Scan';
            })
            .catch(error => {
                console.error('Error getting results:', error);
                showError('Failed to get results: ' + error.message);
                
                // Hide loading spinner
                loadingSpinner.style.display = 'none';
                
                // Reset button
                startScanButton.textContent = 'Start Scan';
            });
    }

    // Display scan results
    function displayResults(results) {
        // Clear container
        resultsContainer.innerHTML = '';
        
        // Check if we have results
        if (!results || results.length === 0) {
            resultsContainer.innerHTML = `
                <div class="no-results">
                    <h3>No arbitrage opportunities found</h3>
                    <p>Try selecting different subcategories or try again later.</p>
                </div>
            `;
            return;
        }
        
        // Create results header
        const header = document.createElement('h2');
        header.textContent = `Found ${results.length} Arbitrage Opportunities`;
        resultsContainer.appendChild(header);
        
        // Add subcategories info
        const subInfo = document.createElement('p');
        subInfo.textContent = `Category: ${categorySelect.value} • Subcategories: ${selectedSubcategories.join(', ')}`;
        resultsContainer.appendChild(subInfo);
        
        // Create results grid
        const grid = document.createElement('div');
        grid.className = 'results-grid';
        
        // Add each result
        results.forEach(result => {
            const card = createResultCard(result);
            grid.appendChild(card);
        });
        
        // Add grid to container
        resultsContainer.appendChild(grid);
        
        // Scroll to results
        header.scrollIntoView({ behavior: 'smooth' });
    }

    // Create a result card
    function createResultCard(result) {
        const card = document.createElement('div');
        card.className = 'result-card';
        
        // Get buy and sell images
        const imageUrl = result.buyImage || result.sellImage || 'https://via.placeholder.com/200';
        
        // Get condition classes
        const buyConditionClass = getConditionClass(result.buyCondition);
        const sellConditionClass = getConditionClass(result.sellCondition);
        
        // Format fees
        const marketplaceFee = result.fees?.marketplace || 0;
        const shippingFee = result.fees?.shipping || 0;
        
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
                        <div class="price">$${result.buyPrice.toFixed(2)}</div>
                        <div class="condition ${buyConditionClass}">${result.buyCondition || 'New'}</div>
                    </div>
                    <div class="sell-info">
                        <div class="marketplace">Sell on ${result.sellMarketplace}</div>
                        <div class="price">$${result.sellPrice.toFixed(2)}</div>
                        <div class="condition ${sellConditionClass}">${result.sellCondition || 'New'}</div>
                    </div>
                </div>
                
                <div class="profit-info">
                    <div class="profit">Profit: $${result.profit.toFixed(2)}</div>
                    <div class="profit-percentage">ROI: ${result.profitPercentage.toFixed(1)}%</div>
                    <div class="fees">
                        Fees: $${marketplaceFee.toFixed(2)} • 
                        Shipping: $${shippingFee.toFixed(2)}
                    </div>
                </div>
                
                <div class="confidence">
                    <div class="confidence-bar">
                        <div class="confidence-fill" style="width: ${result.similarity || 0}%"></div>
                    </div>
                    <div class="confidence-text">${result.similarity || 0}% match</div>
                </div>
            </div>
            <div class="card-actions">
                <a href="${result.buyLink}" target="_blank" class="btn btn-outline">View Buy</a>
                <a href="${result.sellLink}" target="_blank" class="btn btn-primary">View Sell</a>
            </div>
        `;
        
        return card;
    }

    // Get condition class
    function getConditionClass(condition) {
        if (!condition) return '';
        
        condition = condition.toLowerCase();
        if (condition.includes('new') || condition === 'mint' || condition === 'sealed') {
            return 'condition-new';
        } else {
            return 'condition-used';
        }
    }

    // Show error message
    function showError(message) {
        // Create toast notification
        const toast = document.createElement('div');
        toast.className = 'toast error';
        toast.textContent = message;
        
        // Add to document
        document.body.appendChild(toast);
        
        // Remove after 5 seconds
        setTimeout(() => {
            if (document.body.contains(toast)) {
                toast.style.opacity = '0';
                
                // Remove after fade
                setTimeout(() => {
                    if (document.body.contains(toast)) {
                        document.body.removeChild(
// FlipHawk Scan Page JavaScript (continued)
                setTimeout(() => {
                    if (document.body.contains(toast)) {
                        document.body.removeChild(toast);
                    }
                }, 300);
            }
        }, 5000);
    }
});
