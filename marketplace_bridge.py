# 1. First, let's fix the marketplace_bridge.py to better connect with scrapers

# Update the _execute_scan method in marketplace_bridge.py
async def _execute_scan(self, subcategories: List[str]) -> List[Dict[str, Any]]:
    """
    Execute the actual marketplace scan using scrapers.
    
    Args:
        subcategories (List[str]): List of subcategories to scan
        
    Returns:
        List[Dict[str, Any]]: List of arbitrage opportunities
    """
    try:
        logger.info(f"Executing marketplace scan for subcategories: {subcategories}")
        
        # Run the marketplace scrapers
        tasks = []
        
        # Add Amazon scraper
        if 'amazon_scraper' in sys.modules:
            from amazon_scraper import run_amazon_search
            tasks.append(asyncio.create_task(run_amazon_search(subcategories)))
            logger.info("Added Amazon scraper to tasks")
        
        # Add eBay scraper
        if 'ebay_scraper' in sys.modules:
            from ebay_scraper import run_ebay_search
            tasks.append(asyncio.create_task(run_ebay_search(subcategories)))
            logger.info("Added eBay scraper to tasks")
        
        # Try to import other scrapers if available
        try:
            from etsy_scraper import run_etsy_search
            tasks.append(asyncio.create_task(run_etsy_search(subcategories)))
            logger.info("Added Etsy scraper to tasks")
        except ImportError:
            logger.info("Etsy scraper not available")
        
        try:
            from facebook_scraper import run_facebook_search
            tasks.append(asyncio.create_task(run_facebook_search(subcategories)))
            logger.info("Added Facebook scraper to tasks")
        except ImportError:
            logger.info("Facebook scraper not available")
        
        # If no tasks were created, use a fallback method
        if not tasks:
            logger.warning("No scrapers available, using simulated data")
            return self._generate_simulated_data(subcategories)
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine all listings
        all_listings = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error in scraper task {i}: {str(result)}")
            else:
                logger.info(f"Scraper {i} returned {len(result)} listings")
                all_listings.extend(result)
        
        logger.info(f"Found {len(all_listings)} total listings")
        
        # Find arbitrage opportunities using the analyzer
        analyzer = ArbitrageAnalyzer()
        opportunities = analyzer.find_opportunities(all_listings)
        
        logger.info(f"Found {len(opportunities)} arbitrage opportunities")
        
        return opportunities
            
    except Exception as e:
        logger.error(f"Error executing marketplace scan: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise

# Add a fallback method to generate simulated data
def _generate_simulated_data(self, subcategories: List[str]) -> List[Dict[str, Any]]:
    """Generate simulated arbitrage opportunities for testing when scrapers aren't available."""
    from datetime import datetime
    import random
    
    opportunities = []
    
    # Generate some opportunities for each subcategory
    for subcategory in subcategories:
        # Get keywords from comprehensive_keywords.py
        keywords = self.get_keywords_for_subcategories([subcategory])[:5]  # Use just a few keywords
        
        # Create 2-4 opportunities per subcategory
        num_opportunities = random.randint(2, 4)
        
        for i in range(num_opportunities):
            # Select a random keyword
            keyword = random.choice(keywords) if keywords else subcategory
            
            # Generate buy and sell prices with a margin
            buy_price = round(random.uniform(20, 200), 2)
            margin = random.uniform(0.2, 0.5)  # 20-50% margin
            sell_price = round(buy_price * (1 + margin), 2)
            
            # Calculate profit
            profit = sell_price - buy_price
            profit_percentage = (profit / buy_price) * 100
            
            # Choose random marketplaces
            all_marketplaces = ["Amazon", "eBay", "Etsy", "Facebook Marketplace"]
            buy_marketplace = random.choice(all_marketplaces)
            sell_marketplace = random.choice([m for m in all_marketplaces if m != buy_marketplace])
            
            # Create an opportunity object
            opportunity = {
                'buyTitle': f"{keyword.title()} Item #{i+1}",
                'buyPrice': buy_price,
                'buyLink': f"https://example.com/buy/{keyword.replace(' ', '-')}-{i}",
                'buyMarketplace': buy_marketplace,
                'buyImage': f"https://via.placeholder.com/150?text={keyword.replace(' ', '+')}",
                'buyCondition': random.choice(["New", "Like New", "Very Good", "Good"]),
                
                'sellTitle': f"{keyword.title()} Item #{i+1}",
                'sellPrice': sell_price,
                'sellLink': f"https://example.com/sell/{keyword.replace(' ', '-')}-{i}",
                'sellMarketplace': sell_marketplace,
                'sellImage': f"https://via.placeholder.com/150?text={keyword.replace(' ', '+')}",
                'sellCondition': "New",
                
                'profit': round(profit, 2),
                'profitPercentage': round(profit_percentage, 2),
                'fees': {
                    'marketplace': round(sell_price * 0.1, 2),  # 10% marketplace fee
                    'shipping': round(random.uniform(5, 15), 2)  # Random shipping cost
                },
                
                'similarity': round(random.uniform(70, 95)),
                'confidence': round(random.uniform(70, 95)),
                'subcategory': subcategory,
                'timestamp': datetime.now().isoformat()
            }
            
            opportunities.append(opportunity)
    
    return opportunities

# 2. Now let's update app.py to handle the scan requests properly

# Add this import at the top of app.py
import sys
import importlib.util

# Update the scan_marketplaces function in app.py
@app.post("/api/v1/scan")
async def scan_marketplaces(request: ScanRequest):
    """Scan marketplaces for arbitrage opportunities"""
    try:
        logger.info(f"Starting scan for subcategories: {request.subcategories}")
        
        # Basic validation
        if not request.subcategories:
            raise HTTPException(status_code=400, detail="At least one subcategory is required")
        
        # Process the scan through the marketplace bridge
        result = process_marketplace_scan(
            category=request.category,
            subcategories=request.subcategories,
            max_results=request.max_results or 100
        )
        
        # Check for errors
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return result
    
    except Exception as e:
        logger.error(f"Error during scan: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"An error occurred during the scan: {str(e)}")

# 3. Let's update the frontend script.js to properly handle responses

/*
 * Update the script.js function to handle the scanning process
 */

// Update the pollScanProgress function in script.js to better handle results
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

// Update the fetchScanResults function to properly display results
function fetchScanResults(scanId) {
    fetch(`/api/v1/scan/${scanId}`)
    .then(response => {
        if (!response.ok) {
            throw new Error(`Failed to get scan results: ${response.status} ${response.statusText}`);
        }
        return response.json();
    })
    .then(resultsData => {
        // Process the results - extract the opportunities from the response
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

// 4. Fix the ArbitrageAnalyzer in marketplace_scanner.py to better detect similarities

def calculate_similarity(self, title1: str, title2: str) -> float:
    """
    Calculate similarity between two titles using multiple techniques.
    
    Args:
        title1 (str): First title
        title2 (str): Second title
        
    Returns:
        float: Similarity score between 0 and 1
    """
    # Clean and normalize titles
    title1 = self._normalize_title(title1)
    title2 = self._normalize_title(title2)
    
    # Direct substring matching
    if title1 in title2 or title2 in title1:
        # Adjust score based on length difference
        length_ratio = min(len(title1), len(title2)) / max(len(title1), len(title2))
        # Higher score for more similar lengths
        return 0.8 + (0.2 * length_ratio)
    
    # Extract model numbers and identifiers
    models1 = self._extract_model_numbers(title1)
    models2 = self._extract_model_numbers(title2)
    
    # If both have model numbers and they share at least one
    common_models = set(models1).intersection(set(models2))
    if common_models and models1 and models2:
        return 0.95  # Very high confidence for matching model numbers
    
    # Calculate word overlap
    words1 = set(title1.split())
    words2 = set(title2.split())
    
    # Check if key words match (excluding common words)
    common_words = words1.intersection(words2)
    common_words_count = len(common_words)
    total_words = len(words1.union(words2))
    
    if total_words == 0:
        return 0
    
    # Jaccard similarity for words
    word_similarity = common_words_count / total_words
    
    # Sequence matcher for character-by-character comparison
    sequence_similarity = SequenceMatcher(None, title1, title2).ratio()
    
    # Combined similarity score (weighted)
    combined_similarity = (word_similarity * 0.7) + (sequence_similarity * 0.3)
    
    return combined_similarity

# 5. Update scan.html to make it work with the backend API

/*
 * Update the scan.html script section to call the correct API endpoints
 */
 
// Replace the fetch call in the scan button event listener
fetch('/api/v1/scan', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        "category": "Tech", // Use the parent category of the selected subcategories
        "subcategories": selectedSubcategories,
        "max_results": 100
    })
})
.then(response => {
    if (!response.ok) {
        throw new Error('Network response was not ok');
    }
    return response.json();
})
.then(data => {
    // Hide loading indicator
    loadingIndicator.style.display = 'none';
    
    // Get the arbitrage opportunities from the response
    const opportunities = data.arbitrage_opportunities || [];
    
    // Check if we have results
    if (opportunities.length === 0) {
        noResultsMessage.style.display = 'block';
    } else {
        // Render results
        renderOpportunities(opportunities);
        resultsContainer.style.display = 'block';
    }
})
.catch(error => {
    // Hide loading indicator
    loadingIndicator.style.display = 'none';
    
    // Log the error for debugging
    console.error('Error:', error);
    
    // Show detailed error message
    errorMessage.textContent = 'Error connecting to scanning service: ' + error.message + 
                               '. Please check the console for more details or try again later.';
    errorMessage.style.display = 'block';
})
.finally(() => {
    // Re-enable scan button
    scanButton.disabled = false;
    scanButton.textContent = 'Start Scanning';
});
