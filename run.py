# run.py
import uvicorn
import logging
import os

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

if __name__ == "__main__":
    # Get port from environment or use default 10000
    port = int(os.environ.get("PORT", 10000))
    
    # Log starting information
    logger.info(f"Starting FlipHawk server on port {port}")
    
    # Run the application
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)
