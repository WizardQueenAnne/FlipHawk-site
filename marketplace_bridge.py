"""
Marketplace Bridge - Connection between API and Marketplace Scanner
This module bridges the gap between the API endpoints and the marketplace scanner functionality.
"""

import asyncio
import logging
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
import threading

# Import the marketplace scanner
from marketplace_scanner import run_arbitrage_scan, ArbitrageAnalyzer
from amazon_scraper import run_amazon_search
from ebay_scraper import run_ebay_search
from facebook_scraper import run_facebook_search
from comprehensive_keywords import COMPREHENSIVE_KEYWORDS, generate_keywords

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ScanManager:
    """Manager class to handle scanning operations and results caching."""
    
    def __init__(self):
        """Initialize the scan manager."""
        self.active_scans = {}
        self.scan_results = {}
        self.scan_counters = {}
        self.analyzer = ArbitrageAnalyzer()
        
    def get_scan_info(self, scan_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific scan.
        
        Args:
            scan_id (str): The scan ID to retrieve
            
        Returns:
            Optional[Dict[str, Any]]: Scan information or None if not found
        """
        return self.active_scans.get(scan_id)
    
    def get_scan_results(self, scan_id: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get the results of a completed scan.
        
        Args:
            scan_id (str): The scan ID to retrieve results for
            
        Returns:
            Optional[List[Dict[str, Any]]]: Scan results or None if not found
        """
        return self.scan_results.get(scan_id)
    
    def update_scan_progress(self, scan_id: str, progress: int, status: str = None):
        """
        Update the progress of a scan.
        
        Args:
            scan_id (str): The scan ID to update
            progress (int): The new progress value (0-100)
            status (str, optional): New status if provided
        """
        if scan_id in self.active_scans:
            self.active_scans[scan_id]['progress'] = progress
            if status:
                self.active_scans[scan_id]['status'] = status
    
    def get_keywords_for_subcategories(self, subcategories: List[str]) -> List[str]:
        """
        Get all keywords for the specified subcategories.
        
        Args:
            subcategories (List[str]): List of subcategories to get keywords for
            
        Returns:
            List[str]: Combined list of keywords for all subcategories
        """
        all_keywords = []
        
        # Loop through all categories and subcategories in COMPREHENSIVE_KEYWORDS
        for category, subcats in COMPREHENSIVE_KEYWORDS.items():
            for subcat in subcats:
                # Check if this subcategory is in our list
                if subcat in subcategories:
                    # Add keywords for this subcategory
                    subcat_keywords = generate_keywords(subcat, include_variations=True, max_keywords=10)
                    all_keywords.extend(subcat_keywords)
        
        # Remove duplicates while preserving order
        unique_keywords = []
        for keyword in all_keywords:
            if keyword not in unique_keywords:
                unique_keywords.append(keyword)
        
        logger.info(f"Generated {len(unique_keywords)} keywords for subcategories: {subcategories}")
        return unique_keywords[:20]  # Limit to 20 keywords for performance
    
    def run_scanning_thread(self, scan_id: str, category: str, subcategories: List[str], max_results: int):
        """
        Run the scanning process in a separate thread.
        
        Args:
            scan_id (str): The scan ID
            category (str): Main category
            subcategories (List[str]): List of subcategories
            max_results (int): Maximum number of results to return
        """
        try:
            logger.info(f"Starting scanning thread for scan {scan_id}")
            
            # Update scan status
            self.update_scan_progress(scan_id, 10, 'processing')
            
            # Get all keywords for the selected subcategories
            keywords = self.get_keywords_for_subcategories(subcategories)
            
            # Update scan status
            self.update_scan_progress(scan_id, 20, 'searching marketplaces')
            
            # Create a new event loop for the async operations
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Run the arbitrage scan
                opportunities = loop.run_until_complete(self._execute_scan(subcategories, keywords))
                
                # Update scan status
                self.update_scan_progress(scan_id, 90, 'processing results')
                
                # Process opportunities if any
                if opportunities:
                    # Store results
                    self.scan_results[scan_id] = opportunities
                    
                    # Update scan status
                    self.update_scan_progress(scan_id, 100, 'completed')
                    self.active_scans[scan_id]['completion_time'] = datetime.now().isoformat()
                    
                    logger.info(f"Scan {scan_id} completed with {len(opportunities)} opportunities")
                else:
                    # Update scan status with empty results
                    self.scan_results[scan_id] = []
                    self.update_scan_progress(scan_id, 100, 'completed_no_results')
                    self.active_scans[scan_id]['completion_time'] = datetime.now().isoformat()
                    
                    logger.info(f"Scan {scan_id} completed with no opportunities found")
            
            except Exception as e:
                logger.error(f"Error in scanning thread for scan {scan_id}: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
                
                # Update scan status
                self.update_scan_progress(scan_id, 100, 'failed')
                self.active_scans[scan_id]['error'] = str(e)
                self.scan_results[scan_id] = []
                
            finally:
                loop.close()
        
        except Exception as e:
            logger.error(f"Unhandled error in scanning thread for scan {scan_id}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            
            # Update scan status
            self.update_scan_progress(scan_id, 100, 'failed')
            self.active_scans[scan_id]['error'] = str(e)
            self.scan_results[scan_id] = []
    
    async def _execute_scan(self, subcategories: List[str], keywords: List[str]) -> List[Dict[str, Any]]:
        """
        Execute the actual marketplace scan using scrapers.
        
        Args:
            subcategories (List[str]): List of subcategories to scan
            keywords (List[str]): List of keywords to search for
            
        Returns:
            List[Dict[str, Any]]: List of arbitrage opportunities
        """
        try:
            logger.info(f"Executing marketplace scan for subcategories: {subcategories}")
            logger.info(f"Using keywords: {keywords}")
            
            # Run the marketplace scrapers
            amazon_task = asyncio.create_task(run_amazon_search(subcategories))
            ebay_task = asyncio.create_task(run_ebay_search(subcategories))
            facebook_task = asyncio.create_task(run_facebook_search(subcategories))
            
            # Wait for all tasks to complete
            results = await asyncio.gather(amazon_task, ebay_task, facebook_task)
            
            # Combine all listings
            all_listings = []
            for result in results:
                if result:  # Verify that result is not None or empty
                    all_listings.extend(result)
            
            logger.info(f"Found {len(all_listings)} total listings")
            
            # Find arbitrage opportunities
            opportunities = self.analyzer.find_opportunities(all_listings)
            
            logger.info(f"Found {len(opportunities)} arbitrage opportunities")
            
            # For the first implementation, just return the listed opportunities
            return opportunities
            
        except Exception as e:
            logger.error(f"Error executing marketplace scan: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            raise
    
    def execute_scan(self, category: str, subcategories: List[str], 
                   max_results: int = 100) -> str:
        """
        Execute a new scan for arbitrage opportunities.
        
        Args:
            category (str): The main category
            subcategories (List[str]): List of subcategories to scan
            max_results (int, optional): Maximum number of results to return
            
        Returns:
            str: Scan ID for tracking
        """
        # Generate a scan ID
        scan_id = f"{int(datetime.now().timestamp())}"
        
        # Register the scan
        self.active_scans[scan_id] = {
            'status': 'initializing',
            'progress': 0,
            'category': category,
            'subcategories': subcategories,
            'start_time': datetime.now().isoformat(),
            'max_results': max_results
        }
        
        # Start a new thread for the scanning process
        scan_thread = threading.Thread(
            target=self.run_scanning_thread,
            args=(scan_id, category, subcategories, max_results)
        )
        scan_thread.daemon = True
        scan_thread.start()
        
        return scan_id
    
    def get_formatted_results(self, scan_id: str) -> Dict[str, Any]:
        """
        Get formatted results for API response.
        
        Args:
            scan_id (str): The scan ID to get results for
            
        Returns:
            Dict[str, Any]: Formatted results with metadata
        """
        if scan_id not in self.active_scans:
            return {"error": "Scan ID not found"}
        
        scan_info = self.active_scans[scan_id]
        opportunities = self.scan_results.get(scan_id, [])
        
        # Limit results if needed
        max_results = scan_info.get('max_results', 100)
        if len(opportunities) > max_results:
            opportunities = opportunities[:max_results]
        
        # Format for response
        result = {
            "arbitrage_opportunities": opportunities,
            "meta": {
                "scan_id": scan_id,
                "timestamp": datetime.now().isoformat(),
                "subcategories": scan_info.get('subcategories', []),
                "category": scan_info.get('category', ''),
                "total_opportunities": len(opportunities),
                "status": scan_info.get('status', 'unknown'),
                "progress": scan_info.get('progress', 0)
            }
        }
        
        return result

# Create a global instance of the scan manager
scan_manager = ScanManager()

def process_marketplace_scan(category: str, subcategories: List[str], 
                           max_results: int = 100) -> Dict[str, Any]:
    """
    Process a marketplace scan request and return results.
    
    Args:
        category (str): The main category
        subcategories (List[str]): List of subcategories to scan
        max_results (int, optional): Maximum number of results to return
        
    Returns:
        Dict[str, Any]: Scan results with metadata
    """
    try:
        # Execute the scan
        scan_id = scan_manager.execute_scan(category, subcategories, max_results)
        
        # Get the initial scan status
        scan_info = scan_manager.get_scan_info(scan_id)
        
        # Create an initial response
        initial_response = {
            "meta": {
                "scan_id": scan_id,
                "timestamp": datetime.now().isoformat(),
                "subcategories": subcategories,
                "category": category,
                "status": scan_info.get('status', 'initializing'),
                "progress": scan_info.get('progress', 0),
                "message": "Scan initiated successfully. Check progress endpoint for updates."
            },
            "arbitrage_opportunities": []  # Initially empty
        }
        
        return initial_response
        
    except Exception as e:
        logger.error(f"Error processing marketplace scan: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        
        # Return error response
        return {
            "error": str(e),
            "meta": {
                "status": "failed",
                "timestamp": datetime.now().isoformat()
            },
            "arbitrage_opportunities": []
        }
