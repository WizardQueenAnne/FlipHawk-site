"""
Unified marketplace scanner for FlipHawk arbitrage system.
This module combines all the marketplace scrapers and finds arbitrage opportunities.
"""

import asyncio
import time
import logging
import random
import numpy as np
from typing import List, Dict, Any, Tuple
from difflib import SequenceMatcher
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Import scrapers
from amazon_scraper import run_amazon_search
from ebay_scraper import run_ebay_search
from walmart_scraper import run_walmart_search

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
        self.vectorizer = TfidfVectorizer(
            stop_words='english',
            ngram_range=(1, 3),
            max_features=5000
        )
        self.model_patterns = [
            r'(?:model|part|sku|item|ref)?\s*(?:#|number|no\.?)?\s*([a-z0-9]{4,})',
            r'[a-z]+\d+[a-z]*\d*',
            r'\d{3,}[a-z]+\d*'
        ]
    
    def calculate_similarity(self, title1: str, title2: str) -> float:
        """
        Calculate similarity using multiple methods with better scoring for exact matches.
        
        Args:
            title1 (str): First title
            title2 (str): Second title
            
        Returns:
            float: Similarity score between 0 and 1
        """
        # Basic sequence matching
        sequence_sim = SequenceMatcher(None, title1, title2).ratio()
        
        # TF-IDF cosine similarity
        try:
            tfidf_matrix = self.vectorizer.fit_transform([title1, title2])
            cosine_sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        except:
            cosine_sim = 0.0
        
        # Check for exact substring matches
        words1 = set(title1.split())
        words2 = set(title2.split())
        word_overlap = len(words1.intersection(words2)) / len(words1.union(words2)) if words1 and words2 else 0
        
        # If titles are very similar or have significant overlap, boost the score
        if sequence_sim > 0.8 or word_overlap > 0.7:
            sequence_sim = min(1.0, sequence_sim * 1.2)
            word_overlap = min(1.0, word_overlap * 1.2)
        
        # Weighted combination with improved scoring
        weights = {
            'sequence': 0.3,
            'cosine': 0.4,
            'word_overlap': 0.3
        }
        
        final_similarity = (
            weights['sequence'] * sequence_sim +
            weights['cosine'] * cosine_sim +
            weights['word_overlap'] * word_overlap
        )
        
        # Boost exact matches
        if sequence_sim > 0.95:
            final_similarity = min(1.0, final_similarity * 1.1)
        
        return final_similarity
    
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
            source = listing.get('source')
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
                for sell_listing in sell_listings:
                    # Calculate similarity between listings
                    buy_title = buy_listing.get('normalized_title', '')
                    sell_title = sell_listing.get('normalized_title', '')
                    
                    if not buy_title or not sell_title:
                        continue
                    
                    similarity = self.calculate_similarity(buy_title, sell_title)
                    
                    # Only consider listings that are similar enough
                    if similarity >= 0.7:
                        # Calculate profit metrics
                        buy_price = buy_listing.get('price', 0)
                        sell_price = sell_listing.get('price', 0)
                        
                        # Add shipping costs if available
                        buy_shipping = buy_listing.get('shipping_cost', 0)
                        if not buy_listing.get('free_shipping', False):
                            buy_price += buy_shipping
                        
                        profit = sell_price - buy_price
                        profit_percentage = (profit / buy_price) * 100 if buy_price > 0 else 0
                        
                        # Check profit thresholds
                        if profit >= min_profit and profit_percentage >= min_profit_percent:
                            # Calculate confidence score based on similarity
                            confidence = self._calculate_confidence(buy_listing, sell_listing, similarity, profit_percentage)
                            
                            # Only include opportunities with reasonable confidence
                            if confidence >= 60:
                                opportunity = {
                                    'title': buy_listing.get('title'),
                                    'buy_title': buy_listing.get('title'),
                                    'sell_title': sell_listing.get('title'),
                                    'buy_price': buy_price,
                                    'sell_price': sell_price,
                                    'buy_marketplace': source_buy,
                                    'sell_marketplace': source_sell,
                                    'buy_link': buy_listing.get('link'),
                                    'sell_link': sell_listing.get('link'),
                                    'profit': profit,
                                    'profit_percentage': profit_percentage,
                                    'confidence': round(confidence),
                                    'similarity': similarity,
                                    'buy_condition': buy_listing.get('condition', 'New'),
                                    'sell_condition': sell_listing.get('condition', 'New'),
                                    'buy_shipping': buy_shipping,
                                    'image_url': buy_listing.get('image_url') or sell_listing.get('image_url'),
                                    'subcategory': buy_listing.get('subcategory'),
                                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                                }
                                
                                opportunities.append(opportunity)
        
        # Sort opportunities by profit percentage
        opportunities.sort(key=lambda x: x['profit_percentage'], reverse=True)
        
        logger.info(f"Found {len(opportunities)} arbitrage opportunities")
        return opportunities
    
    def _calculate_confidence(self, buy_listing: Dict[str, Any], sell_listing: Dict[str, Any], similarity: float, profit_percentage: float) -> float:
        """
        Calculate confidence score for the arbitrage opportunity.
        
        Args:
            buy_listing (Dict[str, Any]): Listing to buy from
            sell_listing (Dict[str, Any]): Listing to sell on
            similarity (float): Title similarity score
            profit_percentage (float): Profit percentage
            
        Returns:
            float: Confidence score between 0 and 100
        """
        # Base confidence from similarity - boost if high similarity
        if similarity >= 0.9:
            base_confidence = 95  # Very high confidence for nearly identical matches
        elif similarity >= 0.8:
            base_confidence = 85
        else:
            base_confidence = similarity * 100
        
        # Condition penalty - less severe for very high similarity
        condition_penalty = 0
        buy_condition = buy_listing.get('condition', 'New').lower()
        sell_condition = sell_listing.get('condition', 'New').lower()
        
        if buy_condition != sell_condition:
            if similarity >= 0.9:
                condition_penalty = 5  # Minor penalty for high similarity matches
            else:
                condition_penalty = 10
        
        # Bonus for high profit percentage
        profit_bonus = min(5, profit_percentage / 10)
        
        # Calculate final confidence
        confidence = base_confidence - condition_penalty + profit_bonus
        
        # Ensure confidence reflects true matches better
        if similarity >= 0.9 and confidence < 90:
            confidence = 90  # Minimum 90% confidence for very similar items
        
        return max(0, min(100, confidence))

