# app.py
"""
FlipHawk - Marketplace Arbitrage Application
Main application entry point with fixed API endpoints for direct scraper execution
"""

import asyncio
import logging
import os
import uuid
import time
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import traceback
import json
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Import bridge to scrapers
try:
    from marketplace_bridge import process_marketplace_scan, scan_manager
    bridge_available = True
    logger.info("Marketplace bridge available")
except ImportError:
    bridge_available = False
    logger.warning("Marketplace bridge not available, using fallback")

# Initialize the app
app = FastAPI(title="FlipHawk - Marketplace Arbitrage")

# Enable CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup static files
static_dir = Path("static")
if not static_dir.exists():
    static_dir.mkdir(exist_ok=True)
    # Create subdirectories
    for subdir in ["css", "js", "images"]:
        Path(f"static/{subdir}").mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")

# Pydantic model for scan request
class ScanRequest(BaseModel):
    subcategories: List[str] = Field(..., description="Subcategories to scan")
    category: str = Field(..., description="Main category") 
    max_results: int = Field(100, description="Maximum number of results to return")

# Active scans storage as a fallback
active_scans = {}

# Fallback subcategories data
fallback_categories = {
    "Tech": ["Headphones", "Keyboards", "Graphics Cards", "CPUs", "Laptops", "Monitors", "SSDs", "Routers", "Vintage Tech"],
    "Collectibles": ["Pokémon", "Magic: The Gathering", "Yu-Gi-Oh", "Funko Pops", "Sports Cards", "Comic Books", "Action Figures", "LEGO Sets"],
    "Vintage Clothing": ["Jordans", "Nike Dunks", "Vintage Tees", "Band Tees", "Denim Jackets", "Designer Brands", "Carhartt", "Patagonia"],
    "Antiques": ["Coins", "Watches", "Cameras", "Typewriters", "Vinyl Records", "Vintage Tools", "Old Maps"],
    "Gaming": ["Consoles", "Game Controllers", "Rare Games", "Arcade Machines", "Handhelds", "Gaming Headsets", "VR Gear"],
    "Music Gear": ["Electric Guitars", "Guitar Pedals", "Synthesizers", "Vintage Amps", "Microphones", "DJ Equipment"],
    "Tools & DIY": ["Power Tools", "Hand Tools", "Welding Equipment", "Toolboxes", "Measuring Devices", "Woodworking Tools"],
    "Outdoors & Sports": ["Bikes", "Skateboards", "Scooters", "Camping Gear", "Hiking Gear", "Fishing Gear", "Snowboards"]
}

