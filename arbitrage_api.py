"""
Arbitrage API for FlipHawk system.
This module provides API endpoints for the arbitrage functionality.
"""

from flask import Blueprint, request, jsonify
import asyncio
import logging
import traceback
from typing import List, Dict, Any
from arbitrage_coordinator import run_coordinated_scan

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('arbitrage_api')

# Create blueprint
arbitrage_api = Blueprint('arbitrage_api', __name__)

@arbitrage_api.route('/api/v1/arbitrage/scan', methods=['POST'])
async def scan_for_arbitrage():
    """
    API endpoint to scan for arbitrage opportunities.
    
    Expected request body:
    {
        "category": "Tech",
        "subcategories": ["Headphones", "Keyboards"]
    }
    
    Returns:
        JSON list of arbitrage opportunities
    """
    try:
        # Get request data
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Extract parameters
        category = data.get('category', '')
        subcategories = data.get('subcategories', [])
        
        # Validate parameters
        if not category:
            return jsonify({"error": "Category is required"}), 400
        
        if not subcategories or not isinstance(subcategories, list):
            return jsonify({"error": "Subcategories must be a non-empty list"}), 400
        
        # Log the request
        logger.info(f"Received scan request for category: {category}, subcategories: {subcategories}")
        
        # Run the coordinated scan
        results = await run_coordinated_scan(category, subcategories)
        
        # Return results
        return jsonify(results)
        
    except Exception as e:
        # Log the error
        logger.error(f"Error processing scan request: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Return error response
        return jsonify({
            "error": "Error connecting to scanning service. Please try again later.",
            "details": str(e)
        }), 500

@arbitrage_api.route('/api/v1/arbitrage/status', methods=['GET'])
def get_scan_status():
    """
    API endpoint to check the status of the arbitrage system.
    
    Returns:
        JSON status information
    """
    from arbitrage_coordinator import coordinator
    
    # Get active scan count
    active_scans = coordinator.get_active_scan_count()
    
    # Get cache size
    cache_size = len(coordinator.scan_results_cache)
    
    return jsonify({
        "status": "operational",
        "active_scans": active_scans,
        "cache_size": cache_size,
        "cache_lifetime_seconds": coordinator.cache_lifetime
    })

@arbitrage_api.route('/api/v1/arbitrage/clear-cache', methods=['POST'])
def clear_cache():
    """
    API endpoint to clear the arbitrage cache.
    
    Expected request body (optional):
    {
        "category": "Tech",
        "subcategories": ["Headphones", "Keyboards"]
    }
    
    If no body is provided, all cache will be cleared.
    
    Returns:
        JSON status message
    """
    from arbitrage_coordinator import coordinator
    
    try:
        # Get request data
        data = request.get_json()
        
        if data:
            # Extract parameters
            category = data.get('category')
            subcategories = data.get('subcategories')
            
            # Clear specific cache
            if category and subcategories:
                coordinator.clear_cache(category, subcategories)
                return jsonify({
                    "message": f"Cache cleared for {category}:{','.join(subcategories)}",
                    "success": True
                })
        
        # Clear all cache
        coordinator.clear_cache()
        return jsonify({
            "message": "All cache cleared",
            "success": True
        })
        
    except Exception as e:
        # Log the error
        logger.error(f"Error clearing cache: {str(e)}")
        
        # Return error response
        return jsonify({
            "error": "Error clearing cache",
            "details": str(e),
            "success": False
        }), 500

@arbitrage_api.route('/api/v1/arbitrage/calculate', methods=['POST'])
def calculate_arbitrage_metrics():
    """
    API endpoint to calculate arbitrage metrics for a given opportunity.
    
    Expected request body:
    {
        "buy_price": 100.0,
        "sell_price": 150.0,
        "buy_marketplace": "Amazon",
        "sell_marketplace": "eBay",
        "shipping_cost": 10.0,
        "item_category": "Electronics"
    }
    
    Returns:
        JSON metrics
    """
    try:
        # Get request data
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Extract parameters
        buy_price = data.get('buy_price', 0.0)
        sell_price = data.get('sell_price', 0.0)
        buy_marketplace = data.get('buy_marketplace', 'Unknown')
        sell_marketplace = data.get('sell_marketplace', 'Unknown')
        shipping_cost = data.get('shipping_cost', 0.0)
        item_category = data.get('item_category', 'Unknown')
        
        # Validate parameters
        if buy_price <= 0 or sell_price <= 0:
            return jsonify({"error": "Buy price and sell price must be greater than 0"}), 400
        
        # Calculate metrics
        metrics = calculate_metrics(
            buy_price=buy_price,
            sell_price=sell_price,
            buy_marketplace=buy_marketplace,
            sell_marketplace=sell_marketplace,
            shipping_cost=shipping_cost,
            item_category=item_category
        )
        
        return jsonify(metrics)
        
    except Exception as e:
        # Log the error
        logger.error(f"Error calculating metrics: {str(e)}")
        
        # Return error response
        return jsonify({
            "error": "Error calculating metrics",
            "details": str(e)
        }), 500

def calculate_metrics(buy_price: float, sell_price: float, buy_marketplace: str, 
                     sell_marketplace: str, shipping_cost: float = 0.0, 
                     item_category: str = 'Unknown') -> Dict[str, Any]:
    """
    Calculate arbitrage metrics for a given opportunity.
    
    Args:
        buy_price (float): Price to buy the item
        sell_price (float): Price to sell the item
        buy_marketplace (str): Marketplace to buy from
        sell_marketplace (str): Marketplace to sell on
        shipping_cost (float): Shipping cost
        item_category (str): Category of the item
        
    Returns:
        Dict[str, Any]: Calculated metrics
    """
    # Calculate profit
    profit = sell_price - buy_price - shipping_cost
    
    # Calculate ROI percentage
    roi_percentage = (profit / buy_price) * 100 if buy_price > 0 else 0
    
    # Calculate sales tax (approximate as 8% of buy price)
    sales_tax = buy_price * 0.08
    
    # Calculate marketplace fee
    marketplace_fee = 0.0
    
    if 'ebay' in sell_marketplace.lower():
        # eBay fee: 10-15% of sell price including shipping
        marketplace_fee = sell_price * 0.125  # 12.5% average
        payment_fee = sell_price * 0.029 + 0.30  # PayPal fee (2.9% + $0.30)
    elif 'amazon' in sell_marketplace.lower():
        # Amazon fee: 15% of sell price + variable closing fee
        marketplace_fee = sell_price * 0.15 + 1.80  # $1.80 variable closing fee
        payment_fee = 0.0  # Included in marketplace fee
    elif 'facebook' in sell_marketplace.lower():
        # Facebook Marketplace fee
        marketplace_fee = sell_price * 0.05  # 5% fee
        payment_fee = 0.0  # Included in marketplace fee
    else:
        # Default fee
        marketplace_fee = sell_price * 0.10  # 10% fee
        payment_fee = sell_price * 0.029 + 0.30  # Standard payment processing
    
    # Calculate net profit
    total_cost = buy_price + shipping_cost + sales_tax
    total_fees = marketplace_fee + payment_fee
    net_profit = sell_price - total_cost - total_fees
    
    # Calculate net ROI percentage
    net_roi_percentage = (net_profit / total_cost) * 100 if total_cost > 0 else 0
    
    # Estimate time to sell based on category and marketplaces
    time_to_sell = estimate_time_to_sell(item_category, sell_marketplace, roi_percentage)
    
    # Calculate velocity score
    velocity_score = calculate_velocity_score(item_category, roi_percentage, sell_marketplace)
    
    return {
        "profit": round(profit, 2),
        "roi_percentage": round(roi_percentage, 2),
        "sales_tax": round(sales_tax, 2),
        "marketplace_fee": round(marketplace_fee, 2),
        "payment_fee": round(payment_fee, 2),
        "total_cost": round(total_cost, 2),
        "total_fees": round(total_fees, 2),
        "net_profit": round(net_profit, 2),
        "net_roi_percentage": round(net_roi_percentage, 2),
        "estimated_time_to_sell_days": time_to_sell,
        "velocity_score": velocity_score
    }

def estimate_time_to_sell(category: str, marketplace: str, roi_percentage: float) -> int:
    """
    Estimate time to sell based on category, marketplace, and ROI.
    
    Args:
        category (str): Item category
        marketplace (str): Selling marketplace
        roi_percentage (float): ROI percentage
        
    Returns:
        int: Estimated time to sell in days
    """
    # Base time
    base_time = 14  # Default 2 weeks
    
    # Adjust for category
    fast_categories = ["Electronics", "Video Games", "Tech", "Collectibles"]
    slow_categories = ["Antiques", "Art", "Books", "Clothing"]
    
    if any(fast_cat.lower() in category.lower() for fast_cat in fast_categories):
        base_time -= 7  # Fast categories sell in 1 week
    elif any(slow_cat.lower() in category.lower() for slow_cat in slow_categories):
        base_time += 7  # Slow categories sell in 3 weeks
    
    # Adjust for marketplace
    if "amazon" in marketplace.lower():
        base_time -= 3  # Amazon sells faster
    elif "ebay" in marketplace.lower():
        base_time -= 1  # eBay sells moderately fast
    elif "facebook" in marketplace.lower():
        base_time += 2  # Facebook Marketplace can be slower
    
    # Adjust for ROI
    if roi_percentage > 50:
        base_time -= 2  # High ROI items may need to be priced higher, taking longer to sell
    elif roi_percentage < 20:
        base_time -= 3  # Low ROI items are likely priced more competitively and sell faster
    
    # Ensure minimum of 1 day
    return max(1, base_time)

def calculate_velocity_score(category: str, roi_percentage: float, marketplace: str) -> int:
    """
    Calculate a velocity score (0-100) based on how quickly an item is likely to sell.
    
    Args:
        category (str): Item category
        roi_percentage (float): ROI percentage
        marketplace (str): Selling marketplace
        
    Returns:
        int: Velocity score from 0 to 100
    """
    # Base score
    score = 50
    
    # Adjust for category
    fast_categories = ["Electronics", "Video Games", "Tech", "Collectibles"]
    if any(fast_cat.lower() in category.lower() for fast_cat in fast_categories):
        score += 15
    
    # Adjust for ROI
    if roi_percentage < 20:
        score += 10  # Low ROI items sell faster due to competitive pricing
    elif roi_percentage > 50:
        score -= 5  # High ROI items may be priced higher, selling slower
    
    # Adjust for marketplace
    if "amazon" in marketplace.lower():
        score += 15  # Amazon has high velocity
    elif "ebay" in marketplace.lower():
        score += 10  # eBay has good velocity
    elif "facebook" in marketplace.lower():
        score -= 5  # Facebook Marketplace can be slower
    
    # Ensure score is between 0 and 100
    return max(0, min(100, score))

@arbitrage_api.route('/api/v1/arbitrage/recommendations', methods=['POST'])
def get_recommendations():
    """
    API endpoint to get arbitrage recommendations for a user.
    
    Expected request body:
    {
        "user_id": "12345",
        "categories": ["Tech", "Gaming"],
        "budget": 500.0,
        "min_roi": 20.0
    }
    
    Returns:
        JSON recommendations
    """
    try:
        # Get request data
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Extract parameters
        user_id = data.get('user_id')
        categories = data.get('categories', [])
        budget = data.get('budget', 0.0)
        min_roi = data.get('min_roi', 0.0)
        
        # Validate parameters
        if not user_id:
            return jsonify({"error": "User ID is required"}), 400
        
        if budget <= 0:
            return jsonify({"error": "Budget must be greater than 0"}), 400
        
        # Get recommendations
        # TODO: Implement real recommendation system
        # For now, return dummy data
        recommendations = [
            {
                "category": "Tech",
                "subcategory": "Headphones",
                "estimated_profit": 45.28,
                "estimated_roi": 32.5,
                "buy_marketplace": "Amazon",
                "sell_marketplace": "eBay",
                "confidence": 89
            },
            {
                "category": "Gaming",
                "subcategory": "Consoles",
                "estimated_profit": 78.15,
                "estimated_roi": 28.7,
                "buy_marketplace": "Walmart",
                "sell_marketplace": "eBay",
                "confidence": 92
            },
            {
                "category": "Tech",
                "subcategory": "Graphics Cards",
                "estimated_profit": 112.42,
                "estimated_roi": 24.3,
                "buy_marketplace": "Newegg",
                "sell_marketplace": "Facebook Marketplace",
                "confidence": 85
            }
        ]
        
        return jsonify({
            "user_id": user_id,
            "recommendations": recommendations,
            "budget": budget,
            "min_roi": min_roi
        })
        
    except Exception as e:
        # Log the error
        logger.error(f"Error getting recommendations: {str(e)}")
        
        # Return error response
        return jsonify({
            "error": "Error getting recommendations",
            "details": str(e)
        }), 500

@arbitrage_api.route('/api/v1/arbitrage/demo', methods=['GET'])
def get_demo_results():
    """
    API endpoint to get demo arbitrage results.
    This is for demonstration purposes only.
    
    Returns:
        JSON demo results
    """
    # Demo data
    demo_results = [
        {
            "title": "Sony WH-1000XM4 Wireless Noise Cancelling Headphones",
            "buyPrice": 248.99,
            "sellPrice": 328.95,
            "buyMarketplace": "Amazon",
            "sellMarketplace": "eBay",
            "buyLink": "https://www.amazon.com/Sony-WH-1000XM4-Canceling-Headphones-Phone-Call/dp/B0863TXGM3",
            "sellLink": "https://www.ebay.com/itm/294567830291",
            "profit": 59.24,
            "profitPercentage": 23.8,
            "confidence": 96,
            "buyCondition": "New",
            "sellCondition": "New",
            "buyShipping": 0.0,
            "estimatedTax": 19.92,
            "platformFee": 41.12,
            "paymentFee": 9.84,
            "totalCost": 268.91,
            "totalFees": 50.96,
            "netProfit": 9.08,
            "netProfitPercentage": 3.4,
            "image_url": "https://m.media-amazon.com/images/I/71o8Q5XJS5L._AC_SL1500_.jpg",
            "subcategory": "Headphones",
            "category": "Tech",
            "velocityScore": 75,
            "estimatedSellDays": 5
        },
        {
            "title": "Nintendo Switch OLED Model with White Joy-Con",
            "buyPrice": 299.99,
            "sellPrice": 389.99,
            "buyMarketplace": "Walmart",
            "sellMarketplace": "eBay",
            "buyLink": "https://www.walmart.com/ip/883373078",
            "sellLink": "https://www.ebay.com/itm/284501147237",
            "profit": 65.00,
            "profitPercentage": 21.7,
            "confidence": 94,
            "buyCondition": "New",
            "sellCondition": "New",
            "buyShipping": 0.0,
            "estimatedTax": 24.00,
            "platformFee": 48.75,
            "paymentFee": 11.61,
            "totalCost": 323.99,
            "totalFees": 60.36,
            "netProfit": 5.64,
            "netProfitPercentage": 1.7,
            "image_url": "https://i5.walmartimages.com/seo/Nintendo-Switch-OLED-Model-with-White-Joy-Con_5582993c-6c91-4ea2-9c50-b0fa8f61ed63.5ef42888ae311da21c3cd7f6ed3c0a59.jpeg",
            "subcategory": "Consoles",
            "category": "Gaming",
            "velocityScore": 82,
            "estimatedSellDays": 3
        },
        {
            "title": "Logitech G Pro X Mechanical Gaming Keyboard",
            "buyPrice": 89.99,
            "sellPrice": 129.99,
            "buyMarketplace": "Amazon",
            "sellMarketplace": "Facebook Marketplace",
            "buyLink": "https://www.amazon.com/Logitech-Mechanical-Keyboard-Detachable-Switches/dp/B07QQB9VCV",
            "sellLink": "https://www.facebook.com/marketplace/item/1234567890",
            "profit": 33.20,
            "profitPercentage": 36.9,
            "confidence": 88,
            "buyCondition": "New",
            "sellCondition": "New",
            "buyShipping": 0.0,
            "estimatedTax": 7.20,
            "platformFee": 6.50,
            "paymentFee": 0.0,
            "totalCost": 97.19,
            "totalFees": 6.50,
            "netProfit": 26.30,
            "netProfitPercentage": 27.1,
            "image_url": "https://m.media-amazon.com/images/I/61eDXJjg9bL._AC_SL1500_.jpg",
            "subcategory": "Keyboards",
            "category": "Tech",
            "velocityScore": 68,
            "estimatedSellDays": 7
        },
        {
            "title": "Apple AirPods Pro (2nd Generation) with MagSafe Case",
            "buyPrice": 169.99,
            "sellPrice": 229.00,
            "buyMarketplace": "Walmart",
            "sellMarketplace": "eBay",
            "buyLink": "https://www.walmart.com/ip/Apple-AirPods-Pro-2nd-Generation-with-MagSafe-Case/1974637301",
            "sellLink": "https://www.ebay.com/itm/284567890123",
            "profit": 45.37,
            "profitPercentage": 26.7,
            "confidence": 95,
            "buyCondition": "New",
            "sellCondition": "New",
            "buyShipping": 0.0,
            "estimatedTax": 13.60,
            "platformFee": 28.63,
            "paymentFee": 6.94,
            "totalCost": 183.59,
            "totalFees": 35.57,
            "netProfit": 9.84,
            "netProfitPercentage": 5.4,
            "image_url": "https://i5.walmartimages.com/seo/Apple-AirPods-Pro-2nd-Generation-with-MagSafe-Case_51342b5c-0a25-4cef-b4a3-429a7b47fd2a.353102d28b0a7c3236804c11848c1a7d.jpeg",
            "subcategory": "Headphones",
            "category": "Tech",
            "velocityScore": 78,
            "estimatedSellDays": 4
        }
    ]
    
    return jsonify(demo_results)
