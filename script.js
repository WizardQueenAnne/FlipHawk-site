// FlipHawk Frontend Script
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
    
    // Initialize
    initEventListeners();
    
    // Set up event listeners
    function initEventListeners() {
        // Category selection
        categoryCards.forEach(card => {
            card.addEventListener('click', function() {
                if (scanInProgress) return; // Prevent changing category during scan
                
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
    
    // Show subcategories for selected category
    function showSubcategories(category) {
        // Fetch subcategories from backend
        fetch('/api/v1/categories/subcategories', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                category: category
            })
        })
        .then(response => response.json())
        .then(data => {
            // Clear previous subcategories
            subcategoryGrid.innerHTML = '';
            
            // Get subcategories from response
            const subcategories = data.subcategories || [];
            
            // Create subcategory chips
            subcategories.forEach(subcategory => {
                const chip = document.createElement('div');
                chip.className = 'subcategory-chip';
                chip.textContent = subcategory;
                chip.addEventListener('click', () => toggleSubcategory(chip, subcategory));
                subcategoryGrid.appendChild(chip);
            });
            
            // Show subcategory panel
            subcategoryPanel.style.display = 'block';
            
            // Reset selections
            selectedSubcategories = [];
            updateSelectedCount();
            updateSearchButton();
            
            // Scroll to subcategories
            subcategoryPanel.scrollIntoView({ behavior: 'smooth' });
        })
        .catch(error => {
            console.error('Error fetching subcategories:', error);
            
            // Fallback to local data if API call fails
            const fallbackSubcategories = getFallbackSubcategories(category);
            
            // Clear and recreate subcategories
            subcategoryGrid.innerHTML = '';
            fallbackSubcategories.forEach(subcategory => {
                const chip = document.createElement('div');
                chip.className = 'subcategory-chip';
                chip.textContent = subcategory;
                chip.addEventListener('click', () => toggleSubcategory(chip, subcategory));
                subcategoryGrid.appendChild(chip);
            });
            
            // Show subcategory panel
            subcategoryPanel.style.display = 'block';
            
            // Reset selections
            selectedSubcategories = [];
            updateSelectedCount();
            updateSearchButton();
        });
    }
    
    // Fallback subcategories if API call fails
    function getFallbackSubcategories(category) {
        const fallbackData = {
            "Tech": ["Headphones", "Keyboards", "Graphics Cards", "CPUs", "Laptops", "Monitors", "SSDs", "Routers", "Vintage Tech"],
            "Collectibles": ["Pokémon", "Magic: The Gathering", "Yu-Gi-Oh", "Funko Pops", "Sports Cards", "Comic Books", "Action Figures", "LEGO Sets"],
            "Vintage Clothing": ["Jordans", "Nike Dunks", "Vintage Tees", "Band Tees", "Denim Jackets", "Designer Brands", "Carhartt", "Patagonia"],
            "Antiques": ["Coins", "Watches", "Cameras", "Typewriters", "Vinyl Records", "Vintage Tools", "Old Maps"],
            "Gaming": ["Consoles", "Game Controllers", "Rare Games", "Arcade Machines", "Handhelds", "Gaming Headsets", "VR Gear"],
            "Music Gear": ["Electric Guitars", "Guitar Pedals", "Synthesizers", "Vintage Amps", "Microphones", "DJ Equipment"],
            "Tools & DIY": ["Power Tools", "Hand Tools", "Welding Equipment", "Toolboxes", "Measuring Devices", "Woodworking Tools"],
            "Outdoors & Sports": ["Bikes", "Skateboards", "Scooters", "Camping Gear", "Hiking Gear", "Fishing Gear", "Snowboards"]
        };
        
        return fallbackData[category] || [];
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
        selectedCount.textContent = `${selectedSubcategories.length} subcategories selected`;
    }
    
    // Update search button state based on selections
    function updateSearchButton() {
        if (selectedSubcategories.length > 0) {
            searchButton.classList.add('active');
            searchButton.disabled = false;
        } else {
            searchButton.classList.remove('active');
            searchButton.disabled = true;
        }
    }
    
    // Start scan function
    function startScan() {
        // Check if category and subcategories are selected
        if (!selectedCategory || selectedSubcategories.length === 0) {
            showToast('Please select a category and at least one subcategory', 'error');
            return;
        }
        
        // Set scan in progress
        scanInProgress = true;
        scanAborted = false;
        
        // Clear previous results
        resultsContainer.innerHTML = '';
        
        // Show loading indicators
        loadingSpinner.style.display = 'block';
        progressContainer.style.display = 'block';
        scanStatus.style.display = 'block';
        scanStatus.textContent = 'Initializing scan...';
        progressBar.style.width = '0%';
        
        // Update search button to be an abort button
        searchButton.textContent = 'Cancel Scan';
        searchButton.classList.add('loading');
        
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
                throw new Error(`Failed to start scan: ${response.status} ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            // Get the scan ID
            const scanId = data.meta.scan_id;
            
            if (!scanId) {
                throw new Error('No scan ID returned from server');
            }
            
            // Start polling for progress
            pollScanProgress(scanId);
        })
        .catch(error => {
            console.error('Error starting scan:', error);
            
            // Reset scan state
            scanInProgress = false;
            searchButton.textContent = 'Begin Resale Search';
            searchButton.classList.remove('loading');
            
            // Hide loading indicators
            loadingSpinner.style.display = 'none';
            progressContainer.style.display = 'none';
            
            // Show error message
            scanStatus.textContent = `Error: ${error.message}`;
            scanStatus.style.color = 'var(--primary-color)';
            scanStatus.style.display = 'block';
            
            // Reset after a delay
            setTimeout(() => {
                scanStatus.style.display = 'none';
                scanStatus.style.color = 'var(--text-color)';
            }, 5000);
        });
    }
    
    // Poll for scan progress
    function pollScanProgress(scanId) {
        let pollCount = 0;
        const maxPolls = 30; // Maximum number of polls (30 polls at 2 second intervals = 1 minute max)
        
        const pollInterval = setInterval(() => {
            // Check if scan has been aborted
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
            
            // Check if maximum polls reached
            if (pollCount > maxPolls) {
                clearInterval(pollInterval);
                
                // Just get results anyway
                fetchScanResults(scanId);
                return;
            }
            
            // Poll for scan progress
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
                
                // Update status message based on status
                const status = progressData.status || 'processing';
                updateStatusMessage(status, progress);
                
                // Check if scan is complete
                if (progress >= 100 || ['completed', 'completed_no_results', 'failed'].includes(status)) {
                    clearInterval(pollInterval);
                    
                    // Fetch the results
                    fetchScanResults(scanId);
                }
            })
            .catch(error => {
                console.error('Error polling scan progress:', error);
                
                // Don't stop polling on error, just continue
                // Simulate progress to provide feedback to user
                const currentWidth = progressBar.style.width || '0%';
                const currentProgress = parseInt(currentWidth) || 0;
                
                // Increment by 5% but don't go over 95%
                const newProgress = Math.min(95, currentProgress + 5);
                progressBar.style.width = `${newProgress}%`;
                
                // Update status message
                if (newProgress < 30) {
                    scanStatus.textContent = 'Connecting to marketplace scrapers...';
                } else if (newProgress < 50) {
                    scanStatus.textContent = 'Searching Amazon marketplace...';
                } else if (newProgress < 70) {
                    scanStatus.textContent = 'Searching eBay marketplace...';
                } else if (newProgress < 85) {
                    scanStatus.textContent = 'Finding matching products across marketplaces...';
                } else {
                    scanStatus.textContent = 'Calculating profit margins...';
                }
            });
        }, 2000); // Poll every 2 seconds
    }
    
    // Fetch scan results
    function fetchScanResults(scanId) {
        fetch(`/api/v1/scan/${scanId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`Failed to get scan results: ${response.status} ${response.statusText}`);
            }
            return response.json();
        })
        .then(resultsData => {
            // Process the results
            const opportunities = resultsData.arbitrage_opportunities || [];
            
            // Display the results
            displayResults(opportunities);
            
            // Reset scan state
            scanInProgress = false;
            searchButton.textContent = 'Begin Resale Search';
            searchButton.classList.remove('loading');
            
            // Hide loading indicators
            loadingSpinner.style.display = 'none';
            progressContainer.style.display = 'none';
            scanStatus.style.display = 'none';
        })
        .catch(error => {
            console.error('Error fetching scan results:', error);
            
            // Show error message
            scanStatus.textContent = `Error retrieving results: ${error.message}`;
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
    
    // Update status message based on scan status
    function updateStatusMessage(status, progress) {
        let message = '';
        
        switch (status) {
            case 'initializing':
                message = 'Initializing scan...';
                break;
            case 'searching marketplaces':
                if (progress < 30) {
                    message = 'Starting marketplace scrapers...';
                } else if (progress < 50) {
                    message = 'Searching Amazon marketplace...';
                } else if (progress < 70) {
                    message = 'Searching eBay marketplace...';
                } else {
                    message = 'Searching multiple marketplaces...';
                }
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
                message = 'Scan failed. Please try again.';
                break;
            default:
                message = `Scanning for ${selectedSubcategories.join(', ')}...`;
        }
        
        scanStatus.textContent = message;
    }
    
    // Display scan results
    function displayResults(opportunities) {
        // Clear previous results
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
        
        // Create result cards for each opportunity
        const opportunitiesGrid = document.createElement('div');
        opportunitiesGrid.className = 'opportunities';
        
        opportunities.forEach(opportunity => {
            const card = document.createElement('div');
            card.className = 'opportunity-card';
            
            // Get image URL
            const imageUrl = opportunity.buyImage || opportunity.image_url || '';
            
            // Create image element if available
            let imageHtml = '';
            if (imageUrl) {
                imageHtml = `<img src="${imageUrl}" alt="${opportunity.buyTitle}" style="width: 100%; height: auto; margin-bottom: 10px; border-radius: 4px;">`;
            }
            
            // Format confidence for display
            const confidence = opportunity.confidence || opportunity.similarity || 80;
            
            // Handle fees information
            let marketplaceFee = 0;
            let shippingFee = 0;
            
            if (opportunity.fees) {
                marketplaceFee = opportunity.fees.marketplace || 0;
                shippingFee = opportunity.fees.shipping || 0;
            }
            
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
                            <span class="condition-badge condition-${opportunity.buyCondition.toLowerCase().replace(/\s+/g, '-')}">${opportunity.buyCondition}</span>
                        </div>
                        <div class="sell-info">
                            <div class="marketplace">Sell on ${opportunity.sellMarketplace}</div>
                            <div class="price">$${opportunity.sellPrice.toFixed(2)}</div>
                            <span class="condition-badge condition-${opportunity.sellCondition.toLowerCase().replace(/\s+/g, '-')}">${opportunity.sellCondition}</span>
                        </div>
                    </div>
                    
                    <div class="profit-details">
                        <div class="profit">Profit: ${opportunity.profit.toFixed(2)}</div>
                        <div class="profit-percentage">ROI: ${opportunity.profitPercentage.toFixed(2)}%</div>
                        <div class="fees">
                            Fees: ${marketplaceFee.toFixed(2)} • Shipping: ${shippingFee.toFixed(2)}
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
    
    // Function to show toast notification
    function showToast(message, type = 'error') {
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
