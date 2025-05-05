# FlipHawk - Marketplace Arbitrage System

This guide explains how to properly connect the FlipHawk backend scraper system with the frontend user interface.

## System Overview

FlipHawk is an arbitrage scanner application that searches multiple marketplaces for profitable resale opportunities. The system has the following components:

1. **Frontend UI** - HTML/CSS/JavaScript interface for user interactions
2. **FastAPI Backend** - API endpoints that process requests and respond with data
3. **Marketplace Scrapers** - Python modules that search marketplaces (Amazon, eBay, Facebook, etc.)
4. **Arbitrage Scanner** - Core logic that analyzes listings to find profitable opportunities

## Integration Changes

The following files have been modified or created to properly connect the frontend with the backend:

1. **app.py** - Updated with proper API routes that connect to the marketplace scanner
2. **marketplace_bridge.py** - New bridge module that connects API endpoints with scanner functionality
3. **script.js** - Updated frontend JavaScript to properly communicate with the backend
4. **integration_test.py** - Testing script to verify the integration works correctly

## Setup Instructions

### 1. Install Dependencies

Ensure all required Python packages are installed:

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file in the root directory with any necessary configurations:

```
PORT=8000
DEBUG=True
MARKETPLACE_API_TIMEOUT=30
```

### 3. File Updates

Ensure your project structure has the following updated files:

```
FlipHawk/
├── app.py                # Updated FastAPI application
├── marketplace_bridge.py # New bridge module
├── marketplace_scanner.py # Existing scanner module
├── amazon_scraper.py     # Existing scraper
├── ebay_scraper.py       # Existing scraper
├── facebook_scraper.py   # Existing scraper
├── static/
│   ├── js/
│   │   └── script.js     # Updated script
│   └── css/
│       └── styles.css
├── index.html            # Main frontend page
├── scan.html             # Scan page
└── requirements.txt      # Dependencies
```

## Running The Application

1. Start the backend server:

```bash
uvicorn app:app --reload --port 8000
```

2. Access the application:
   - Open your browser and go to `http://localhost:8000`
   - Navigate to the scan page at `http://localhost:8000/scan`

3. Using the application:
   - Select a category and subcategories
   - Click "Begin Resale Search"
   - The system will search multiple marketplaces and return arbitrage opportunities

## Testing the Integration

Run the integration test script to verify the connection between frontend and backend:

```bash
python integration_test.py
```

The test script will check:
1. API health endpoint
2. Scan functionality
3. Progress tracking

## Troubleshooting

If you encounter "Error connecting to scanning service" issues:

1. **API Connectivity:**
   - Check that the FastAPI server is running
   - Verify the correct port is being used

2. **Scanner Errors:**
   - Check console logs for detailed error messages
   - Verify marketplace scrapers are functioning correctly

3. **Data Format Issues:**
   - Ensure the data format returned by the scanner matches what the frontend expects
   - Check the structure of opportunity objects in the console

4. **Timeout Issues:**
   - If scans take too long, adjust the timeout settings in the `marketplace_bridge.py` file

## Additional Notes

- The demonstration uses simulated data when certain marketplace connections are unavailable
- For a full deployment, ensure all API keys are properly configured for each marketplace
- Consider adding rate limiting and error handling for production environments
