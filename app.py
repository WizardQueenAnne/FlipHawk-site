"""
FlipHawk - Marketplace Arbitrage Application
Main application entry point - Updated with proper scanner connections
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
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

# FastAPI implementation with proper HTML template serving
from fastapi import FastAPI, HTTPException, Request, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# Import the marketplace bridge module for scanner integration
from marketplace_bridge import process_marketplace_scan, scan_manager

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

# Pydantic models for request/response
class ScanRequest(BaseModel):
    subcategories: List[str] = Field(..., description="List of subcategories to scan for arbitrage opportunities")
    category: Optional[str] = Field("General", description="Main category for the subcategories")
    marketplaces: Optional[List[str]] = Field(None, description="Optional list of marketplaces to include in the scan")
    max_results: Optional[int] = Field(100, description="Maximum number of results to return")

class OpportunityFees(BaseModel):
    marketplace: float = Field(0.0, description="Marketplace fees")
    shipping: float = Field(0.0, description="Shipping costs")

class ArbitrageOpportunity(BaseModel):
    buyTitle: str = Field(..., description="Title of the item to buy")
    buyPrice: float = Field(..., description="Price to buy the item")
    buyLink: str = Field(..., description="Link to buy the item")
    buyMarketplace: str = Field(..., description="Marketplace to buy from")
    buyImage: Optional[str] = Field(None, description="Image URL of the item to buy")
    buyCondition: Optional[str] = Field("New", description="Condition of the item to buy")
    
    sellTitle: str = Field(..., description="Title of the item to sell")
    sellPrice: float = Field(..., description="Price to sell the item")
    sellLink: str = Field(..., description="Link to sell the item")
    sellMarketplace: str = Field(..., description="Marketplace to sell on")
    sellImage: Optional[str] = Field(None, description="Image URL of the item to sell")
    sellCondition: Optional[str] = Field("New", description="Condition of the item to sell")
    
    profit: float = Field(..., description="Profit from the arbitrage opportunity")
    profitPercentage: float = Field(..., description="Profit percentage")
    fees: OpportunityFees = Field(default_factory=OpportunityFees, description="Fees associated with the opportunity")
    
    similarity: int = Field(..., description="Similarity percentage between buy and sell items")
    confidence: int = Field(..., description="Confidence level in the arbitrage opportunity")
    subcategory: Optional[str] = Field(None, description="Subcategory of the item")
    timestamp: Optional[str] = Field(None, description="Timestamp when the opportunity was found")

class ScanResult(BaseModel):
    arbitrage_opportunities: List[ArbitrageOpportunity] = Field([], description="List of arbitrage opportunities")
    meta: Dict[str, Any] = Field(default_factory=dict, description="Metadata about the scan")

# Store ongoing scans and their results
active_scans = {}
scan_results = {}

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
    
    # Last resort - return a simple HTML page
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
                    <a href="/scan" class="cta">Start Scanning</a>
                </div>
            </body>
        </html>
        """
        return HTMLResponse(content=html_content)

@app.get("/api")
async def api_root():
    """API root endpoint - health check"""
    return {"status": "ok", "message": "Marketplace Arbitrage API is running"}

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/v1/scan")
async def scan_marketplaces(request: ScanRequest):
    """Scan marketplaces for arbitrage opportunities"""
    try:
        logger.info(f"Starting scan for subcategories: {request.subcategories}")
        
        # Basic validation
        if not request.subcategories:
            raise HTTPException(status_code=400, detail="At least one subcategory is required")
        
        # Process the scan through the marketplace bridge
        result = process_marketplace_scan(
            category=request.category,
            subcategories=request.subcategories,
            max_results=request.max_results or 100
        )
        
        # Check for errors
        if "error" in result and not result.get("arbitrage_opportunities"):
            raise HTTPException(status_code=500, detail=result["error"])
        
        return result
    
    except Exception as e:
        logger.error(f"Error during scan: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"An error occurred during the scan: {str(e)}")

@app.get("/api/progress/{scan_id}")
async def get_scan_progress(scan_id: str):
    """Get the progress of a scan"""
    scan_info = scan_manager.get_scan_info(scan_id)
    
    if not scan_info:
        raise HTTPException(status_code=404, detail=f"Scan with ID {scan_id} not found")
    
    return {
        "scan_id": scan_id,
        "progress": scan_info.get('progress', 0),
        "status": scan_info.get('status', 'unknown'),
        "category": scan_info.get('category', ''),
        "subcategories": scan_info.get('subcategories', []),
        "start_time": scan_info.get('start_time', ''),
        "completion_time": scan_info.get('completion_time', None)
    }

@app.get("/scan", response_class=HTMLResponse)
async def scan_page(request: Request):
    """Scan page for finding arbitrage opportunities"""
    # Check if scan.html exists in the templates directory
    if os.path.exists("scan.html"):
        with open("scan.html", "r") as f:
            return HTMLResponse(content=f.read())
    elif os.path.exists("templates/scan.html"):
        with open("templates/scan.html", "r") as f:
            return HTMLResponse(content=f.read())
    
    # Otherwise create a basic scan page (default implementation)
    # This part remains unchanged from your original code
    html_content = """
    <!DOCTYPE html>
    <html>
        <head>
            <title>FlipHawk - Scan</title>
            <style>
                /* Styles remain unchanged */
            </style>
        </head>
        <body>
            <!-- Content remains unchanged -->
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)

# Support for static files with direct paths
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    if os.path.exists("static/favicon.ico"):
        return FileResponse("static/favicon.ico")
    elif os.path.exists("static/favicon.png"):
        return FileResponse("static/favicon.png")
    return None

if __name__ == "__main__":
    # Get the port from environment variable or use default
    port = int(os.environ.get("PORT", 8000))
    
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)
