#!/usr/bin/env python3
"""
Calendarium API Test Script
Test all major API endpoints for the Calendarium Flask application
"""

import requests
import json
import sys

BASE_URL = "http://localhost:5001/api/v1"

def test_endpoint(method, endpoint, data=None, description=""):
    """Test a single API endpoint"""
    url = BASE_URL + endpoint
    print(f"\n{'='*60}")
    print(f"Testing: {method} {endpoint}")
    print(f"Description: {description}")
    print(f"URL: {url}")
    
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data, headers={'Content-Type': 'application/json'})
        elif method == "PUT":
            response = requests.put(url, json=data, headers={'Content-Type': 'application/json'})
        elif method == "DELETE":
            response = requests.delete(url)
        
        print(f"Status Code: {response.status_code}")
        
        if response.headers.get('content-type', '').startswith('application/json'):
            result = response.json()
            print("Response:")
            print(json.dumps(result, indent=2))
        else:
            print(f"Response Content Type: {response.headers.get('content-type', 'Unknown')}")
            if len(response.content) < 200:
                print(f"Response: {response.text}")
            else:
                print(f"Response Length: {len(response.content)} bytes")
        
        return response.status_code < 400
        
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    print("🗓️  Calendarium API Test Suite")
    print("="*60)
    
    tests = [
        ("GET", "/maintenance/health", None, "Check application health"),
        ("GET", "/maintenance/stats", None, "Get application statistics"),
        ("GET", "/categories/", None, "List all categories"),
        ("GET", "/entries/", None, "List all entries"),
        ("GET", "/quotes/", None, "List all quotes"),
        ("POST", "/maintenance/import", {
            "categories": [{
                "name": "API Test Category",
                "symbol": "🧪",
                "color_hex": "#FF9800",
                "repeat_annually": False,
                "display_celebration": False,
                "is_protected": False
            }]
        }, "Test batch import with new category"),
    ]
    
    passed = 0
    total = len(tests)
    
    for method, endpoint, data, description in tests:
        if test_endpoint(method, endpoint, data, description):
            passed += 1
    
    print(f"\n{'='*60}")
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
