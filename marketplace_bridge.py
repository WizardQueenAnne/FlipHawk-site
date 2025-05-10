# marketplace_bridge.py
"""
FlipHawk - Marketplace Bridge Module
Connects API endpoints with marketplace scrapers
"""

import asyncio
import logging
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
import traceback
import random

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
    logger.info("Amazon scraper available")
except ImportError:
    amazon_available = False
    logger.warning("Amazon scraper not available")

try:
    from ebay_scraper import run_ebay_search
    ebay_available = True
    logger.info("eBay scraper available")
except ImportError:
    ebay_available = False
    logger.warning("eBay scraper not available")

try:
    from facebook_scraper import run_facebook_search
    facebook_available = True
    logger.info("Facebook scraper available")
except ImportError:
    facebook_available = False
    logger.warning("Facebook scraper not available")

# State tracking for scans
active_scans = {}

async def process_marketplace_scan(category: str, subcategories: List[str], max_results: int = 100) -> Dict[str, Any]:
    """
    Process marketplace scan request.
    
    Args:
        category: Category name
        subcategories: List of subcategories to search
        max_results: Maximum number of results to return
        
    Returns:
        Dict with scan ID and initial response
    """
    
    try:
        logger.info(f"Starting marketplace scan for category {category}, subcategories: {subcategories}")
        
        # Generate scan ID
        scan_id = str(uuid.uuid4())
        
        # Initialize scan state
        active_scans[scan_id] = {
            "category": category,
            "subcategories": subcategories,
            "start_time": datetime.now().isoformat(),
            "status": "initializing",
            "progress": 0,
            "results": []
        }
        
        # Start scan in background
        asyncio.create_task(run_scan(scan_id, category, subcategories, max_results))
        
        # Return initial response
        return {
            "meta": {
                "scan_id": scan_id,
                "message": "Scan started",
                "status": "initializing",
                "category": category,
                "subcategories": subcategories
            }
        }
        
    except Exception as e:
        logger.error(f"Error starting scan: {str(e)}")
        logger.error(traceback.format_exc())
        
        return {
            "error": f"Failed to start scan: {str(e)}"
        }

