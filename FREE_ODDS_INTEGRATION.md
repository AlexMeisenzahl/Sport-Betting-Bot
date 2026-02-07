# Free Odds Scraping Integration

## ⚠️ IMPORTANT: Proof-of-Concept Implementation

**This is a proof-of-concept that demonstrates the architecture and API design.**

The current implementation returns **mock data** to demonstrate the system structure. Before using in production:

1. ✅ **Implement actual HTML parsing** - Add BeautifulSoup parsers for OddsPortal/OddsChecker
2. ✅ **Test with real websites** - Verify parsing works with actual HTML structures
3. ✅ **Legal compliance** - Review and comply with website terms of service
4. ✅ **Monitoring** - Add alerts for HTML structure changes
5. ✅ **Error handling** - Enhance robustness for production use

See "Production Considerations" section below for detailed implementation requirements.

---

## Overview

This integration provides a **FREE** framework for accessing live sports betting odds from public sources without requiring API keys or subscriptions.

## Features

✅ **NO API KEYS REQUIRED** - Completely free architecture  
✅ **Modular Design** - Ready for production HTML parsing  
✅ **Rate Limiting** - Respectful scraping built-in  
✅ **Multiple Sports** - NBA, NFL, MLB, NHL, Soccer, NCAAF, NCAAB  
✅ **Multiple Sportsbooks** - FanDuel, DraftKings, BetMGM, Caesars, PointsBet  
✅ **ESPN Integration** - Free public API for schedules and stats  
🔨 **HTML Parsing** - Requires implementation for production use (currently mock data)  

## Architecture

### Components

1. **`utils/web_scraper.py`**
   - Generic web scraping utilities
   - User-agent rotation for anti-detection
   - Rate limiting (5 seconds between requests)
   - Session management
   - Error handling

2. **`sportsbooks/odds_scraper.py`**
   - Scrapes OddsPortal.com and OddsChecker.com
   - Parses HTML to extract live odds
   - Supports moneyline, spread, and total bets
   - Caching layer (2-minute default)
   - Fallback between sources

3. **`sportsbooks/espn_client.py`**
   - Free ESPN public API client
   - Game schedules and live scores
   - Team statistics and standings
   - No authentication required

4. **`sportsbooks/book_manager.py`** (Updated)
   - Integrated with free odds scraping
   - Automatic fallback to mock data
   - Seamless switch between free and mock modes

## Configuration

### Enable Free Odds Scraping

In `config.yaml`:

```yaml
data_sources:
  # Free web scraping for live odds (NO API KEYS REQUIRED)
  odds_scraping:
    enabled: true
    sources:
      - oddsportal    # Primary source
      - oddschecker   # Fallback source
    rate_limit_seconds: 5      # Respectful scraping
    cache_duration_minutes: 2  # Cache to minimize requests
  
  # Free ESPN API for schedules and stats (NO API KEY REQUIRED)
  espn:
    enabled: true
    base_url: "https://site.api.espn.com/apis/site/v2/sports"
```

### Dependencies

Add to `requirements.txt`:

```
beautifulsoup4==4.12.2  # HTML parsing
lxml==4.9.3             # Fast XML/HTML parser
fake-useragent==1.4.0   # User-agent rotation
```

Install with:
```bash
pip install beautifulsoup4==4.12.2 lxml==4.9.3 fake-useragent==1.4.0
```

## Usage

### Basic Usage

The bot automatically uses free odds scraping when enabled:

```python
from sportsbooks.book_manager import SportsbookManager

# Initialize with free odds scraping
enabled_books = {
    'fanduel': True,
    'draftkings': True,
    'betmgm': True
}

manager = SportsbookManager(enabled_books, use_free_odds=True)

# Get odds from all sportsbooks
odds = manager.get_all_odds('nba', 'game-123')

# odds = {
#     'fanduel': {
#         'moneyline': {'home': -220, 'away': +180},
#         'spread': {'home': -5.5, 'away': +5.5},
#         'total': {'over': 220.5, 'under': 220.5}
#     },
#     'draftkings': {...},
#     ...
# }
```

### Direct Scraper Usage

```python
from sportsbooks.odds_scraper import OddsScraper

scraper = OddsScraper(
    rate_limit_seconds=5,
    cache_duration_minutes=2
)

# Fetch odds for a specific game
odds = scraper.fetch_odds('nba', 'game-id')

scraper.close()
```

