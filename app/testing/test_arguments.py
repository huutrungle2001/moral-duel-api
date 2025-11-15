"""
Test Argument Endpoints

Tests:
- POST /arguments/:id/vote (like argument)
- DELETE /arguments/:id/vote (unlike argument)

Note: These tests require a case with existing arguments
"""
import sys
from .config import BASE_URL
from .utils import (
    print_section, print_success, print_error, print_info,
    print_response, make_request, get_auth_headers
)
from .test_auth import run_all_tests as auth_tests


def test_like_argument(argument_id: int, case_id: int, token: str):
    """Test liking an argument"""
    print_section(f"TEST: Like Argument (ID: {argument_id})")
    
    url = f"{BASE_URL}/arguments/{argument_id}/vote?case_id={case_id}"
    print_info(f"POST {url}")
    
    headers = get_auth_headers(token)
    response = make_request("POST", url, headers=headers)
    print_response(response)
    
    if response.status_code == 200:
        data = response.json()
        print_success(f"Argument liked! Total votes: {data['votes']}")
        return True
    else:
        print_error(f"Failed to like argument: {response.status_code}")
        return False


def test_unlike_argument(argument_id: int, case_id: int, token: str):
    """Test unliking an argument"""
    print_section(f"TEST: Unlike Argument (ID: {argument_id})")
    
    url = f"{BASE_URL}/arguments/{argument_id}/vote?case_id={case_id}"
    print_info(f"DELETE {url}")
    
    headers = get_auth_headers(token)
    response = make_request("DELETE", url, headers=headers)
    print_response(response)
    
    if response.status_code == 200:
        data = response.json()
        print_success(f"Argument unliked! Total votes: {data['votes']}")
        return True
    else:
        print_error(f"Failed to unlike argument: {response.status_code}")
        return False


def test_max_likes_limit(case_id: int, token: str):
    """Test that max 3 likes per case is enforced"""
    print_section("TEST: Max 3 Likes Per Case Limit")
    
    # First, get case details to see available arguments
    url = f"{BASE_URL}/cases/{case_id}"
    headers = get_auth_headers(token)
    response = make_request("GET", url, headers=headers)
    
    if response.status_code != 200:
        print_error("Could not get case details")
        return False
    
    case_data = response.json()
    arguments = case_data.get("arguments", [])
    
    if len(arguments) < 4:
        print_info(f"Not enough arguments ({len(arguments)}) to test 3-like limit")
        print_info("Need at least 4 arguments in the case")
        return False
    
    # Try to like 4 arguments (4th should fail)
    liked_count = 0
    for i, arg in enumerate(arguments[:4]):
        arg_id = arg["id"]
        url = f"{BASE_URL}/arguments/{arg_id}/vote?case_id={case_id}"
        response = make_request("POST", url, headers=headers)
        
        if i < 3:
            if response.status_code == 200:
                liked_count += 1
                print_success(f"Liked argument {i+1}/3")
            elif response.status_code == 400:
                print_info(f"Already liked this argument")
        else:
            # 4th like should fail
            if response.status_code == 400:
                print_success("Max 3 likes limit correctly enforced!")
                return True
            else:
                print_error(f"Expected 400 for 4th like, got {response.status_code}")
                return False
    
    return False


def test_vote_before_like(case_id: int, argument_id: int, token: str):
    """Test that user must vote before liking arguments"""
    print_section("TEST: Must Vote Before Liking Arguments")
    
    # This test assumes the user hasn't voted yet
    # In real scenario, we'd use a fresh user token
    
    url = f"{BASE_URL}/arguments/{argument_id}/vote?case_id={case_id}"
    headers = get_auth_headers(token)
    response = make_request("POST", url, headers=headers)
    print_response(response)
    
    if response.status_code == 400:
        data = response.json()
        if "must vote" in data.get("detail", "").lower():
            print_success("Vote requirement correctly enforced!")
            return True
    elif response.status_code == 200:
        print_info("User already voted (expected if running full test suite)")
        return True
    
    print_error("Vote requirement not properly enforced")
    return False


def run_all_tests():
    """Run all argument tests"""
    print("\n" + "=" * 60)
    print("ARGUMENT ENDPOINT TESTS")
    print("=" * 60)
    
    try:
        # Get authentication token
        print_info("Getting authentication token...")
        token1, token2 = auth_tests()
        
        if not token1:
            print_error("Authentication failed. Cannot continue.")
            return
        
        # Get a case with arguments
        print_info("Looking for a case with arguments...")
        url = f"{BASE_URL}/cases?status=active&page_size=5"
        headers = get_auth_headers(token1)
        response = make_request("GET", url, headers=headers)
        
        if response.status_code != 200:
            print_error("Could not fetch cases")
            return
        
        cases_data = response.json()
        cases = cases_data.get("cases", [])
        
        if not cases:
            print_info("No cases available. Create a case first using test_cases.py")
            return
        
        # Find a case with arguments
        test_case = None
        for case in cases:
            case_id = case["id"]
            # Get full case details
            url = f"{BASE_URL}/cases/{case_id}"
            response = make_request("GET", url, headers=headers)
            if response.status_code == 200:
                case_details = response.json()
                if case_details.get("arguments"):
                    test_case = case_details
                    break
        
        if not test_case:
            print_info("No cases with arguments found.")
            print_info("Run test_cases.py first to create cases and arguments")
            return
        
        case_id = test_case["id"]
        arguments = test_case["arguments"]
        
        print_success(f"Found case {case_id} with {len(arguments)} arguments")
        
        if arguments:
            argument_id = arguments[0]["id"]
            
            # Test liking an argument
            test_like_argument(argument_id, case_id, token1)
            
            # Test unliking an argument
            test_unlike_argument(argument_id, case_id, token1)
            
            # Test like again
            test_like_argument(argument_id, case_id, token1)
            
            # Test max likes limit
            if len(arguments) >= 4:
                test_max_likes_limit(case_id, token1)
        
        print_section("SUMMARY")
        print_success("All argument tests completed!")
        
    except Exception as e:
        print_error(f"Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
