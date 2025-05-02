import asyncio
import json
import logging
from typing import Dict, List, Any
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from scraper_manager import ScraperManager
from comprehensive_keywords import KEYWORDS

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

app = FastAPI(title="Marketplace Arbitrage API")

# Enable CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

@app.get("/")
async def root():
    """Root endpoint - health check"""
    return {"status": "ok", "message": "Marketplace Arbitrage API is running"}

@app.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """Search for listings across marketplaces and find arbitrage opportunities"""
    try:
        # Use provided keywords or default to comprehensive keywords
        keywords = request.keywords or KEYWORDS
        
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

@app.get("/marketplaces")
async def get_marketplaces():
    """Get all available marketplaces"""
    return {"marketplaces": list(scraper_manager.scrapers.keys())}

@app.get("/keywords")
async def get_keywords():
    """Get all available keywords"""
    return {"keywords": KEYWORDS}

@app.get("/opportunities")
async def get_opportunities():
    """Get the latest arbitrage opportunities"""
    opportunities = scraper_manager.arbitrage_opportunities
    return {
        "opportunities": opportunities,
        "count": len(opportunities),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "scrapers": list(scraper_manager.scrapers.keys())
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