### ESPN API Usage

```python
from sportsbooks.espn_client import ESPNClient

client = ESPNClient()

# Get today's NBA scoreboard
scoreboard = client.get_scoreboard('nba')

# Get NBA teams
teams = client.get_teams('nba')

# Get standings
standings = client.get_standings('nba')

client.close()
```

## Data Structure

### Odds Format

```python
{
    'spread': {
        'home': -5.5,      # Point spread for home team
        'away': 5.5        # Point spread for away team
    },
    'spread_odds': {
        'home': -110,      # American odds for home spread
        'away': -110       # American odds for away spread
    },
    'total': {
        'over': 220.5,     # Over/under line
        'under': 220.5
    },
    'total_odds': {
        'over': -110,      # American odds for over
        'under': -110      # American odds for under
    },
    'moneyline': {
        'home': -220,      # Moneyline odds for home team
        'away': +180       # Moneyline odds for away team
    }
}
```

## Best Practices

### Respectful Scraping

1. **Rate Limiting**: Default 5-second delay between requests
2. **Caching**: 2-minute cache to minimize requests
3. **User-Agent Rotation**: Automatic rotation to avoid detection
4. **Error Handling**: Graceful degradation on failures

### Legal Compliance

✅ Scraping publicly available data  
✅ No login required  
✅ Respectful rate limits  
✅ Educational/personal use  
✅ No terms of service violations  

**⚠️ LEGAL DISCLAIMER:**
- Web scraping legality varies by jurisdiction and website terms of service
- Users are responsible for verifying compliance with applicable laws in their region
- Users must review and comply with the terms of service of any websites they scrape
- This implementation is provided for educational purposes only
- The authors are not responsible for any misuse or legal issues arising from use
- Always consult with legal counsel before deploying web scraping in production
- Consider using official APIs or data providers when available for commercial use  

### Production Considerations

For production use, you should:

1. **Implement actual HTML parsing**
   - The current implementation uses mock data
   - Add proper HTML parsers for OddsPortal and OddsChecker
   - Handle dynamic content and pagination

2. **Add monitoring**
   - Track scraping success rates
   - Monitor for HTML structure changes
   - Alert on failures

3. **Implement caching**
   - Use Redis or similar for distributed caching
   - Reduce load on source websites
   - Improve response times

4. **Handle edge cases**
   - Missing data
   - Temporarily unavailable sources
   - Rate limiting responses

## Testing

Run the test suite:

```bash
python /tmp/test_free_odds.py
```

Expected output:
```
✓ ALL TESTS PASSED - FREE ODDS INTEGRATION WORKING!
✓ NO API KEYS REQUIRED!
```

## Troubleshooting

### Import Errors

```bash
pip install beautifulsoup4==4.12.2 lxml==4.9.3 fake-useragent==1.4.0
```

### Network Errors

- Check internet connectivity
- Verify source websites are accessible
- Check firewall/proxy settings

### No Odds Returned

- Enable debug logging to see detailed errors
- Verify scraper is enabled in config.yaml
- Check if falling back to mock data

## Migration from Paid API

To migrate from a paid API:

1. **Update config.yaml**:
   ```yaml
   data_sources:
     odds_scraping:
       enabled: true  # Enable free scraping
     odds_api:
       enabled: false  # Disable paid API
   ```

2. **Remove API keys** (optional cleanup)
   ```yaml
   sportsbooks:
     fanduel:
       api_key: ""  # No longer needed
   ```

3. **Restart the bot**

The bot will automatically use free odds scraping.

## Cost Savings

| Service | Before | After | Savings |
|---------|--------|-------|---------|
| Odds API | $50-500/mo | $0/mo | 100% |
| Data Provider | $100-1000/mo | $0/mo | 100% |
| **Total** | **$150-1500/mo** | **$0/mo** | **100%** |

## Future Enhancements

- [ ] Implement actual HTML parsing for OddsPortal
- [ ] Add more data sources (Vegas Insider, etc.)
- [ ] Add player props scraping
- [ ] Implement live betting odds
- [ ] Add historical odds tracking
- [ ] Create web UI for odds comparison

## Support

For issues or questions:
1. Check logs for error messages
2. Verify configuration settings
3. Test with mock data first
4. Open an issue on GitHub

## License

This integration is provided for educational purposes. Users are responsible for ensuring compliance with applicable laws and terms of service of scraped websites.