async def scan_marketplaces(subcategories: List[str]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Scan multiple marketplaces for the given subcategories.
    
    Args:
        subcategories (List[str]): List of subcategories to search for
        
    Returns:
        Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]: (All listings, Arbitrage opportunities)
    """
    logger.info(f"Starting marketplace scan for subcategories: {subcategories}")
    
    # Run marketplace searches concurrently
    try:
        amazon_task = asyncio.create_task(run_amazon_search(subcategories))
        ebay_task = asyncio.create_task(run_ebay_search(subcategories))
        walmart_task = asyncio.create_task(run_walmart_search(subcategories))
        
        # Wait for all searches to complete
        amazon_results, ebay_results, walmart_results = await asyncio.gather(
            amazon_task, ebay_task, walmart_task
        )
        
        # Combine all listings
        all_listings = amazon_results + ebay_results + walmart_results
        
        logger.info(f"Total listings found: {len(all_listings)}")
        logger.info(f"- Amazon: {len(amazon_results)} listings")
        logger.info(f"- eBay: {len(ebay_results)} listings")
        logger.info(f"- Walmart: {len(walmart_results)} listings")
        
        # Find arbitrage opportunities
        analyzer = ArbitrageAnalyzer()
        opportunities = analyzer.find_opportunities(all_listings)
        
        return all_listings, opportunities
        
    except Exception as e:
        logger.error(f"Error during marketplace scan: {str(e)}")
        return [], []

def calculate_profit_metrics(opportunity: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate additional profit metrics for an opportunity.
    
    Args:
        opportunity (Dict[str, Any]): Arbitrage opportunity
        
    Returns:
        Dict[str, Any]: Updated opportunity with additional metrics
    """
    # Copy the opportunity to avoid modifying the original
    updated = opportunity.copy()
    
    # Calculate tax (approximate as 8% of buy price)
    buy_price = updated.get('buy_price', 0)
    sell_price = updated.get('sell_price', 0)
    
    estimated_tax = buy_price * 0.08
    updated['estimated_tax'] = round(estimated_tax, 2)
    
    # Calculate shipping (if not already included)
    buy_shipping = updated.get('buy_shipping', 0)
    
    # Calculate platform fees (approximate)
    sell_marketplace = updated.get('sell_marketplace', '').lower()
    
    if 'ebay' in sell_marketplace:
        # eBay fee: 10-15% of sell price including shipping
        sell_fee = sell_price * 0.125  # 12.5% average
        updated['platform_fee'] = round(sell_fee, 2)
        
        # PayPal fee (2.9% + $0.30)
        payment_fee = sell_price * 0.029 + 0.30
        updated['payment_fee'] = round(payment_fee, 2)
    
    elif 'amazon' in sell_marketplace:
        # Amazon fee: 15% of sell price + variable closing fee
        sell_fee = sell_price * 0.15 + 1.80  # $1.80 variable closing fee
        updated['platform_fee'] = round(sell_fee, 2)
        updated['payment_fee'] = 0  # Included in platform fee
    
    elif 'walmart' in sell_marketplace:
        # Walmart fee: 15% of sell price
        sell_fee = sell_price * 0.15
        updated['platform_fee'] = round(sell_fee, 2)
        updated['payment_fee'] = 0  # Included in platform fee
    
    else:
        # Default fees if marketplace is unknown
        sell_fee = sell_price * 0.10
        updated['platform_fee'] = round(sell_fee, 2)
        payment_fee = sell_price * 0.029 + 0.30
        updated['payment_fee'] = round(payment_fee, 2)
    
    # Calculate total cost
    total_cost = buy_price + estimated_tax + buy_shipping
    updated['total_cost'] = round(total_cost, 2)
    
    # Calculate total fees
    platform_fee = updated.get('platform_fee', 0)
    payment_fee = updated.get('payment_fee', 0)
    total_fees = platform_fee + payment_fee
    updated['total_fees'] = round(total_fees, 2)
    
    # Calculate net profit
    net_profit = sell_price - total_cost - total_fees
    updated['net_profit'] = round(net_profit, 2)
    
    # Calculate net profit percentage (ROI)
    net_profit_percentage = (net_profit / total_cost) * 100 if total_cost > 0 else 0
    updated['net_profit_percentage'] = round(net_profit_percentage, 2)
    
    return updated

