# API Testing Scripts

Manual testing scripts that make real HTTP requests to verify API endpoints work correctly.

## Prerequisites

1. **Start the API server:**
   ```bash
   make dev
   ```
   Or:
   ```bash
   python main.py
   ```

2. **Install requests library (if not already installed):**
   ```bash
   pip install requests
   ```

## Running Tests

### Run All Tests
```bash
python -m app.testing.test_all
```

### Run Individual Test Suites

**Authentication Tests:**
```bash
python -m app.testing.test_auth
```
Tests:
- User registration
- User login
- Invalid credentials
- Wallet connect (placeholder)

**Case Tests:**
```bash
python -m app.testing.test_cases
```
Tests:
- List cases (with/without auth)
- List cases with filters and pagination
- Create case
- Get case details
- Vote on case
- Duplicate vote prevention
- Submit argument

**Argument Tests:**
```bash
python -m app.testing.test_arguments
```
Tests:
- Like argument
- Unlike argument
- Max 3 likes per case limit
- Vote before like requirement

## Test Configuration

Edit `app/testing/config.py` to change:
- API base URL (default: `http://localhost:8000`)
- Test user credentials
- Test case data

## Understanding Test Output

Tests use color-coded output:
- 🟢 **Green (✓)**: Success
- 🔴 **Red (✗)**: Error/Failure
- 🟡 **Yellow (ℹ)**: Information/Warning
- 🔵 **Blue**: Section headers

Each test shows:
1. HTTP method and URL
2. Request data (if applicable)
3. Response status code
4. Response body (formatted JSON)
5. Success/failure message

## Test Flow

### Complete Test Flow (test_all.py)
1. **Authentication Tests** → Get tokens for test users
2. **Case Tests** → Create and interact with cases
3. **Argument Tests** → Test argument voting

### Typical User Journey
```
1. Register/Login → Get JWT token
2. List cases → Browse available moral dilemmas
3. Get case details → View specific case with arguments
4. Vote on case → Submit YES or NO vote
5. Like 3 arguments → Required before submitting own
6. Submit argument → Add your perspective
```

## Common Issues

### "Could not connect to API"
- Make sure the server is running: `make dev`
- Check that port 8000 is not blocked
- Verify `BASE_URL` in `config.py`

### "Email already registered"
- This is normal if running tests multiple times
- The script will automatically try to login instead

### "User must vote before submitting arguments"
- You need to vote on a case first
- Then like 3 arguments
- Then you can submit your own argument

### "Not enough arguments to test"
- Some tests require existing arguments in cases
- Run the full test suite to create test data
- Or manually create arguments via the API

## Adding New Tests

1. Create a new test file: `test_<feature>.py`
2. Import utilities from `utils.py`
3. Follow the existing test pattern
4. Add to `test_all.py` if needed

Example:
```python
from .config import BASE_URL
from .utils import print_section, print_success, make_request

def test_my_feature():
    print_section("TEST: My Feature")
    url = f"{BASE_URL}/my-endpoint"
    response = make_request("GET", url)
    
    if response.status_code == 200:
        print_success("Feature works!")
    
if __name__ == "__main__":
    test_my_feature()
```

## Notes

- These are **manual integration tests**, not unit tests
- They make real HTTP requests to the running API
- They create real data in the database
- Run `make db-reset` to clean test data (⚠️ deletes all data)
- Tests are idempotent - safe to run multiple times
- User accounts are reused if they already exist
