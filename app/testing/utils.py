"""Utility functions for testing"""
import json
import requests
from typing import Dict, Any, Optional
from .config import Colors


def print_section(title: str):
    """Print a section header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{title}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.END}\n")


def print_success(message: str):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")


def print_error(message: str):
    """Print error message"""
    print(f"{Colors.RED}✗ {message}{Colors.END}")


def print_info(message: str):
    """Print info message"""
    print(f"{Colors.YELLOW}ℹ {message}{Colors.END}")


def print_response(response: requests.Response):
    """Print formatted response"""
    print(f"\n{Colors.BOLD}Status Code:{Colors.END} {response.status_code}")
    try:
        data = response.json()
        print(f"{Colors.BOLD}Response:{Colors.END}")
        print(json.dumps(data, indent=2))
    except:
        print(f"{Colors.BOLD}Response:{Colors.END} {response.text}")


def make_request(
    method: str,
    url: str,
    headers: Optional[Dict[str, str]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None
) -> requests.Response:
    """Make HTTP request and handle errors"""
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, params=params)
        elif method.upper() == "POST":
            response = requests.post(url, headers=headers, json=json_data)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=headers)
        elif method.upper() == "PUT":
            response = requests.put(url, headers=headers, json=json_data)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        return response
    except requests.exceptions.ConnectionError:
        print_error("Could not connect to API. Make sure the server is running (make dev)")
        raise
    except Exception as e:
        print_error(f"Request failed: {str(e)}")
        raise


def get_auth_headers(token: str) -> Dict[str, str]:
    """Get authorization headers"""
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
