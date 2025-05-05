"""
FlipHawk - Scraper Manager
Coordinates multiple marketplace scrapers and finds arbitrage opportunities
"""

import asyncio
import logging
import random
from typing import List, Dict, Any
from datetime import datetime

# Import scrapers
try:
    from amazon_scraper import run_amazon_search
    amazon_available = True
except ImportError:
    amazon_available = False
    print("Amazon scraper not available")

try:
    from ebay_scraper import run_ebay_search
    ebay_available = True
except ImportError:
    ebay_available = False
    print("eBay scraper not available")

try:
    from etsy_scraper import run_etsy_search
    etsy_available = True
except ImportError:
    etsy_available = False
    print("Etsy scraper not available")

try:
    from facebook_scraper import run_facebook_search
    facebook_available = True
except ImportError:
    facebook_available = False
    print("Facebook scraper not available")

# Import keyword generator
from comprehensive_keywords import generate_keywords

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('scraper_manager')

class ScraperManager:
    """
    Manages multiple marketplace scrapers and finds arbitrage opportunities
    between listings on different platforms.
    """
    
    def __init__(self):
        """Initialize the scraper manager with available scrapers."""
        self.scrapers = {}
        self.raw_listings = {}
        self.arbitrage_opportunities = []
        self.last_scan_time = None
        
        # Add available scrapers
        if amazon_available:
            self.scrapers['amazon'] = run_amazon_search
            self.raw_listings['amazon'] = []
        
        if ebay_available:
            self.scrapers['ebay'] = run_ebay_search
            self.raw_listings['ebay'] = []
        
        if etsy_available:
            self.scrapers['etsy'] = run_etsy_search
            self.raw_listings['etsy'] = []
        
        if facebook_available:
            self.scrapers['facebook'] = run_facebook_search
            self.raw_listings['facebook'] = []
        
        # If no scrapers are available, create a dummy scraper for testing
        if not self.scrapers:
            logger.warning("No scrapers available. Using dummy scraper for testing.")
            self.scrapers['dummy'] = self._dummy_search
            self.raw_listings['dummy'] = []
        
        logger.info(f"ScraperManager initialized with scrapers: {', '.join(self.scrapers.keys())}")
    
    async def _dummy_search(self, subcategories: List[str]) -> List[Dict[str, Any]]:
        """
        Dummy search function for testing when no real scrapers are available.
        Generates fake product listings based on subcategories.
        """
        # Wait a bit to simulate real search
        await asyncio.sleep(2)
        
        all_listings = []
        brands = {
            "Headphones": ["Sony", "Bose", "Apple", "Sennheiser", "JBL"],
            "Keyboards": ["Logitech", "Corsair", "Razer", "HyperX", "Keychron"],
            "Graphics Cards": ["NVIDIA", "AMD", "ASUS", "MSI", "EVGA"],
            "Monitors": ["LG", "Samsung", "Dell", "ASUS", "ViewSonic"],
            "Vintage Tech": ["Sony", "Nintendo", "Apple", "IBM", "Commodore"],
            "Default": ["Brand A", "Brand B", "Brand C", "Brand D", "Brand E"]
        }
        
        conditions = ["New", "Like New", "Very Good", "Good", "Acceptable"]
        
        for subcategory in subcategories:
            # Get relevant brands for this subcategory
            subcategory_brands = brands.get(subcategory, brands["Default"])
            
            # Generate 10-20 listings for this subcategory
            num_listings = random.randint(10, 20)
            
            for i in range(num_listings):
                brand = random.choice(subcategory_brands)
                condition = random.choice(conditions)
                price = round(random.uniform(20, 500), 2)
                
                listing = {
                    "title": f"{brand} {subcategory} Model {random.randint(100, 999)}",
                    "price": price,
                    "link": f"https://example.com/product/{i}",
                    "image_url": f"https://example.com/images/{i}.jpg",
                    "condition": condition,
                    "seller_rating": random.randint(80, 100),
                    "free_shipping": random.choice([True, False]),
                    "source": "dummy",
                    "subcategory": subcategory,
                    "listing_id": f"dummy-{i}",
                    "timestamp": datetime.now().isoformat()
                }
                
                all_listings.append(listing)
        
        return all_listings
    
    async def run_all_scrapers(self, subcategories: List[str]) -> bool:
        """
        Run all available scrapers for the specified subcategories.
        
        Args:
            subcategories (List[str]): List of subcategories to search
            
        Returns:
            bool: True if scan was successful, False otherwise
        """
        try:
            # Clear previous results
            for marketplace in self.raw_listings:
                self.raw_listings[marketplace] = []
            
            self.arbitrage_opportunities = []
            self.last_scan_time = datetime.now()
            
            # Create tasks for all scrapers
            tasks = []
            for marketplace, scraper_func in self.scrapers.items():
                tasks.append(self._run_scraper(marketplace, scraper_func, subcategories))
            
            # Wait for all scrapers to complete
            await asyncio.gather(*tasks)
            
            # Log results
            total_listings = sum(len(listings) for listings in self.raw_listings.values())
            logger.info(f"Scan completed. Found {total_listings} total listings across all marketplaces.")
            
            return True
            
        except Exception as e:
            logger.error(f"Error running scrapers: {str(e)}")
            return False
    
    async def _run_scraper(self, marketplace: str, scraper_func, subcategories: List[str]):
        """Run a specific scraper and store the results."""
        try:
            logger.info(f"Running {marketplace} scraper for {len(subcategories)} subcategories")
            start_time = datetime.now()
            
            # Run the scraper function
            listings = await scraper_func(subcategories)
            
            # Store the results
            self.raw_listings[marketplace] = listings
            
            # Log completion
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"{marketplace} scraper completed in {duration:.2f}s. Found {len(listings)} listings.")
            
        except Exception as e:
            logger.error(f"Error running {marketplace} scraper: {str(e)}")
            self.raw_listings[marketplace] = []
    
    def find_arbitrage_opportunities(self) -> List[Dict[str, Any]]:
        """
        Find arbitrage opportunities by comparing listings across marketplaces.
        
        Returns:
            List[Dict[str, Any]]: List of arbitrage opportunities
        """
        try:
            self.arbitrage_opportunities = []
            
            # Get lists of listings from each marketplace
            all_marketplaces = list(self.raw_listings.keys())
            
            # Need at least 2 marketplaces with listings
            valid_marketplaces = [m for m in all_marketplaces if self.raw_listings[m]]
            if len(valid_marketplaces) < 2:
                logger.warning("Not enough marketplaces with listings to find arbitrage opportunities")
                return []
            
            # Compare each marketplace with every other marketplace
            for i, buy_marketplace in enumerate(valid_marketplaces):
                for sell_marketplace in valid_marketplaces[i+1:]:
                    # Skip comparing a marketplace with itself
                    if buy_marketplace == sell_marketplace:
                        continue
                    
                    # Compare listings
                    buy_listings = self.raw_listings[buy_marketplace]
                    sell_listings = self.raw_listings[sell_marketplace]
                    
                    # Find opportunities
                    opportunities = self._compare_listings(buy_listings, sell_listings, buy_marketplace, sell_marketplace)
                    self.arbitrage_opportunities.extend(opportunities)
                    
                    # Also check the other direction (sell_marketplace -> buy_marketplace)
                    opportunities = self._compare_listings(sell_listings, buy_listings, sell_marketplace, buy_marketplace)
                    self.arbitrage_opportunities.extend(opportunities)
            
            # Sort opportunities by profit (highest first)
            self.arbitrage_opportunities.sort(key=lambda x: x['profit'], reverse=True)
            
            logger.info(f"Found {len(self.arbitrage_opportunities)} arbitrage opportunities")
            return self.arbitrage_opportunities
            
        except Exception as e:
            logger.error(f"Error finding arbitrage opportunities: {str(e)}")
            return []
    
    def _compare_listings(self, buy_listings: List[Dict], sell_listings: List[Dict], 
                          buy_marketplace: str, sell_marketplace: str) -> List[Dict]:
        """
        Compare listings between two marketplaces to find arbitrage opportunities.
        
        Args:
            buy_listings: List of listings from the buy marketplace
            sell_listings: List of listings from the sell marketplace
            buy_marketplace: Name of the buy marketplace
            sell_marketplace: Name of the sell marketplace
            
        Returns:
            List of arbitrage opportunities
        """
        opportunities = []
        
        # Simple title matching algorithm
        for buy_listing in buy_listings:
            buy_title = buy_listing.get('title', '').lower()
            buy_price = buy_listing.get('price', 0)
            
            if not buy_title or buy_price <= 0:
                continue
            
            for sell_listing in sell_listings:
                sell_title = sell_listing.get('title', '').lower()
                sell_price = sell_listing.get('price', 0)
                
                if not sell_title or sell_price <= 0:
                    continue
                
                # Skip if sell price is not higher than buy price
                if sell_price <= buy_price:
                    continue
                
                # Calculate title similarity
                similarity = self._calculate_title_similarity(buy_title, sell_title)
                
                # If similarity is high enough, consider it a match
                if similarity >= 0.5:
                    # Calculate profit
                    profit = sell_price - buy_price
                    
                    # Calculate fees (estimated)
                    marketplace_fee = self._calculate_marketplace_fee(sell_marketplace, sell_price)
                    shipping_cost = self._estimate_shipping_cost(buy_listing.get('subcategory', ''), buy_price)
                    
                    # Adjust profit
                    adjusted_profit = profit - marketplace_fee - shipping_cost
                    
                    # Skip if not profitable
                    if adjusted_profit <= 0:
                        continue
                    
                    # Prepare opportunity data
                    opportunity = {
                        'buyTitle': buy_listing.get('title', ''),
                        'buyPrice': buy_price,
                        'buyLink': buy_listing.get('link', ''),
                        'buyMarketplace': buy_marketplace,
                        'buyImage': buy_listing.get('image_url', ''),
                        'buyCondition': buy_listing.get('condition', 'Unknown'),
                        
                        'sellTitle': sell_listing.get('title', ''),
                        'sellPrice': sell_price,
                        'sellLink': sell_listing.get('link', ''),
                        'sellMarketplace': sell_marketplace,
                        'sellImage': sell_listing.get('image_url', ''),
                        'sellCondition': sell_listing.get('condition', 'Unknown'),
                        
                        'profit': round(adjusted_profit, 2),
                        'profitPercentage': round((adjusted_profit / buy_price) * 100, 2),
                        'fees': {
                            'marketplace': round(marketplace_fee, 2),
                            'shipping': round(shipping_cost, 2)
                        },
                        
                        'similarity': round(similarity * 100),
                        'confidence': round(similarity * 100),
                        'subcategory': buy_listing.get('subcategory', ''),
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    opportunities.append(opportunity)
        
        return opportunities
    
    def _calculate_title_similarity(self, title1: str, title2: str) -> float:
        """
        Calculate the similarity between two titles.
        This is a simple implementation - you might want to use more sophisticated NLP techniques.
        
        Args:
            title1: First title
            title2: Second title
            
        Returns:
            float: Similarity score between 0 and 1
        """
        # Normalize titles
        title1 = title1.lower()
        title2 = title2.lower()
        
        # Split into words
        words1 = set(title1.split())
        words2 = set(title2.split())
        
        # Calculate Jaccard similarity
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        if union == 0:
            return 0
        
        return intersection / union
    
    def _calculate_marketplace_fee(self, marketplace: str, price: float) -> float:
        """
        Estimate the marketplace fee.
        
        Args:
            marketplace: Marketplace name
            price: Selling price
            
        Returns:
            float: Estimated fee
        """
        # Default fee is 10%
        fee_percentage = 0.10
        
        # Adjust based on marketplace
        if marketplace == 'amazon':
            fee_percentage = 0.15
        elif marketplace == 'ebay':
            fee_percentage = 0.12
        elif marketplace == 'etsy':
            fee_percentage = 0.08
        elif marketplace == 'facebook':
            fee_percentage = 0.05
        
        return price * fee_percentage
    
    def _estimate_shipping_cost(self, subcategory: str, price: float) -> float:
        """
        Estimate shipping cost based on subcategory and price.
        
        Args:
            subcategory: Product subcategory
            price: Product price
            
        Returns:
            float: Estimated shipping cost
        """
        # Default shipping cost
        shipping_cost = 5.99
        
        # Adjust based on subcategory
        if subcategory == 'Headphones':
            shipping_cost = 7.99
        elif subcategory == 'Keyboards':
            shipping_cost = 9.99
        elif subcategory == 'Graphics Cards':
            shipping_cost = 12.99
        elif subcategory == 'Monitors':
            shipping_cost = 19.99
        elif subcategory == 'Laptops':
            shipping_cost = 14.99
        
        # Add insurance for expensive items
        if price > 100:
            shipping_cost += 3.99
        
        return shipping_cost
    
    def get_results_for_frontend(self) -> Dict[str, Any]:
        """
        Format the results for the frontend.
        
        Returns:
            Dict containing raw listings and arbitrage opportunities
        """
        # Count listings by marketplace
        marketplace_counts = {m: len(listings) for m, listings in self.raw_listings.items()}
        
        # Group opportunities by subcategory
        subcategory_counts = {}
        for opp in self.arbitrage_opportunities:
            subcategory = opp.get('subcategory', 'Other')
            subcategory_counts[subcategory] = subcategory_counts.get(subcategory, 0) + 1
        
        return {
            "raw_listings": self.raw_listings,
            "arbitrage_opportunities": self.arbitrage_opportunities,
            "meta": {
                "timestamp": datetime.now().isoformat(),
                "marketplace_counts": marketplace_counts,
                "subcategory_counts": subcategory_counts,
                "total_opportunities": len(self.arbitrage_opportunities)
            }
        }
