"""
Run All API Tests

This script runs all test modules in sequence to verify the complete API functionality.
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.testing.config import BASE_URL
from app.testing.utils import print_section, print_success, print_error, print_info, Colors


def main():
    """Run all tests and report results."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}MORAL DUEL API - COMPLETE TEST SUITE{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.END}")
    print(f"\n{Colors.BOLD}API URL:{Colors.END} {BASE_URL}")
    print(f"{Colors.BOLD}Test Coverage:{Colors.END} Authentication, Cases, Arguments\n")
    
    results = {}
    
    # Test 1: Authentication
    try:
        print_section("1. AUTHENTICATION TESTS")
        from app.testing.test_auth import run_all_tests as test_auth
        token1, token2 = test_auth()
        results["auth"] = token1 is not None
        if not token1:
            print_error("Authentication tests failed. Stopping.")
            return
    except Exception as e:
        print_error(f"Authentication tests failed: {str(e)}")
        results["auth"] = False
        return
    
    # Test 2: Cases
    try:
        print_section("2. CASE ENDPOINT TESTS")
        from app.testing.test_cases import run_all_tests as test_cases
        test_cases()
        results["cases"] = True
    except Exception as e:
        print_error(f"Case tests failed: {str(e)}")
        results["cases"] = False
    
    # Test 3: Arguments
    try:
        print_section("3. ARGUMENT ENDPOINT TESTS")
        from app.testing.test_arguments import run_all_tests as test_arguments
        test_arguments()
        results["arguments"] = True
    except Exception as e:
        print_error(f"Argument tests failed: {str(e)}")
        results["arguments"] = False
    
    # Print summary
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}TEST SUMMARY{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.END}\n")
    
    total_tests = len(results)
    passed_tests = sum(1 for v in results.values() if v)
    
    for test_name, passed in results.items():
        status = f"{Colors.GREEN}✓ PASSED{Colors.END}" if passed else f"{Colors.RED}✗ FAILED{Colors.END}"
        print(f"{test_name.upper():20} {status}")
    
    print(f"\n{Colors.BOLD}Total:{Colors.END} {passed_tests}/{total_tests} test suites passed")
    
    if passed_tests == total_tests:
        print(f"\n{Colors.GREEN}✓ All tests passed!{Colors.END}\n")
    else:
        print(f"\n{Colors.RED}✗ Some tests failed.{Colors.END}\n")


if __name__ == "__main__":
    main()
