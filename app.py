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

# Choose framework based on imports available
try:
    # FastAPI implementation with proper HTML template serving
    from fastapi import FastAPI, HTTPException, Request
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse, HTMLResponse
    from fastapi.staticfiles import StaticFiles
    from fastapi.templating import Jinja2Templates
    from pydantic import BaseModel
    
    # Import required modules
    from scraper_manager import ScraperManager
    from comprehensive_keywords import COMPREHENSIVE_KEYWORDS

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
    
    app.mount("/static", StaticFiles(directory="static"), name="static")
    
    # Setup templates
    templates_dir = Path("templates")
    if not templates_dir.exists():
        templates_dir.mkdir(exist_ok=True)
    
    templates = Jinja2Templates(directory="templates")
    
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
        """Root endpoint - renders the main HTML template"""
        return templates.TemplateResponse("index.html", {"request": request})
    
    @app.get("/api", response_class=JSONResponse)
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
    
    @app.get("/api/health")
    async def health_check():
        """Health check endpoint"""
        return {
            "status": "ok",
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat(),
            "scrapers": list(scraper_manager.scrapers.keys())
        }

except ImportError:
    # Fall back to Flask implementation if FastAPI is not installed
    from flask import Flask, request, jsonify, render_template, send_from_directory
    from flask_cors import CORS
    import asyncio
    
    # Import the scraper manager
    from scraper_manager import ScraperManager
    from comprehensive_keywords import COMPREHENSIVE_KEYWORDS
    
    # Create static and templates directories if they don't exist
    static_dir = Path("static")
    if not static_dir.exists():
        static_dir.mkdir(exist_ok=True)
        
    templates_dir = Path("templates")
    if not templates_dir.exists():
        templates_dir.mkdir(exist_ok=True)
    
    app = Flask(__name__, 
                static_folder="static",
                template_folder="templates")
    CORS(app)
    
    # Initialize scraper manager
    scraper_manager = ScraperManager()
    
    @app.route("/")
    def root():
        """Root endpoint - renders the main HTML template"""
        return render_template("index.html")
    
    @app.route("/api")
    def api_root():
        """API root endpoint - health check"""
        return jsonify({"status": "ok", "message": "Marketplace Arbitrage API is running"})
    
    @app.route("/api/search", methods=["POST"])
    def search():
        """Search for listings across marketplaces and find arbitrage opportunities"""
        try:
            data = request.get_json()
            
            # Use provided keywords or default to comprehensive keywords
            keywords = data.get("keywords") or []
            if not keywords:
                # Extract keywords from all categories in COMPREHENSIVE_KEYWORDS
                for category, subcats in COMPREHENSIVE_KEYWORDS.items():
                    for subcat, keyword_list in subcats.items():
                        # Take first 5 keywords from each subcategory
                        keywords.extend(keyword_list[:5])
            
            # Filter marketplaces if specified
            marketplaces = data.get("marketplaces")
            if marketplaces:
                scraper_manager.scrapers = {k: v for k, v in scraper_manager.scrapers.items() if k in marketplaces}
            
            # Create event loop for async operations
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Run scrapers with the keywords
                loop.run_until_complete(scraper_manager.run_all_scrapers(keywords))
                
                # Find arbitrage opportunities
                scraper_manager.find_arbitrage_opportunities()
                
                # Get results formatted for frontend
                results = scraper_manager.get_results_for_frontend()
                
                # Limit results if requested
                max_results = data.get("max_results", 100)
                if max_results > 0:
                    results["arbitrage_opportunities"] = results["arbitrage_opportunities"][:max_results]
                    for marketplace in results["raw_listings"]:
                        results["raw_listings"][marketplace] = results["raw_listings"][marketplace][:max_results]
                
                return jsonify(results)
            finally:
                loop.close()
        
        except Exception as e:
            logger.error(f"Error during search: {str(e)}")
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/marketplaces")
    def get_marketplaces():
        """Get all available marketplaces"""
        return jsonify({"marketplaces": list(scraper_manager.scrapers.keys())})
    
    @app.route("/api/keywords")
    def get_keywords():
        """Get all available keywords"""
        # Extract all keywords from COMPREHENSIVE_KEYWORDS
        all_keywords = []
        for category, subcats in COMPREHENSIVE_KEYWORDS.items():
            for subcat, keyword_list in subcats.items():
                all_keywords.extend(keyword_list)
        return jsonify({"keywords": all_keywords})
    
    @app.route("/api/opportunities")
    def get_opportunities():
        """Get the latest arbitrage opportunities"""
        opportunities = scraper_manager.arbitrage_opportunities
        return jsonify({
            "opportunities": opportunities,
            "count": len(opportunities),
            "timestamp": datetime.now().isoformat()
        })
    
    @app.route("/api/health")
    def health_check():
        """Health check endpoint"""
        return jsonify({
            "status": "ok",
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat(),
            "scrapers": list(scraper_manager.scrapers.keys())
        })

if __name__ == "__main__":
    try:
        # Try to start with FastAPI (using Uvicorn)
        import uvicorn
        uvicorn.run("app:app", host="0.0.0.0", port=int(os.environ.get("PORT", 8000)), reload=True)
    except ImportError:
        # Fall back to Flask
        port = int(os.environ.get("PORT", 8000))
        app.run(host="0.0.0.0", port=port, debug=True)
