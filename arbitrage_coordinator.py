"""
Arbitrage Coordinator for FlipHawk system.
This module coordinates the scanning of marketplaces and processing of results.
"""

import asyncio
import logging
import time
from typing import List, Dict, Any, Optional
from marketplace_scanner import run_arbitrage_scan

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('arbitrage_coordinator')

class ArbitrageCoordinator:
    """
    Coordinator class for handling arbitrage scans across marketplaces.
    Manages the scanning process and caches results.
    """
    
    def __init__(self):
        """Initialize the arbitrage coordinator."""
        self.active_scans = {}
        self.scan_results_cache = {}
        self.cache_expiry = {}  # Cache expiry time in seconds
        self.cache_lifetime = 10 * 60  # 10 minutes
    
    async def coordinate_scan(self, category: str, subcategories: List[str]) -> List[Dict[str, Any]]:
        """
        Coordinate the scanning process for the given category and subcategories.
        
        Args:
            category (str): The main category to scan
            subcategories (List[str]): List of subcategories to scan
            
        Returns:
            List[Dict[str, Any]]: List of arbitrage opportunities
        """
        # Generate a unique key for this scan
        scan_key = f"{category}:{','.join(sorted(subcategories))}"
        
        # Check if we have a recent cached result
        if scan_key in self.scan_results_cache:
            if time.time() < self.cache_expiry.get(scan_key, 0):
                logger.info(f"Using cached results for {scan_key}")
                return self.scan_results_cache[scan_key]
        
        # Check if a scan is already in progress
        if scan_key in self.active_scans:
            logger.info(f"Scan already in progress for {scan_key}, waiting for results")
            # Wait for the existing scan to complete
            while scan_key in self.active_scans:
                await asyncio.sleep(0.5)
            
            # Return the cached result if available
            if scan_key in self.scan_results_cache:
                return self.scan_results_cache[scan_key]
        
        # Mark scan as active
        self.active_scans[scan_key] = True
        
        try:
            # Set up the event loop for the arbitrage scan
            loop = asyncio.get_event_loop()
            
            # Need to run in a separate thread since this is a blocking operation
            start_time = time.time()
            logger.info(f"Starting arbitrage scan for {scan_key}")
            
            # Run the arbitrage scan
            results = await loop.run_in_executor(None, lambda: run_arbitrage_scan(subcategories))
            
            # Process and filter results if needed
            if results:
                # Add category information
                for result in results:
                    if 'category' not in result:
                        result['category'] = category
            
            end_time = time.time()
            scan_duration = end_time - start_time
            logger.info(f"Scan completed in {scan_duration:.2f} seconds with {len(results)} results")
            
            # Cache the results
            self.scan_results_cache[scan_key] = results
            self.cache_expiry[scan_key] = time.time() + self.cache_lifetime
            
            return results
            
        finally:
            # Remove from active scans
            if scan_key in self.active_scans:
                del self.active_scans[scan_key]
    
    def get_cached_results(self, category: str, subcategories: List[str]) -> Optional[List[Dict[str, Any]]]:
        """
        Get cached results for the specified category and subcategories if available.
        
        Args:
            category (str): The main category
            subcategories (List[str]): List of subcategories
            
        Returns:
            Optional[List[Dict[str, Any]]]: Cached results or None if not available
        """
        scan_key = f"{category}:{','.join(sorted(subcategories))}"
        
        if scan_key in self.scan_results_cache:
            if time.time() < self.cache_expiry.get(scan_key, 0):
                return self.scan_results_cache[scan_key]
        
        return None
    
    def clear_cache(self, category: Optional[str] = None, subcategories: Optional[List[str]] = None):
        """
        Clear the cache for specific category/subcategories or all cache if not specified.
        
        Args:
            category (Optional[str]): Category to clear
            subcategories (Optional[List[str]]): Subcategories to clear
        """
        if category and subcategories:
            scan_key = f"{category}:{','.join(sorted(subcategories))}"
            if scan_key in self.scan_results_cache:
                del self.scan_results_cache[scan_key]
                if scan_key in self.cache_expiry:
                    del self.cache_expiry[scan_key]
        else:
            # Clear all cache
            self.scan_results_cache.clear()
            self.cache_expiry.clear()
    
    def get_active_scan_count(self) -> int:
        """Get the number of currently active scans."""
        return len(self.active_scans)

# Create a global instance of the coordinator
coordinator = ArbitrageCoordinator()

async def run_coordinated_scan(category: str, subcategories: List[str]) -> List[Dict[str, Any]]:
    """
    Run a coordinated scan for the given category and subcategories.
    This is the main entry point for the arbitrage scanning system.
    
    Args:
        category (str): The main category to scan
        subcategories (List[str]): List of subcategories to scan
        
    Returns:
        List[Dict[str, Any]]: List of arbitrage opportunities
    """
    return await coordinator.coordinate_scan(category, subcategories)
