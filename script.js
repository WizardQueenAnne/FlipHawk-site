// Updated scan function to properly handle real scanning with polling
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
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + (localStorage.getItem('token') || 'guest-token')
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
        const maxPolls = 60; // Maximum number of polls (30 seconds * 60 = 30 minutes max)
        
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
            fetch(`/api/progress/${scanId}`, {
                headers: {
                    'Authorization': 'Bearer ' + (localStorage.getItem('token') || 'guest-token')
                }
            })
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
                if (progress >= 100 && (status === 'completed' || status === 'completed_no_results' || status === 'failed')) {
                    clearInterval(pollInterval);
                    
                    // Fetch the final results
                    fetch(`/api/v1/scan/${scanId}`, {
                        headers: {
                            'Authorization': 'Bearer ' + (localStorage.getItem('token') || 'guest-token')
                        }
                    })
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
        scanStatus.textContent = 'Error connecting to scanning service. Please try again later. Details: ' + error.message;
        scanStatus.style.color = 'var(--primary-color)';
        scanStatus.style.display = 'block';
        
        setTimeout(() => {
            scanStatus.style.display = 'none';
            scanStatus.style.color = 'var(--text-color)';
        }, 7000);
    });
}

// Function to update status message based on scan status
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
                message = 'Scanning Facebook Marketplace...';
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

// Updated display results function to handle the actual data format from the backend
function displayResults(results) {
    // Clear previous results
    resultsContainer.innerHTML = '';
    
    if (!results || results.length === 0) {
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
        <h2>Found ${results.length} Opportunities</h2>
        <p>Category: ${selectedCategory} • Subcategories: ${selectedSubcategories.join(', ')}</p>
    `;
    
    resultsContainer.appendChild(resultsHeader);
    
    // Create result cards for each opportunity
    results.forEach(result => {
        const resultCard = document.createElement('div');
        resultCard.className = 'result-card';
        
        // Create image element if available
        let imageHtml = '';
        if (result.image_url) {
            imageHtml = `<img src="${result.image_url}" alt="${result.title || result.buyTitle}" class="result-image">`;
        } else if (result.buyImage) {
            imageHtml = `<img src="${result.buyImage}" alt="${result.title || result.buyTitle}" class="result-image">`;
        }
        
        // Prepare the display values - handle both possible response formats
        const title = result.buyTitle || result.title || '';
        const buyPrice = result.buyPrice || result.price || 0;
        const sellPrice = result.sellPrice || result.sell_price || 0;
        const profit = result.profit || (sellPrice - buyPrice);
        const profitPercentage = result.profitPercentage || (profit * 100 / buyPrice);
        const buyLink = result.buyLink || result.buy_link || '#';
        const sellLink = result.sellLink || result.sell_link || '#';
        const buyMarketplace = result.buyMarketplace || result.buy_marketplace || 'Unknown';
        const sellMarketplace = result.sellMarketplace || result.sell_marketplace || 'Unknown';
        const subcategory = result.subcategory || selectedSubcategories[0];
        const confidence = result.confidence || result.similarity_score || 85;
        const buyCondition = result.buyCondition || 'New';
        const sellCondition = result.sellCondition || 'New';
        
        // Handle fee data
        let marketplaceFee = 0;
        let shippingFee = 0;
        
        if (result.fees) {
            marketplaceFee = result.fees.marketplace || 0;
            shippingFee = result.fees.shipping || 0;
        } else {
            // Estimate fees if not provided
            marketplaceFee = sellPrice * 0.1; // Assume 10% marketplace fee
            shippingFee = 5; // Assume $5 shipping
        }
        
        resultCard.innerHTML = `
            ${imageHtml}
            <div class="result-details">
                <div class="profit-badge">$${profit.toFixed(2)} profit</div>
                <h3>${title}</h3>
                <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                    <div>
                        <strong>Buy on ${buyMarketplace}</strong><br>
                        Price: $${buyPrice.toFixed(2)}<br>
                        Condition: ${buyCondition}
                    </div>
                    <div>
                        <strong>Sell on ${sellMarketplace}</strong><br>
                        Price: $${sellPrice.toFixed(2)}<br>
                        Condition: ${sellCondition}
                    </div>
                </div>
                <div style="background-color: rgba(0,0,0,0.05); padding: 10px; border-radius: 8px; margin-bottom: 10px;">
                    <strong>Profit: $${profit.toFixed(2)}</strong> (ROI: ${profitPercentage.toFixed(1)}%)<br>
                    Marketplace Fee: $${marketplaceFee.toFixed(2)} | Shipping: $${shippingFee.toFixed(2)}<br>
                    Match Confidence: ${confidence}%
                </div>
                <div style="font-size: 0.9em; color: #666;">Category: ${selectedCategory} > ${subcategory}</div>
                <div style="margin-top: 15px; display: flex; gap: 10px;">
                    <a href="${buyLink}" target="_blank" style="
                        background: var(--primary-color);
                        color: white;
                        padding: 8px 15px;
                        border-radius: 8px;
                        text-decoration: none;
                        font-weight: 600;
                    ">Buy Now</a>
                    <a href="${sellLink}" target="_blank" style="
                        background: var(--secondary-color);
                        color: white;
                        padding: 8px 15px;
                        border-radius: 8px;
                        text-decoration: none;
                        font-weight: 600;
                    ">Sell Here</a>
                </div>
            </div>
        `;
        
        resultsContainer.appendChild(resultCard);
    });
    
    // Scroll to results
    resultsHeader.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// Updated start scan function to use the updated scanning function
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
    
    // Call the updated scan function with real data
    scanWithProgressUpdates(requestData);
}
