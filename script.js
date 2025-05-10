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
    let scanAborted = false;
    let currentScanId = null;
    let pollingInterval = null;
    
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
                
                // Stop polling
                if (pollingInterval) {
                    clearInterval(pollingInterval);
                    pollingInterval = null;
                }
                
                // Reset scan state
                setTimeout(() => {
                    scanInProgress = false;
                    searchButton.textContent = 'Begin Resale Search';
                    searchButton.classList.remove('loading');
                    searchButton.classList.add('active');
                    
                    // Hide loading indicators
                    loadingSpinner.style.display = 'none';
                    progressContainer.style.display = 'none';
                    scanStatus.style.display = 'none';
                }, 1000);
                
                return;
            }
            
            startScan();
        });
    }
    
    // Show subcategories for selected category
    function showSubcategories(category) {
        // Fetch subcategories from backend
        fetch('/api/categories/subcategories', {
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
    
    // Start scan function with real-time progress reporting
    function startScan() {
        // Check if category and subcategories are selected
        if (!selectedCategory || selectedSubcategories.length === 0) {
            showToast('Please select a category and at least one subcategory', 'error');
            return;
        }
        
        // Set scan in progress state
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
        searchButton.disabled = false;
        searchButton.textContent = 'Cancel Scan';
        searchButton.classList.add('loading');
        searchButton.classList.remove('active');
        
        // Prepare the request data
        const requestData = {
            category: selectedCategory,
            subcategories: selectedSubcategories,
            max_results: 100
        };
        
        // Call the scan API
        fetch('/api/scan', {
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
            const scanId = data.meta?.scan_id;
            
            if (!scanId) {
                throw new Error('No scan ID returned from server');
            }
            
            // Store current scan ID
            currentScanId = scanId;
            
            // Start polling for progress
            pollScanProgress(scanId);
        })
        .catch(error => {
            console.error('Error starting scan:', error);
            
            // Reset scan state
            scanInProgress = false;
            searchButton.textContent = 'Begin Resale Search';
            searchButton.classList.remove('loading');
            searchButton.classList.add('active');
            
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
        // Clear any existing polling interval
        if (pollingInterval) {
            clearInterval(pollingInterval);
        }
        
        let lastProgress = 0;
        let pollCount = 0;
        const maxPolls = 300; // Maximum number of polls (300 polls at 1 second intervals = 5 minutes max)
        
        pollingInterval = setInterval(() => {
            // Check if scan has been aborted
            if (scanAborted) {
                clearInterval(pollingInterval);
                pollingInterval = null;
                return;
            }
            
            // Increment poll count
            pollCount++;
            
            // Check if maximum polls reached
            if (pollCount > maxPolls) {
                clearInterval(pollingInterval);
                pollingInterval = null;
                
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
                lastProgress = progress;
                
                // Update status message based on status
                const status = progressData.status || 'processing';
                updateStatusMessage(status, progress);
                
                // Check if scan is complete
                if (progress >= 100 || ['completed', 'completed_no_results', 'failed', 'error', 'cancelled'].includes(status)) {
                    clearInterval(pollingInterval);
                    pollingInterval = null;
                    
                    if (!scanAborted) {
                        // Fetch the results
                        fetchScanResults(scanId);
                    }
                }
            })
            .catch(error => {
                console.error('Error polling scan progress:', error);
                
                // Don't stop polling on error, just continue
                // Increment progress slightly to show activity
                if (lastProgress < 95) {
                    lastProgress += 2;
                    progressBar.style.width = `${lastProgress}%`;
                    
                    // Update status message
                    if (lastProgress < 30) {
                        scanStatus.textContent = 'Connecting to marketplace scrapers...';
                    } else if (lastProgress < 50) {
                        scanStatus.textContent = 'Searching Amazon marketplace...';
                    } else if (lastProgress < 70) {
                        scanStatus.textContent = 'Searching eBay marketplace...';
                    } else if (lastProgress < 85) {
                        scanStatus.textContent = 'Finding matching products across marketplaces...';
                    } else {
                        scanStatus.textContent = 'Calculating profit margins...';
                    }
                }
            });
        }, 1000); // Poll every 1 second
    }
    
    // Update status message based on scan status
    function updateStatusMessage(status, progress) {
        let message = '';
        
        switch (status) {
            case 'initializing':
                message = 'Initializing scan...';
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
// FlipHawk Frontend Script (continued)
            case 'searching facebook':
                message = 'Searching Facebook marketplace...';
                break;
            case 'processing results':
                message = 'Processing results...';
                break;
            case 'finding opportunities':
                message = 'Finding arbitrage opportunities...';
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
        fetch(`/api/scan/${scanId}`)
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
            currentScanId = null;
            searchButton.textContent = 'Begin Resale Search';
            searchButton.classList.remove('loading');
            searchButton.classList.add('active');
            
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
                currentScanId = null;
                searchButton.textContent = 'Begin Resale Search';
                searchButton.classList.remove('loading');
                searchButton.classList.add('active');
                
                // Hide loading indicators
                loadingSpinner.style.display = 'none';
                progressContainer.style.display = 'none';
                scanStatus.style.display = 'none';
                scanStatus.style.color = 'var(--text-color)';
            }, 5000);
        });
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
        opportunitiesGrid.style.display = 'grid';
        opportunitiesGrid.style.gridTemplateColumns = 'repeat(auto-fill, minmax(300px, 1fr))';
        opportunitiesGrid.style.gap = '20px';
        
        opportunities.forEach(opportunity => {
            const card = document.createElement('div');
            card.className = 'opportunity-card';
            card.style.background = 'var(--card-bg)';
            card.style.borderRadius = '15px';
            card.style.overflow = 'hidden';
            card.style.transition = 'transform 0.3s';
            
            // Get image URL for the card
            const imageUrl = opportunity.buyImage || opportunity.sellImage || '';
            
            // Format the card content
            card.innerHTML = createOpportunityCardHtml(opportunity, imageUrl);
            
            opportunitiesGrid.appendChild(card);
        });
        
        resultsContainer.appendChild(opportunitiesGrid);
        
        // Scroll to results
        resultsHeader.scrollIntoView({ behavior: 'smooth' });
    }
    
    // Helper function to create opportunity card HTML
    function createOpportunityCardHtml(opportunity, imageUrl) {
        // Get all necessary data with fallbacks for missing fields
        const buyPrice = opportunity.buyPrice || 0;
        const sellPrice = opportunity.sellPrice || 0;
        const profit = opportunity.profit || (sellPrice - buyPrice);
        const profitPercentage = opportunity.profitPercentage || ((profit / buyPrice) * 100);
        const buyCondition = opportunity.buyCondition || 'Unknown';
        const sellCondition = opportunity.sellCondition || 'Unknown';
        const buyMarketplace = opportunity.buyMarketplace || 'Unknown';
        const sellMarketplace = opportunity.sellMarketplace || 'Unknown';
        const buyLink = opportunity.buyLink || '#';
        const sellLink = opportunity.sellLink || '#';
        const buyTitle = opportunity.buyTitle || 'Unknown Item';
        const sellTitle = opportunity.sellTitle || 'Unknown Item';
        
        // Calculate fees
        let marketplaceFee = 0;
        let shippingFee = 0;
        
        if (opportunity.fees) {
            marketplaceFee = opportunity.fees.marketplace || 0;
            shippingFee = opportunity.fees.shipping || 0;
        }
        
        // Calculate confidence
        const confidence = opportunity.confidence || opportunity.similarity || 80;
        
        // Create image HTML if available
        let imageHtml = '';
        if (imageUrl) {
            imageHtml = `<img src="${imageUrl}" alt="${buyTitle}" style="width: 100%; height: auto; max-height: 200px; object-fit: contain; margin-bottom: 10px; border-radius: 4px;">`;
        }
        
        // Create buy condition and sell condition classes
        const buyConditionClass = getConditionClass(buyCondition);
        const sellConditionClass = getConditionClass(sellCondition);
        
        // Create the HTML
        return `
            <div style="background-color: var(--primary-color); padding: 15px; color: white;">
                <h3 style="margin: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-size: 16px;">${buyTitle}</h3>
            </div>
            <div style="padding: 15px;">
                ${imageHtml}
                <div style="display: flex; justify-content: space-between; margin-bottom: 15px;">
                    <div style="flex: 1;">
                        <div style="font-size: 12px; color: #aaa;">Buy on ${buyMarketplace}</div>
                        <div style="font-size: 18px; font-weight: bold; margin: 5px 0; color: var(--primary-color);">$${buyPrice.toFixed(2)}</div>
                        <span style="display: inline-block; padding: 3px 8px; border-radius: 3px; font-size: 12px; background-color: rgba(78, 205, 196, 0.2); color: var(--secondary-color);">${buyCondition}</span>
                    </div>
                    <div style="flex: 1;">
                        <div style="font-size: 12px; color: #aaa;">Sell on ${sellMarketplace}</div>
                        <div style="font-size: 18px; font-weight: bold; margin: 5px 0; color: var(--secondary-color);">$${sellPrice.toFixed(2)}</div>
                        <span style="display: inline-block; padding: 3px 8px; border-radius: 3px; font-size: 12px; background-color: rgba(255, 230, 109, 0.2); color: var(--accent-color);">${sellCondition}</span>
                    </div>
                </div>
                
                <div style="background-color: rgba(255,255,255,0.05); padding: 10px; border-radius: 5px; margin-bottom: 15px;">
                    <div style="font-size: 18px; font-weight: bold; color: #4CAF50;">Profit: $${profit.toFixed(2)}</div>
                    <div style="color: #4CAF50;">ROI: ${profitPercentage.toFixed(2)}%</div>
                    <div style="font-size: 12px; color: #aaa; margin-top: 5px;">
                        Fees: $${marketplaceFee.toFixed(2)} • Shipping: $${shippingFee.toFixed(2)}
                    </div>
                </div>
                
                <div style="margin-top: 10px;">
                    <div style="height: 6px; background-color: rgba(255,255,255,0.1); border-radius: 3px; overflow: hidden; margin-bottom: 5px;">
                        <div style="height: 100%; background-color: var(--primary-color); width: ${confidence}%;"></div>
                    </div>
                    <div style="font-size: 12px; color: #aaa; text-align: right;">${confidence}% match</div>
                </div>
            </div>
            <div style="display: flex; justify-content: space-between; padding: 15px; border-top: 1px solid rgba(255,255,255,0.05);">
                <a href="${buyLink}" target="_blank" style="padding: 8px 15px; border-radius: 5px; text-decoration: none; font-weight: bold; font-size: 14px; border: 1px solid var(--primary-color); color: var(--primary-color);">View Buy</a>
                <a href="${sellLink}" target="_blank" style="padding: 8px 15px; border-radius: 5px; text-decoration: none; font-weight: bold; font-size: 14px; background-color: var(--primary-color); color: white;">View Sell</a>
            </div>
        `;
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
