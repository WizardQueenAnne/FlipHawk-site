"""
FlipHawk - Marketplace Arbitrage Application
Main application entry point
"""

import asyncio
import json
import logging
from typing import Dict, List, Any
from datetime import datetime
import os
from pathlib import Path

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

# Import required modules
from scraper_manager import ScraperManager
from comprehensive_keywords import COMPREHENSIVE_KEYWORDS

# FastAPI implementation
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

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

# Add static file mounting
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize scraper manager
scraper_manager = ScraperManager()

# Pydantic models for request/response
class SearchRequest(BaseModel):
    keywords: List[str] = None
    marketplaces: List[str] = None
    max_results: int = 100

class SearchResponse(BaseModel):
    listings: Dict[str, List[Dict]]
    arbitrage_opportunities: List[Dict]
    meta: Dict[str, Any]

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Root endpoint - returns the index.html file"""
    # Check if index.html exists in the root directory
    if os.path.exists("index.html"):
        with open("index.html", "r") as f:
            return HTMLResponse(content=f.read())
    
    # Fallback to templates directory if it exists
    elif os.path.exists("templates/index.html"):
        with open("templates/index.html", "r") as f:
            return HTMLResponse(content=f.read())
    
    # Last resort - return a simple HTML message
    else:
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
                    <p>To access the API, visit <a href="/api">/api</a>.</p>
                    <a href="/api" class="cta">Go to API</a>
                </div>
            </body>
        </html>
        """
        return HTMLResponse(content=html_content)

@app.get("/api")
async def api_root():
    """API root endpoint - health check"""
    return {"status": "ok", "message": "Marketplace Arbitrage API is running"}

@app.post("/api/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """Search for listings across marketplaces and find arbitrage opportunities"""
    try:
        # Use provided keywords or default to comprehensive keywords
        keywords = request.keywords or []
        if not keywords:
            # Extract keywords from all categories in COMPREHENSIVE_KEYWORDS
            for category, subcats in COMPREHENSIVE_KEYWORDS.items():
                for subcat, keyword_list in subcats.items():
                    # Take first 5 keywords from each subcategory
                    keywords.extend(keyword_list[:5])
        
        # Filter marketplaces if specified
        if request.marketplaces:
            scraper_manager.scrapers = {k: v for k, v in scraper_manager.scrapers.items() if k in request.marketplaces}
        
        # Run scrapers with the keywords
        await scraper_manager.run_all_scrapers(keywords)
        
        # Find arbitrage opportunities
        scraper_manager.find_arbitrage_opportunities()
        
        # Get results formatted for frontend
        results = scraper_manager.get_results_for_frontend()
        
        # Limit results if requested
        if request.max_results and request.max_results > 0:
            results["arbitrage_opportunities"] = results["arbitrage_opportunities"][:request.max_results]
            for marketplace in results["raw_listings"]:
                results["raw_listings"][marketplace] = results["raw_listings"][marketplace][:request.max_results]
        
        return results
    
    except Exception as e:
        logger.error(f"Error during search: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/marketplaces")
async def get_marketplaces():
    """Get all available marketplaces"""
    return {"marketplaces": list(scraper_manager.scrapers.keys())}

@app.get("/api/keywords")
async def get_keywords():
    """Get all available keywords"""
    # Extract all keywords from COMPREHENSIVE_KEYWORDS
    all_keywords = []
    for category, subcats in COMPREHENSIVE_KEYWORDS.items():
        for subcat, keyword_list in subcats.items():
            all_keywords.extend(keyword_list)
    return {"keywords": all_keywords}

@app.get("/api/opportunities")
async def get_opportunities():
    """Get the latest arbitrage opportunities"""
    opportunities = scraper_manager.arbitrage_opportunities
    return {
        "opportunities": opportunities,
        "count": len(opportunities),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/scan", response_class=HTMLResponse)
async def scan_page(request: Request):
    """Scan page for finding arbitrage opportunities"""
    # Look for scan.html in templates directory
    if os.path.exists("templates/scan.html"):
        with open("templates/scan.html", "r") as f:
            return HTMLResponse(content=f.read())
    
    # Fallback to a simple HTML message
    html_content = """
    <!DOCTYPE html>
    <html>
        <head>
            <title>FlipHawk - Scan</title>
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
                .btn {
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
                <h1>FlipHawk - Scan</h1>
                <p>The scan page is not available yet.</p>
                <a href="/" class="btn">Back to Home</a>
            </div>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.post("/api/v1/arbitrage/scan")
async def arbitrage_scan(subcategories: Dict[str, List[str]]):
    """
    API endpoint to scan for arbitrage opportunities.
    """
    try:
        # Extract subcategories from request
        subcategory_list = subcategories.get('subcategories', [])
        
        if not subcategory_list:
            return {"error": "No subcategories provided"}
        
        # Initialize scraper manager if needed
        if not hasattr(app, 'scraper_manager'):
            from scraper_manager import ScraperManager
            app.scraper_manager = ScraperManager()
        
        # Run the scan
        await app.scraper_manager.run_all_scrapers(subcategory_list)
        
        # Find arbitrage opportunities
        app.scraper_manager.find_arbitrage_opportunities()
        
        # Return the opportunities
        return app.scraper_manager.arbitrage_opportunities
    
    except Exception as e:
        logger.error(f"Error during arbitrage scan: {str(e)}")
        return {"error": str(e)}

# Support for static files with direct paths
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    if os.path.exists("static/favicon.ico"):
        return FileResponse("static/favicon.ico")
    elif os.path.exists("static/favicon.png"):
        return FileResponse("static/favicon.png")
    return None

@app.get("/robots.txt", include_in_schema=False)
async def robots():
    if os.path.exists("static/robots.txt"):
        return FileResponse("static/robots.txt")
    return None

if __name__ == "__main__":
    # Get the port from environment variable or use default
    port = int(os.environ.get("PORT", 8000))
    
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)
