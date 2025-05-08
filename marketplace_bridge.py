# marketplace_bridge.py
"""
FlipHawk Marketplace Bridge
Connects the frontend API with backend scrapers to perform marketplace scans
"""

import asyncio
import logging
import uuid
import time
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('marketplace_bridge')

# Import scrapers
try:
    from amazon_scraper import run_amazon_search
    amazon_available = True
    logger.info("Amazon scraper loaded successfully")
except ImportError:
    amazon_available = False
    logger.warning("Amazon scraper not available")

try:
    from ebay_scraper import run_ebay_search
    ebay_available = True
    logger.info("eBay scraper loaded successfully")
except ImportError:
    ebay_available = False
    logger.warning("eBay scraper not available")

try:
    from mercari_scraper import run_mercari_search
    mercari_available = True
    logger.info("Mercari scraper loaded successfully")
except ImportError:
    mercari_available = False
    logger.warning("Mercari scraper not available")

# Try to import comprehensive_keywords
try:
    from comprehensive_keywords import get_keywords_for_subcategory, COMPREHENSIVE_KEYWORDS
    keywords_available = True
    logger.info("Comprehensive keywords loaded successfully")
except ImportError:
    keywords_available = False
    logger.warning("Comprehensive keywords not available")

class ScanManager:
    """Manages scan requests and tracks their progress."""
    
    def __init__(self):
        """Initialize the scan manager."""
        self.scans = {}
        self.results = {}
        self.active_scans = 0
        self.loop = None
    
    def get_event_loop(self):
        """Get or create an event loop."""
        if self.loop is None or self.loop.is_closed():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
        return self.loop
    
    def initialize_scan(self, category: str, subcategories: List[str]) -> str:
        """
        Initialize a new scan and return its ID.
        
        Args:
            category: The parent category
            subcategories: List of subcategories to scan
            
        Returns:
            scan_id: Unique ID for the scan
        """
        scan_id = str(uuid.uuid4())
        
        self.scans[scan_id] = {
            'category': category,
            'subcategories': subcategories,
            'status': 'initializing',
            'progress': 0,
            'start_time': datetime.now().isoformat(),
            'completion_time': None
        }
        
        self.results[scan_id] = {
            'meta': {
                'scan_id': scan_id,
                'category': category,
                'subcategories': subcategories,
                'timestamp': datetime.now().isoformat()
            },
            'arbitrage_opportunities': []
        }
        
        return scan_id
    
    def get_scan_info(self, scan_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a scan.
        
        Args:
            scan_id: The scan ID
            
        Returns:
            dict: Scan information, or None if not found
        """
        return self.scans.get(scan_id)
    
    def update_scan_progress(self, scan_id: str, progress: int, status: str = None):
        """
        Update the progress of a scan.
        
        Args:
            scan_id: The scan ID
            progress: Progress percentage (0-100)
            status: New status (if provided)
        """
        if scan_id in self.scans:
            self.scans[scan_id]['progress'] = progress
            
            if status:
                self.scans[scan_id]['status'] = status
                
            if progress >= 100:
                self.scans[scan_id]['completion_time'] = datetime.now().isoformat()
    
    def get_formatted_results(self, scan_id: str) -> Dict[str, Any]:
        """
        Get formatted scan results.
        
        Args:
            scan_id: The scan ID
            
        Returns:
            dict: Formatted scan results
        """
        if scan_id not in self.results:
            return {"error": f"Scan with ID {scan_id} not found"}
        
        return self.results[scan_id]
    
    def store_scan_results(self, scan_id: str, opportunities: List[Dict[str, Any]]):
        """
        Store scan results.
        
        Args:
            scan_id: The scan ID
            opportunities: List of arbitrage opportunities
        """
        if scan_id in self.results:
            self.results[scan_id]['arbitrage_opportunities'] = opportunities
            
            # Update scan info
            self.update_scan_progress(scan_id, 100, 'completed' if opportunities else 'completed_no_results')
            
            # Add timestamp to results
            self.results[scan_id]['meta']['completed_at'] = datetime.now().isoformat()
            self.results[scan_id]['meta']['total_opportunities'] = len(opportunities)
            
            # Calculate some stats
            marketplaces = set()
            subcategories = set()
            
            for opp in opportunities:
                if 'buyMarketplace' in opp:
                    marketplaces.add(opp['buyMarketplace'])
                if 'sellMarketplace' in opp:
                    marketplaces.add(opp['sellMarketplace'])
                if 'subcategory' in opp:
                    subcategories.add(opp['subcategory'])
            
            self.results[scan_id]['meta']['marketplaces'] = list(marketplaces)
            self.results[scan_id]['meta']['found_subcategories'] = list(subcategories)

# Create a global scan manager instance
scan_manager = ScanManager()

def process_marketplace_scan(category: str, subcategories: List[str], max_results: int = 100) -> Dict[str, Any]:
    """
    Process a marketplace scan request.
    
    Args:
        category: The parent category
        subcategories: List of subcategories to scan
        max_results: Maximum number of results to return
        
    Returns:
        dict: Initial response with scan ID
    """
    try:
        logger.info(f"Processing scan request for category: {category}, subcategories: {subcategories}")
        
        # Initialize the scan
        scan_id = scan_manager.initialize_scan(category, subcategories)
        
        # Start the scan in a background task
        loop = scan_manager.get_event_loop()
        task = loop.create_task(_execute_scan_task(scan_id, category, subcategories, max_results))
        
        # Return initial response with scan ID
        return {
            'meta': {
                'scan_id': scan_id,
                'message': 'Scan started',
                'status': 'initializing',
                'category': category,
                'subcategories': subcategories
            }
        }
        
    except Exception as e:
        logger.error(f"Error processing scan request: {str(e)}")
        return {
            'error': f"Failed to start scan: {str(e)}",
            'details': traceback.format_exc()
        }

async def _execute_scan_task(scan_id: str, category: str, subcategories: List[str], max_results: int):
    """
    Execute the scan task in the background.
    
    Args:
        scan_id: The scan ID
        category: The parent category
        subcategories: List of subcategories to scan
        max_results: Maximum number of results
    """
    try:
        # Update progress
        scan_manager.update_scan_progress(scan_id, 5, 'searching marketplaces')
        
        # Get all keywords for the selected subcategories
        keywords = []
        if keywords_available:
            for subcategory in subcategories:
                for cat, subcats in COMPREHENSIVE_KEYWORDS.items():
                    if subcategory in subcats:
                        subcat_keywords = subcats[subcategory]
                        logger.info(f"Adding {len(subcat_keywords)} keywords for {subcategory}")
                        keywords.extend(subcat_keywords)
            
            if not keywords:
                # Fallback to subcategory names as keywords if no keywords found
                keywords = subcategories
        else:
            # If comprehensive_keywords.py is not available, use subcategory names as keywords
            keywords = subcategories
        
        # Log keywords being used
        logger.info(f"Using {len(keywords)} keywords for scanning: {keywords[:5]}...")
        
        # Update progress
        scan_manager.update_scan_progress(scan_id, 10, 'searching marketplaces')
        
        # Execute the actual scan using the keywords
        listings = await _execute_marketplace_scan(subcategories, keywords)
        
        # Update progress
        scan_manager.update_scan_progress(scan_id, 50, 'processing results')
        
        # Find arbitrage opportunities from listings
        opportunities = _find_arbitrage_opportunities(listings)
        
        # Update progress
        scan_manager.update_scan_progress(scan_id, 80, 'finalizing results')
        
        # Limit the number of results if needed
        if max_results > 0 and len(opportunities) > max_results:
            opportunities = opportunities[:max_results]
        
        # Store the results
        scan_manager.store_scan_results(scan_id, opportunities)
        
    except Exception as e:
        logger.error(f"Error executing scan task: {str(e)}")
        logger.error(traceback.format_exc())
        scan_manager.update_scan_progress(scan_id, 100, 'failed')

async def _execute_marketplace_scan(subcategories: List[str], keywords: List[str]) -> List[Dict[str, Any]]:
    """
    Execute the marketplace scan using scrapers.
    
    Args:
        subcategories: List of subcategories to scan
        keywords: List of keywords to search for
        
    Returns:
        List[Dict[str, Any]]: List of product listings
    """
    try:
        logger.info(f"Executing marketplace scan for subcategories: {subcategories}")
        
        # Run the marketplace scrapers
        tasks = []
        
        # Add Amazon scraper
        if amazon_available:
            tasks.append(asyncio.create_task(run_amazon_search(subcategories)))
            logger.info("Added Amazon scraper to tasks")
        
        # Add eBay scraper
        if ebay_available:
            tasks.append(asyncio.create_task(run_ebay_search(subcategories)))
            logger.info("Added eBay scraper to tasks")
        
        # Add Mercari scraper
        if mercari_available:
            tasks.append(asyncio.create_task(run_mercari_search(subcategories)))
            logger.info("Added Mercari scraper to tasks")
        
        # If no tasks were created, use a fallback method
        if not tasks:
            logger.warning("No scrapers available, using simulated data")
            return _generate_simulated_data(subcategories)
        
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
        
        return all_listings
            
    except Exception as e:
        logger.error(f"Error executing marketplace scan: {str(e)}")
        logger.error(traceback.format_exc())
        return []

def _find_arbitrage_opportunities(listings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Find arbitrage opportunities in listings.
    
    Args:
        listings: List of product listings
        
    Returns:
        List[Dict[str, Any]]: List of arbitrage opportunities
    """
    # Group listings by source
    listings_by_source = {}
    for listing in listings:
        source = listing.get('source', listing.get('marketplace', 'unknown'))
        if source not in listings_by_source:
            listings_by_source[source] = []
        listings_by_source[source].append(listing)
    
    # Get all sources
    sources = list(listings_by_source.keys())
    
    # No opportunities if less than 2 sources
    if len(sources) < 2:
        return []
    
    opportunities = []
    
    # Compare each possible pair of sources
    for i, buy_source in enumerate(sources):
        for j, sell_source in enumerate(sources):
            if i == j:  # Skip same source
                continue
            
            buy_listings = listings_by_source[buy_source]
            sell_listings = listings_by_source[sell_source]
            
            # Compare each buy listing with each sell listing
            for buy_listing in buy_listings:
                buy_title = buy_listing.get('title', '')
                buy_price = buy_listing.get('price', 0)
                
                if not buy_title or buy_price <= 0:
                    continue
                
                for sell_listing in sell_listings:
                    sell_title = sell_listing.get('title', '')
                    sell_price = sell_listing.get('price', 0)
                    
                    if not sell_title or sell_price <= 0:
                        continue
                    
                    # Skip if buy price is not less than sell price
                    if buy_price >= sell_price:
                        continue
                    
                    # Simple title similarity check
                    similarity = _calculate_title_similarity(buy_title, sell_title)
                    
                    # Only include if similarity is high enough
                    if similarity >= 0.7:
                        # Calculate profit
                        profit = sell_price - buy_price
                        
                        # Calculate fees (simplified)
                        marketplace_fee = sell_price * 0.10  # 10% marketplace fee
                        shipping_fee = 7.99  # Fixed shipping fee
                        
                        # Calculate adjusted profit
                        adjusted_profit = profit - marketplace_fee - shipping_fee
                        
                        # Skip if not profitable after fees
                        if adjusted_profit <= 0:
                            continue
                        
                        # Create opportunity
                        opportunity = {
                            'buyTitle': buy_listing.get('title', ''),
                            'buyPrice': buy_price,
                            'buyLink': buy_listing.get('link', ''),
                            'buyMarketplace': buy_source,
                            'buyImage': buy_listing.get('image_url', ''),
                            'buyCondition': buy_listing.get('condition', 'New'),
                            
                            'sellTitle': sell_listing.get('title', ''),
                            'sellPrice': sell_price,
                            'sellLink': sell_listing.get('link', ''),
                            'sellMarketplace': sell_source,
                            'sellImage': sell_listing.get('image_url', ''),
                            'sellCondition': sell_listing.get('condition', 'New'),
                            
                            'profit': round(adjusted_profit, 2),
                            'profitPercentage': round((adjusted_profit / buy_price) * 100, 2),
                            'fees': {
                                'marketplace': round(marketplace_fee, 2),
                                'shipping': round(shipping_fee, 2)
                            },
                            
                            'similarity': round(similarity * 100),
                            'confidence': round(similarity * 100),
                            'subcategory': buy_listing.get('subcategory', '')
                        }
                        
                        opportunities.append(opportunity)
    
    # Sort by profit (highest first)
    opportunities.sort(key=lambda x: x['profit'], reverse=True)
    
    return opportunities

def _calculate_title_similarity(title1: str, title2: str) -> float:
    """
    Calculate similarity between two titles.
    
    Args:
        title1: First title
        title2: Second title
        
    Returns:
        float: Similarity score between 0 and 1
    """
    from difflib import SequenceMatcher
    
    # Normalize titles
    title1 = title1.lower()
    title2 = title2.lower()
    
    # Simple word overlap
    words1 = set(title1.split())
    words2 = set(title2.split())
    
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    if not union:
        return 0
    
    # Jaccard similarity
    jaccard = len(intersection) / len(union)
    
    # Sequence matcher
    sequence = SequenceMatcher(None, title1, title2).ratio()
    
    # Combined score (weighted)
    combined = (jaccard * 0.7) + (sequence * 0.3)
    
    return combined

def _generate_simulated_data(subcategories: List[str]) -> List[Dict[str, Any]]:
    """Generate simulated product listings for testing."""
    import random
    from datetime import datetime
    
    listings = []
    
    # Generate some listings for each subcategory
    for subcategory in subcategories:
        # Create 10-15 listings per subcategory
        num_listings = random.randint(10, 15)
        
        for i in range(num_listings):
            # Generate buy and sell prices with a margin
            buy_price = round(random.uniform(20, 200), 2)
            
            # Create a listing object
            listing = {
                'title': f"{subcategory} Item #{i+1}",
                'price': buy_price,
                'link': f"https://example.com/buy/{subcategory.lower().replace(' ', '-')}-{i}",
                'source': random.choice(["Amazon", "eBay", "Mercari"]),
                'image_url': f"https://via.placeholder.com/150?text={subcategory.replace(' ', '+')}",
                'condition': random.choice(["New", "Like New", "Very Good", "Good"]),
                'subcategory': subcategory,
                'timestamp': datetime.now().isoformat()
            }
            
            listings.append(listing)
    
    return listings

def get_keywords_for_subcategories(subcategories: List[str]) -> List[str]:
    """
    Get all keywords for a list of subcategories from comprehensive_keywords.py.
    
    Args:
        subcategories: List of subcategories
        
    Returns:
        List[str]: List of keywords
    """
    if not keywords_available:
        logger.warning("comprehensive_keywords.py not available, using subcategories as keywords")
        return subcategories
    
    all_keywords = []
    
    for category, subcats in COMPREHENSIVE_KEYWORDS.items():
        for subcategory in subcategories:
            if subcategory in subcats:
                all_keywords.extend(subcats[subcategory])
    
    return all_keywords
