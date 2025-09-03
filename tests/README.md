# Test Suite

This directory contains comprehensive unit tests for the tech challenge

## Test Structure

- `conftest.py` - Common fixtures and test configuration
- `test_adapters.py` - Tests for the Adapters class and interface
- `test_cases.py` - Tests for the Cases class and interface


## Running Tests

### Install Dependencies

First, install the test dependencies:

```bash
# Using uv (recommended)
uv sync --extra test
```

### Run All Tests

```bash
pytest
```


### Run Tests with Coverage

```bash
# Install coverage if not already installed
pip install coverage

# Run tests with coverage
coverage run -m pytest
coverage report
coverage html  # Generate HTML report
```




## Test Fixtures

Common test fixtures are defined in `conftest.py`:
- `sample_message` - Sample Messages entity
- `sample_conversation` - Sample Conversations entity
- `sample_message_model` - Sample MessageModel
- `mock_drivers_interface` - Mock DriversInterface
- `mock_adapters_interface` - Mock AdaptersInterface
- `mock_async_engine` - Mock AsyncEngine

## Adding New Tests

When adding new tests:

1. Follow the existing naming convention: `test_*.py`
2. Use descriptive test method names: `test_method_name_scenario`
3. Include docstrings explaining what each test validates
4. Use appropriate pytest markers (`@pytest.mark.asyncio` for async tests)
5. Mock external dependencies appropriately
6. Test both success and failure scenarios

## Test Configuration

The test configuration is defined in `pytest.ini`:
- Async mode is automatically enabled
- Test discovery patterns are configured
- Verbose output is enabled by default
- Custom markers are defined for test categorization
