# api_integration.py
import os
import json
import logging
import time
import asyncio
import aiohttp
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger('api_integration')

class EnhancedAPIIntegration:
    """Enhanced API Integration class for making requests to various marketplaces."""
    
    def __init__(self):
        self.api_keys = self._load_api_keys()
        self.session = None
        self.rate_limits = {
            'amazon': {'calls_per_second': 1, 'last_call': 0},
            'ebay': {'calls_per_second': 5, 'last_call': 0},
            'tcgplayer': {'calls_per_second': 5, 'last_call': 0},
            'walmart': {'calls_per_second': 2, 'last_call': 0},
            'etsy': {'calls_per_second': 5, 'last_call': 0},
            'mercari': {'calls_per_second': 2, 'last_call': 0}
        }
        self.tokens = {}
        
    def _load_api_keys(self) -> Dict[str, str]:
        """Load API keys from environment variables or config file"""
        try:
            # Try to load from environment variables first
            api_keys = {
                'amazon': os.environ.get('AMAZON_API_KEY', ''),
                'ebay': os.environ.get('EBAY_API_KEY', ''),
                'tcgplayer': os.environ.get('TCGPLAYER_API_KEY', ''),
                'walmart': os.environ.get('WALMART_API_KEY', ''),
                'etsy': os.environ.get('ETSY_API_KEY', ''),
                'mercari': os.environ.get('MERCARI_API_KEY', '')
            }
            
            # If any keys are missing, try to load from config file
            if '' in api_keys.values():
                try:
                    with open('config.json', 'r') as f:
                        config = json.load(f)
                        for marketplace, key in config.get('api_keys', {}).items():
                            if marketplace in api_keys and not api_keys[marketplace]:
                                api_keys[marketplace] = key
                except FileNotFoundError:
                    logger.warning("Config file not found. Using available environment variables.")
            
            return api_keys
        except Exception as e:
            logger.error(f"Error loading API keys: {str(e)}")
            return {}

    async def initialize(self):
        """Initialize API session and authenticate with services"""
        self.session = aiohttp.ClientSession()
        
        # Initialize tokens for services that need authentication
        tasks = []
        for marketplace in ['ebay', 'amazon', 'tcgplayer', 'etsy']:
            if self.api_keys.get(marketplace):
                tasks.append(self.authenticate(marketplace))
        
        if tasks:
            await asyncio.gather(*tasks)
        
        logger.info(f"API Integration initialized with tokens for: {', '.join(self.tokens.keys())}")
    
    async def close(self):
        """Close the API session"""
        if self.session:
            await self.session.close()
            self.session = None

    async def authenticate(self, marketplace: str) -> str:
        """Authenticate with the marketplace API and get access token"""
        if not self.session:
            await self.initialize()
        
        try:
            api_key = self.api_keys.get(marketplace)
            if not api_key:
                logger.warning(f"No API key available for {marketplace}")
                return ""
            
            if marketplace == 'ebay':
                url = 'https://api.ebay.com/identity/v1/oauth2/token'
                headers = {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Authorization': f'Basic {api_key}'
                }
                data = {
                    'grant_type': 'client_credentials',
                    'scope': 'https://api.ebay.com/oauth/api_scope'
                }
                
                async with self.session.post(url, headers=headers, data=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        self.tokens['ebay'] = result.get('access_token', '')
                        return self.tokens['ebay']
                    else:
                        logger.error(f"eBay authentication failed: {response.status}")
                        return ""
            
            elif marketplace == 'amazon':
                # Amazon authentication logic
                # Implementation depends on which Amazon API you're using (MWS, SP-API, etc.)
                logger.info("Amazon authentication placeholder - implement based on specific API requirements")
                self.tokens['amazon'] = "placeholder_token"
                return self.tokens['amazon']
            
            elif marketplace == 'tcgplayer':
                url = 'https://api.tcgplayer.com/token'
                headers = {'Content-Type': 'application/x-www-form-urlencoded'}
                data = {
                    'grant_type': 'client_credentials',
                    'client_id': api_key.split(':')[0],
                    'client_secret': api_key.split(':')[1]
                }
                
                async with self.session.post(url, headers=headers, data=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        self.tokens['tcgplayer'] = result.get('access_token', '')
                        return self.tokens['tcgplayer']
                    else:
                        logger.error(f"TCGPlayer authentication failed: {response.status}")
                        return ""
            
            elif marketplace == 'etsy':
                # Etsy OAuth 2.0 authentication
                url = 'https://api.etsy.com/v3/public/oauth/token'
                headers = {'Content-Type': 'application/x-www-form-urlencoded'}
                data = {
                    'grant_type': 'client_credentials',
                    'client_id': api_key
                }
                
                async with self.session.post(url, headers=headers, data=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        self.tokens['etsy'] = result.get('access_token', '')
                        return self.tokens['etsy']
                    else:
                        logger.error(f"Etsy authentication failed: {response.status}")
                        return ""
            
            else:
                logger.warning(f"Authentication not implemented for {marketplace}")
                return ""
                
        except Exception as e:
            logger.error(f"Error during {marketplace} authentication: {str(e)}")
            return ""

    async def make_api_request(self, marketplace: str, endpoint: str, method: str = 'GET', 
                              params: Dict = None, data: Dict = None, headers: Dict = None) -> Dict:
        """Make an API request to the specified marketplace"""
        if not self.session:
            await self.initialize()
        
        if not headers:
            headers = {}
        
        # Add authentication token if available
        if marketplace in self.tokens and self.tokens[marketplace]:
            headers['Authorization'] = f'Bearer {self.tokens[marketplace]}'
        
        # Respect rate limits
        await self._respect_rate_limit(marketplace)
        
        try:
            if method.upper() == 'GET':
                async with self.session.get(endpoint, params=params, headers=headers) as response:
                    return await self._process_response(response, marketplace)
            elif method.upper() == 'POST':
                async with self.session.post(endpoint, params=params, json=data, headers=headers) as response:
                    return await self._process_response(response, marketplace)
            else:
                logger.warning(f"Unsupported HTTP method: {method}")
                return {"error": f"Unsupported HTTP method: {method}"}
        
        except Exception as e:
            logger.error(f"Error making {marketplace} API request: {str(e)}")
            return {"error": str(e)}

    async def _process_response(self, response, marketplace: str) -> Dict:
        """Process API response"""
        try:
            if response.status == 200:
                return await response.json()
            elif response.status == 401:
                # Token expired, try to re-authenticate
                logger.info(f"{marketplace} token expired. Re-authenticating...")
                await self.authenticate(marketplace)
                return {"error": "Authentication token expired. Please retry the request."}
            elif response.status == 429:
                # Rate limit exceeded
                logger.warning(f"{marketplace} rate limit exceeded. Will retry later.")
                return {"error": "Rate limit exceeded"}
            else:
                error_text = await response.text()
                logger.error(f"{marketplace} API error ({response.status}): {error_text}")
                return {"error": f"API error: {response.status}", "details": error_text}
        except Exception as e:
            logger.error(f"Error processing {marketplace} response: {str(e)}")
            return {"error": str(e)}

    async def _respect_rate_limit(self, marketplace: str):
        """Respect API rate limits by adding delays if necessary"""
        if marketplace not in self.rate_limits:
            return
        
        rate_info = self.rate_limits[marketplace]
        current_time = datetime.now().timestamp()
        time_since_last_call = current_time - rate_info['last_call']
        min_interval = 1.0 / rate_info['calls_per_second']
        
        if time_since_last_call < min_interval:
            delay = min_interval - time_since_last_call
            logger.debug(f"Rate limiting {marketplace}: sleeping for {delay:.2f}s")
            await asyncio.sleep(delay)
        
        # Update last call time
        self.rate_limits[marketplace]['last_call'] = datetime.now().timestamp()

# Create a singleton instance
api_integration = EnhancedAPIIntegration()
