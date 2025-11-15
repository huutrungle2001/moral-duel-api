"""Test configuration"""

# API Base URL
BASE_URL = "http://localhost:8000"

# Test user credentials
TEST_USER_1 = {
    "email": "test_user1@example.com",
    "password": "testpassword123",
    "name": "Test User One"
}

TEST_USER_2 = {
    "email": "test_user2@example.com",
    "password": "testpassword456",
    "name": "Test User Two"
}

TEST_USER_3 = {
    "email": "test_user3@example.com",
    "password": "testpassword789",
    "name": "Test User Three"
}

# Test case data
TEST_CASE = {
    "title": "Should we prioritize AI safety over rapid AI development?",
    "context": "As AI technology advances rapidly, there's a debate about whether we should slow down development to ensure safety measures are in place, or continue at full speed to maintain competitive advantage and realize benefits sooner. This raises questions about responsibility, risk, and the greater good."
}

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'
