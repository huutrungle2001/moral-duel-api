"""
Test Authentication Endpoints

Tests:
- POST /auth/register
- POST /auth/login
- POST /auth/wallet/connect (placeholder)
- GET /auth/wallet/verify (placeholder)
"""
import sys
from .config import BASE_URL, TEST_USER_1, TEST_USER_2
from .utils import (
    print_section, print_success, print_error, print_info,
    print_response, make_request
)


def test_register():
    """Test user registration"""
    print_section("TEST: Register User")
    
    url = f"{BASE_URL}/auth/register"
    print_info(f"POST {url}")
    print_info(f"Data: {TEST_USER_1}")
    
    response = make_request("POST", url, json_data=TEST_USER_1)
    print_response(response)
    
    if response.status_code == 201:
        data = response.json()
        if "access_token" in data and "user" in data:
            print_success("Registration successful!")
            return data["access_token"], data["user"]
        else:
            print_error("Registration response missing required fields")
            return None, None
    elif response.status_code == 400:
        print_info("User might already exist (this is expected if running tests multiple times)")
        # Try to login instead
        return test_login()
    else:
        print_error(f"Registration failed with status {response.status_code}")
        return None, None


def test_login():
    """Test user login"""
    print_section("TEST: Login User")
    
    url = f"{BASE_URL}/auth/login"
    login_data = {
        "email": TEST_USER_1["email"],
        "password": TEST_USER_1["password"]
    }
    
    print_info(f"POST {url}")
    print_info(f"Data: {login_data}")
    
    response = make_request("POST", url, json_data=login_data)
    print_response(response)
    
    if response.status_code == 200:
        data = response.json()
        if "access_token" in data and "user" in data:
            print_success("Login successful!")
            return data["access_token"], data["user"]
        else:
            print_error("Login response missing required fields")
            return None, None
    else:
        print_error(f"Login failed with status {response.status_code}")
        return None, None


def test_register_second_user():
    """Test registering a second user for voting tests"""
    print_section("TEST: Register Second User")
    
    url = f"{BASE_URL}/auth/register"
    print_info(f"POST {url}")
    print_info(f"Data: {TEST_USER_2}")
    
    response = make_request("POST", url, json_data=TEST_USER_2)
    print_response(response)
    
    if response.status_code == 201:
        data = response.json()
        print_success("Second user registration successful!")
        return data["access_token"], data["user"]
    elif response.status_code == 400:
        print_info("Second user already exists, logging in...")
        url = f"{BASE_URL}/auth/login"
        login_data = {
            "email": TEST_USER_2["email"],
            "password": TEST_USER_2["password"]
        }
        response = make_request("POST", url, json_data=login_data)
        if response.status_code == 200:
            data = response.json()
            return data["access_token"], data["user"]
    
    return None, None


def test_invalid_login():
    """Test login with invalid credentials"""
    print_section("TEST: Invalid Login")
    
    url = f"{BASE_URL}/auth/login"
    invalid_data = {
        "email": "nonexistent@example.com",
        "password": "wrongpassword"
    }
    
    print_info(f"POST {url}")
    print_info(f"Data: {invalid_data}")
    
    response = make_request("POST", url, json_data=invalid_data)
    print_response(response)
    
    if response.status_code == 401:
        print_success("Invalid login correctly rejected!")
    else:
        print_error(f"Expected 401, got {response.status_code}")


def test_wallet_connect():
    """Test wallet connect endpoint (placeholder)"""
    print_section("TEST: Wallet Connect (Placeholder)")
    
    url = f"{BASE_URL}/auth/wallet/connect"
    wallet_data = {
        "neo_address": "NX8GreRFGFK5wpGMWetpX93HmtrezGogzk",
        "signature": "mock_signature",
        "message": "mock_message"
    }
    
    print_info(f"POST {url}")
    print_info(f"Data: {wallet_data}")
    
    response = make_request("POST", url, json_data=wallet_data)
    print_response(response)
    
    if response.status_code == 200:
        print_info("Wallet connect endpoint is ready (implementation pending)")
    else:
        print_error(f"Unexpected status code: {response.status_code}")


def run_all_tests():
    """Run all authentication tests"""
    print("\n" + "=" * 60)
    print("AUTHENTICATION ENDPOINT TESTS")
    print("=" * 60)
    
    try:
        # Test registration and login
        token1, user1 = test_register()
        if not token1:
            print_error("Registration/login failed. Cannot continue tests.")
            return None, None
        
        # Test second user
        token2, user2 = test_register_second_user()
        
        # Test invalid login
        test_invalid_login()
        
        # Test wallet endpoints (placeholders)
        test_wallet_connect()
        
        print_section("SUMMARY")
        print_success("All authentication tests completed!")
        print_info(f"User 1 Token: {token1[:20]}...")
        print_info(f"User 1 ID: {user1['id']}")
        if token2:
            print_info(f"User 2 Token: {token2[:20]}...")
            print_info(f"User 2 ID: {user2['id']}")
        
        return token1, token2
        
    except Exception as e:
        print_error(f"Test failed with error: {str(e)}")
        return None, None


if __name__ == "__main__":
    run_all_tests()
