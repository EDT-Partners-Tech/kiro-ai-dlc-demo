# Test Instructions - Blog Posts API

## Test Suite Overview

**Total Tests**: 35 test cases
- **Example-Based Tests**: 26 tests (test_api.py)
- **Property-Based Tests**: 9 tests (test_api_pbt.py)

**Coverage Areas**:
- ✅ All 5 API endpoints (POST, GET, GET/{id}, PATCH, DELETE)
- ✅ Input validation and error handling
- ✅ Pagination and filtering
- ✅ Tag management
- ✅ Concurrency (last-write-wins)
- ✅ Security headers
- ✅ Data model serialization round-trips
- ✅ Invariant properties

## Running Tests

### Install Test Dependencies

```bash
python3 -m pip install pytest pytest-asyncio httpx hypothesis
```

### Run All Tests

```bash
python3 -m pytest tests/ -v
```

### Run with Coverage Report

```bash
python3 -m pip install pytest-cov
python3 -m pytest tests/ --cov=app --cov-report=html
# Open htmlcov/index.html in browser
```

### Run Specific Test File

```bash
# Example-based tests only
python3 -m pytest tests/test_api.py -v

# Property-based tests only
python3 -m pytest tests/test_api_pbt.py -v
```

### Run Specific Test

```bash
python3 -m pytest tests/test_api.py::test_create_post_success -v
```

### Run Tests Matching Pattern

```bash
# Tests containing "pagination"
python3 -m pytest tests/ -k "pagination" -v

# Tests containing "tag"
python3 -m pytest tests/ -k "tag" -v
```

### Run Tests with Different Hypothesis Settings

```bash
# Generate more examples per test
python3 -m pytest tests/test_api_pbt.py -v --hypothesis-seed=123

# Show hypothesis statistics
python3 -m pytest tests/test_api_pbt.py -v -vv
```

## Test Categories

### CREATE Endpoint Tests (7 tests)

```bash
pytest tests/test_api.py::test_create_post_success
pytest tests/test_api.py::test_create_post_with_tags
pytest tests/test_api.py::test_create_post_missing_title
pytest tests/test_api.py::test_create_post_empty_title
pytest tests/test_api.py::test_create_post_missing_content
pytest tests/test_api.py::test_create_post_title_too_long
pytest tests/test_api.py::test_create_post_content_too_long
```

**Coverage**: Successful creation, validation, error handling

### READ Endpoint Tests (3 tests)

```bash
pytest tests/test_api.py::test_get_post_success
pytest tests/test_api.py::test_get_post_not_found
pytest tests/test_api.py::test_get_post_with_tags
```

**Coverage**: Single post retrieval, tags, not found

### LIST Endpoint Tests (6 tests)

```bash
pytest tests/test_api.py::test_list_posts_empty
pytest tests/test_api.py::test_list_posts_success
pytest tests/test_api.py::test_list_posts_pagination_limit
pytest tests/test_api.py::test_list_posts_pagination_cursor
pytest tests/test_api.py::test_list_posts_filter_by_tag
pytest tests/test_api.py::test_list_posts_filter_nonexistent_tag
```

**Coverage**: Pagination, filtering, cursor handling

### UPDATE Endpoint Tests (5 tests)

```bash
pytest tests/test_api.py::test_update_post_success
pytest tests/test_api.py::test_update_post_partial
pytest tests/test_api.py::test_update_post_with_tags
pytest tests/test_api.py::test_update_post_not_found
pytest tests/test_api.py::test_update_post_empty_update
```

**Coverage**: Full update, partial update, tag updates, not found

### DELETE Endpoint Tests (3 tests)

```bash
pytest tests/test_api.py::test_delete_post_success
pytest tests/test_api.py::test_delete_post_not_found
pytest tests/test_api.py::test_delete_post_with_tags
```

**Coverage**: Deletion, not found, cascade handling

### Security Tests (1 test)

