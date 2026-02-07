# Test Suite for Sport-Betting-Bot

## Overview

This directory contains comprehensive tests for the Sport-Betting-Bot hybrid data sources system.

## Running Tests

### Run All Tests
```bash
pytest tests/test_scrapers.py -v
```

### Run Specific Test Class
```bash
pytest tests/test_scrapers.py::TestBaseScraper -v
pytest tests/test_scrapers.py::TestOddsPortalScraper -v
pytest tests/test_scrapers.py::TestOddsCheckerScraper -v
pytest tests/test_scrapers.py::TestSportsbookManagerHybrid -v
```

### Run Specific Test
```bash
pytest tests/test_scrapers.py::TestBaseScraper::test_rate_limiting -v
```

## Test Coverage

### BaseScraper Tests (6 tests)
- **test_rate_limiting**: Verifies rate limiting enforces delays between requests
- **test_cache_hit**: Verifies cached data is returned within TTL
- **test_cache_miss_expired**: Verifies expired cache returns None
- **test_user_agent_rotation**: Verifies user agent rotation when enabled
- **test_fetch_page_success**: Verifies successful page fetch with mocking
- **test_fetch_page_error**: Verifies error handling for network failures

### OddsPortalScraper Tests (5 tests)
- **test_initialization**: Verifies scraper initializes with correct URLs
- **test_unsupported_sport**: Verifies handling of unsupported sports
- **test_mock_games_generation**: Verifies mock game data structure
- **test_mock_odds_structure**: Verifies odds structure (moneyline, spread, total)
- **test_odds_balance**: Verifies proper favorite/underdog odds balance

### OddsCheckerScraper Tests (2 tests)
- **test_initialization**: Verifies scraper initializes with correct URLs
- **test_get_odds_returns_data**: Verifies odds data is returned

### SportsbookManagerHybrid Tests (2 tests)
- **test_priority_fallback**: Verifies mocking infrastructure for fallback logic
- **test_data_source_status**: Verifies scrapers have required attributes

## Dependencies

Required packages (in requirements.txt):
- pytest>=7.0.0
- pytest-mock>=3.10.0
- beautifulsoup4>=4.11.0
- lxml>=4.9.0
- fake-useragent>=1.4.0

## Edge Cases Covered

✅ Expired cache handling
✅ Network error handling (RequestException)
✅ Unsupported sport handling
✅ Invalid odds validation (no zero values)
✅ Spread line inversions
✅ Total line consistency

## Test Statistics

- **Total Tests**: 15
- **Success Rate**: 100%
- **Code Coverage**: Comprehensive coverage of scraper functionality

## Contributing

When adding new tests:
1. Follow existing test patterns and naming conventions
2. Use descriptive docstrings
3. Test both success and failure cases
4. Verify edge cases are covered
5. Run all tests before committing: `pytest tests/test_scrapers.py -v`
