# app.py
"""
FlipHawk - Marketplace Arbitrage Application
Main application entry point - Simplified for direct scraper execution
"""

import asyncio
import logging
import os
from typing import List, Dict, Any
from pathlib import Path
from datetime import datetime
import traceback
import threading
import random
import time
import json
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
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

# Try to import scrapers
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
    category: str = Field("Tech", description="Main category") 

# Active scans storage
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

# Main scraping function
async def run_scrapers(scan_id, subcategories):
    """Run scrapers for subcategories and store results"""
    try:
        # Initialize results
        active_scans[scan_id]["status"] = "running"
        active_scans[scan_id]["progress"] = 5
        active_scans[scan_id]["results"] = []
        
        # Create event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Create tasks for available scrapers
        tasks = []
        scrapers_count = 0
        
        if amazon_available:
            tasks.append(run_amazon_search(subcategories))
            scrapers_count += 1
            
        if ebay_available:
            tasks.append(run_ebay_search(subcategories))
            scrapers_count += 1
            
        if facebook_available:
            tasks.append(run_facebook_search(subcategories))
            scrapers_count += 1
        
        # If no scrapers available, use dummy data
        if not tasks:
            logger.warning("No scrapers available, using dummy data")
            active_scans[scan_id]["results"] = generate_dummy_results(subcategories)
            active_scans[scan_id]["status"] = "completed"
            active_scans[scan_id]["progress"] = 100
            return
            
        # Update progress
        active_scans[scan_id]["progress"] = 10
        
        # Run tasks
        all_listings = []
        
        # Execute scrapers one by one to show progress
        for i, task in enumerate(tasks):
            try:
                # Update status
                active_scans[scan_id]["status"] = f"Running scraper {i+1}/{len(tasks)}"
                
                # Run scraper
                scraper_results = await task
                all_listings.extend(scraper_results)
                
                # Update progress after each scraper
                progress = 10 + ((i + 1) * 60) // len(tasks)
                active_scans[scan_id]["progress"] = progress
                
            except Exception as e:
                logger.error(f"Error running scraper {i+1}: {str(e)}")
                traceback.print_exc()
        
        # Find arbitrage opportunities
        active_scans[scan_id]["status"] = "Finding opportunities"
        active_scans[scan_id]["progress"] = 80
        
        # Process results
        opportunities = find_arbitrage_opportunities(all_listings)
        
        # Store results
        active_scans[scan_id]["results"] = opportunities
        active_scans[scan_id]["status"] = "completed"
        active_scans[scan_id]["progress"] = 100
        
        logger.info(f"Scan {scan_id} completed with {len(opportunities)} opportunities")
        
    except Exception as e:
        logger.error(f"Error in scan {scan_id}: {str(e)}")
        traceback.print_exc()
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

@app.post("/api/scan")
async def start_scan(request: ScanRequest):
    """Start a new scan"""
    try:
        # Validate request
        if not request.subcategories:
            return {"error": "No subcategories provided"}
            
        # Generate scan ID
        scan_id = f"scan_{int(time.time())}"
        
        # Store scan info
        active_scans[scan_id] = {
            "subcategories": request.subcategories,
            "category": request.category,
            "status": "initializing",
            "progress": 0,
            "start_time": datetime.now().isoformat(),
            "results": []
        }
        
        # Start scrapers in background
        threading.Thread(
            target=lambda: asyncio.run(run_scrapers(scan_id, request.subcategories)),
            daemon=True
        ).start()
        
        # Return scan ID
        return {
            "scan_id": scan_id,
            "status": "started",
            "message": "Scan started successfully"
        }
        
    except Exception as e:
        logger.error(f"Error starting scan: {str(e)}")
        traceback.print_exc()
        return {"error": str(e)}

@app.get("/api/scan/{scan_id}/progress")
async def get_scan_progress(scan_id: str):
    """Get scan progress"""
    if scan_id not in active_scans:
        return {"error": "Scan not found"}
        
    return {
        "scan_id": scan_id,
        "status": active_scans[scan_id]["status"],
        "progress": active_scans[scan_id]["progress"]
    }

@app.get("/api/scan/{scan_id}/results")
async def get_scan_results(scan_id: str):
    """Get scan results"""
    if scan_id not in active_scans:
        return {"error": "Scan not found"}
        
    scan_data = active_scans[scan_id]
    
    return {
        "scan_id": scan_id,
        "status": scan_data["status"],
        "progress": scan_data["progress"],
        "category": scan_data["category"],
        "subcategories": scan_data["subcategories"],
        "results": scan_data["results"]
    }

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
