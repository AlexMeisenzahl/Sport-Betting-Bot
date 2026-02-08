# Paper Trading System - Quick Example

This is a quick walkthrough of using the paper trading system.

## Prerequisites

```bash
# Install dependencies
pip install -r requirements.txt

# Copy configuration
cp config.example.yaml config.yaml
```

## Get API Key (Optional but Recommended)

1. Visit https://the-odds-api.com/
2. Sign up for free (500 requests/month)
3. Add your API key to config.yaml or set environment variable:

```bash
export THE_ODDS_API_KEY="your_api_key_here"
```

**Note:** The system works without an API key using free web scrapers, but The Odds API provides better data quality.

## Example Workflow

### 1. Analyze Current Opportunities

Check what betting opportunities are available right now:

```bash
python3 paper_trading_cli.py analyze --sport NBA
```

Example output:
```
============================================================
CURRENT OPPORTUNITIES - 2026-02-07 18:30:00
============================================================

ARBITRAGE (2 opportunities):
------------------------------------------------------------
  1. Lakers @ Celtics
     Selection: Lakers
     Profit Margin: 1.23%
     Guaranteed Profit: $1.23

  2. Warriors @ Nets  
     Selection: Warriors
     Profit Margin: 0.85%
     Guaranteed Profit: $0.85

VALUE BETTING (5 opportunities):
------------------------------------------------------------
  1. Lakers @ Celtics
     Selection: Lakers ML
     Edge: +7.2%
     Odds: +150
  
  2. Warriors @ Nets
     Selection: Warriors -5.5
     Edge: +5.8%
     Odds: -110
```

### 2. Place Some Bets

The system doesn't auto-place bets - you review opportunities and decide which to take. For paper trading, you can manually add bets through the Python API:

```python
from betting.paper_trader import PaperTrader

trader = PaperTrader(starting_bankroll=10000)

# Place a bet
bet = {
    'game_id': 'lakers_vs_celtics_20260207',
    'sport': 'NBA',
    'bet_type': 'moneyline',
    'selection': 'Lakers',
    'odds': +150,
    'stake': 100,
    'strategy': 'value_betting',
    'sportsbook': 'FanDuel'
}

bet_id = trader.place_bet(bet)
print(f"Placed bet: {bet_id}")
print(f"Remaining bankroll: ${trader.bankroll:.2f}")
```

### 3. Monitor Performance Dashboard

Watch your paper trading performance in real-time:

```bash
python3 paper_trading_cli.py dashboard
```

You'll see:
- Current bankroll and P&L
- Win rate and ROI
- Recent and pending bets
- Strategy performance comparison
- Active opportunities

Press Ctrl+C to exit.

### 4. Run Live Monitoring

Continuously monitor for opportunities across multiple sports:

```bash
python3 paper_trading_cli.py live --sports NBA NFL
```

The bot will:
- Poll odds every 5 minutes (configurable)
- Run all enabled strategies
- Show opportunities as they appear
- Send desktop notifications for high-value opportunities
- Log everything for review

Press Ctrl+C to stop.

### 5. Settle Completed Games

After games finish, settle your bets:

```bash
python3 paper_trading_cli.py settle
```

This will:
- Check all pending bets
- Fetch game results from APIs
- Automatically settle wins/losses/pushes
- Update your bankroll

### 6. Generate Reports

#### Daily Summary
```bash
python3 paper_trading_cli.py report --type daily
```

Example output:
```
============================================================
DAILY SUMMARY - 2026-02-07
============================================================

BANKROLL:
  Current: $10,250.00
  Starting: $10,000.00
  Net P&L: $+250.00 (+2.50%)

TODAY'S ACTIVITY:
  Total Bets: 8
  Wins: 5
  Losses: 3
  Pushes: 0
  Win Rate: 62.5%
  Total Staked: $800.00
  Total Profit: $+250.00
  Avg CLV: +2.3%
```

#### Weekly Summary
```bash
python3 paper_trading_cli.py report --type weekly
```

#### Strategy Performance
```bash
python3 paper_trading_cli.py report --type strategy
```

Shows performance breakdown by strategy (value betting, line shopping, arbitrage).

### 7. Export Data

Export all bet history to CSV for analysis:

```bash
python3 paper_trading_cli.py export --output my_bets.csv
```

Open in Excel/Google Sheets to analyze:
- Which strategies work best
- Which sports are most profitable
- Time of day patterns
- Bookmaker comparisons

## Configuration Tips

### Adjust Strategy Thresholds

Edit `config.yaml`:

```yaml
strategies:
  value_betting:
    enabled: true
    min_edge: 0.05  # Lower for more bets, higher for quality
    
  arbitrage:
    enabled: true
    min_profit_margin: 0.01  # Even 0.5% is valuable
```

### Set Bet Sizing

```yaml
paper_trading:
  starting_bankroll: 10000
  bet_sizing_method: 'flat'  # or 'kelly' or 'percentage'
  flat_bet_size: 100  # Fixed $100 per bet
  max_bet_size: 500
  min_bet_size: 10
```

### Configure Notifications

```yaml
notifications:
  enabled: true
  high_value_threshold: 0.10  # Notify if edge > 10%
  arbitrage_alerts: true  # Always notify on arbitrage
  daily_summary: true
```

## Understanding Key Metrics

### CLV (Closing Line Value)
The most important metric for long-term profitability. If you consistently beat the closing line, you'll be profitable long-term even with a 50% win rate.

- **Positive CLV**: You got better odds than closing line ✓
- **Negative CLV**: Market moved against you ✗

### Win Rate
You need 52.4% win rate to break even at standard -110 odds due to the vig (bookmaker commission).

### ROI (Return on Investment)
```
ROI = Total Profit / Total Staked
```
Professional bettors target 5-10% ROI long-term.

### Edge
Your estimated advantage on a bet:
```
Edge = True Probability - Implied Probability from Odds
```

## Best Practices

1. **Start Small**: Begin with conservative stakes while learning
2. **Track CLV**: This is your #1 indicator of long-term success
3. **Be Patient**: Don't chase every opportunity, wait for quality
4. **Line Shop**: Always get the best available odds (free money!)
5. **Record Keep**: Export data regularly for analysis
6. **Risk Manage**: Never risk more than 1-2% per bet

## Common Workflows

### Daily Routine
```bash
# Morning: Check overnight opportunities
python3 paper_trading_cli.py analyze --sport NBA

# Settle yesterday's games
python3 paper_trading_cli.py settle

# Check daily performance
python3 paper_trading_cli.py report --type daily

# Start live monitoring for today
python3 paper_trading_cli.py live --sports NBA NFL
```

### Weekly Review
```bash
# Generate weekly report
python3 paper_trading_cli.py report --type weekly

# Check strategy performance
python3 paper_trading_cli.py report --type strategy

# Export data for deeper analysis
python3 paper_trading_cli.py export --output week_$(date +%Y%m%d).csv
```

## Troubleshooting

### "No games found"
- Check if sports are in season
- Verify API key is correct
- Try different sports: `--sport NFL` or `--sport MLB`

### "API rate limit exceeded"
- System auto-falls back to free scrapers
- Wait for API limit to reset (monthly)
- Increase cache duration in config to reduce calls

### "No opportunities found"
- Lower thresholds in config.yaml
- Markets might be efficient right now (normal)
- Try different sports or times of day

## Next Steps

1. Run the system for 30 days to test strategies
2. Analyze which strategies work best for you
3. Identify your edge (sports, bet types, timing)
4. When confident, consider real betting (outside this system)

Remember: **Past performance doesn't guarantee future results**. Use this for education and strategy testing only.
