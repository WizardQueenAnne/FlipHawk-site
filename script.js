// Updated scan function to communicate properly with the backend
function scanWithProgressUpdates(requestData) {
    // Simulate a multi-step scanning process for UI feedback
    const totalSteps = 100;
    let currentStep = 0;
    
    // Messages for different scanning stages
    const stageMessages = [
        { step: 0, message: 'Initializing marketplaces scanners...' },
        { step: 5, message: 'Connecting to Amazon...' },
        { step: 10, message: 'Connecting to eBay...' },
        { step: 15, message: 'Connecting to Facebook Marketplace...' },
        { step: 20, message: 'Connecting to other marketplaces...' },
        { step: 25, message: `Scanning for ${selectedSubcategories.join(', ')}...` },
        { step: 60, message: 'Finding matching products across platforms...' },
        { step: 80, message: 'Calculating potential profits...' },
        { step: 90, message: 'Preparing results...' },
        { step: 95, message: 'Finalizing scan...' }
    ];
    
    // Set up a progress interval to provide UI feedback
    scanProgressInterval = setInterval(() => {
        if (scanAborted) {
            clearInterval(scanProgressInterval);
            scanProgressInterval = null;
            return;
        }
        
        // Increment progress
        currentStep += Math.floor(Math.random() * 3) + 1;
        const progress = Math.min(currentStep, 95); // Cap at 95% until we get results
        
        // Update progress bar
        progressBar.style.width = `${progress}%`;
        
        // Update message based on current step
        for (let i = stageMessages.length - 1; i >= 0; i--) {
            if (progress >= stageMessages[i].step) {
                scanStatus.textContent = stageMessages[i].message;
                break;
            }
        }
        
        // Stop at 95% and wait for API response
        if (progress >= 95) {
            clearInterval(scanProgressInterval);
            scanProgressInterval = null;
        }
    }, 300);
    
    // Make the actual API call to the backend
    fetch('/api/v1/scan', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + (localStorage.getItem('token') || 'guest-token')
        },
        body: JSON.stringify(requestData)
    })
    .then(response => {
        // Clear progress interval if it's still running
        if (scanProgressInterval) {
            clearInterval(scanProgressInterval);
            scanProgressInterval = null;
        }
        
        // Complete the progress bar
        progressBar.style.width = '100%';
        
        if (!response.ok) {
            throw new Error(`Failed to connect to scanning service: ${response.status} ${response.statusText}`);
        }
        
        return response.json();
    })
    .then(data => {
        // Process and display results
        setTimeout(() => {
            // Use the arbitrage_opportunities array from the API response
            const opportunities = data.arbitrage_opportunities || [];
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

// Updated display results function to handle the format returned by the backend
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
        const title = result.title || result.buyTitle || '';
        const buyPrice = result.buyPrice || result.price || 0;
        const sellPrice = result.sellPrice || result.sell_price || 0;
        const profit = result.netProfit || result.profit || (sellPrice - buyPrice);
        const profitPercentage = result.netProfitPercentage || result.profitPercentage || (profit * 100 / buyPrice);
        const buyLink = result.buyLink || result.buy_link || '#';
        const sellLink = result.sellLink || result.sell_link || '#';
        const buyMarketplace = result.buyMarketplace || result.buy_marketplace || 'Unknown';
        const sellMarketplace = result.sellMarketplace || result.sell_marketplace || 'Unknown';
        const subcategory = result.subcategory || selectedSubcategories[0];
        const confidence = result.confidence || result.similarity || 85;
        
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
                <p>Buy for: $${buyPrice.toFixed(2)} from ${buyMarketplace} | Sell for: $${sellPrice.toFixed(2)} on ${sellMarketplace}</p>
                <p>ROI: ${profitPercentage.toFixed(1)}% | Similarity Confidence: ${confidence}%</p>
                <p>Category: ${selectedCategory} > ${subcategory}</p>
                <p>Marketplace Fee: $${marketplaceFee.toFixed(2)} | Shipping: $${shippingFee.toFixed(2)}</p>
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
                    ">View Listing</a>
                </div>
            </div>
        `;
        
        resultsContainer.appendChild(resultCard);
    });
    
    // Scroll to results
    resultsHeader.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// Updated start scan function to use the new scan function
function startScan() {
    // Check if category and subcategories are selected
    if (!selectedCategory || selectedSubcategories.length === 0) {
        showToast('Please select a category and at least one subcategory', 'error');
        return;
    }
    
    // Set scan in progress flag
    scanInProgress = true;
    scanAborted = false;
    
    // Clear previous results and show loading indicators
    resultsContainer.innerHTML = '';
    loadingSpinner.style.display = 'block';
    progressContainer.style.display = 'block';
    scanStatus.style.display = 'block';
    scanStatus.textContent = 'Initializing scan...';
    progressBar.style.width = '0%';
    
    // Update search button to be an abort button
    searchButton.textContent = 'Cancel Scan';
    searchButton.classList.add('loading');
    
    // Create the API request data
    const requestData = {
        category: selectedCategory,
        subcategories: selectedSubcategories,
        max_results: 100
    };
    
    // Call the updated scan function
    scanWithProgressUpdates(requestData);
}