```bash
pytest tests/test_api.py::test_security_headers_present
```

**Coverage**: HTTP security headers

### Concurrency Tests (1 test)

```bash
pytest tests/test_api.py::test_concurrent_updates_last_write_wins
```

**Coverage**: Last-write-wins behavior

### Property-Based Tests (9 tests)

```bash
pytest tests/test_api_pbt.py -v
```

**Coverage**:
- BlogPost serialization round-trips
- Tag serialization round-trips
- BlogPostCreate validation
- Field length invariants
- Pagination invariants

## Test Output Examples

### Successful Run

```
============================= test session starts ==============================
collected 35 items

tests/test_api.py::test_create_post_success PASSED                       [  2%]
tests/test_api.py::test_create_post_with_tags PASSED                     [  5%]
...
====================== 35 passed in 1.16s =======================
```

### Test with Failures

```
tests/test_api.py::test_create_post_success PASSED                       [  2%]
tests/test_api.py::test_create_post_with_tags FAILED                     [  5%]

FAILED tests/test_api.py::test_create_post_with_tags - AssertionError: ...
```

## Debugging Tests

### Run with Full Traceback

```bash
pytest tests/ -v --tb=long
```

### Run with Print Statements

```bash
pytest tests/ -v -s
```

### Run Single Test with Debugging

```bash
pytest tests/test_api.py::test_create_post_success -vv -s
```

### Generate Pytest Config for Local Debugging

```bash
pytest tests/ --collect-only
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: 3.10
      - run: pip install -r requirements.txt
      - run: pytest tests/ -v --cov=app
```

## Performance Testing

### Run Tests with Timing

```bash
pytest tests/ -v --durations=10
```

This shows the 10 slowest tests.

### Run Only Fast Tests

```bash
pytest tests/ -v -m "not slow"
```

## Property-Based Testing Details

### Hypothesis Configuration

Hypothesis is configured in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
hypothesis_profile = 'default'
```

### Common Hypothesis Settings

- `max_examples` (default 100): Number of examples to generate per test
- `seed`: Fixed seed for reproducible failures
- `deadline`: Timeout per example (in milliseconds)

### Reproducing Hypothesis Failures

When a hypothesis test fails, it prints the seed:

```
Falsifying example: test_blog_post_dict_round_trip(
    blog_post=BlogPost(title='...', content='...')
)
```

Rerun with the same seed:

```bash
pytest tests/test_api_pbt.py::test_blog_post_dict_round_trip --hypothesis-seed=123456789
```

## Test Maintenance

### Adding New Tests

1. Add to appropriate test file (test_api.py or test_api_pbt.py)
2. Follow naming convention: `test_<feature>_<scenario>`
3. Use fixtures for setup/teardown
4. Run full test suite after adding

### Updating Tests

1. Make test changes
2. Run affected tests: `pytest tests/ -k "<keyword>" -v`
3. Verify no regressions: `pytest tests/ -v`

### Disabling Tests Temporarily

```python
@pytest.mark.skip(reason="Feature not yet implemented")
def test_future_feature():
    pass
```

## Test Metrics

- **Pass Rate**: 35/35 (100%)
- **Coverage Target**: >80% for critical paths
- **Execution Time**: <2 seconds (typical)
- **Property Examples**: 100 examples per PBT test

## Troubleshooting

### Import Errors

Ensure correct working directory:

```bash
cd /path/to/blog-posts-api
python3 -m pytest tests/
```

### Database Locked

Tests use in-memory SQLite. If locked:

```bash
pkill -f pytest
rm blog-posts.db  # if exists
pytest tests/
```

### Test Timeouts

Increase pytest timeout:

```bash
pytest tests/ --timeout=300
```

## Next Steps

After tests pass:

1. Run code quality checks (black, ruff, mypy)
2. Review test coverage
3. Deploy to staging environment
4. Run integration tests
5. Deploy to production
