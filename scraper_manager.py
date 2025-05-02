import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any

from ebay_scraper import EbayScraper
from amazon_scraper import AmazonScraper
from tcgplayer_scraper import TCGPlayerScraper
from walmart_scraper import WalmartScraper
from facebook_scraper import FacebookScraper
from etsy_scraper import EtsyScraper
from mercari_scraper import MercariScraper
from offerup_scraper import OfferUpScraper
from comprehensive_keywords import COMPREHENSIVE_KEYWORDS  # Fixed import

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
        self.scrapers = {
            'ebay': EbayScraper(),
            'amazon': AmazonScraper(),
            'tcgplayer': TCGPlayerScraper(),
            'walmart': WalmartScraper(),
            'facebook': FacebookScraper(),
            'etsy': EtsyScraper(),
            'mercari': MercariScraper(),
            'offerup': OfferUpScraper()
        }
        self.results = {}
        self.arbitrage_opportunities = []
        
    async def run_all_scrapers(self, keywords=None):
        """Run all scrapers with provided keywords or default comprehensive keywords"""
        if keywords is None:
            keywords = []
            # Extract keywords from all categories in COMPREHENSIVE_KEYWORDS
            for category, subcats in COMPREHENSIVE_KEYWORDS.items():
                for subcat, keyword_list in subcats.items():
                    # Take first 5 keywords from each subcategory
                    keywords.extend(keyword_list[:5])
        
        logger.info(f"Starting scraper run with {len(keywords)} keywords")
        tasks = []
        
        for marketplace, scraper in self.scrapers.items():
            tasks.append(self.run_scraper(marketplace, scraper, keywords))
        
        await asyncio.gather(*tasks)
        return self.results
    
    async def run_scraper(self, marketplace: str, scraper: Any, keywords: List[str]):
        """Run a specific scraper with the given keywords"""
        try:
            logger.info(f"Starting {marketplace} scraper with {len(keywords)} keywords")
            results = await scraper.search_listings(keywords)
            self.results[marketplace] = results
            logger.info(f"Completed {marketplace} scraper. Found {len(results)} listings")
            return results
        except Exception as e:
            logger.error(f"Error in {marketplace} scraper: {str(e)}")
            self.results[marketplace] = []
            return []
    
    def find_arbitrage_opportunities(self):
        """Analyze results from all marketplaces to find arbitrage opportunities"""
        logger.info("Finding arbitrage opportunities...")
        self.arbitrage_opportunities = []
        
        # Create a combined list of all products with their marketplace and price
        all_products = []
        for marketplace, listings in self.results.items():
            for listing in listings:
                all_products.append({
                    "marketplace": marketplace,
                    "title": listing["title"],
                    "price": listing["price"],
                    "url": listing["url"],
                    "listing_id": listing.get("listing_id", ""),
                    "image_url": listing.get("image_url", "")
                })
        
        # Group products by similar titles
        from difflib import SequenceMatcher
        
        def similar(a, b):
            """Check if two strings are similar"""
            return SequenceMatcher(None, a, b).ratio() > 0.7
        
        # Find matching products across marketplaces
        processed = set()
        for i, product1 in enumerate(all_products):
            if i in processed:
                continue
                
            similar_products = [product1]
            title1 = product1["title"].lower()
            
            for j, product2 in enumerate(all_products):
                if i == j or j in processed:
                    continue
                    
                title2 = product2["title"].lower()
                if similar(title1, title2) and product1["marketplace"] != product2["marketplace"]:
                    similar_products.append(product2)
                    processed.add(j)
            
            if len(similar_products) > 1:
                # Sort by price
                similar_products.sort(key=lambda x: float(x["price"]) if isinstance(x["price"], (int, float)) else 
                                     float(str(x["price"]).replace("$", "").replace(",", "")))
                
                lowest = similar_products[0]
                highest = similar_products[-1]
                
                # Calculate price difference
                try:
                    lowest_price = float(lowest["price"]) if isinstance(lowest["price"], (int, float)) else float(str(lowest["price"]).replace("$", "").replace(",", ""))
                    highest_price = float(highest["price"]) if isinstance(highest["price"], (int, float)) else float(str(highest["price"]).replace("$", "").replace(",", ""))
                    price_diff = highest_price - lowest_price
                    profit_margin = (price_diff / lowest_price) * 100  # as percentage
                    
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
    
    def get_results_for_frontend(self):
        """Format results for the frontend application"""
        # Find arbitrage opportunities if not already done
        if not self.arbitrage_opportunities:
            self.find_arbitrage_opportunities()
        
        return {
            "raw_listings": self.results,
            "arbitrage_opportunities": self.arbitrage_opportunities,
            "meta": {
                "total_listings": sum(len(listings) for listings in self.results.values()),
                "opportunities_count": len(self.arbitrage_opportunities),
                "timestamp": datetime.now().isoformat()
            }
        }

# Example usage
async def main():
    manager = ScraperManager()
    await manager.run_all_scrapers()
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
    asyncio.run(main())
