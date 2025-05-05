"""
FlipHawk - Marketplace Arbitrage Application
Main application entry point
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

# Import comprehensive_keywords for keyword generation
try:
    from comprehensive_keywords import COMPREHENSIVE_KEYWORDS
    keywords_available = True
except ImportError:
    logger.warning("comprehensive_keywords.py not found. Using default keywords.")
    COMPREHENSIVE_KEYWORDS = {}
    keywords_available = False

# Create a dummy scraper manager for testing
class DummyScraper:
    """Dummy scraper for testing without real implementation"""
    
    def __init__(self):
        self.results = []
        self.opportunities = []
        
    async def search_marketplaces(self, subcategories: List[str]) -> List[Dict[str, Any]]:
        """Generate dummy marketplace listings for testing"""
        import random
        
        # Clear previous results
        self.results = []
        self.opportunities = []
        
        # Marketplaces to simulate
        marketplaces = ["Amazon", "eBay", "Etsy", "Facebook Marketplace"]
        
        # Generate 3-10 opportunities per subcategory
        for subcategory in subcategories:
            num_opportunities = random.randint(3, 10)
            
            for i in range(num_opportunities):
                # Generate random buy and sell prices
                buy_price = round(random.uniform(20, 200), 2)
                sell_price = round(buy_price * random.uniform(1.2, 2.0), 2)
                profit = round(sell_price - buy_price, 2)
                profit_percentage = round((profit / buy_price) * 100, 2)
                
                # Generate fees
                marketplace_fee = round(sell_price * 0.1, 2)  # 10% marketplace fee
                shipping = round(random.uniform(5, 15), 2)
                
                # Adjust profit for fees
                adjusted_profit = round(profit - marketplace_fee - shipping, 2)
                adjusted_profit_percentage = round((adjusted_profit / buy_price) * 100, 2)
                
                # Only add if profitable
                if adjusted_profit <= 0:
                    continue
                
                # Generate buy and sell marketplaces
                buy_marketplace = random.choice(marketplaces)
                remaining_marketplaces = [m for m in marketplaces if m != buy_marketplace]
                sell_marketplace = random.choice(remaining_marketplaces)
                
                # Generate item title
                item_name = f"{subcategory} {random.randint(1000, 9999)}"
                
                # Add some randomness to titles to make them different but similar
                buy_title = f"Brand New {item_name} Model X{random.randint(10, 99)}"
                sell_title = f"{item_name} X{random.randint(10, 99)} (New)"
                
                # Generate confidence score (similarity)
                confidence = random.randint(50, 95)
                
                # Create opportunity
                opportunity = {
                    "buyTitle": buy_title,
                    "buyPrice": buy_price,
                    "buyLink": f"https://example.com/{buy_marketplace.lower()}/{i}",
                    "buyMarketplace": buy_marketplace,
                    "buyImage": f"https://picsum.photos/seed/{buy_marketplace}{i}/200/200",
                    "buyCondition": "New",
                    
                    "sellTitle": sell_title,
                    "sellPrice": sell_price,
                    "sellLink": f"https://example.com/{sell_marketplace.lower()}/{i}",
                    "sellMarketplace": sell_marketplace,
                    "sellImage": f"https://picsum.photos/seed/{sell_marketplace}{i}/200/200",
                    "sellCondition": "New",
                    
                    "profit": adjusted_profit,
                    "profitPercentage": adjusted_profit_percentage,
                    "fees": {
                        "marketplace": marketplace_fee,
                        "shipping": shipping
                    },
                    
                    "similarity": confidence,
                    "confidence": confidence,
                    "subcategory": subcategory,
                    "timestamp": datetime.now().isoformat()
                }
                
                self.opportunities.append(opportunity)
                
            # Add a small delay to simulate processing time
            await asyncio.sleep(0.2)
        
        return self.opportunities
    
    def get_results(self) -> Dict[str, Any]:
        """Get scan results in the expected format"""
        return {
            "arbitrage_opportunities": self.opportunities,
            "meta": {
                "timestamp": datetime.now().isoformat(),
                "subcategories": list(set(opp["subcategory"] for opp in self.opportunities)),
                "total_opportunities": len(self.opportunities),
                "marketplaces": list(set([opp["buyMarketplace"] for opp in self.opportunities] + 
                                       [opp["sellMarketplace"] for opp in self.opportunities]))
            }
        }

# Create a dummy scraper
dummy_scraper = DummyScraper()

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
        "timestamp": datetime.now().isoformat(),
        "keywords_available": keywords_available
    }

@app.post("/api/scan")
async def scan_marketplaces(request: ScanRequest):
    """Scan marketplaces for arbitrage opportunities"""
    try:
        logger.info(f"Starting scan for subcategories: {request.subcategories}")
        
        # Basic validation
        if not request.subcategories:
            raise HTTPException(status_code=400, detail="At least one subcategory is required")
        
        # Use dummy scraper to generate results
        opportunities = await dummy_scraper.search_marketplaces(request.subcategories)
        
        # Get results
        results = dummy_scraper.get_results()
        
        # Limit results if requested
        if request.max_results:
            results["arbitrage_opportunities"] = results["arbitrage_opportunities"][:request.max_results]
        
        # Add progress information
        results["meta"]["progress"] = 100
        results["meta"]["status"] = "completed"
        
        return results
    
    except Exception as e:
        logger.error(f"Error during scan: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"An error occurred during the scan: {str(e)}")

@app.get("/api/progress/{scan_id}")
async def get_scan_progress(scan_id: str):
    """Get the progress of a scan"""
    # In a real implementation, this would check a database or cache
    # For now, just return 100% complete
    return {
        "scan_id": scan_id,
        "progress": 100,
        "status": "completed",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/scan", response_class=HTMLResponse)
async def scan_page(request: Request):
    """Scan page for finding arbitrage opportunities"""
    # Check if scan.html exists in the templates directory
    if os.path.exists("templates/scan.html"):
        with open("templates/scan.html", "r") as f:
            return HTMLResponse(content=f.read())
    
    # Otherwise create a basic scan page
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
                .category {
                    margin-bottom: 20px;
                    border: 1px solid #ddd;
                    padding: 15px;
                    border-radius: 8px;
                }
                .category h3 {
                    margin-top: 0;
                    color: #D16B34;
                }
                .subcategory {
                    margin-bottom: 8px;
                }
                .btn {
                    display: inline-block;
                    background-color: #D16B34;
                    color: white;
                    padding: 10px 20px;
                    border-radius: 4px;
                    border: none;
                    cursor: pointer;
                    font-size: 16px;
                    margin-top: 20px;
                }
                .btn:hover {
                    background-color: #b15426;
                }
                .btn:disabled {
                    background-color: #ccc;
                    cursor: not-allowed;
                }
                .loading {
                    display: none;
                    text-align: center;
                    margin-top: 20px;
                }
                .spinner {
                    border: 4px solid #f3f3f3;
                    border-top: 4px solid #D16B34;
                    border-radius: 50%;
                    width: 30px;
                    height: 30px;
                    animation: spin 1s linear infinite;
                    margin: 0 auto 10px;
                }
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
                .progress-container {
                    margin-top: 20px;
                    display: none;
                }
                .progress-bar {
                    height: 20px;
                    background-color: #f3f3f3;
                    border-radius: 10px;
                    overflow: hidden;
                }
                .progress-fill {
                    height: 100%;
                    background-color: #D16B34;
                    width: 0%;
                    transition: width 0.3s ease;
                }
                .results {
                    margin-top: 30px;
                    display: none;
                }
                .opportunity {
                    border: 1px solid #ddd;
                    border-radius: 8px;
                    padding: 15px;
                    margin-bottom: 15px;
                }
                .opportunity-header {
                    display: flex;
                    justify-content: space-between;
                    margin-bottom: 10px;
                }
                .profit {
                    color: green;
                    font-weight: bold;
                }
                .comparison {
                    display: flex;
                    justify-content: space-between;
                }
                .buy, .sell {
                    flex: 1;
                    padding: 10px;
                }
                .marketplace {
                    font-size: 12px;
                    color: #666;
                }
                .price {
                    font-size: 18px;
                    font-weight: bold;
                }
                .error {
                    display: none;
                    color: red;
                    padding: 10px;
                    background-color: #ffe6e6;
                    border-radius: 4px;
                    margin-top: 20px;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>FlipHawk - Scan for Arbitrage</h1>
                <p>Select subcategories to scan for arbitrage opportunities across marketplaces.</p>
                
                <div class="category">
                    <h3>Tech</h3>
                    <div class="subcategory">
                        <label>
                            <input type="checkbox" name="subcategory" value="Headphones"> Headphones
                        </label>
                    </div>
                    <div class="subcategory">
                        <label>
                            <input type="checkbox" name="subcategory" value="Keyboards"> Keyboards
                        </label>
                    </div>
                    <div class="subcategory">
                        <label>
                            <input type="checkbox" name="subcategory" value="Graphics Cards"> Graphics Cards
                        </label>
                    </div>
                </div>
                
                <div class="category">
                    <h3>Collectibles</h3>
                    <div class="subcategory">
                        <label>
                            <input type="checkbox" name="subcategory" value="Pokémon"> Pokémon
                        </label>
                    </div>
                    <div class="subcategory">
                        <label>
                            <input type="checkbox" name="subcategory" value="Magic: The Gathering"> Magic: The Gathering
                        </label>
                    </div>
                </div>
                
                <div class="error" id="error"></div>
                
                <button id="scanButton" class="btn">Start Scanning</button>
                
                <div class="loading" id="loading">
                    <div class="spinner"></div>
                    <p>Scanning marketplaces for opportunities...</p>
                </div>
                
                <div class="progress-container" id="progressContainer">
                    <p>Scan progress: <span id="progressPercent">0</span>%</p>
                    <div class="progress-bar">
                        <div class="progress-fill" id="progressFill"></div>
                    </div>
                </div>
                
                <div class="results" id="results">
                    <h2>Arbitrage Opportunities</h2>
                    <div id="opportunitiesList"></div>
                </div>
                
                <script>
                    document.addEventListener('DOMContentLoaded', function() {
                        const scanButton = document.getElementById('scanButton');
                        const loading = document.getElementById('loading');
                        const progressContainer = document.getElementById('progressContainer');
                        const progressPercent = document.getElementById('progressPercent');
                        const progressFill = document.getElementById('progressFill');
                        const results = document.getElementById('results');
                        const opportunitiesList = document.getElementById('opportunitiesList');
                        const error = document.getElementById('error');
                        
                        let scanId = null;
                        let checkProgressInterval = null;
                        
                        scanButton.addEventListener('click', async function() {
                            // Get selected subcategories
                            const checkboxes = document.querySelectorAll('input[name="subcategory"]:checked');
                            const subcategories = Array.from(checkboxes).map(cb => cb.value);
                            
                            if (subcategories.length === 0) {
                                error.textContent = 'Please select at least one subcategory to scan';
                                error.style.display = 'block';
                                return;
                            }
                            
                            error.style.display = 'none';
                            results.style.display = 'none';
                            scanButton.disabled = true;
                            loading.style.display = 'block';
                            progressContainer.style.display = 'block';
                            
                            // Reset progress
                            progressPercent.textContent = '0';
                            progressFill.style.width = '0%';
                            
                            try {
                                // Start scan
                                const response = await fetch('/api/scan', {
                                    method: 'POST',
                                    headers: {
                                        'Content-Type': 'application/json'
                                    },
                                    body: JSON.stringify({
                                        subcategories: subcategories,
                                        max_results: 20
                                    })
                                });
                                
                                if (!response.ok) {
                                    throw new Error('Failed to start scan');
                                }
                                
                                const data = await response.json();
                                
                                // Simulate progress updates
                                let progress = 0;
                                const interval = setInterval(() => {
                                    progress += 5;
                                    if (progress > 100) {
                                        clearInterval(interval);
                                        progress = 100;
                                    }
                                    
                                    progressPercent.textContent = progress;
                                    progressFill.style.width = `${progress}%`;
                                    
                                    if (progress === 100) {
                                        // Display results
                                        displayResults(data);
                                    }
                                }, 200);
                                
                            } catch (err) {
                                console.error('Error during scan:', err);
                                error.textContent = `Error: ${err.message}`;
                                error.style.display = 'block';
                                scanButton.disabled = false;
                                loading.style.display = 'none';
                                progressContainer.style.display = 'none';
                            }
                        });
                        
                        function displayResults(data) {
                            loading.style.display = 'none';
                            scanButton.disabled = false;
                            
                            if (!data.arbitrage_opportunities || data.arbitrage_opportunities.length === 0) {
                                error.textContent = 'No arbitrage opportunities found';
                                error.style.display = 'block';
                                return;
                            }
                            
                            // Clear previous results
                            opportunitiesList.innerHTML = '';
                            
                            // Add each opportunity
                            data.arbitrage_opportunities.forEach(opp => {
                                const div = document.createElement('div');
                                div.className = 'opportunity';
                                
                                div.innerHTML = `
                                    <div class="opportunity-header">
                                        <h3>${opp.buyTitle}</h3>
                                        <div class="profit">
                                            Profit: $${opp.profit.toFixed(2)} (${opp.profitPercentage.toFixed(2)}%)
                                        </div>
                                    </div>
                                    <div class="comparison">
                                        <div class="buy">
                                            <div class="marketplace">Buy on ${opp.buyMarketplace}</div>
                                            <div class="price">$${opp.buyPrice.toFixed(2)}</div>
                                            <div class="condition">${opp.buyCondition}</div>
                                            <a href="${opp.buyLink}" target="_blank">View Listing</a>
                                        </div>
                                        <div class="sell">
                                            <div class="marketplace">Sell on ${opp.sellMarketplace}</div>
                                            <div class="price">$${opp.sellPrice.toFixed(2)}</div>
                                            <div class="condition">${opp.sellCondition}</div>
                                            <a href="${opp.sellLink}" target="_blank">View Listing</a>
                                        </div>
                                    </div>
                                    <div class="confidence">
                                        Confidence: ${opp.confidence}%
                                    </div>
                                `;
                                
                                opportunitiesList.appendChild(div);
                            });
                            
                            results.style.display = 'block';
                        }
                    });
                </script>
            </div>
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
