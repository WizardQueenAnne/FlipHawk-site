import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any

# Import the modules that contain the scraper functions
from amazon_scraper import run_amazon_search
from ebay_scraper import run_ebay_search
from tcgplayer_scraper import run_tcgplayer_search
from walmart_scraper import run_walmart_search
from facebook_scraper import run_facebook_search
from etsy_scraper import run_etsy_search
from mercari_scraper import run_mercari_search
from offerup_scraper import run_offerup_search
from stockx_scraper import run_stockx_search
from comprehensive_keywords import COMPREHENSIVE_KEYWORDS, generate_keywords

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scraper_manager.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class ScraperManager:
    """Enhanced Scraper Manager to coordinate all marketplace scrapers"""
    
    def __init__(self):
        # Store scraper functions directly
        self.scrapers = {
            'amazon': run_amazon_search,
            'ebay': run_ebay_search,
            'tcgplayer': run_tcgplayer_search,
            'walmart': run_walmart_search,
            'facebook': run_facebook_search,
            'etsy': run_etsy_search,
            'mercari': run_mercari_search,
            'offerup': run_offerup_search,
            'stockx': run_stockx_search
        }
        self.results = {}
        self.arbitrage_opportunities = []
    
    async def run_all_scrapers(self, keywords=None, subcategories=None):
        """
        Run all scrapers with provided keywords or subcategories or default comprehensive keywords.
        
        Args:
            keywords (List[str], optional): List of keywords to search for
            subcategories (List[str], optional): List of subcategories to search for
        
        Returns:
            Dict: Results from all scrapers
        """
        if keywords is None:
            keywords = []
            
            # If subcategories are provided, generate keywords from them
            if subcategories:
                for subcategory in subcategories:
                    subcat_keywords = generate_keywords(subcategory, include_variations=True, max_keywords=5)
                    keywords.extend(subcat_keywords)
            else:
                # Extract keywords from all categories in COMPREHENSIVE_KEYWORDS
                for category, subcats in COMPREHENSIVE_KEYWORDS.items():
                    for subcat, keyword_list in subcats.items():
                        # Take first 5 keywords from each subcategory
                        keywords.extend(keyword_list[:5])
        
        logger.info(f"Starting scraper run with {len(keywords)} keywords")
        tasks = []
        
        # Create tasks for each marketplace, passing either keywords or subcategories
        for marketplace, scraper_func in self.scrapers.items():
            if subcategories:
                # Run with subcategories when available
                tasks.append(self._run_scraper(marketplace, scraper_func, subcategories))
            else:
                # Fallback to keywords if no subcategories
                tasks.append(self._run_keyword_search(marketplace, scraper_func, keywords))
        
        # Run all tasks concurrently
        await asyncio.gather(*tasks)
        return self.results
    
    async def _run_scraper(self, marketplace: str, scraper_func, subcategories: List[str]):
        """
        Run a specific scraper with the given subcategories.
        
        Args:
            marketplace (str): Name of the marketplace
            scraper_func: Function to run the scraper
            subcategories (List[str]): List of subcategories to search for
        
        Returns:
            List: Results from the scraper
        """
        try:
            logger.info(f"Starting {marketplace} scraper with {len(subcategories)} subcategories")
            # Call the scraper function with subcategories
            results = await scraper_func(subcategories)
            self.results[marketplace] = results
            logger.info(f"Completed {marketplace} scraper. Found {len(results)} listings")
            return results
        except Exception as e:
            logger.error(f"Error in {marketplace} scraper: {str(e)}")
            self.results[marketplace] = []
            return []
    
    async def _run_keyword_search(self, marketplace: str, scraper_func, keywords: List[str]):
        """
        Run a specific scraper with the given keywords.
        
        Args:
            marketplace (str): Name of the marketplace
            scraper_func: Function to run the scraper
            keywords (List[str]): List of keywords to search for
            
        Returns:
            List: Results from the scraper
        """
        try:
            # This is a fallback method when we don't have subcategories
            # We'll try to adapt the function call based on what we expect the scraper to support
            logger.info(f"Starting {marketplace} scraper with {len(keywords)} keywords")
            
            # First try to get a scraper instance (some might have a class-based approach)
            try:
                # Dynamic import to get the scraper class if it exists
                module_name = f"{marketplace}_scraper"
                class_name = f"{marketplace.capitalize()}Scraper"
                
                # Try to import the module
                import importlib
                module = importlib.import_module(module_name)
                
                # Try to get the scraper class and create an instance
                scraper_class = getattr(module, class_name, None)
                if scraper_class:
                    scraper = scraper_class()
                    if hasattr(scraper, 'search_listings'):
                        results = await scraper.search_listings(keywords)
                        self.results[marketplace] = results
                        logger.info(f"Completed {marketplace} scraper. Found {len(results)} listings")
                        return results
            except (ImportError, AttributeError) as e:
                # If we can't get a class instance, we'll try the function directly
                pass
            
            # Use subcategories approach with generated keywords
            subcategories = []
            for keyword in keywords:
                # Try to map keywords to subcategories
                for category, subcats in COMPREHENSIVE_KEYWORDS.items():
                    for subcat, keyword_list in subcats.items():
                        if keyword.lower() in [k.lower() for k in keyword_list]:
                            if subcat not in subcategories:
                                subcategories.append(subcat)
            
            # If we found subcategories, use them
            if subcategories:
                results = await scraper_func(subcategories)
            else:
                # Fallback: create a temporary subcategory from keywords
                temp_subcategories = [keywords[0].capitalize()] if keywords else ["General"]
                results = await scraper_func(temp_subcategories)
            
            self.results[marketplace] = results
            logger.info(f"Completed {marketplace} scraper with keywords. Found {len(results)} listings")
            return results
            
        except Exception as e:
            logger.error(f"Error in {marketplace} scraper: {str(e)}")
            self.results[marketplace] = []
            return []
    
    def find_arbitrage_opportunities(self):
        """
        Analyze results from all marketplaces to find arbitrage opportunities.
        
        Returns:
            List[Dict]: List of arbitrage opportunities
        """
        logger.info("Finding arbitrage opportunities...")
        self.arbitrage_opportunities = []
        
        # Create a combined list of all products with their marketplace and price
        all_products = []
        for marketplace, listings in self.results.items():
            for listing in listings:
                # Ensure listing has all required fields
                if not isinstance(listing, dict):
                    continue
                
                if 'title' not in listing or 'price' not in listing:
                    continue
                
                # Some listings might have different URL field names
                url = listing.get('url', listing.get('link', ''))
                
                # Get listing ID from various possible fields
                listing_id = listing.get('listing_id', listing.get('item_id', ''))
                if not listing_id and 'id' in listing:
                    listing_id = listing['id']
                
                # Get image URL from various possible fields
                image_url = listing.get('image_url', listing.get('imageUrl', ''))
                
                # Get normalized title if available, or create one
                normalized_title = listing.get('normalized_title', listing.get('title', '').lower())
                
                all_products.append({
                    "marketplace": marketplace,
                    "title": listing["title"],
                    "price": self._extract_price(listing["price"]),
                    "url": url,
                    "listing_id": listing_id,
                    "image_url": image_url,
                    "subcategory": listing.get("subcategory", ""),
                    "condition": listing.get("condition", "New"),
                    "normalized_title": normalized_title
                })
        
        # Group products by similar titles
        from difflib import SequenceMatcher
        
        # Function to check title similarity
        def similar(a, b):
            """Check if two strings are similar"""
            if not a or not b:
                return False
            return SequenceMatcher(None, a, b).ratio() > 0.7
        
        # Find matching products across marketplaces
        processed = set()
        for i, product1 in enumerate(all_products):
            if i in processed:
                continue
                
            similar_products = [product1]
            title1 = product1["normalized_title"]
            
            for j, product2 in enumerate(all_products):
                if i == j or j in processed:
                    continue
                    
                title2 = product2["normalized_title"]
                # Only match across different marketplaces
                if similar(title1, title2) and product1["marketplace"] != product2["marketplace"]:
                    similar_products.append(product2)
                    processed.add(j)
            
            # Only consider opportunities with multiple matching products
            if len(similar_products) > 1:
                # Sort by price to find cheapest and most expensive
                similar_products.sort(key=lambda x: float(x["price"]))
                
                lowest = similar_products[0]
                highest = similar_products[-1]
                
                # Calculate price difference and profit margin
                try:
                    lowest_price = float(lowest["price"])
                    highest_price = float(highest["price"])
                    price_diff = highest_price - lowest_price
                    profit_margin = (price_diff / lowest_price) * 100 if lowest_price > 0 else 0
                    
                    # Only include opportunities with significant profit margin
                    if profit_margin > 15:  # Only include opportunities with >15% margin
                        self.arbitrage_opportunities.append({
                            "buy_from": lowest,
                            "sell_on": highest,
                            "price_difference": price_diff,
                            "profit_margin": profit_margin,
                            "similar_products": similar_products,
                            "timestamp": datetime.now().isoformat()
                        })
                except (ValueError, TypeError) as e:
                    logger.error(f"Error calculating price difference: {str(e)}")
        
        logger.info(f"Found {len(self.arbitrage_opportunities)} arbitrage opportunities")
        return self.arbitrage_opportunities
    
    def _extract_price(self, price_value):
        """
        Extract numerical price from various possible price formats.
        
        Args:
            price_value: Price value (could be string, float, int, or dictionary)
            
        Returns:
            float: Extracted price value
        """
        try:
            if isinstance(price_value, (int, float)):
                return float(price_value)
            
            if isinstance(price_value, str):
                # Remove currency symbols and commas
                price_clean = price_value.replace('$', '').replace(',', '').strip()
                # Extract first number if multiple are present
                price_match = re.search(r'(\d+(?:\.\d+)?)', price_clean)
                if price_match:
                    return float(price_match.group(1))
                return 0.0
            
            if isinstance(price_value, dict):
                # Some APIs might return a price object with value/currency
                if 'value' in price_value:
                    return float(price_value['value'])
                return 0.0
            
            return 0.0
        except (ValueError, TypeError):
            return 0.0
    
    def get_results_for_frontend(self):
        """
        Format results for the frontend application.
        
        Returns:
            Dict: Formatted results for frontend
        """
        # Find arbitrage opportunities if not already done
        if not self.arbitrage_opportunities:
            self.find_arbitrage_opportunities()
        
        # Format opportunities for frontend
        frontend_opportunities = []
        for opp in self.arbitrage_opportunities:
            # Extract key details for frontend display
            frontend_opp = {
                "title": opp["buy_from"]["title"],
                "buyTitle": opp["buy_from"]["title"],
                "sellTitle": opp["sell_on"]["title"],
                "buyPrice": round(float(opp["buy_from"]["price"]), 2),
                "sellPrice": round(float(opp["sell_on"]["price"]), 2),
                "buyMarketplace": opp["buy_from"]["marketplace"],
                "sellMarketplace": opp["sell_on"]["marketplace"],
                "buyLink": opp["buy_from"]["url"],
                "sellLink": opp["sell_on"]["url"],
                "profit": round(opp["price_difference"], 2),
                "profitPercentage": round(opp["profit_margin"], 2),
                "image_url": opp["buy_from"]["image_url"] or opp["sell_on"]["image_url"],
                "subcategory": opp["buy_from"].get("subcategory", ""),
                "buyCondition": opp["buy_from"].get("condition", "New"),
                "sellCondition": opp["sell_on"].get("condition", "New")
            }
            frontend_opportunities.append(frontend_opp)
        
        return {
            "raw_listings": self.results,
            "arbitrage_opportunities": frontend_opportunities,
            "meta": {
                "total_listings": sum(len(listings) for listings in self.results.values()),
                "opportunities_count": len(frontend_opportunities),
                "timestamp": datetime.now().isoformat()
            }
        }

# Example usage
async def main():
    manager = ScraperManager()
    
    # Run with subcategories
    subcategories = ["Headphones", "Keyboards"]
    await manager.run_all_scrapers(subcategories=subcategories)
    
    # Find opportunities
    opportunities = manager.find_arbitrage_opportunities()
    frontend_data = manager.get_results_for_frontend()
    
    # Output the results to show in console/terminal
    print(f"Total opportunities found: {len(opportunities)}")
    for i, opp in enumerate(opportunities[:5], 1):  # Show top 5 opportunities
        print(f"\nOpportunity #{i}:")
        print(f"Buy from {opp['buy_from']['marketplace']} at ${opp['buy_from']['price']}")
        print(f"Sell on {opp['sell_on']['marketplace']} at ${opp['sell_on']['price']}")
        print(f"Profit margin: {opp['profit_margin']:.2f}%")
    
    return frontend_data

if __name__ == "__main__":
    import re  # Add missing import for regex
    asyncio.run(main())