def calculate_velocity_score(opportunity: Dict[str, Any]) -> int:
    """
    Calculate how quickly an item is likely to sell (0-100).
    
    Args:
        opportunity (Dict[str, Any]): Arbitrage opportunity
        
    Returns:
        int: Velocity score from 0 to 100
    """
    score = 50  # Base score
    
    # Adjust based on profit percentage
    profit_percentage = opportunity.get('profit_percentage', 0)
    if profit_percentage > 50:
        score += 20
    elif profit_percentage > 30:
        score += 10
    
    # Adjust based on confidence
    confidence = opportunity.get('confidence', 0)
    if confidence > 90:
        score += 15
    elif confidence > 80:
        score += 10
    
    # Adjust based on marketplace
    sell_marketplace = opportunity.get('sell_marketplace', '').lower()
    if 'ebay' in sell_marketplace:
        score += 5  # eBay tends to have higher velocity
    elif 'amazon' in sell_marketplace:
        score += 10  # Amazon typically has highest velocity
    
    # Adjust based on subcategory (if available)
    subcategory = opportunity.get('subcategory', '')
    high_velocity_categories = ['Headphones', 'Graphics Cards', 'Laptops', 'Consoles', 'Nike Dunks', 'Jordans']
    if any(subcat in subcategory for subcat in high_velocity_categories):
        score += 10
    
    return min(100, max(0, score))

def estimate_sell_days(opportunity: Dict[str, Any], velocity_score: int) -> int:
    """
    Estimate how many days until the item sells.
    
    Args:
        opportunity (Dict[str, Any]): Arbitrage opportunity
        velocity_score (int): The calculated velocity score
        
    Returns:
        int: Estimated number of days to sell
    """
    if velocity_score > 80:
        return 3
    elif velocity_score > 60:
        return 7
    elif velocity_score > 40:
        return 14
    else:
        return 21

def run_arbitrage_scan(subcategories: List[str]) -> List[Dict[str, Any]]:
    """
    Run a complete arbitrage scan across all marketplaces.
    
    Args:
        subcategories (List[str]): List of subcategories to search for
        
    Returns:
        List[Dict[str, Any]]: List of processed arbitrage opportunities
    """
    try:
        logger.info(f"Starting arbitrage scan for subcategories: {subcategories}")
        
        # Create new event loop for the async operations
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            start_time = time.time()
            
            # Scan marketplaces
            all_listings, opportunities = loop.run_until_complete(scan_marketplaces(subcategories))
            
            # Process opportunities
            processed_results = []
            
            for opportunity in opportunities:
                # Calculate additional profit metrics
                processed = calculate_profit_metrics(opportunity)
                
                # Calculate velocity score and estimated sell days
                velocity_score = calculate_velocity_score(processed)
                estimated_sell_days = estimate_sell_days(processed, velocity_score)
                
                processed['velocity_score'] = velocity_score
                processed['estimated_sell_days'] = estimated_sell_days
                
                processed_results.append(processed)
            
            end_time = time.time()
            scan_duration = end_time - start_time
            
            logger.info(f"Scan completed in {scan_duration:.2f} seconds")
            logger.info(f"Found {len(processed_results)} arbitrage opportunities")
            
            return processed_results
            
        except Exception as e:
            logger.error(f"Error running arbitrage scan: {str(e)}")
            return []
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Unexpected error in arbitrage scan: {str(e)}")
        return []

# Entry point for direct execution
if __name__ == "__main__":
    # Test the arbitrage scanner
    test_subcategories = ["Headphones", "Mechanical Keyboards"]
    results = run_arbitrage_scan(test_subcategories)
    
    print(f"Found {len(results)} arbitrage opportunities")
    for i, opp in enumerate(results[:5], 1):
        print(f"\nOpportunity #{i}:")
        print(f"Title: {opp['title']}")
        print(f"Buy: ${opp['buy_price']:.2f} from {opp['buy_marketplace']}")
        print(f"Sell: ${opp['sell_price']:.2f} on {opp['sell_marketplace']}")
        print(f"Profit: ${opp['net_profit']:.2f} ({opp['net_profit_percentage']:.2f}% ROI)")
        print(f"Confidence: {opp['confidence']}%")
        print(f"Velocity Score: {opp['velocity_score']}")
        print(f"Estimated Sell Time: {opp['estimated_sell_days']} days")
        print(f"Buy Link: {opp['buy_link']}")
        print(f"Sell Link: {opp['sell_link']}")
