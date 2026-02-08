# Paper Trading System - Architecture

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Paper Trading CLI                                │
│                     (paper_trading_cli.py)                              │
│                                                                          │
│  Commands: analyze | live | dashboard | settle | report | export        │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
                    ▼               ▼               ▼
        ┌───────────────┐  ┌──────────────┐  ┌──────────────┐
        │  Sportsbook   │  │   Strategy   │  │    Paper     │
        │   Manager     │  │   Manager    │  │    Trader    │
        └───────────────┘  └──────────────┘  └──────────────┘
                │                  │                  │
        ┌───────┴────────┐        │          ┌───────┴────────┐
        │                │        │          │                │
        ▼                ▼        ▼          ▼                ▼
┌──────────────┐  ┌──────────┐  ┌──────────────┐  ┌──────────────┐
│  The Odds    │  │  Odds    │  │  Strategies: │  │    Game      │
│     API      │  │ Scrapers │  │ - Value      │  │   Results    │
│              │  │          │  │ - Shopping   │  │   Tracker    │
│  (Primary)   │  │ (Backup) │  │ - Arbitrage  │  │              │
└──────────────┘  └──────────┘  └──────────────┘  └──────────────┘
                                                            │
        ┌───────────────────────────────────────────────────┤
        │                       │                           │
        ▼                       ▼                           ▼
┌──────────────┐        ┌──────────────┐          ┌──────────────┐
│   Terminal   │        │    Report    │          │ Notification │
│  Dashboard   │        │  Generator   │          │   Alerter    │
│              │        │              │          │              │
│  (Rich UI)   │        │ (CSV/Text)   │          │  (Desktop)   │
└──────────────┘        └──────────────┘          └──────────────┘
                                │
                                ▼
                        ┌──────────────┐
                        │ Data Storage │
                        │              │
                        │  - Bets      │
                        │  - Results   │
                        │  - State     │
                        └──────────────┘
```

## Component Relationships

### Data Flow: Odds Acquisition

```
User Request
    │
    ▼
SportsbookManager
    │
    ├─► Try: The Odds API
    │   └─► Success? Return data
    │
    ├─► Fail? Try: OddsPortal Scraper
    │   └─► Success? Return data
    │
    └─► Fail? Try: OddsChecker Scraper
        └─► Success/Fail? Return data or error
```

### Data Flow: Opportunity Detection

```
Odds Data
    │
    ▼
StrategyManager
    │
    ├─► ValueBettingStrategy
    │   └─► Calculate edge, filter by threshold
    │
    ├─► LineShoppingStrategy
    │   └─► Compare odds, find best prices
    │
    └─► ArbitrageStrategy
        └─► Check for guaranteed profits
            │
            ▼
    All Opportunities
            │
            ├─► Notify via BetAlerter
            ├─► Display in Dashboard
            └─► Include in Reports
```

### Data Flow: Bet Lifecycle

```
Place Bet
    │
    ▼
PaperTrader.place_bet()
    │
    ├─► Validate stake vs bankroll
    ├─► Deduct stake
    ├─► Store bet as 'pending'
    └─► Save state to JSON
        │
        ▼
    Wait for game completion
        │
        ▼
GameResultTracker
    │
    ├─► Fetch results from API
    ├─► Determine win/loss/push
    └─► Call PaperTrader.settle_bet()
        │
        ▼
PaperTrader.settle_bet()
    │
    ├─► Calculate profit/loss
    ├─► Update bankroll
    ├─► Calculate CLV
    ├─► Move to 'settled'
    └─► Save state to JSON
```

## Module Dependencies

```
paper_trading_cli.py
├── betting.paper_trader
│   └── Data: bets, bankroll, state
├── sportsbooks.manager
│   ├── sportsbooks.odds_api
│   └── sportsbooks.scrapers
├── strategies.manager
│   ├── strategies.value_betting
│   ├── strategies.line_shopping
│   └── strategies.arbitrage
├── results.tracker
│   └── API clients for results
├── dashboard.terminal_dashboard
│   └── rich (external library)
├── dashboard.reports
│   └── CSV generation
└── notifications.alerter
    └── plyer (external library)
