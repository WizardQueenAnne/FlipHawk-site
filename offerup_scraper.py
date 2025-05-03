import asyncio
import aiohttp
import logging
import json
import re
import random
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import quote, urljoin, quote_plus
from functools import wraps
from json import JSONDecodeError

from api_integration import EnhancedAPIIntegration
from comprehensive_keywords import generate_keywords, COMPREHENSIVE_KEYWORDS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("offerup_scraper.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class RetryConfig:
    """Configuration for retry mechanism."""
    MAX_RETRIES = 3
    BASE_DELAY = 1.0
    MAX_DELAY = 60.0
    EXPONENTIAL_BASE = 2.0
    JITTER = 0.1

def exponential_backoff_with_jitter(attempt: int) -> float:
    """Calculate delay with exponential backoff and jitter."""
    delay = min(
        RetryConfig.BASE_DELAY * (RetryConfig.EXPONENTIAL_BASE ** attempt),
        RetryConfig.MAX_DELAY
    )
    jitter = delay * RetryConfig.JITTER * (2 * random.random() - 1)
    return delay + jitter

def retry_with_backoff(max_retries: int = RetryConfig.MAX_RETRIES):
    """Decorator for implementing retry with exponential backoff."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except (aiohttp.ClientError, asyncio.TimeoutError, JSONDecodeError) as e:
                    if attempt == max_retries - 1:
                        logger.error(f"All {max_retries} attempts failed for {func.__name__}: {str(e)}")
                        raise
                    
                    delay = exponential_backoff_with_jitter(attempt)
                    logger.warning(f"Attempt {attempt + 1} failed in {func.__name__}. Retrying in {delay:.2f}s. Error: {str(e)}")
                    await asyncio.sleep(delay)
            
            return None
        return wrapper
    return decorator

class OfferUpScr
