"""
Test Profile and Leaderboard Endpoints

Tests:
- GET /profile (get user profile)
- GET /profile/stats (get user statistics)
- GET /leaderboard (get top users)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.testing.config import BASE_URL
from app.testing.utils import (
    print_section, print_success, print_error, print_info,
    print_response, make_request, get_auth_headers
)
from app.testing.test_auth import run_all_tests as auth_tests


def test_get_profile(token: str):
    """Test getting user profile"""
    print_section("TEST: Get User Profile")
    
    url = f"{BASE_URL}/profile"
    print_info(f"GET {url}")
    
    headers = get_auth_headers(token)
    response = make_request("GET", url, headers=headers)
    print_response(response)
    
    if response.status_code == 200:
        data = response.json()
        print_success(f"Profile retrieved: {data['user']['name']}")
        print_info(f"Total Points: {data['user']['total_points']}")
        print_info(f"Voting Accuracy: {data['statistics']['voting_accuracy']}%")
        print_info(f"Total Votes: {data['statistics']['total_votes']}")
        print_info(f"Total Arguments: {data['statistics']['total_arguments']}")
        return True
    else:
        print_error(f"Failed to get profile: {response.status_code}")
        return False


def test_get_profile_stats(token: str):
    """Test getting user statistics"""
    print_section("TEST: Get User Statistics")
    
    url = f"{BASE_URL}/profile/stats"
    print_info(f"GET {url}")
    
    headers = get_auth_headers(token)
    response = make_request("GET", url, headers=headers)
    print_response(response)
    
    if response.status_code == 200:
        data = response.json()
        print_success("Statistics retrieved")
        print_info(f"Voting Stats: {data['voting']}")
        print_info(f"Arguments Stats: {data['arguments']}")
        print_info(f"Cases Stats: {data['cases']}")
        return True
    else:
        print_error(f"Failed to get stats: {response.status_code}")
        return False


def test_get_leaderboard(timeframe: str = "all_time"):
    """Test getting leaderboard"""
    print_section(f"TEST: Get Leaderboard ({timeframe})")
    
    url = f"{BASE_URL}/leaderboard"
    params = {"timeframe": timeframe, "limit": 10}
    print_info(f"GET {url}")
    print_info(f"Params: {params}")
    
    response = make_request("GET", url, params=params)
    print_response(response)
    
    if response.status_code == 200:
        data = response.json()
        print_success(f"Leaderboard retrieved: {data['total_users']} users")
        
        if data['leaderboard']:
            print_info("Top 3 users:")
            for user in data['leaderboard'][:3]:
                print_info(f"  {user['rank']}. {user['name']} - {user['points']} points")
        
        return True
    else:
        print_error(f"Failed to get leaderboard: {response.status_code}")
        return False


def run_all_tests():
    """Run all profile and leaderboard tests"""
    print("\n" + "=" * 60)
    print("PROFILE & LEADERBOARD TESTS")
    print("=" * 60)
    
    try:
        # Get authentication tokens
        print_info("Getting authentication tokens...")
        token1, token2 = auth_tests()
        
        if not token1:
            print_error("Authentication failed. Cannot continue.")
            return
        
        # Test profile endpoints
        test_get_profile(token1)
        test_get_profile_stats(token1)
        
        # Test leaderboard
        test_get_leaderboard("all_time")
        test_get_leaderboard("monthly")
        test_get_leaderboard("weekly")
        
        print_section("SUMMARY")
        print_success("All profile & leaderboard tests completed!")
        
    except Exception as e:
        print_error(f"Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
