"""
Integration test for the FlipHawk backend and frontend connection.
This script tests the connection between the frontend and backend by simulating requests.
"""

import requests
import json
import time
import sys
import os

# Test configurations
BASE_URL = "http://localhost:8000"  # Adjust if your app runs on a different port
TEST_SUBCATEGORIES = ["Headphones", "Keyboards"]
TEST_CATEGORY = "Tech"
MAX_RESULTS = 5

def test_health_endpoint():
    """Test the health endpoint to make sure the API is up."""
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        if response.status_code == 200:
            print("✅ Health endpoint is working")
            return True
        else:
            print(f"❌ Health endpoint returned status code {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Failed to connect to health endpoint: {str(e)}")
        return False

def test_scan_endpoint():
    """Test the scan endpoint with actual subcategories."""
    try:
        payload = {
            "category": TEST_CATEGORY,
            "subcategories": TEST_SUBCATEGORIES,
            "max_results": MAX_RESULTS
        }
        
        print(f"🔄 Sending request to scan endpoint with subcategories: {TEST_SUBCATEGORIES}")
        
        response = requests.post(
            f"{BASE_URL}/api/v1/scan",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            opps_count = len(result.get("arbitrage_opportunities", []))
            
            print(f"✅ Scan endpoint returned {opps_count} opportunities")
            
            # Check if we have the expected fields in response
            if "meta" in result and "arbitrage_opportunities" in result:
                print("✅ Response has the correct structure")
                
                # Check opportunities format
                if opps_count > 0:
                    opp = result["arbitrage_opportunities"][0]
                    required_fields = ["buyTitle", "buyPrice", "sellTitle", "sellPrice", "profit", "profitPercentage"]
                    
                    missing_fields = [field for field in required_fields if field not in opp]
                    if missing_fields:
                        print(f"❌ Opportunity is missing required fields: {missing_fields}")
                    else:
                        print("✅ Opportunities have the required fields")
                        return True
            else:
                print("❌ Response is missing 'meta' or 'arbitrage_opportunities'")
        else:
            print(f"❌ Scan endpoint returned status code {response.status_code}")
            print(f"Response: {response.text}")
            
        return False
    except Exception as e:
        print(f"❌ Failed to connect to scan endpoint: {str(e)}")
        return False

def test_progress_endpoint():
    """Test the progress endpoint with a simulated scan ID."""
    try:
        # First create a scan
        payload = {
            "category": TEST_CATEGORY,
            "subcategories": TEST_SUBCATEGORIES,
            "max_results": MAX_RESULTS
        }
        
        scan_response = requests.post(
            f"{BASE_URL}/api/v1/scan",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if scan_response.status_code != 200:
            print(f"❌ Could not create scan to test progress endpoint")
            return False
            
        scan_data = scan_response.json()
        scan_id = scan_data.get("meta", {}).get("scan_id")
        
        if not scan_id:
            print("❌ No scan_id found in response")
            return False
            
        print(f"🔄 Checking progress for scan ID: {scan_id}")
        
        progress_response = requests.get(f"{BASE_URL}/api/progress/{scan_id}")
        
        if progress_response.status_code == 200:
            progress_data = progress_response.json()
            print(f"✅ Progress endpoint returned data for scan {scan_id}")
            print(f"   Progress: {progress_data.get('progress')}%, Status: {progress_data.get('status')}")
            return True
        else:
            print(f"❌ Progress endpoint returned status code {progress_response.status_code}")
            print(f"Response: {progress_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Failed to connect to progress endpoint: {str(e)}")
        return False

def run_all_tests():
    """Run all integration tests."""
    print("🔍 Starting FlipHawk Integration Tests")
    print("======================================")
    
    health_ok = test_health_endpoint()
    if not health_ok:
        print("❌ Health check failed, aborting further tests")
        return False
        
    scan_ok = test_scan_endpoint()
    progress_ok = test_progress_endpoint()
    
    all_ok = health_ok and scan_ok and progress_ok
    
    print("\n📋 Test Summary:")
    print(f"Health endpoint: {'✅ PASS' if health_ok else '❌ FAIL'}")
    print(f"Scan endpoint:   {'✅ PASS' if scan_ok else '❌ FAIL'}")
    print(f"Progress endpoint: {'✅ PASS' if progress_ok else '❌ FAIL'}")
    print(f"\nOverall result: {'✅ ALL TESTS PASSED' if all_ok else '❌ SOME TESTS FAILED'}")
    
    return all_ok

if __name__ == "__main__":
    success = run_all_tests()
    if not success:
        sys.exit(1)
