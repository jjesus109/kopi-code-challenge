# Test Suite

This directory contains comprehensive unit tests for the tech challenge response application.

## Test Structure

- `conftest.py` - Common fixtures and test configuration
- `test_adapters.py` - Tests for the Adapters class and interface
- `test_drivers.py` - Tests for the Drivers class and interface
- `test_cases.py` - Tests for the Cases class and interface
- `test_entities.py` - Tests for the database entities
- `test_models.py` - Tests for the Pydantic models

## Running Tests

### Install Dependencies

First, install the test dependencies:

```bash
# Using uv (recommended)
uv sync --extra test

# Or using pip
pip install -e ".[test]"
```

### Run All Tests

```bash
pytest
```

### Run Specific Test Files

```bash
# Run only adapter tests
pytest tests/test_adapters.py

# Run only driver tests
pytest tests/test_drivers.py

# Run only case tests
pytest tests/test_cases.py
```

### Run Tests with Verbose Output

```bash
pytest -v
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

## Test Categories

### Unit Tests
- **Adapters**: Test message transformation and delegation to drivers
- **Drivers**: Test database operations and session management
- **Cases**: Test business logic and delegation to adapters
- **Entities**: Test SQLModel entity creation and validation
- **Models**: Test Pydantic model validation and serialization

### Test Coverage

The test suite covers:
- ✅ Happy path scenarios
- ✅ Edge cases and error conditions
- ✅ Interface compliance
- ✅ Data validation
- ✅ Async/await functionality
- ✅ Mock interactions
- ✅ Database session management

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
