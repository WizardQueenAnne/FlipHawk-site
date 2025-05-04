import asyncio
import json
import logging
from typing import Dict, List, Any
from datetime import datetime

# Support for both Flask and FastAPI
try:
    # FastAPI implementation
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel
    
    # Import the scraper manager
    from scraper_manager import ScraperManager
    from comprehensive_keywords import COMPREHENSIVE_KEYWORDS  # Fixed import
    
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
    
    @app.get("/marketplaces")
    async def get_marketplaces():
        """Get all available marketplaces"""
        return {"marketplaces": list(scraper_manager.scrapers.keys())}
    
    @app.get("/keywords")
    async def get_keywords():
        """Get all available keywords"""
        # Extract all keywords from COMPREHENSIVE_KEYWORDS
        all_keywords = []
        for category, subcats in COMPREHENSIVE_KEYWORDS.items():
            for subcat, keyword_list in subcats.items():
                all_keywords.extend(keyword_list)
        return {"keywords": all_keywords}
    
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

except ImportError:
    # Fall back to Flask implementation if FastAPI is not installed
    from flask import Flask, request, jsonify
    from flask_cors import CORS
    
    # Import the scraper manager
    from scraper_manager import ScraperManager
    from comprehensive_keywords import COMPREHENSIVE_KEYWORDS  # Fixed import
    
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
    
    app = Flask(__name__)
    CORS(app)
    
    # Initialize scraper manager
    scraper_manager = ScraperManager()
    
    @app.route("/")
def index():
    # Instead of returning JSON:
    # return jsonify({"status": "ok", "message": "Marketplace Arbitrage API is running"})
    
    # Return a rendered HTML template:
    return render_template("index.html")
    
    @app.route("/search", methods=["POST"])
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
    
    @app.route("/marketplaces")
    def get_marketplaces():
        """Get all available marketplaces"""
        return jsonify({"marketplaces": list(scraper_manager.scrapers.keys())})
    
    @app.route("/keywords")
    def get_keywords():
        """Get all available keywords"""
        # Extract all keywords from COMPREHENSIVE_KEYWORDS
        all_keywords = []
        for category, subcats in COMPREHENSIVE_KEYWORDS.items():
            for subcat, keyword_list in subcats.items():
                all_keywords.extend(keyword_list)
        return jsonify({"keywords": all_keywords})
    
    @app.route("/opportunities")
    def get_opportunities():
        """Get the latest arbitrage opportunities"""
        opportunities = scraper_manager.arbitrage_opportunities
        return jsonify({
            "opportunities": opportunities,
            "count": len(opportunities),
            "timestamp": datetime.now().isoformat()
        })
    
    @app.route("/health")
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
        uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
    except ImportError:
        # Fall back to Flask
        app.run(host="0.0.0.0", port=8000, debug=True)
