#!/usr/bin/env python3
"""
VyapaarSetu AI - Extended System Test
Test the new database models, API routes, and order flow
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:5000"
API_KEY = "vyapaarsetu_api_key_2024"

headers = {
    "Content-Type": "application/json",
    "X-API-Key": API_KEY
}

def test_api_endpoint(method, endpoint, data=None, expected_status=200):
    """Test an API endpoint"""
    url = f"{BASE_URL}{endpoint}"
    print(f"\n🧪 Testing {method} {endpoint}")
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data)
        elif method == "PUT":
            response = requests.put(url, headers=headers, json=data)
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == expected_status:
            print(f"   ✅ SUCCESS")
            if response.content:
                try:
                    result = response.json()
                    print(f"   Response: {json.dumps(result, indent=2)[:200]}...")
                    return result
                except:
                    print(f"   Response: {response.text[:200]}...")
                    return response.text
        else:
            print(f"   ❌ FAILED - Expected {expected_status}, got {response.status_code}")
            print(f"   Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return None

def main():
    print("🚀 VyapaarSetu AI Extended System Test")
    print("=" * 50)
    
    # Test 1: Health check
    test_api_endpoint("GET", "/health")
    
    # Test 2: Dashboard stats (should work even with empty DB)
    stats = test_api_endpoint("GET", "/api/v1/dashboard/stats")
    
    # Test 3: Create a test customer and order
    print("\n📦 Creating test order...")
    order_data = {
        "phone_number": "+919876543210",
        "customer_name": "Test Customer",
        "amount": 1500.0,
        "items": ["Samosa", "Chai", "Pakora"],
        "delivery_address": "123 Test Street, Mumbai",
        "language": "hi"
    }
    
    order_result = test_api_endpoint("POST", "/api/v1/orders", order_data, 201)
    
    if order_result and order_result.get('order_id'):
        order_id = order_result['order_id']
        print(f"   Created order: {order_id}")
        
        # Test 4: Get order details
        test_api_endpoint("GET", f"/api/v1/orders/{order_id}")
        
        # Test 5: Get orders list
        test_api_endpoint("GET", "/api/v1/orders")
        
        # Test 6: Initiate call (will fail without valid phone, but tests the endpoint)
        call_data = {
            "order_id": order_id,
            "phone_number": "+919876543210"
        }
        print("\n📞 Testing call initiation (expected to fail with trial Twilio)...")
        test_api_endpoint("POST", "/api/v1/call/initiate", call_data, 500)  # Expect failure
        
        # Test 7: Test approval workflow
        print("\n✅ Testing approval workflow...")
        approval_data = {
            "action": "APPROVE",
            "agent_name": "Test Agent"
        }
        test_api_endpoint("POST", f"/api/v1/orders/{order_id}/approve", approval_data)
        
        # Test 8: Check updated stats
        print("\n📊 Checking updated stats...")
        test_api_endpoint("GET", "/api/v1/dashboard/stats")
        
        # Test 9: Get audit log
        test_api_endpoint("GET", f"/api/v1/audit/{order_id}")
    
    # Test 10: Android login
    print("\n📱 Testing Android login...")
    login_data = {
        "username": "agent",
        "password": "agent123"
    }
    login_result = test_api_endpoint("POST", "/api/v1/auth/login", login_data)
    
    if login_result and login_result.get('token'):
        token = login_result['token']
        print(f"   Got JWT token: {token[:20]}...")
        
        # Test mobile endpoints with JWT
        mobile_headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
        
        print("\n📱 Testing mobile endpoints...")
        mobile_url = f"{BASE_URL}/api/v1/mobile/orders"
        response = requests.get(mobile_url, headers=mobile_headers)
        print(f"   Mobile orders: {response.status_code}")
        
        mobile_stats_url = f"{BASE_URL}/api/v1/mobile/stats"
        response = requests.get(mobile_stats_url, headers=mobile_headers)
        print(f"   Mobile stats: {response.status_code}")
    
    print("\n" + "=" * 50)
    print("🎉 Extended system test completed!")
    print("\nNext steps:")
    print("1. Install dashboard dependencies: cd vyapaarsetu-dashboard && npm install")
    print("2. Start dashboard: npm run dev")
    print("3. Open http://localhost:3000")
    print("4. Test the Android app with the JWT token")

if __name__ == "__main__":
    main()