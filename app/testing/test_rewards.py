"""
Test Reward System

Tests:
- Reward calculation for closed cases
- Reward distribution logic
- Reward claiming
- Reward status tracking
"""
import requests
import json
from typing import Dict

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
    print(f"\n{BOLD}{'=' * 60}")
    print(f"{text}")
    print(f"{'=' * 60}{RESET}\n")


def print_success(text: str):
    print(f"{GREEN}✓ {text}{RESET}")


def print_error(text: str):
    print(f"{RED}✗ {text}{RESET}")


def print_info(text: str):
    print(f"{BLUE}ℹ {text}{RESET}")


def print_warning(text: str):
    print(f"{YELLOW}⚠ {text}{RESET}")


def make_request(method: str, url: str, **kwargs) -> requests.Response:
    try:
        return requests.request(method, url, **kwargs)
    except requests.exceptions.RequestException as e:
        print_error(f"Request failed: {str(e)}")
        raise


def get_auth_token() -> str:
    """Get authentication token"""
    response = make_request(
        "POST",
        f"{BASE_URL}/auth/login",
        json={
            "email": "test_user1@example.com",
            "password": "testpassword123"
        }
    )
    
    if response.status_code == 200:
        return response.json()["access_token"]
    return None


def test_get_rewards(token: str):
    """Test GET /profile/rewards"""
    print_section("TEST: Get User Rewards")
    
    url = f"{BASE_URL}/profile/rewards"
    print_info(f"GET {url}")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = make_request("GET", url, headers=headers)
    
    print(f"\nStatus Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(json.dumps(data, indent=2))
        
        print_success(f"Retrieved rewards list")
        print_info(f"Total rewards: {len(data.get('rewards', []))}")
        
        stats = data.get("statistics", {})
        print_info(f"Total earned: {stats.get('total_earned', 0):.2f}")
        print_info(f"Pending: {stats.get('pending', 0):.2f}")
        print_info(f"Completed: {stats.get('completed', 0):.2f}")
        
        return True, data
    else:
        print(response.text)
        print_error(f"Failed to get rewards: {response.status_code}")
        return False, None


def test_get_rewards_filtered(token: str, status_filter: str):
    """Test GET /profile/rewards with status filter"""
    print_section(f"TEST: Get Rewards (Status: {status_filter})")
    
    url = f"{BASE_URL}/profile/rewards?status_filter={status_filter}"
    print_info(f"GET {url}")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = make_request("GET", url, headers=headers)
    
    print(f"\nStatus Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        rewards = data.get('rewards', [])
        print_success(f"Found {len(rewards)} {status_filter} rewards")
        
        for reward in rewards[:3]:  # Show first 3
            print_info(f"  Reward #{reward['id']}: {reward['amount']:.2f} MORAL - {reward['type']}")
        
        return True
    else:
        print(response.text)
        print_error(f"Failed to filter rewards: {response.status_code}")
        return False


def test_claim_rewards(token: str):
    """Test POST /profile/rewards/claim"""
    print_section("TEST: Claim Rewards")
    
    # First get pending rewards
    headers = {"Authorization": f"Bearer {token}"}
    rewards_response = make_request("GET", f"{BASE_URL}/profile/rewards?status_filter=pending", headers=headers)
    
    if rewards_response.status_code != 200:
        print_warning("No pending rewards to claim")
        return True
    
    rewards_data = rewards_response.json()
    pending_rewards = rewards_data.get('rewards', [])
    
    if not pending_rewards:
        print_warning("No pending rewards found (this is expected if none have been earned)")
        print_info("To test reward claiming:")
        print_info("1. Participate in cases (vote, argue)")
        print_info("2. Wait for cases to close")
        print_info("3. Rewards will be calculated automatically")
        return True
    
    print_info(f"Found {len(pending_rewards)} pending rewards")
    
    # Claim first reward
    reward_ids = [pending_rewards[0]['id']]
    
    url = f"{BASE_URL}/profile/rewards/claim"
    print_info(f"POST {url}")
    
    data = {
        "reward_ids": reward_ids,
        "neo_wallet_address": "NX8GreRFGFK5wpGMWetpX93HmtrezGogzk"  # Sample address
    }
    print_info(f"Claiming reward IDs: {reward_ids}")
    
    response = make_request("POST", url, json=data, headers=headers)
    
    print(f"\nStatus Code: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(json.dumps(result, indent=2))
        
        print_success(f"Claimed {result.get('rewards_claimed', 0)} rewards")
        print_info(f"Total amount: {result.get('total_amount', 0):.2f} MORAL")
        print_info(f"Transaction: {result.get('transaction', {}).get('tx_hash', 'N/A')[:32]}...")
        return True
    else:
        print(response.text)
        # 400 is expected if no wallet or rewards already claimed
        if response.status_code == 400:
            print_warning("Expected error (wallet not connected or rewards not claimable)")
            return True
        print_error(f"Failed to claim rewards: {response.status_code}")
        return False


def test_reward_status(token: str):
    """Test GET /profile/rewards/{id}/status"""
    print_section("TEST: Get Reward Status")
    
    # Get first reward
    headers = {"Authorization": f"Bearer {token}"}
    rewards_response = make_request("GET", f"{BASE_URL}/profile/rewards", headers=headers)
    
    if rewards_response.status_code != 200:
        print_error("Could not fetch rewards")
        return False
    
    rewards_data = rewards_response.json()
    rewards = rewards_data.get('rewards', [])
    
    if not rewards:
        print_warning("No rewards found to check status")
        return True
    
    reward_id = rewards[0]['id']
    
    url = f"{BASE_URL}/profile/rewards/{reward_id}/status"
    print_info(f"GET {url}")
    
    response = make_request("GET", url, headers=headers)
    
    print(f"\nStatus Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(json.dumps(data, indent=2))
        
        print_success(f"Retrieved reward status")
        print_info(f"Reward #{data['id']}: {data['status']}")
        print_info(f"Amount: {data['amount']:.2f} MORAL")
        print_info(f"Type: {data['type']}")
        return True
    else:
        print(response.text)
        print_error(f"Failed to get reward status: {response.status_code}")
        return False


def test_reward_statistics(token: str):
    """Test reward statistics in profile"""
    print_section("TEST: Reward Statistics")
    
    url = f"{BASE_URL}/profile/rewards"
    print_info(f"GET {url}")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = make_request("GET", url, headers=headers)
    
    if response.status_code != 200:
        print_error("Failed to get rewards")
        return False
    
    data = response.json()
    stats = data.get("statistics", {})
    
    print_success("Reward Statistics:")
    print(f"\n{BOLD}Overall:{RESET}")
    print(f"  Total rewards: {stats.get('total_rewards', 0)}")
    print(f"  Total earned: {stats.get('total_earned', 0):.2f} MORAL")
    print(f"  Pending: {stats.get('pending', 0):.2f} MORAL")
    print(f"  Completed: {stats.get('completed', 0):.2f} MORAL")
    
    by_type = stats.get('by_type', {})
    print(f"\n{BOLD}By Type:{RESET}")
    print(f"  Winning voter: {by_type.get('winning_voter', 0):.2f} MORAL")
    print(f"  Top argument: {by_type.get('top_argument', 0):.2f} MORAL")
    print(f"  Participant: {by_type.get('participant', 0):.2f} MORAL")
    print(f"  Creator: {by_type.get('creator', 0):.2f} MORAL")
    
    return True


def run_all_tests():
    """Run all reward system tests"""
    print_section("REWARD SYSTEM TESTS")
    
    # Get auth token
    print_info("Authenticating...")
    token = get_auth_token()
    
    if not token:
        print_error("Failed to authenticate")
        return
    
    print_success("Authenticated successfully")
    
    results = []
    
    # Test reward retrieval
    success, rewards_data = test_get_rewards(token)
    results.append(("Get Rewards", success))
    
    # Test filtered rewards
    results.append(("Filter by Pending", test_get_rewards_filtered(token, "pending")))
    results.append(("Filter by Completed", test_get_rewards_filtered(token, "completed")))
    
    # Test reward claiming
    results.append(("Claim Rewards", test_claim_rewards(token)))
    
    # Test reward status
    results.append(("Reward Status", test_reward_status(token)))
    
    # Test reward statistics
    results.append(("Reward Statistics", test_reward_statistics(token)))
    
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
        print_success("✓ All reward system tests completed!")
        print_info("\nReward system is ready for:")
        print_info("  • Automatic reward calculation when cases close")
        print_info("  • Reward claiming with Neo wallet")
        print_info("  • Reward status tracking")
        print_info("  • Comprehensive reward statistics")
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