@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint - returns index.html or simple HTML"""
    if os.path.exists("index.html"):
        with open("index.html", "r") as f:
            return HTMLResponse(content=f.read())
    
    html_content = """
    <!DOCTYPE html>
    <html>
        <head>
            <title>FlipHawk</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background-color: #F9E8C7;
                    color: #2D1E0F;
                }
                .container {
                    max-width: 800px;
                    margin: 0 auto;
                    background-color: white;
                    padding: 20px;
                    border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
                }
                h1 {
                    color: #D16B34;
                }
                .cta {
                    display: inline-block;
                    background-color: #D16B34;
                    color: white;
                    padding: 10px 20px;
                    border-radius: 4px;
                    text-decoration: none;
                    margin-top: 20px;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>FlipHawk - Marketplace Arbitrage</h1>
                <p>Welcome to FlipHawk! The API is running successfully.</p>
                <p>To access the scan page, visit <a href="/scan">/scan</a>.</p>
                <a href="/scan" class="cta">Start Scanning</a>
            </div>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/scan", response_class=HTMLResponse)
async def scan_page():
    """Scan page"""
    if os.path.exists("scan.html"):
        with open("scan.html", "r") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<html><body><h1>Scan Page</h1><p>Please create scan.html file</p></body></html>")

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@app.get("/api/categories")
async def get_categories():
    """Get available categories"""
    # Try to import comprehensive_keywords
    try:
        from comprehensive_keywords import COMPREHENSIVE_KEYWORDS
        return {"categories": list(COMPREHENSIVE_KEYWORDS.keys())}
    except ImportError:
        # Use fallback
        return {"categories": list(fallback_categories.keys())}

@app.get("/api/categories/{category}/subcategories")
async def get_subcategories(category: str):
    """Get subcategories for a category"""
    # Try to import comprehensive_keywords
    try:
        from comprehensive_keywords import COMPREHENSIVE_KEYWORDS
        if category in COMPREHENSIVE_KEYWORDS:
            subcats = COMPREHENSIVE_KEYWORDS[category]
            if isinstance(subcats, dict):
                return {"subcategories": list(subcats.keys())}
            return {"subcategories": list(subcats)}
    except ImportError:
        pass
        
    # Use fallback
    if category in fallback_categories:
        return {"subcategories": fallback_categories[category]}
    return {"subcategories": []}

@app.post("/api/categories/subcategories")
async def get_subcategories_post(data: dict):
    """Get subcategories for a category (POST method)"""
    category = data.get("category", "")
    if not category:
        return {"subcategories": []}
    
    # Try to import comprehensive_keywords
    try:
        from comprehensive_keywords import COMPREHENSIVE_KEYWORDS
        if category in COMPREHENSIVE_KEYWORDS:
            subcats = COMPREHENSIVE_KEYWORDS[category]
            if isinstance(subcats, dict):
                return {"subcategories": list(subcats.keys())}
            return {"subcategories": list(subcats)}
    except ImportError:
        pass
        
    # Use fallback
    if category in fallback_categories:
        return {"subcategories": fallback_categories[category]}
    return {"subcategories": []}

@app.post("/api/scan")
async def start_scan(request: ScanRequest, background_tasks: BackgroundTasks):
    """Start a new scan"""
    try:
        # Validate request
        if not request.subcategories:
            return JSONResponse(status_code=400, content={"error": "No subcategories provided"})
            
        logger.info(f"Starting scan for category: {request.category}, subcategories: {request.subcategories}")
        
        # Use marketplace_bridge if available, otherwise use fallback
        if bridge_available:
            # Process scan using the bridge
            result = process_marketplace_scan(
                request.category, 
                request.subcategories, 
                request.max_results
            )
            return result
        else:
            # Fallback logic for direct method without bridge
            # Generate scan ID
            scan_id = f"scan_{uuid.uuid4()}"
            
            # Initialize scan info
            active_scans[scan_id] = {
                "subcategories": request.subcategories,
                "category": request.category,
                "status": "initializing",
                "progress": 0,
                "start_time": datetime.now().isoformat(),
                "results": []
            }
            
            # Start scan in background
            background_tasks.add_task(run_scan_without_bridge, scan_id, request.subcategories, request.category)
            
            # Return scan ID
            return {
                "meta": {
                    "scan_id": scan_id,
                    "message": "Scan started",
                    "status": "initializing",
                    "category": request.category,
                    "subcategories": request.subcategories
                }
            }
        
    except Exception as e:
        logger.error(f"Error starting scan: {str(e)}")
        logger.error(traceback.format_exc())
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/api/progress/{scan_id}")
async def get_scan_progress(scan_id: str):
    """Get the progress of a scan"""
    try:
        # Use marketplace_bridge if available
        if bridge_available:
            scan_info = scan_manager.get_scan_info(scan_id)
            if not scan_info:
                return JSONResponse(status_code=404, content={"error": "Scan not found"})
            
            return {
                "scan_id": scan_id,
                "status": scan_info.get("status", "unknown"),
                "progress": scan_info.get("progress", 0)
            }
        else:
            # Fallback to direct method
            if scan_id not in active_scans:
                return JSONResponse(status_code=404, content={"error": "Scan not found"})
                
            scan_data = active_scans[scan_id]
            
            return {
                "scan_id": scan_id,
                "status": scan_data.get("status", "unknown"),
                "progress": scan_data.get("progress", 0)
            }
    except Exception as e:
        logger.error(f"Error getting scan progress: {str(e)}")
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/api/scan/{scan_id}")
async def get_scan_results(scan_id: str):
    """Get the results of a scan"""
    try:
        # Use marketplace_bridge if available
        if bridge_available:
            results = scan_manager.get_formatted_results(scan_id)
            if "error" in results:
                return JSONResponse(status_code=404, content={"error": results["error"]})
            
            return results
        else:
            # Fallback to direct method
            if scan_id not in active_scans:
                return JSONResponse(status_code=404, content={"error": "Scan not found"})
                
            scan_data = active_scans[scan_id]
            
            return {
                "scan_id": scan_id,
                "status": scan_data.get("status", "unknown"),
                "progress": scan_data.get("progress", 0),
                "category": scan_data.get("category", ""),
                "subcategories": scan_data.get("subcategories", []),
                "arbitrage_opportunities": scan_data.get("results", [])
            }
    except Exception as e:
        logger.error(f"Error getting scan results: {str(e)}")
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/api/scan/{scan_id}/results")
async def get_scan_results_alt(scan_id: str):
    """Alternative endpoint for scan results (for compatibility)"""
    return await get_scan_results(scan_id)

# Fallback function for running scans without bridge
async def run_scan_without_bridge(scan_id: str, subcategories: List[str], category: str):
    """Run scan without using marketplace_bridge"""
    try:
        # Update progress
        active_scans[scan_id]["status"] = "running"
        active_scans[scan_id]["progress"] = 5
        
        # Import and run scrapers directly
        success = False
        all_listings = []
        
        # Import scrapers at runtime to avoid circular imports
        try:
            from amazon_scraper import run_amazon_search
            logger.info("Running Amazon scraper...")
            
            # Create event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Update progress
            active_scans[scan_id]["progress"] = 20
            active_scans[scan_id]["status"] = "searching amazon"
            
            # Run Amazon scraper
            amazon_results = await run_amazon_search(subcategories)
            all_listings.extend(amazon_results)
            success = True
            
            # Update progress
            active_scans[scan_id]["progress"] = 40
        except ImportError:
            logger.warning("Amazon scraper not available")
        except Exception as e:
            logger.error(f"Error running Amazon scraper: {str(e)}")
        
        try:
            from ebay_scraper import run_ebay_search
            logger.info("Running eBay scraper...")
            
            # Create event loop if needed
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # Update progress
            active_scans[scan_id]["progress"] = 50
            active_scans[scan_id]["status"] = "searching ebay"
            
            # Run eBay scraper
            ebay_results = await run_ebay_search(subcategories)
            all_listings.extend(ebay_results)
            success = True
            
            # Update progress
            active_scans[scan_id]["progress"] = 70
        except ImportError:
            logger.warning("eBay scraper not available")
        except Exception as e:
            logger.error(f"Error running eBay scraper: {str(e)}")
        
        # If both scrapers failed, generate dummy data
        if not success:
            logger.warning("All scrapers failed, generating dummy data")
            active_scans[scan_id]["results"] = generate_dummy_results(subcategories)
            active_scans[scan_id]["status"] = "completed"
            active_scans[scan_id]["progress"] = 100
            return
        
        # Find arbitrage opportunities
        active_scans[scan_id]["status"] = "finding opportunities"
        active_scans[scan_id]["progress"] = 85
        
        # Use helper function to find opportunities
        opportunities = find_arbitrage_opportunities(all_listings)
        
        # Update scan results
        active_scans[scan_id]["results"] = opportunities
        active_scans[scan_id]["status"] = "completed"
        active_scans[scan_id]["progress"] = 100
        
        logger.info(f"Scan {scan_id} completed with {len(opportunities)} opportunities")
    
    except Exception as e:
        logger.error(f"Error in scan {scan_id}: {str(e)}")
        logger.error(traceback.format_exc())
        active_scans[scan_id]["status"] = "error"
        active_scans[scan_id]["error"] = str(e)
        active_scans[scan_id]["progress"] = 100

def find_arbitrage_opportunities(listings):
    """Find arbitrage opportunities from listings"""
    # Group listings by source
    listings_by_source = {}
    for listing in listings:
        source = listing.get("source", listing.get("marketplace", "unknown"))
        if source not in listings_by_source:
            listings_by_source[source] = []
        listings_by_source[source].append(listing)
    
    # If less than 2 sources, return empty list
    if len(listings_by_source) < 2:
        logger.warning("Not enough sources for arbitrage")
        return []
    
    opportunities = []
    
    # Compare each pair of sources
    for buy_source, buy_listings in listings_by_source.items():
        for sell_source, sell_listings in listings_by_source.items():
            if buy_source == sell_source:
                continue
                
            # Compare listings
            for buy_listing in buy_listings:
                buy_price = buy_listing.get("price", 0)
                if buy_price <= 0:
                    continue
                    
                buy_title = buy_listing.get("title", "")
                
                for sell_listing in sell_listings:
                    sell_price = sell_listing.get("price", 0)
                    if sell_price <= 0:
                        continue
                        
                    # Skip if sell price not higher than buy price
                    if sell_price <= buy_price:
                        continue
                        
                    sell_title = sell_listing.get("title", "")
                    
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
    
    return opportunities

def calculate_title_similarity(title1, title2):
    """Calculate similarity between two titles"""
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
        
    return len(intersection) / len(union)

def generate_dummy_results(subcategories):
    """Generate dummy results for testing"""
    import random
    
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

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """Serve favicon"""
    if os.path.exists("static/favicon.ico"):
        return FileResponse("static/favicon.ico")
    return None

if __name__ == "__main__":
    # Get port from environment
    port = int(os.environ.get("PORT", 8000))
    
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)
