"""
Enhanced Arbitrage API for FlipHawk system.
This module provides improved API endpoints for the arbitrage functionality.
"""

from flask import Blueprint, request, jsonify, current_app
import asyncio
import logging
import traceback
import json
from typing import List, Dict, Any
from arbitrage_coordinator import run_coordinated_scan, coordinator
from models import db, User, CategoryPerformance, PriceHistory, AuthenticityFlag, VelocityMetrics
from auth import token_required, record_price_history
from datetime import datetime

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
        
        # Check for cached results first
        cached_results = coordinator.get_cached_results(category, subcategories)
        if cached_results:
            logger.info(f"Returning cached results for {category}:{','.join(subcategories)}")
            return jsonify(cached_results)
        
        # Run the coordinated scan
        results = await run_coordinated_scan(category, subcategories)
        
        # Store price history for listings in results
        try:
            store_price_history(results)
        except Exception as e:
            logger.error(f"Error storing price history: {str(e)}")
        
        # Calculate and store metrics for categories
        try:
            update_category_metrics(category, subcategories, results)
        except Exception as e:
            logger.error(f"Error updating category metrics: {str(e)}")
        
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

def store_price_history(results: List[Dict[str, Any]]):
    """
    Store price history for listings in results.
    
    Args:
        results (List[Dict[str, Any]]): List of arbitrage opportunities
    """
    with current_app.app_context():
        for result in results:
            try:
                # Create a unique identifier based on the title
                buy_title = result.get('buyTitle', result.get('title', ''))
                if not buy_title:
                    continue
                
                item_identifier = create_item_identifier(buy_title)
                
                # Store buy price
                buy_price = result.get('buyPrice', 0)
                buy_marketplace = result.get('buyMarketplace', '')
                if buy_price > 0 and buy_marketplace:
                    buy_condition = result.get('buyCondition', 'Unknown')
                    record_price_history(item_identifier, buy_price, buy_marketplace, buy_condition)
                
                # Store sell price
                sell_price = result.get('sellPrice', 0)
                sell_marketplace = result.get('sellMarketplace', '')
                if sell_price > 0 and sell_marketplace:
                    sell_condition = result.get('sellCondition', 'Unknown')
                    record_price_history(item_identifier, sell_price, sell_marketplace, sell_condition)
                
                # Store velocity metrics if available
                if 'velocityScore' in result and item_identifier:
                    velocity_score = result.get('velocityScore', 0)
                    estimated_sell_days = result.get('estimatedSellDays', 0)
                    
                    # Check if metrics already exist
                    existing_metrics = VelocityMetrics.query.filter_by(item_identifier=item_identifier).first()
                    
                    if existing_metrics:
                        # Update existing metrics
                        existing_metrics.velocity_score = velocity_score
                        existing_metrics.estimated_sell_days = estimated_sell_days
                        existing_metrics.last_updated = datetime.utcnow()
                    else:
                        # Create new metrics
                        new_metrics = VelocityMetrics(
                            item_identifier=item_identifier,
                            velocity_score=velocity_score,
                            estimated_sell_days=estimated_sell_days
                        )
                        db.session.add(new_metrics)
                
                # Check for authenticity concerns
                if result.get('confidence', 0) < 70:
                    flag = AuthenticityFlag(
                        item_identifier=item_identifier,
                        risk_score=100 - result.get('confidence', 0),
                        reasons=json.dumps({"low_confidence": True, "similarity_score": result.get('similarity', 0)})
                    )
                    db.session.add(flag)
            
            except Exception as e:
                logger.error(f"Error processing result for price history: {str(e)}")
                continue
        
        # Commit all changes
        db.session.commit()

def update_category_metrics(category: str, subcategories: List[str], results: List[Dict[str, Any]]):
    """
    Update category performance metrics based on scan results.
    
    Args:
        category (str): Main category
        subcategories (List[str]): List of subcategories
        results (List[Dict[str, Any]]): List of arbitrage opportunities
    """
    with current_app.app_context():
        for subcategory in subcategories:
            # Filter results for this subcategory
            subcat_results = [r for r in results if r.get('subcategory') == subcategory]
            
            if not subcat_results:
                continue
            
            # Calculate metrics
            total_opportunities = len(subcat_results)
            avg_profit = sum(r.get('profit', 0) for r in subcat_results) / total_opportunities if total_opportunities > 0 else 0
            avg_profit_margin = sum(r.get('profitPercentage', 0) for r in subcat_results) / total_opportunities if total_opportunities > 0 else 0
            avg_velocity = sum(r.get('velocityScore', 0) for r in subcat_results) / total_opportunities if total_opportunities > 0 else 0
            
            # Check if entry exists
            perf = CategoryPerformance.query.filter_by(
                category=category,
                subcategory=subcategory
            ).first()
            
            if perf:
                # Update existing entry
                perf.total_opportunities += total_opportunities
                perf.average_profit = (perf.average_profit + avg_profit) / 2  # Simple moving average
                perf.average_profit_margin = (perf.average_profit_margin + avg_profit_margin) / 2
                perf.average_velocity_score = (perf.average_velocity_score + avg_velocity) / 2
                perf.last_updated = datetime.utcnow()
            else:
                # Create new entry
                perf = CategoryPerformance(
                    category=category,
                    subcategory=subcategory,
                    total_opportunities=total_opportunities,
                    successful_flips=0,  # Will be updated when sales are recorded
                    average_profit=avg_profit,
                    average_profit_margin=avg_profit_margin,
                    average_velocity_score=avg_velocity
                )
                db.session.add(perf)
        
        # Commit changes
        db.session.commit()

def create_item_identifier(title: str) -> str:
    """
    Create a unique identifier for an item based on its title.
    
    Args:
        title (str): Item title
        
    Returns:
        str: Unique identifier
    """
    import re
    # Remove special characters and convert to lowercase
    clean_title = re.sub(r'[^a-z0-9\s]', '', title.lower())
    
    # Extract model numbers or key identifiers
    models = re.findall(r'[a-z0-9]+\d+[a-z0-9]*', clean_title)
    if models:
        return '-'.join(models[:3])  # Use up to 3 model identifiers
    else:
        # Fall back to using key words from title
        words = clean_title.split()
        return '-'.join(words[:5])  # Use first 5 words