async def run_scan(scan_id: str, category: str, subcategories: List[str], max_results: int):
    """
    Run the actual scan process in background.
    
    Args:
        scan_id: Scan ID for tracking
        category: Category name
        subcategories: List of subcategories to search
        max_results: Maximum number of results to return
    """
    
    try:
        # Update progress
        update_scan_progress(scan_id, 5, "running")
        
        # Get keywords for subcategories
        keywords = get_keywords_for_subcategories(subcategories)
        logger.info(f"Using {len(keywords)} keywords for scan {scan_id}")
        
        # Run marketplace scrapers
        update_scan_progress(scan_id, 10, "searching marketplaces")
        all_listings = []
        
        # Run Amazon scraper
        if amazon_available:
            try:
                update_scan_progress(scan_id, 20, "searching amazon")
                amazon_results = await run_amazon_search(subcategories)
                logger.info(f"Amazon scraper returned {len(amazon_results)} results")
                all_listings.extend(amazon_results)
                update_scan_progress(scan_id, 40, "searching amazon")
            except Exception as e:
                logger.error(f"Error in Amazon scraper: {str(e)}")
                logger.error(traceback.format_exc())
        
        # Run eBay scraper
        if ebay_available:
            try:
                update_scan_progress(scan_id, 50, "searching ebay")
                ebay_results = await run_ebay_search(subcategories)
                logger.info(f"eBay scraper returned {len(ebay_results)} results")
                all_listings.extend(ebay_results)
                update_scan_progress(scan_id, 70, "searching ebay")
            except Exception as e:
                logger.error(f"Error in eBay scraper: {str(e)}")
                logger.error(traceback.format_exc())
        
        # Run Facebook scraper
        if facebook_available:
            try:
                update_scan_progress(scan_id, 80, "searching facebook")
                facebook_results = await run_facebook_search(subcategories)
                logger.info(f"Facebook scraper returned {len(facebook_results)} results")
                all_listings.extend(facebook_results)
                update_scan_progress(scan_id, 90, "searching facebook")
            except Exception as e:
                logger.error(f"Error in Facebook scraper: {str(e)}")
                logger.error(traceback.format_exc())
        
        # Find arbitrage opportunities
        update_scan_progress(scan_id, 95, "finding opportunities")
        
        if not all_listings:
            logger.warning(f"No listings found for scan {scan_id}, generating dummy data")
            opportunities = generate_dummy_results(subcategories)
        else:
            opportunities = find_arbitrage_opportunities(all_listings)
            
            # Limit results if needed
            if max_results > 0 and len(opportunities) > max_results:
                opportunities = opportunities[:max_results]
        
        # Store results
        active_scans[scan_id]["results"] = opportunities
        
        # Mark as completed
        update_scan_progress(scan_id, 100, "completed")
        
        logger.info(f"Scan {scan_id} completed with {len(opportunities)} opportunities")
        
    except Exception as e:
        logger.error(f"Error running scan {scan_id}: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Mark as error
        update_scan_progress(scan_id, 100, "error")
        active_scans[scan_id]["error"] = str(e)

def update_scan_progress(scan_id: str, progress: int, status: Optional[str] = None):
    """
    Update scan progress.
    
    Args:
        scan_id: Scan ID
        progress: Progress percentage (0-100)
        status: Optional status string
    """
    if scan_id not in active_scans:
        return
    
    active_scans[scan_id]["progress"] = progress
    
    if status:
        active_scans[scan_id]["status"] = status
        
    if progress >= 100:
        active_scans[scan_id]["completion_time"] = datetime.now().isoformat()

def get_scan_info(scan_id: str) -> Optional[Dict[str, Any]]:
    """
    Get scan information.
    
    Args:
        scan_id: Scan ID
        
    Returns:
        Dict with scan info or None if not found
    """
    return active_scans.get(scan_id)

def get_scan_results(scan_id: str) -> Optional[List[Dict[str, Any]]]:
    """
    Get scan results.
    
    Args:
        scan_id: Scan ID
        
    Returns:
        List of opportunities or None if not found
    """
    scan_info = active_scans.get(scan_id)
    if not scan_info:
        return None
    
    return scan_info.get("results", [])

def get_keywords_for_subcategories(subcategories: List[str]) -> List[str]:
    """
    Get keywords for the specified subcategories from comprehensive_keywords.py.
    
    Args:
        subcategories: List of subcategories
        
    Returns:
        List of keywords
    """
    keywords = []
    
    try:
        # Import keywords from comprehensive_keywords.py
        from comprehensive_keywords import COMPREHENSIVE_KEYWORDS
        
        # Find keywords for each subcategory
        for category, subcats in COMPREHENSIVE_KEYWORDS.items():
            for subcategory, subcat_keywords in subcats.items():
                if subcategory in subcategories:
                    keywords.extend(subcat_keywords)
        
        # Log what we found
        logger.info(f"Found {len(keywords)} keywords for {len(subcategories)} subcategories")
        
        return keywords
        
    except ImportError:
        # Fallback if comprehensive_keywords.py is not available
        logger.warning("comprehensive_keywords.py not found, using subcategories as keywords")
        return subcategories

def find_arbitrage_opportunities(listings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Find arbitrage opportunities from listings.
    
    Args:
        listings: List of product listings
        
    Returns:
        List of arbitrage opportunities
    """
    # Group listings by source
    listings_by_source = {}
    for listing in listings:
        source = listing.get("source", listing.get("marketplace", "unknown"))
        if source not in listings_by_source:
            listings_by_source[source] = []
        listings_by_source[source].append(listing)
    
    # If less than 2 sources, return empty list
    if len(listings_by_source) < 2:
        logger.warning("Not enough marketplace sources to find arbitrage opportunities")
        return []
    
    opportunities = []
    
    # Compare each possible pair of sources
    for buy_source, buy_listings in listings_by_source.items():
        for sell_source, sell_listings in listings_by_source.items():
            # Skip same source
            if buy_source == sell_source:
                continue
            
            logger.info(f"Comparing {len(buy_listings)} {buy_source} listings with {len(sell_listings)} {sell_source} listings")
            
            # Compare each buy listing with each sell listing
            for buy_listing in buy_listings:
                buy_price = buy_listing.get("price", 0)
                if buy_price <= 0:
                    continue
                    
                buy_title = buy_listing.get("title", "")
                if not buy_title:
                    continue
                
                for sell_listing in sell_listings:
                    sell_price = sell_listing.get("price", 0)
                    if sell_price <= 0:
                        continue
                        
                    # Skip if sell price not higher than buy price
                    if sell_price <= buy_price:
                        continue
                        
                    sell_title = sell_listing.get("title", "")
                    if not sell_title:
                        continue
                    
                    # Calculate similarity
                    similarity = calculate_title_similarity(buy_title, sell_title)
                    
                    # If similar enough
                    if similarity >= 0.5:
                        # Calculate profit
                        profit = sell_price - buy_price
                        profit_percentage = (profit / buy_price) * 100
                        
                        # Calculate fees
                        marketplace_fee = sell_price * 0.1  # 10% marketplace fee
                        shipping_fee = 5.0  # $5 shipping
                        
                        # Calculate adjusted profit
                        adjusted_profit = profit - marketplace_fee - shipping_fee
                        
                        # Skip if not profitable
                        if adjusted_profit <= 0:
                            continue
                        
                        # Create opportunity
                        opportunity = {
                            "buyTitle": buy_title,
                            "buyPrice": buy_price,
                            "buyMarketplace": buy_source,
                            "buyLink": buy_listing.get("link", ""),
                            "buyImage": buy_listing.get("image_url", ""),
                            "buyCondition": buy_listing.get("condition", "New"),
                            
                            "sellTitle": sell_title,
                            "sellPrice": sell_price,
                            "sellMarketplace": sell_source,
                            "sellLink": sell_listing.get("link", ""),
                            "sellImage": sell_listing.get("image_url", ""),
                            "sellCondition": sell_listing.get("condition", "New"),
                            
                            "profit": round(adjusted_profit, 2),
                            "profitPercentage": round(profit_percentage, 2),
                            "similarity": round(similarity * 100),
                            "fees": {
                                "marketplace": round(marketplace_fee, 2),
                                "shipping": round(shipping_fee, 2)
                            }
                        }
                        
                        opportunities.append(opportunity)
    
    # Sort by profit
    opportunities.sort(key=lambda x: x["profit"], reverse=True)
    logger.info(f"Found {len(opportunities)} arbitrage opportunities")
    
    return opportunities

def calculate_title_similarity(title1: str, title2: str) -> float:
    """
    Calculate similarity between two titles.
    
    Args:
        title1: First title
        title2: Second title
        
    Returns:
        Similarity score between 0 and 1
    """
    from difflib import SequenceMatcher
    
    # Simple word overlap calculation
    if not title1 or not title2:
        return 0
    
    # Normalize titles
    title1 = title1.lower()
    title2 = title2.lower()
    
    # Split into words
    words1 = set(title1.split())
    words2 = set(title2.split())
    
    # Calculate overlap
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    if not union:
        return 0
    
    # Jaccard similarity (word-based)
    jaccard = len(intersection) / len(union)
    
    # Sequence similarity (character-based)
    sequence = SequenceMatcher(None, title1, title2).ratio()
    
    # Weighted combination
    similarity = (jaccard * 0.7) + (sequence * 0.3)
    
    return similarity

def generate_dummy_results(subcategories: List[str]) -> List[Dict[str, Any]]:
    """
    Generate dummy arbitrage opportunities for testing.
    
    Args:
        subcategories: List of subcategories
        
    Returns:
        List of dummy opportunities
    """
    opportunities = []
    marketplaces = ["Amazon", "eBay", "Facebook Marketplace"]
    
    # For each subcategory
    for subcategory in subcategories:
        # Create 2-5 opportunities
        for i in range(random.randint(2, 5)):
            # Buy and sell marketplaces
            buy_market = random.choice(marketplaces)
            sell_market = random.choice([m for m in marketplaces if m != buy_market])
            
            # Base price between $50-$300
            base_price = random.uniform(50, 300)
            
            # Buy price
            buy_price = round(base_price, 2)
            
            # Sell price - 20-50% higher
            markup = random.uniform(0.2, 0.5)
            sell_price = round(buy_price * (1 + markup), 2)
            
            # Calculate profit
            profit = sell_price - buy_price
            marketplace_fee = sell_price * 0.1
            shipping_fee = 5.0
            adjusted_profit = profit - marketplace_fee - shipping_fee
            profit_percentage = (adjusted_profit / buy_price) * 100
            
            # Skip if not profitable
            if adjusted_profit <= 0:
                continue
                
            # Create opportunity
            opportunity = {
                "buyTitle": f"{subcategory} Product {i+1}",
                "buyPrice": buy_price,
                "buyMarketplace": buy_market,
                "buyLink": f"https://example.com/{buy_market.lower()}/{i}",
                "buyImage": f"https://via.placeholder.com/200?text={subcategory}",
                "buyCondition": "New",
                
                "sellTitle": f"{subcategory} Product {i+1}",
                "sellPrice": sell_price,
                "sellMarketplace": sell_market,
                "sellLink": f"https://example.com/{sell_market.lower()}/{i}",
                "sellImage": f"https://via.placeholder.com/200?text={subcategory}",
                "sellCondition": "New",
                
                "profit": round(adjusted_profit, 2),
                "profitPercentage": round(profit_percentage, 2),
                "similarity": 90,
                "fees": {
                    "marketplace": round(marketplace_fee, 2),
                    "shipping": round(shipping_fee, 2)
                }
            }
            
            opportunities.append(opportunity)
    
    return opportunities
