// static/js/scan.js - Updated file

document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const categorySelect = document.getElementById('category-select');
    const subcategoryContainer = document.getElementById('subcategory-container');
    const startScanButton = document.getElementById('start-scan');
    const scanStatusContainer = document.getElementById('scan-status-container');
    const progressBar = document.getElementById('progress-bar');
    const statusText = document.getElementById('status-text');
    const resultsContainer = document.getElementById('results-container');
    
    // Global variables
    let selectedSubcategories = [];
    let scanInProgress = false;
    let currentScanId = null;
    let pollingInterval = null;
    
    // Initialize
    init();
    
    // Set up initial state
    function init() {
        // Load categories
        loadCategories();
        
        // Set up event listeners
        setupEventListeners();
        
        console.log("FlipHawk scan page initialized");
    }
    
    // Set up event listeners
    function setupEventListeners() {
        // Category selection change
        if (categorySelect) {
            categorySelect.addEventListener('change', function() {
                loadSubcategories(this.value);
            });
        }
        
        // Start scan button
        if (startScanButton) {
            startScanButton.addEventListener('click', function() {
                if (scanInProgress) {
                    // Cancel scan
                    cancelScan();
                } else {
                    // Start scan
                    startScan();
                }
            });
        }
    }
    
    // Load available categories
    function loadCategories() {
        fetch('/api/categories')
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (categorySelect) {
                    // Clear current options except the placeholder
                    while (categorySelect.options.length > 1) {
                        categorySelect.remove(1);
                    }
                    
                    // Add new options
                    data.categories.forEach(category => {
                        const option = document.createElement('option');
                        option.value = category;
                        option.textContent = category;
                        categorySelect.appendChild(option);
                    });
                }
            })
            .catch(error => {
                console.error('Error loading categories:', error);
                showToast('Failed to load categories: ' + error.message, 'error');
            });
    }
    
    // Load subcategories for a category
    function loadSubcategories(category) {
        if (!category) return;
        
        fetch(`/api/categories/${encodeURIComponent(category)}/subcategories`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (subcategoryContainer) {
                    // Clear current subcategories
                    subcategoryContainer.innerHTML = '';
                    
                    // Add new subcategories
                    data.subcategories.forEach(subcategory => {
                        const checkbox = document.createElement('div');
                        checkbox.className = 'subcategory-checkbox';
                        checkbox.innerHTML = `
                            <input type="checkbox" id="subcategory-${subcategory.replace(/\s+/g, '-').toLowerCase()}" value="${subcategory}">
                            <label for="subcategory-${subcategory.replace(/\s+/g, '-').toLowerCase()}">${subcategory}</label>
                        `;
                        
                        // Add event listener
                        const input = checkbox.querySelector('input');
                        input.addEventListener('change', function() {
                            if (this.checked) {
                                if (!selectedSubcategories.includes(this.value)) {
                                    selectedSubcategories.push(this.value);
                                }
                            } else {
                                selectedSubcategories = selectedSubcategories.filter(s => s !== this.value);
                            }
                            
                            updateStartScanButton();
                        });
                        
                        subcategoryContainer.appendChild(checkbox);
                    });
                    
                    // Show subcategory container
                    subcategoryContainer.style.display = 'grid';
                    
                    // Reset selected subcategories
                    selectedSubcategories = [];
                    updateStartScanButton();
                }
            })
            .catch(error => {
                console.error('Error loading subcategories:', error);
                showToast('Failed to load subcategories: ' + error.message, 'error');
            });
    }
    
    // Update start scan button state
    function updateStartScanButton() {
        if (startScanButton) {
            if (selectedSubcategories.length > 0) {
                startScanButton.disabled = false;
            } else {
                startScanButton.disabled = true;
            }
        }
    }
    
    // Start scan
    function startScan() {
        // Get selected category
        const category = categorySelect.value;
        
        // Validate selections
        if (!category) {
            showToast('Please select a category', 'error');
            return;
        }
        
        if (selectedSubcategories.length === 0) {
            showToast('Please select at least one subcategory', 'error');
            return;
        }
        
        // Set scan in progress
        scanInProgress = true;
        
        // Update UI
        startScanButton.textContent = 'Cancel Scan';
        scanStatusContainer.style.display = 'block';
        progressBar.style.width = '0%';
        statusText.textContent = 'Starting scan...';
        resultsContainer.innerHTML = '';
        
        // Prepare request data
        const requestData = {
            category: category,
            subcategories: selectedSubcategories,
            max_results: 100
        };
        
        console.log('Starting scan with data:', requestData);
        
        // Send request
        fetch('/api/v1/scan', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // Check for error
            if (data.error) {
                throw new Error(data.error);
            }
            
            // Get scan ID
            currentScanId = data.meta?.scan_id;
            
            if (!currentScanId) {
                throw new Error('No scan ID received');
            }
            
            console.log(`Scan started with ID: ${currentScanId}`);
            
            // Start polling for progress
            startPolling(currentScanId);
        })
        .catch(error => {
            console.error('Error starting scan:', error);
            resetScanState();
            showToast(`Error: ${error.message}`, 'error');
        });
    }
    
    // Start polling for scan progress
    function startPolling(scanId) {
        // Clear any existing interval
        if (pollingInterval) {
            clearInterval(pollingInterval);
        }
        
        let consecutiveErrors = 0;
        const maxErrors = 5;
        
        pollingInterval = setInterval(() => {
            if (!scanInProgress) {
                clearInterval(pollingInterval);
                pollingInterval = null;
                return;
            }
            
            fetch(`/api/progress/${scanId}`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    return response.json();
                })
                .then(data => {
                    // Reset consecutive errors counter
                    consecutiveErrors = 0;
                    
                    // Update progress
                    const progress = data.progress || 0;
                    progressBar.style.width = `${progress}%`;
                    
                    // Update status text
                    const status = data.status || '';
                    updateStatusText(status, progress);
                    
                    // Check if scan is complete
                    if (progress >= 100 || ['completed', 'error'].includes(status)) {
                        // Stop polling
                        clearInterval(pollingInterval);
                        pollingInterval = null;
                        
                        // Get results
                        if (status === 'completed') {
                            fetchResults(scanId);
                        } else if (status === 'error') {
                            resetScanState();
                            showToast('An error occurred during scanning', 'error');
                        }
                    }
                })
                .catch(error => {
                    console.error('Error polling scan progress:', error);
                    consecutiveErrors++;
                    
                    // If too many consecutive errors, stop polling
                    if (consecutiveErrors >= maxErrors) {
                        clearInterval(pollingInterval);
                        pollingInterval = null;
                        resetScanState();
                        showToast(`Error: ${error.message}`, 'error');
                    }
                });
        }, 1000); // Poll every second
    }
    
    // Fetch scan results
    function fetchResults(scanId) {
        fetch(`/api/v1/scan/${scanId}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                // Check for error
                if (data.error) {
                    throw new Error(data.error);
                }
                
                // Display results
                displayResults(data);
                
                // Reset scan state
                resetScanState();
            })
            .catch(error => {
                console.error('Error fetching scan results:', error);
                resetScanState();
                showToast(`Error: ${error.message}`, 'error');
            });
    }
    
    // Display scan results
    function displayResults(data) {
        const opportunities = data.arbitrage_opportunities || [];
        const category = data.category || '';
        const subcategories = data.subcategories || [];
        
        console.log(`Displaying ${opportunities.length} opportunities`);
        
        // Clear results container
        resultsContainer.innerHTML = '';
        
        // Create header
        const header = document.createElement('h2');
        header.textContent = `Found ${opportunities.length} Opportunities`;
        resultsContainer.appendChild(header);
        
        const subheader = document.createElement('p');
        subheader.textContent = `Category: ${category} • Subcategories: ${subcategories.join(', ')}`;
        resultsContainer.appendChild(subheader);
        
        // Display no results message if needed
        if (opportunities.length === 0) {
            const noResults = document.createElement('div');
            noResults.className = 'no-results';
            noResults.innerHTML = '<p>No opportunities found. Try selecting different subcategories.</p>';
            resultsContainer.appendChild(noResults);
            return;
        }
        
        // Create results grid
        const resultsGrid = document.createElement('div');
        resultsGrid.className = 'results-grid';
        
        // Add each opportunity
        opportunities.forEach(opportunity => {
            const card = createOpportunityCard(opportunity);
            resultsGrid.appendChild(card);
        });
        
        resultsContainer.appendChild(resultsGrid);
    }
    
    // Create opportunity card
    function createOpportunityCard(opportunity) {
        const card = document.createElement('div');
        card.className = 'result-card';
        
        // Get condition classes
        const buyConditionClass = getConditionClass(opportunity.buyCondition);
        const sellConditionClass = getConditionClass(opportunity.sellCondition);
        
        // Format image URLs
        const buyImage = opportunity.buyImage || 'https://via.placeholder.com/200?text=No+Image';
        
        // Format numbers
        const buyPrice = typeof opportunity.buyPrice === 'number' ? opportunity.buyPrice.toFixed(2) : parseFloat(opportunity.buyPrice).toFixed(2);
        const sellPrice = typeof opportunity.sellPrice === 'number' ? opportunity.sellPrice.toFixed(2) : parseFloat(opportunity.sellPrice).toFixed(2);
        const profit = typeof opportunity.profit === 'number' ? opportunity.profit.toFixed(2) : parseFloat(opportunity.profit).toFixed(2);
        const profitPercentage = typeof opportunity.profitPercentage === 'number' ? opportunity.profitPercentage.toFixed(1) : parseFloat(opportunity.profitPercentage).toFixed(1);
        const marketplaceFee = opportunity.fees?.marketplace ? parseFloat(opportunity.fees.marketplace).toFixed(2) : '0.00';
        const shippingFee = opportunity.fees?.shipping ? parseFloat(opportunity.fees.shipping).toFixed(2) : '0.00';
        const similarity = opportunity.similarity || 0;
        
        // Create HTML
        card.innerHTML = `
            <div class="card-header">
                <h3>${opportunity.buyTitle}</h3>
            </div>
            <div class="card-image">
                <img src="${buyImage}" alt="${opportunity.buyTitle}" onerror="this.src='https://via.placeholder.com/200?text=No+Image'">
            </div>
            <div class="card-content">
                <div class="comparison">
                    <div class="buy-info">
                        <div class="marketplace">Buy on ${opportunity.buyMarketplace}</div>
                        <div class="price">$${buyPrice}</div>
                        <div class="condition ${buyConditionClass}">${opportunity.buyCondition || 'New'}</div>
                    </div>
                    <div class="sell-info">
                        <div class="marketplace">Sell on ${opportunity.sellMarketplace}</div>
                        <div class="price">$${sellPrice}</div>
                        <div class="condition ${sellConditionClass}">${opportunity.sellCondition || 'New'}</div>
                    </div>
                </div>
                
                <div class="profit-info">
                    <div class="profit">Profit: $${profit}</div>
                    <div class="profit-percentage">ROI: ${profitPercentage}%</div>
                    <div class="fees">
                        Fees: $${marketplaceFee} • 
                        Shipping: $${shippingFee}
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
    
    // Get condition class
    function getConditionClass(condition) {
        if (!condition) return 'condition-new';
        
        const lcCondition = condition.toLowerCase();
        if (lcCondition.includes('new') || lcCondition.includes('mint') || lcCondition.includes('sealed')) {
            return 'condition-new';
        } else {
            return 'condition-used';
        }
    }
    
    // Update status text based on scan status
    function updateStatusText(status, progress) {
        let message = 'Processing...';
        
        switch (status) {
            case 'initializing':
                message = 'Initializing scan...';
                break;
            case 'running':
                message = 'Running scan...';
                break;
            case 'preparing to scan':
                message = 'Preparing to scan...';
                break;
            case 'searching amazon':
                message = 'Searching Amazon marketplace...';
                break;
            case 'amazon search completed':
                message = 'Amazon search completed, continuing...';
                break;
            case 'searching ebay':
                message = 'Searching eBay marketplace...';
                break;
            case 'ebay search completed':
                message = 'eBay search completed, continuing...';
                break;
            case 'searching facebook':
                message = 'Searching Facebook marketplace...';
                break;
            case 'facebook search completed':
                message = 'Facebook search completed, continuing...';
                break;
            case 'finding opportunities':
                message = 'Finding arbitrage opportunities...';
                break;
            case 'completed':
                message = 'Scan completed! Loading results...';
                break;
            case 'error':
                message = 'Error occurred during scan.';
                break;
            default:
                // Set dynamic message based on progress
                if (progress < 10) {
                    message = 'Starting scan...';
                } else if (progress < 30) {
                    message = 'Searching marketplaces...';
                } else if (progress < 60) {
                    message = 'Analyzing listings...';
                } else if (progress < 90) {
                    message = 'Finding opportunities...';
                } else {
                    message = 'Finalizing results...';
                }
        }
        
        statusText.textContent = message;
    }
    
    // Cancel current scan
    function cancelScan() {
        // Stop polling
        if (pollingInterval) {
            clearInterval(pollingInterval);
            pollingInterval = null;
        }
        
        // Reset state
        resetScanState();
        
        // Show message
        showToast('Scan cancelled', 'info');
    }
    
    // Reset scan state
    function resetScanState() {
        scanInProgress = false;
        currentScanId = null;
        
        // Reset UI
        startScanButton.textContent = 'Start Scan';
        scanStatusContainer.style.display = 'none';
    }
    
    // Show toast notification
    function showToast(message, type = 'info') {
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
        
        // Remove after timeout
        setTimeout(() => {
            if (document.body.contains(toast)) {
                document.body.removeChild(toast);
            }
        }, 3000);
    }
});