```

## Storage Schema

### paper_trader_state.json
```json
{
  "bankroll": 10000.00,
  "starting_bankroll": 10000.00,
  "bet_counter": 5,
  "bets": [
    {
      "id": "BET-000001",
      "timestamp": "2026-02-07T12:00:00",
      "status": "settled",
      "sport": "NBA",
      "game_id": "lakers_celtics_20260207",
      "bet_type": "moneyline",
      "selection": "Lakers",
      "odds": 150,
      "stake": 100,
      "strategy": "value_betting",
      "sportsbook": "FanDuel",
      "result": "win",
      "profit": 150,
      "closing_line": 140,
      "clv": 7.14,
      "settled_at": "2026-02-07T22:00:00"
    }
  ],
  "last_updated": "2026-02-07T22:00:00"
}
```

### results.json
```json
{
  "lakers_celtics_20260207": {
    "game_id": "lakers_celtics_20260207",
    "home_team": "Celtics",
    "away_team": "Lakers",
    "home_score": 105,
    "away_score": 108,
    "status": "final",
    "date": "2026-02-07T22:00:00",
    "source": "odds_api"
  }
}
```

## Configuration Schema

```yaml
# API Integration
api_keys:
  the_odds_api: "YOUR_KEY_HERE"

# Paper Trading
paper_trading:
  starting_bankroll: 10000
  bet_sizing_method: 'flat'
  flat_bet_size: 100

# Strategies
strategies:
  value_betting:
    enabled: true
    min_edge: 0.05
  line_shopping:
    enabled: true
    min_difference: 5
  arbitrage:
    enabled: true
    min_profit_margin: 0.01

# Data Sources
data_sources:
  priority_order:
    - "the_odds_api"
    - "odds_scraping"
  cache:
    enabled: true
    ttl_minutes: 5

# Notifications
notifications:
  enabled: true
  high_value_threshold: 0.10
  arbitrage_alerts: true
  daily_summary: true

# Storage
storage:
  bets_file: 'data/bets.json'
  results_file: 'data/results.json'
  state_file: 'data/paper_trader_state.json'
```

## API Integration

### The Odds API

**Endpoints Used:**
- `/v4/sports` - List available sports
- `/v4/sports/{sport}/odds` - Get odds for sport
- `/v4/sports/{sport}/scores` - Get game results

**Rate Limits:**
- Free tier: 500 requests/month
- Recommended: 25 requests/day
- Caching: 5 minutes

**Bookmakers:**
- FanDuel
- DraftKings  
- BetMGM
- Caesars (williamhill_us)
- PointsBet

### Web Scrapers (Backup)

**OddsPortal:**
- Target: oddsportal.com
- Rate limit: 10 requests/minute
- Caching: 5 minutes

**OddsChecker:**
- Target: oddschecker.com
- Rate limit: 10 requests/minute
- Caching: 5 minutes

## Error Handling

### Graceful Degradation

1. **API Failure** → Fall back to scrapers
2. **All Sources Fail** → Log error, continue
3. **Invalid Bet** → Reject, log reason
4. **Settlement Error** → Manual review

### Logging Levels

- **INFO**: Normal operations, opportunities found
- **WARNING**: API limits, fallback triggered
- **ERROR**: Failed operations, invalid data
- **DEBUG**: Detailed trace for development

## Performance Characteristics

### Response Times
- Odds fetch: 1-3 seconds (API), 5-10 seconds (scrapers)
- Strategy analysis: <1 second per game
- Dashboard refresh: <100ms
- Report generation: <1 second

### Resource Usage
- Memory: ~50MB base, +1MB per 1000 bets
- Disk: Minimal (<10MB for 10K bets)
- CPU: Low (<5% during polling)
- Network: ~5MB per analysis (with API)

## Security Considerations

### API Key Storage
- Environment variables (recommended)
- Config file (excluded from git)
- Never hardcoded

### Data Privacy
- All data stored locally
- No external transmission except API calls
- No personal information collected

### Rate Limiting
- Prevents API abuse
- Respects ToS of data sources
- Configurable delays

## Extensibility

### Adding New Strategies
```python
from strategies.base import BaseStrategy

class MyStrategy(BaseStrategy):
    def analyze(self, game, odds):
        # Your logic here
        return opportunities
```

### Adding New Data Sources
```python
from sportsbooks.base import BaseOddsSource

class MyOddsSource(BaseOddsSource):
    def get_odds(self, sport):
        # Your implementation
        return odds_data
```

### Custom Reports
```python
from dashboard.reports import ReportGenerator

class CustomReport(ReportGenerator):
    def my_custom_report(self, paper_trader):
        # Your report logic
        return report_text
```

## Future Enhancements

Potential areas for expansion:
- Machine learning models for probability estimation
- Live betting integration
- More sports and markets
- Advanced risk management
- Portfolio optimization
- Backtesting framework
- Real-time line movement alerts
- Multi-user support
- Web dashboard (complementing terminal)

---

This architecture provides a solid foundation for paper trading sports betting strategies with room for growth and customization.
