"""
Enhanced unified marketplace scanner for FlipHawk arbitrage system.
This module combines all the marketplace scrapers and finds arbitrage opportunities.
"""

import asyncio
import time
import logging
import random
import numpy as np
from typing import List, Dict, Any, Tuple
from difflib import SequenceMatcher
import re
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('marketplace_scanner')

class ArbitrageAnalyzer:
    """Analyze arbitrage opportunities across marketplaces."""
    
    def __init__(self):
        """Initialize the arbitrage analyzer."""
        self.model_patterns = [
            r'(?:model|part|sku|item|ref)?\s*(?:#|number|no\.?)?\s*([a-z0-9]{4,})',
            r'[a-z]+\d+[a-z]*\d*',
            r'\d{3,}[a-z]+\d*'
        ]
    
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
    
    def _normalize_title(self, title: str) -> str:
        """
        Normalize a title by removing common prefixes, suffixes, and noise.
        
        Args:
            title (str): The title to normalize
            
        Returns:
            str: Normalized title
        """
        # Convert to lowercase
        title = title.lower()
        
        # Remove common prefixes and suffixes
        prefixes = ['new', 'brand new', 'authentic', 'genuine', 'original', 'official', 'sealed']
        for prefix in prefixes:
            if title.startswith(prefix):
                title = title[len(prefix):].strip()
        
        suffixes = ['in stock', 'free shipping', 'fast shipping', 'brand new', 'with warranty', 'with guarantee']
        for suffix in suffixes:
            if title.endswith(suffix):
                title = title[:-len(suffix)].strip()
        
        # Remove special characters and extra spaces
        title = re.sub(r'[^\w\s]', ' ', title)
        title = re.sub(r'\s+', ' ', title).strip()
        
        return title
    
    def _extract_model_numbers(self, title: str) -> List[str]:
        """
        Extract possible model numbers from a title.
        
        Args:
            title (str): The title to extract from
            
        Returns:
            List[str]: Extracted model numbers
        """
        models = []
        for pattern in self.model_patterns:
            matches = re.findall(pattern, title)
            models.extend(matches)
        
        # Remove duplicates
        return list(set(models))
    
    def find_opportunities(self, listings: List[Dict[str, Any]], min_profit: float = 10.0, min_profit_percent: float = 20.0) -> List[Dict[str, Any]]:
        """
        Find arbitrage opportunities within the listings.
        
        Args:
            listings (List[Dict[str, Any]]): List of product listings from all marketplaces
            min_profit (float): Minimum profit threshold in dollars
            min_profit_percent (float): Minimum profit threshold as a percentage
            
        Returns:
            List[Dict[str, Any]]: List of found arbitrage opportunities
        """
        logger.info(f"Finding arbitrage opportunities among {len(listings)} listings...")
        
        # Group listings by source (marketplace)
        listings_by_source = {}
        for listing in listings:
            source = listing.get('source', 'unknown')
            if source not in listings_by_source:
                listings_by_source[source] = []
            listings_by_source[source].append(listing)
        
        # Extract unique marketplace names
        marketplaces = list(listings_by_source.keys())
        logger.info(f"Marketplaces: {marketplaces}")
        
        # Create all possible marketplace pairs for comparison
        marketplace_pairs = []
        for i in range(len(marketplaces)):
            for j in range(len(marketplaces)):
                if i != j:  # Don't compare a marketplace to itself
                    marketplace_pairs.append((marketplaces[i], marketplaces[j]))
        
        opportunities = []
        
        # Compare listings across marketplace pairs
        for source_buy, source_sell in marketplace_pairs:
            buy_listings = listings_by_source.get(source_buy, [])
            sell_listings = listings_by_source.get(source_sell, [])
            
            logger.info(f"Comparing {len(buy_listings)} buy listings from {source_buy} with {len(sell_listings)} sell listings from {source_sell}")
            
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
                    
                    # Skip if sell price is not higher than buy price
                    if sell_price <= buy_price:
                        continue
                    
                    # Calculate similarity between listings
                    similarity = self.calculate_similarity(buy_title, sell_title)
                    
                    # Only consider listings that are similar enough
                    if similarity >= 0.7:
                        # Calculate profit metrics
                        profit = sell_price - buy_price
                        profit_percentage = (profit / buy_price) * 100 if buy_price > 0 else 0
                        
                        # Check profit thresholds
                        if profit >= min_profit and profit_percentage >= min_profit_percent:
                            # Calculate additional metrics
                            marketplace_fee = self._calculate_marketplace_fee(source_sell, sell_price)
                            shipping_cost = self._estimate_shipping_cost(buy_listing.get('subcategory', ''), buy_price)
                            
                            # Calculate adjusted profit
                            adjusted_profit = profit - marketplace_fee - shipping_cost
                            
                            # Skip if not profitable after fees
                            if adjusted_profit <= 0:
                                continue
                            
                            # Calculate confidence score based on similarity
                            confidence = int(similarity * 100)
                            
                            # Create opportunity object
                            opportunity = {
                                'buyTitle': buy_listing.get('title', ''),
                                'buyPrice': buy_price,
                                'buyLink': buy_listing.get('link', ''),
                                'buyMarketplace': source_buy,
                                'buyImage': buy_listing.get('image_url', ''),
                                'buyCondition': buy_listing.get('condition', 'New'),
                                
                                'sellTitle': sell_listing.get('title', ''),
                                'sellPrice': sell_price,
                                'sellLink': sell_listing.get('link', ''),
                                'sellMarketplace': source_sell,
                                'sellImage': sell_listing.get('image_url', ''),
                                'sellCondition': sell_listing.get('condition', 'New'),
                                
                                'profit': adjusted_profit,
                                'profitPercentage': (adjusted_profit / buy_price) * 100,
                                'fees': {
                                    'marketplace': marketplace_fee,
                                    'shipping': shipping_cost
                                },
                                
                                'similarity': similarity * 100,
                                'confidence': confidence,
                                'subcategory': buy_listing.get('subcategory', ''),
                                'timestamp': datetime.now().isoformat()
                            }
                            
                            opportunities.append(opportunity)
        
        # Sort opportunities by profit
        opportunities.sort(key=lambda x: x['profit'], reverse=True)
        
        logger.info(f"Found {len(opportunities)} arbitrage opportunities")
        return opportunities
    
    def _calculate_marketplace_fee(self, marketplace: str, price: float) -> float:
        """
        Calculate marketplace fees for selling.
        
        Args:
            marketplace (str): Marketplace name
            price (float): Selling price
            
        Returns:
            float: Estimated marketplace fee
        """
        # Default fee rate
        fee_percentage = 0.1  # 10%
        
        # Adjust based on marketplace
        if marketplace.lower() == 'amazon':
            fee_percentage = 0.15  # 15%
        elif marketplace.lower() == 'ebay':
            fee_percentage = 0.13  # 13%
        elif marketplace.lower() == 'etsy':
            fee_percentage = 0.08  # 8%
        elif marketplace.lower() == 'facebook':
            fee_percentage = 0.05  # 5%
        elif marketplace.lower() == 'mercari':
            fee_percentage = 0.10  # 10%
        
        return price * fee_percentage
    
    def _estimate_shipping_cost(self, subcategory: str, price: float) -> float:
        """
        Estimate shipping cost based on subcategory and price.
        
        Args:
            subcategory (str): Item subcategory
            price (float): Item price
            
        Returns:
            float: Estimated shipping cost
        """
        # Default shipping
        base_shipping = 5.99
        
        # Adjust based on subcategory
        if subcategory == 'Headphones':
            base_shipping = 7.99
        elif subcategory == 'Keyboards':
            base_shipping = 12.99
        elif subcategory == 'Graphics Cards':
            base_shipping = 14.99
        elif subcategory == 'Monitors':
            base_shipping = 24.99
        elif subcategory == 'Vintage Tech':
            base_shipping = 9.99
        elif subcategory == 'Jordans' or subcategory == 'Nike Dunks':
            base_shipping = 9.99
        elif subcategory in ['Pokémon', 'Magic: The Gathering', 'Yu-Gi-Oh']:
            base_shipping = 4.99
        
        # Add insurance for expensive items
        insurance = 0.0
        if price > 100:
            insurance = 3.99
        elif price > 500:
            insurance = 8.99
        
        return base_shipping + insurance

