# tests/test_app.py

import pytest
from flask import url_for
from app import app, db
from arbitrage_bot import run_arbitrage_scan
import json
import time

@pytest.fixture
def client():
    """Test client fixture."""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()

@pytest.fixture
def mock_scan_results():
    """Mock scan results fixture."""
    return [
        {
            "title": "Test Product 1",
            "buyPrice": 50.00,
            "sellPrice": 100.00,
            "buyLink": "https://example.com/buy1",
            "sellLink": "https://example.com/sell1",
            "profit": 50.00,
            "profitPercentage": 100.0,
            "confidence": 90,
            "subcategory": "Test Subcategory"
        },
        {
            "title": "Test Product 2",
            "buyPrice": 75.00,
            "sellPrice": 150.00,
            "buyLink": "https://example.com/buy2",
            "sellLink": "https://example.com/sell2",
            "profit": 75.00,
            "profitPercentage": 100.0,
            "confidence": 85,
            "subcategory": "Test Subcategory"
        }
    ]

class TestAppRoutes:
    """Test application routes."""
    
    def test_index_route(self, client):
        """Test the index route."""
        response = client.get('/')
        assert response.status_code == 200
        assert b'<!DOCTYPE html>' in response.data
    
    def test_static_files(self, client):
        """Test static file serving."""
        # Test CSS
        response = client.get('/styles.css')
        assert response.status_code == 200
        assert response.headers['Content-Type'].startswith('text/css')
        
        # Test JavaScript
        response = client.get('/script.js')
        assert response.status_code == 200
        assert response.headers['Content-Type'].startswith('application/javascript')
    
    def test_scan_endpoint_without_data(self, client):
        """Test scan endpoint without data."""
        response = client.post('/api/v1/scan', json={})
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_scan_endpoint_with_valid_data(self, client, mocker, mock_scan_results):
        """Test scan endpoint with valid data."""
        # Mock the arbitrage scan function
        mocker.patch('app.run_arbitrage_scan', return_value=mock_scan_results)
        
        response = client.post('/api/v1/scan', json={
            'category': 'Test Category',
            'subcategories': ['Test Subcategory']
        })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) == 2
        assert data[0]['title'] == 'Test Product 1'
    
    def test_save_opportunity(self, client, mock_scan_results):
        """Test saving an opportunity."""
        response = client.post('/api/v1/save_opportunity', json={
            'opportunity': mock_scan_results[0],
            'notes': 'Test note'
        })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'id' in data
    
    def test_get_opportunities(self, client, mock_scan_results):
        """Test retrieving saved opportunities."""
        # Save an opportunity first
        client.post('/api/v1/save_opportunity', json={
            'opportunity': mock_scan_results[0]
        })
        
        # Retrieve opportunities
        response = client.get('/api/v1/my_opportunities')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) == 1
        assert data[0]['opportunity']['title'] == 'Test Product 1'
    
    def test_stats_endpoint(self, client):
        """Test stats endpoint."""
        response = client.get('/api/v1/stats')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'total_scans' in data
        assert 'success_rate' in data
        assert 'avg_scan_duration' in data
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get('/api/v1/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert 'timestamp' in data
        assert 'database' in data

class TestArbitrageBot:
    """Test arbitrage bot functionality."""
    
    def test_normalize_title(self):
        """Test title normalization."""
        from arbitrage_bot import Scraper
        scraper = Scraper()
        
        title = "BRAND NEW Apple iPhone 13 Pro 128GB Factory Sealed!!!"
        normalized = scraper.normalize_title(title)
        assert "brand new" not in normalized
        assert "factory sealed" not in normalized
        assert "apple iphone 13 pro 128gb" in normalized
    
    @pytest.mark.asyncio
    async def test_search_ebay_listings(self, mocker):
        """Test eBay search functionality."""
        from arbitrage_bot import Scraper
        scraper = Scraper()
        
        # Mock the fetch_page function
        mock_html = """
        <html>
            <li class="s-item">
                <h3 class="s-item__title">Test Product</h3>
                <span class="s-item__price">$50.00</span>
                <a class="s-item__link" href="https://example.com/item"></a>
            </li>
        </html>
        """
        mocker.patch.object(scraper, 'fetch_page', return_value=mock_html)
        
        listings = await scraper.search_ebay("test keyword")
        assert len(listings) > 0
        assert listings[0].title == "Test Product"
        assert listings[0].price == 50.00
    
    def test_similarity_calculation(self):
        """Test similarity calculation."""
        from arbitrage_bot import ArbitrageAnalyzer
        analyzer = ArbitrageAnalyzer()
        
        title1 = "apple iphone 13 pro 128gb"
        title2 = "iphone 13 pro 128gb apple"
        similarity = analyzer.calculate_similarity(title1, title2)
        assert similarity > 0.8
        
        title3 = "samsung galaxy s21"
        similarity2 = analyzer.calculate_similarity(title1, title3)
        assert similarity2 < 0.5
    
    def test_find_opportunities(self):
        """Test finding arbitrage opportunities."""
        from arbitrage_bot import ArbitrageAnalyzer, Listing
        analyzer = ArbitrageAnalyzer()
        
        low_priced = [
            Listing(
                title="Test Product",
                price=50.00,
                link="https://example.com/low",
                image_url="",
                free_shipping=True,
                normalized_title="test product",
                source="eBay"
            )
        ]
        
        high_priced = [
            Listing(
                title="Test Product Same",
                price=100.00,
                link="https://example.com/high",
                image_url="",
                free_shipping=True,
                normalized_title="test product same",
                source="eBay"
            )
        ]
        
        opportunities = analyzer.find_opportunities(low_priced, high_priced)
        assert len(opportunities) > 0
        assert opportunities[0]['profit'] == 50.00
        assert opportunities[0]['profitPercentage'] == 100.0

class TestUtilities:
    """Test utility functions."""
    
    def test_determine_shipping_cost(self):
        """Test shipping cost calculation."""
        from app import determine_shipping_cost
        
        item = {'subcategory': 'Laptops', 'buyPrice': 500}
        cost = determine_shipping_cost(item)
        assert cost == 15.99
        
        item = {'subcategory': 'Trading Cards', 'buyPrice': 50}
        cost = determine_shipping_cost(item)
        assert cost == 3.99
    
    def test_calculate_ebay_fee(self):
        """Test eBay fee calculation."""
        from app import calculate_ebay_fee
        
        fee = calculate_ebay_fee(100)
        assert fee == 10.5  # 10.5% of 100
        
        fee = calculate_ebay_fee(500)
        assert fee > 10.5  # Should be more than 10.5%
        
        fee = calculate_ebay_fee(2000)
        assert fee < 200  # Should be less than 10%

class TestPerformance:
    """Test performance metrics."""
    
    def test_response_time(self, client):
        """Test response time for main routes."""
        start_time = time.time()
        response = client.get('/')
        end_time = time.time()
        
        assert response.status_code == 200
        assert (end_time - start_time) < 1.0  # Should respond in less than 1 second
    
    def test_concurrent_requests(self, client):
        """Test handling of concurrent requests."""
        import threading
        
        def make_request():
            response = client.get('/api/v1/health')
            assert response.status_code == 200
        
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
    
    def test_memory_usage(self):
        """Test memory usage during operations."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Perform some operations
        from arbitrage_bot import run_arbitrage_scan
        results = run_arbitrage_scan(['Test'])
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 50MB)
        assert memory_increase < 50 * 1024 * 1024
