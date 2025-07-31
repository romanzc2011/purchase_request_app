#!/usr/bin/env python3
"""
Test script to demonstrate user override functionality
Usage: python test_user_override.py
"""

import requests
import json

# API base URL
BASE_URL = "http://localhost:5004/api"

def test_user_override():
    """Test the user override functionality"""
    
    print("🔧 Testing User Override Functionality")
    print("=" * 50)
    
    # First, let's see what the current user is
    print("1. Checking current user...")
    try:
        response = requests.get(f"{BASE_URL}/getApprovalData")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Current user is authenticated")
        else:
            print("   ❌ Not authenticated")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n2. Setting test user override...")
    try:
        # Override with a test user
        override_data = {
            "username": "test_user",
            "email": "test_user@lawb.uscourts.gov", 
            "groups": "IT,ADMIN,MANAGEMENT"
        }
        
        response = requests.post(f"{BASE_URL}/test-override-user", data=override_data)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Override set successfully")
            print(f"   Test user: {result['test_user']}")
        else:
            print(f"   ❌ Failed to set override: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n3. Testing with overridden user...")
    try:
        # Now test an endpoint that uses current_user
        response = requests.get(f"{BASE_URL}/getApprovalData")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Endpoint works with overridden user")
        else:
            print(f"   ❌ Endpoint failed: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n4. Clearing test override...")
    try:
        response = requests.post(f"{BASE_URL}/clear-test-override")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Override cleared successfully")
        else:
            print(f"   ❌ Failed to clear override: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n5. Testing after clearing override...")
    try:
        response = requests.get(f"{BASE_URL}/getApprovalData")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Endpoint works after clearing override")
        else:
            print(f"   ❌ Endpoint failed: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

def test_specific_users():
    """Test different user types"""
    
    print("\n🔧 Testing Different User Types")
    print("=" * 50)
    
    # Test different user configurations
    test_cases = [
        {
            "name": "IT User",
            "username": "matt_strong",
            "email": "matt_strong@lawb.uscourts.gov",
            "groups": "IT"
        },
        {
            "name": "Management User", 
            "username": "lela_robichaux",
            "email": "lela_robichaux@lawb.uscourts.gov",
            "groups": "MANAGEMENT,FINANCE"
        },
        {
            "name": "Deputy Clerk",
            "username": "edmund_brown", 
            "email": "edmund_brown@lawb.uscourts.gov",
            "groups": "DEPUTY_CLERK,MANAGEMENT"
        },
        {
            "name": "Chief Clerk",
            "username": "edward_takara",
            "email": "edward_takara@lawb.uscourts.gov", 
            "groups": "CHIEF_CLERK"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Testing {test_case['name']}...")
        try:
            override_data = {
                "username": test_case["username"],
                "email": test_case["email"],
                "groups": test_case["groups"]
            }
            
            # Set override
            response = requests.post(f"{BASE_URL}/test-override-user", data=override_data)
            if response.status_code == 200:
                print(f"   ✅ {test_case['name']} override set")
                
                # Test approval endpoint
                approval_response = requests.post(f"{BASE_URL}/approveRequest", 
                    json={
                        "ID": "TEST123",
                        "item_uuids": ["test-uuid"],
                        "item_funds": ["511000"],
                        "totalPrice": 100.00,
                        "target_status": ["PENDING APPROVAL"],
                        "action": "APPROVE"
                    })
                print(f"   Approval endpoint status: {approval_response.status_code}")
                
            else:
                print(f"   ❌ Failed to set {test_case['name']} override")
                
        except Exception as e:
            print(f"   ❌ Error testing {test_case['name']}: {e}")

if __name__ == "__main__":
    test_user_override()
    test_specific_users()
    print("\n�� Test complete!") 