# Function to run a complete arbitrage scan
def run_arbitrage_scan(subcategories: List[str]) -> List[Dict[str, Any]]:
    """
    Run a complete arbitrage scan for the given subcategories.
    
    Args:
        subcategories (List[str]): List of subcategories to scan
        
    Returns:
        List[Dict[str, Any]]: List of arbitrage opportunities
    """
    logger.info(f"Starting arbitrage scan for subcategories: {subcategories}")
    
    try:
        # Create an event loop for the async operations
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Import available scrapers
        scrapers = []
        
        try:
            from amazon_scraper import run_amazon_search
            scrapers.append(("amazon", run_amazon_search))
        except ImportError:
            logger.warning("Amazon scraper not available")
        
        try:
            from ebay_scraper import run_ebay_search
            scrapers.append(("ebay", run_ebay_search))
        except ImportError:
            logger.warning("eBay scraper not available")
        
        try:
            from facebook_scraper import run_facebook_search
            scrapers.append(("facebook", run_facebook_search))
        except ImportError:
            logger.warning("Facebook scraper not available")
        
        # Run all available scrapers
        start_time = time.time()
        all_listings = []
        
        tasks = []
        for name, scraper_func in scrapers:
            logger.info(f"Adding {name} scraper to tasks")
            task = asyncio.ensure_future(scraper_func(subcategories))
            tasks.append(task)
        
        # Run all scrapers concurrently
        results = loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
        
        # Process results and combine listings
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error from scraper {scrapers[i][0]}: {str(result)}")
            elif result:
                name = scrapers[i][0]
                logger.info(f"Got {len(result)} listings from {name}")
                all_listings.extend(result)
        
        # Find arbitrage opportunities
        analyzer = ArbitrageAnalyzer()
        opportunities = analyzer.find_opportunities(all_listings)
        
        # Return results
        elapsed_time = time.time() - start_time
        logger.info(f"Arbitrage scan completed in {elapsed_time:.2f} seconds, found {len(opportunities)} opportunities")
        
        return opportunities
    
    except Exception as e:
        logger.error(f"Error running arbitrage scan: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return []
