"""
Test Blockchain Integration

Tests:
- Network connectivity
- Transaction lookup
- Verdict verification
- Case blockchain info
"""
import requests
import json
from typing import Dict, Optional

# Configuration
BASE_URL = "http://localhost:8000"

# ANSI color codes
GREEN = "\033[92m"
RED = "\033[91m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
RESET = "\033[0m"
BOLD = "\033[1m"


def print_section(text: str):
    """Print a section header"""
    print(f"\n{BOLD}{'=' * 60}")
    print(f"{text}")
    print(f"{'=' * 60}{RESET}\n")


def print_success(text: str):
    """Print success message"""
    print(f"{GREEN}✓ {text}{RESET}")


def print_error(text: str):
    """Print error message"""
    print(f"{RED}✗ {text}{RESET}")


def print_info(text: str):
    """Print info message"""
    print(f"{BLUE}ℹ {text}{RESET}")


def print_warning(text: str):
    """Print warning message"""
    print(f"{YELLOW}⚠ {text}{RESET}")


def print_response(response: requests.Response):
    """Print formatted response"""
    print(f"\nStatus Code: {response.status_code}")
    print("Response:")
    try:
        data = response.json()
        print(json.dumps(data, indent=2))
    except:
        print(response.text)


def make_request(method: str, url: str, **kwargs) -> requests.Response:
    """Make HTTP request with error handling"""
    try:
        return requests.request(method, url, **kwargs)
    except requests.exceptions.RequestException as e:
        print_error(f"Request failed: {str(e)}")
        raise


def test_network_info():
    """Test GET /blockchain/network-info"""
    print_section("TEST: Blockchain Network Info")
    
    url = f"{BASE_URL}/blockchain/network-info"
    print_info(f"GET {url}")
    
    response = make_request("GET", url)
    print_response(response)
    
    if response.status_code == 200:
        data = response.json()
        if data.get("enabled"):
            print_success(f"Blockchain connected: {data.get('network', 'Unknown')}")
            print_info(f"Block Height: {data.get('block_height', 'N/A')}")
            print_info(f"RPC URL: {data.get('rpc_url', 'N/A')}")
        else:
            print_warning("Blockchain service not configured")
            print_info(data.get("message", "No details available"))
        return True
    else:
        print_error(f"Failed to get network info: {response.status_code}")
        return False


def test_get_transaction(tx_hash: Optional[str] = None):
    """Test GET /blockchain/transaction/{tx_hash}"""
    print_section("TEST: Get Transaction Details")
    
    # Use a sample transaction hash if none provided
    if not tx_hash:
        tx_hash = "a" * 64  # Mock transaction hash
        print_warning("Using mock transaction hash for testing")
    
    url = f"{BASE_URL}/blockchain/transaction/{tx_hash}"
    print_info(f"GET {url}")
    
    response = make_request("GET", url)
    print_response(response)
    
    if response.status_code == 200:
        data = response.json()
        print_success(f"Transaction lookup: {data.get('status', 'unknown')}")
        if data.get("status") == "confirmed":
            print_info(f"Block Height: {data.get('block_height')}")
            print_info(f"Confirmations: {data.get('confirmations')}")
        return True
    elif response.status_code == 404:
        print_info("Transaction not found (expected for mock hash)")
        return True
    else:
        print_error(f"Failed to get transaction: {response.status_code}")
        return False


def test_verify_verdict():
    """Test POST /blockchain/verify-verdict"""
    print_section("TEST: Verify Verdict Hash")
    
    url = f"{BASE_URL}/blockchain/verify-verdict"
    print_info(f"POST {url}")
    
    # Sample data (this would need a real case in production)
    data = {
        "case_id": 1,
        "verdict_hash": "a" * 64,
        "blockchain_tx_hash": "b" * 64
    }
    print_info(f"Data: {json.dumps(data, indent=2)}")
    
    response = make_request("POST", url, json=data)
    print_response(response)
    
    if response.status_code == 200:
        result = response.json()
        print_success("Verdict verification completed")
        print_info(f"Verified: {result.get('verification', {}).get('verified', False)}")
        return True
    elif response.status_code == 404:
        print_warning("Case not found (expected if database is empty)")
        return True
    else:
        print_error(f"Verification failed: {response.status_code}")
        return False


def test_case_blockchain_info(case_id: int = 1):
    """Test GET /blockchain/case/{case_id}/blockchain"""
    print_section("TEST: Get Case Blockchain Info")
    
    url = f"{BASE_URL}/blockchain/case/{case_id}/blockchain"
    print_info(f"GET {url}")
    
    response = make_request("GET", url)
    print_response(response)
    
    if response.status_code == 200:
        data = response.json()
        print_success(f"Case blockchain info retrieved")
        print_info(f"Case: {data.get('case_title', 'Unknown')}")
        print_info(f"Status: {data.get('case_status', 'Unknown')}")
        print_info(f"Has Blockchain: {data.get('has_blockchain_commitment', False)}")
        if data.get('blockchain_tx_hash'):
            print_info(f"TX Hash: {data['blockchain_tx_hash'][:16]}...")
        return True
    elif response.status_code == 404:
        print_warning(f"Case {case_id} not found")
        return True
    else:
        print_error(f"Failed to get case blockchain info: {response.status_code}")
        return False


def run_all_tests():
    """Run all blockchain tests"""
    print_section("BLOCKCHAIN INTEGRATION TESTS")
    
    results = []
    
    # Test network info
    results.append(("Network Info", test_network_info()))
    
    # Test transaction lookup
    results.append(("Transaction Lookup", test_get_transaction()))
    
    # Test verdict verification
    results.append(("Verdict Verification", test_verify_verdict()))
    
    # Test case blockchain info
    results.append(("Case Blockchain Info", test_case_blockchain_info()))
    
    # Print summary
    print_section("SUMMARY")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        if result:
            print_success(f"{name}: PASSED")
        else:
            print_error(f"{name}: FAILED")
    
    print(f"\n{BOLD}Total: {passed}/{total} tests passed{RESET}\n")
    
    if passed == total:
        print_success("✓ All blockchain tests completed!")
    else:
        print_error(f"✗ {total - passed} test(s) failed")


if __name__ == "__main__":
    try:
        run_all_tests()
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
    except Exception as e:
        print_error(f"Test suite failed: {str(e)}")
        import traceback
        traceback.print_exc()
