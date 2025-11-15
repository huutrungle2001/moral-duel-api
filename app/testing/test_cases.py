"""
Test Case Endpoints

Tests:
- GET /cases (list cases with filters, pagination)
- GET /cases/:id (get case details)
- POST /cases (create case)
- POST /cases/:id/vote (vote on case)
- POST /cases/:id/arguments (submit argument)
"""
import sys
from .config import BASE_URL, TEST_CASE
from .utils import (
    print_section, print_success, print_error, print_info,
    print_response, make_request, get_auth_headers
)
from .test_auth import run_all_tests as auth_tests


def test_list_cases(token: str = None):
    """Test listing all cases"""
    print_section("TEST: List Cases")
    
    url = f"{BASE_URL}/cases"
    print_info(f"GET {url}")
    
    headers = get_auth_headers(token) if token else None
    response = make_request("GET", url, headers=headers)
    print_response(response)
    
    if response.status_code == 200:
        data = response.json()
        print_success(f"Retrieved {data['total']} cases")
        print_info(f"Page: {data['page']}/{data['total_pages']}")
        return data
    else:
        print_error(f"Failed to list cases: {response.status_code}")
        return None


def test_list_cases_with_filters(token: str = None):
    """Test listing cases with filters"""
    print_section("TEST: List Cases with Filters")
    
    url = f"{BASE_URL}/cases"
    params = {
        "status": "active",
        "page": 1,
        "page_size": 10,
        "sort_by": "created_at",
        "sort_order": "desc"
    }
    
    print_info(f"GET {url}")
    print_info(f"Params: {params}")
    
    headers = get_auth_headers(token) if token else None
    response = make_request("GET", url, headers=headers, params=params)
    print_response(response)
    
    if response.status_code == 200:
        data = response.json()
        print_success(f"Filtered results: {len(data['cases'])} cases")
        return data
    else:
        print_error(f"Failed to filter cases: {response.status_code}")
        return None


def test_create_case(token: str):
    """Test creating a case"""
    print_section("TEST: Create Case")
    
    url = f"{BASE_URL}/cases"
    print_info(f"POST {url}")
    print_info(f"Data: {TEST_CASE}")
    
    headers = get_auth_headers(token)
    response = make_request("POST", url, headers=headers, json_data=TEST_CASE)
    print_response(response)
    
    if response.status_code == 201:
        data = response.json()
        print_success(f"Case created with ID: {data['case_id']}")
        return data["case_id"]
    else:
        print_error(f"Failed to create case: {response.status_code}")
        return None


def test_get_case_details(case_id: int, token: str = None):
    """Test getting case details"""
    print_section(f"TEST: Get Case Details (ID: {case_id})")
    
    url = f"{BASE_URL}/cases/{case_id}"
    print_info(f"GET {url}")
    
    headers = get_auth_headers(token) if token else None
    response = make_request("GET", url, headers=headers)
    print_response(response)
    
    if response.status_code == 200:
        data = response.json()
        print_success(f"Retrieved case: {data['title']}")
        print_info(f"Status: {data['status']}")
        print_info(f"Votes - YES: {data['yes_votes']}, NO: {data['no_votes']}")
        print_info(f"Arguments: {len(data['arguments'])}")
        return data
    else:
        print_error(f"Failed to get case details: {response.status_code}")
        return None


def test_vote_on_case(case_id: int, token: str, side: str = "YES"):
    """Test voting on a case"""
    print_section(f"TEST: Vote on Case (ID: {case_id}, Side: {side})")
    
    url = f"{BASE_URL}/cases/{case_id}/vote"
    vote_data = {"side": side}
    
    print_info(f"POST {url}")
    print_info(f"Data: {vote_data}")
    
    headers = get_auth_headers(token)
    response = make_request("POST", url, headers=headers, json_data=vote_data)
    print_response(response)
    
    if response.status_code == 200:
        data = response.json()
        print_success(f"Vote recorded: {data['side']}")
        print_info(f"Updated votes - YES: {data['yes_votes']}, NO: {data['no_votes']}")
        return True
    else:
        print_error(f"Failed to vote: {response.status_code}")
        return False


def test_submit_argument(case_id: int, token: str, side: str = "YES"):
    """Test submitting an argument"""
    print_section(f"TEST: Submit Argument (Case ID: {case_id})")
    
    url = f"{BASE_URL}/cases/{case_id}/arguments"
    argument_data = {
        "content": "This is a test argument for the moral dilemma. We should consider the long-term implications.",
        "side": side
    }
    
    print_info(f"POST {url}")
    print_info(f"Data: {argument_data}")
    
    headers = get_auth_headers(token)
    response = make_request("POST", url, headers=headers, json_data=argument_data)
    print_response(response)
    
    if response.status_code == 201:
        data = response.json()
        print_success(f"Argument submitted with ID: {data['argument_id']}")
        return data["argument_id"]
    else:
        print_error(f"Failed to submit argument: {response.status_code}")
        if response.status_code == 400:
            print_info("Note: You need to vote and like 3 arguments before submitting your own")
        return None


def test_duplicate_vote(case_id: int, token: str):
    """Test that duplicate voting is prevented"""
    print_section(f"TEST: Duplicate Vote Prevention (Case ID: {case_id})")
    
    url = f"{BASE_URL}/cases/{case_id}/vote"
    vote_data = {"side": "NO"}
    
    print_info(f"POST {url}")
    print_info("Attempting to vote again (should fail)")
    
    headers = get_auth_headers(token)
    response = make_request("POST", url, headers=headers, json_data=vote_data)
    print_response(response)
    
    if response.status_code == 400:
        print_success("Duplicate vote correctly prevented!")
        return True
    else:
        print_error(f"Expected 400, got {response.status_code}")
        return False


def run_all_tests():
    """Run all case tests"""
    print("\n" + "=" * 60)
    print("CASE ENDPOINT TESTS")
    print("=" * 60)
    
    try:
        # First get authentication tokens
        print_info("Getting authentication tokens...")
        token1, token2 = auth_tests()
        
        if not token1:
            print_error("Authentication failed. Cannot continue.")
            return
        
        # Test listing cases
        test_list_cases()
        test_list_cases(token1)  # Authenticated request
        test_list_cases_with_filters(token1)
        
        # Create a test case
        case_id = test_create_case(token1)
        
        if case_id:
            # Get case details
            case_details = test_get_case_details(case_id)
            test_get_case_details(case_id, token1)  # Authenticated
            
            # Vote on the case
            if token1:
                test_vote_on_case(case_id, token1, "YES")
                test_duplicate_vote(case_id, token1)
            
            # Try to submit argument (will fail without liking 3 arguments)
            if token1:
                test_submit_argument(case_id, token1, "YES")
        
        print_section("SUMMARY")
        print_success("All case tests completed!")
        
    except Exception as e:
        print_error(f"Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
