# Complete Multi-Strategy Sports Betting Bot

A comprehensive sports betting system that tests **5 different strategies** across **7 major sports** to identify profitable edges before deploying real money.

## 🎯 Core Objective

Test betting strategies in **paper trading mode** for 30 days to identify what actually works, then deploy only the profitable combinations with real money.

---

## ⚡ Features

### 5 Complete Betting Strategies

1. **Sports Arbitrage** - Find guaranteed profit opportunities between sportsbooks
2. **CLV (Closing Line Value) with Predictive Models** - Beat the closing line with statistical models
3. **Sharp Money Tracker** - Detect and follow professional betting action
4. **Prop Bet Analyzer** - Find mispriced player prop bets
5. **Live Betting Engine** - In-game betting opportunities

### 7 Sports Covered

- 🏀 **NBA** - Basketball with comprehensive stats and models
- 🏈 **NFL** - Football with DVOA and weather analysis
- ⚾ **MLB** - Baseball with pitcher-focused models
- 🏒 **NHL** - Hockey with goaltending emphasis
- ⚽ **Soccer** - Football with team form analysis
- 🏈 **NCAAF** - College Football
- 🏀 **NCAAB** - College Basketball

### Multi-Sportsbook Integration

- FanDuel
- DraftKings
- BetMGM
- Caesars
- PointsBet

### Multi-Channel Notifications

- **Desktop Notifications** - Cross-platform alerts for opportunities and events
- **Email Notifications** - SMTP-based email alerts with validation
- **Telegram Bot** - Push notifications via Telegram
- **Sound Alerts** - Audio notifications for critical events
- **Smart Features:**
  - Granular event-type controls (trade, opportunity, error, summary, status changes)
  - Rate limiting to prevent spam
  - Quiet hours configuration
  - Test notification system
  - Email validation and credential security

### Analytics & Tracking

- **Performance Tracker** - Strategy × Sport performance matrix
- **CLV Tracker** - THE KEY METRIC for long-term profitability
- **Risk Management** - Kelly Criterion, drawdown limits, position sizing
- **Real-Time Dashboard** - Live P&L, opportunities, and recommendations

---

## 📊 Paper Trading System

The bot now includes a comprehensive **paper trading system** for testing strategies with real odds data before deploying real money.

### Key Components

1. **The Odds API Integration** (`sportsbooks/odds_api.py`)
   - Real-time odds from FanDuel, DraftKings, BetMGM, Caesars
   - Support for NBA, NFL, MLB, NHL, NCAAF, NCAAB
   - Moneyline, spread, and totals markets
   - 500 free API requests/month
   - 5-minute caching to minimize API usage

2. **SportsbookManager** (`sportsbooks/manager.py`)
   - Intelligent multi-source fallback system
   - Priority: The Odds API → OddsPortal → OddsChecker
   - Automatic source selection and failover
   - Unified data format across all sources

3. **PaperTrader** (`betting/paper_trader.py`)
   - Virtual betting with $10,000 starting bankroll
   - Track all bets, calculate P&L and ROI
   - Calculate CLV (Closing Line Value)
   - Export to CSV for analysis
   - Persistent state across sessions

4. **Betting Strategies**
   - **Value Betting** - Find +EV bets with 5%+ edge
   - **Line Shopping** - Always get the best available odds
   - **Arbitrage** - Risk-free guaranteed profit opportunities

5. **Game Results Tracker** (`results/tracker.py`)
   - Automatic bet settlement from API data
   - Supports The Odds API and ESPN API
   - Manual entry for missing results

6. **Terminal Dashboard** (`dashboard/terminal_dashboard.py`)
   - Live performance metrics
   - Real-time bankroll tracking
   - Recent and pending bets
   - Strategy performance comparison
   - Active opportunities display

7. **Notification System** (`notifications/alerter.py`)
   - Desktop alerts for high-value opportunities
   - Arbitrage opportunity notifications
   - Daily performance summaries
   - API rate limit warnings

### Quick Start

#### 1. Get The Odds API Key (Free Tier)

1. Visit https://the-odds-api.com/
2. Sign up for free account (500 requests/month)
3. Get your API key from the dashboard

#### 2. Configure the Bot

```bash
# Copy example config
cp config.example.yaml config.yaml

# Edit config.yaml and add your API key
api_keys:
  the_odds_api: "YOUR_API_KEY_HERE"
```

Or use environment variable:
```bash
export THE_ODDS_API_KEY="your_api_key_here"
```

#### 3. Run the Paper Trading CLI

**Analyze current opportunities:**
```bash
python paper_trading_cli.py analyze --sport NBA
```

**Run live monitoring:**
```bash
python paper_trading_cli.py live --sports NBA NFL
```

**Show performance dashboard:**
```bash
python paper_trading_cli.py dashboard
```

**Settle completed games:**
```bash
python paper_trading_cli.py settle
```

**Generate reports:**
```bash
# Daily summary
python paper_trading_cli.py report --type daily

# Weekly summary
python paper_trading_cli.py report --type weekly

# Strategy performance
python paper_trading_cli.py report --type strategy
```

**Export bet history:**
```bash
python paper_trading_cli.py export --output my_bets.csv
```

### Configuration Options

Edit `config.yaml` to customize:

```yaml
# Paper Trading Settings
paper_trading:
  starting_bankroll: 10000
  bet_sizing_method: 'flat'  # 'flat', 'kelly', 'percentage'
  flat_bet_size: 100
  max_bet_size: 500
  min_bet_size: 10

# Strategy Settings
strategies:
  value_betting:
    enabled: true
    min_edge: 0.05  # 5% minimum edge
    
  line_shopping:
    enabled: true
    min_difference: 5  # 5 cents minimum
    
  arbitrage:
    enabled: true
    min_profit_margin: 0.01  # 1% minimum

# Notification Settings
notifications:
  enabled: true
  high_value_threshold: 0.10  # Notify if edge > 10%
  arbitrage_alerts: true
  daily_summary: true
```

### Understanding the Metrics

- **Win Rate**: Percentage of won bets (need 52.4%+ to beat -110 vig)
- **ROI**: Return on Investment (profit / total staked)
- **CLV**: Closing Line Value - key metric for long-term profitability
  - Positive CLV = you got better odds than closing line
  - Consistently positive CLV = profitable long-term
- **Edge**: Your estimated advantage over the bookmaker's odds
- **Bankroll**: Current virtual bankroll

### Data Sources Priority

The system tries data sources in this order:

1. **The Odds API** (if API key provided)
   - Most reliable, real-time data
   - 500 requests/month free tier
   - Best odds coverage

2. **OddsPortal Scraper** (free, no API key needed)
   - Backup if API limit reached
   - Slower updates
   - Good coverage

3. **OddsChecker Scraper** (free, no API key needed)
   - Tertiary backup
   - Alternative data source

The bot automatically falls back if a source fails.

---

## 🔔 Notification Setup

The bot includes a comprehensive multi-channel notification system to keep you informed about opportunities, trades, and critical events.

### Quick Start (Desktop Notifications Only)

Desktop notifications are enabled by default and require no configuration:

```yaml
notifications:
  desktop:
    enabled: true  # No setup needed!
```

### Setting Up Email Notifications

1. **Copy the example config:**
   ```bash
   # The first time, copy config.example.yaml to config.yaml
   cp config.example.yaml config.yaml
   ```

2. **Configure email settings in `config.yaml`:**
   ```yaml
   notifications:
     email:
       enabled: true
       from_email: "your-email@gmail.com"
       to_email: "your-email@gmail.com"
       smtp_server: "smtp.gmail.com"
       smtp_port: 587
       password: "YOUR_APP_PASSWORD"  # ⚠️ Use app-specific password!
   ```

3. **Get an app-specific password (Gmail):**
   - Go to Google Account settings → Security
   - Enable 2-Factor Authentication if not already enabled
   - Go to "App passwords"
   - Generate a new app password for "Mail"
   - Use this password in config.yaml

4. **⚠️ SECURITY:** Never commit `config.yaml` to git (it's excluded via .gitignore)

### Setting Up Telegram Notifications

1. **Create a Telegram bot:**
   - Open Telegram and search for @BotFather
   - Send `/newbot` and follow instructions
   - Save your bot token

2. **Get your Chat ID:**
   - Search for @userinfobot in Telegram
   - Send `/start` to get your chat ID
   - Or message your bot and check bot updates

3. **Configure in `config.yaml`:**
   ```yaml
   notifications:
     telegram:
       enabled: true
       bot_token: "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
       chat_id: "987654321"
   ```

### Event Type Configuration

Control which events trigger notifications per channel:

```yaml
notifications:
  desktop:
    enabled: true
    event_types:
      trade: true          # Trade executions
      opportunity: true    # High-value opportunities
      error: true         # Critical errors
      summary: true       # Daily/weekly summaries
      status_change: true # Strategy enable/disable
  
  email:
    enabled: true
    event_types:
      trade: true
      opportunity: false   # Often too frequent for email
      error: true
      summary: true
      status_change: true
```

### Rate Limiting & Quiet Hours

Prevent notification spam:

```yaml
notifications:
  rate_limiting:
    enabled: true
    max_per_hour: 20        # Maximum 20 notifications per hour
    max_per_minute: 5       # Maximum 5 per minute
    cooldown_seconds: 30    # 30s between similar notifications
  
  quiet_hours:
    enabled: true
    start_time: "23:00"    # 11 PM
    end_time: "07:00"      # 7 AM
    timezone: "America/New_York"
```

### Test Your Notifications

Enable test mode to verify your setup:

```yaml
notifications:
  test_mode:
    enabled: true
    send_on_startup: true  # Test when bot starts
```

Or use Python:
```python
from utils.notifier import Notifier
import yaml

with open('config.yaml') as f:
    config = yaml.safe_load(f)

notifier = Notifier(config)
results = notifier.test_notifications()
print(results)  # Shows which channels succeeded
```

### Notification Triggers

Configure when specific notifications are sent:

```yaml
notification_triggers:
  high_value_opportunity:
    enabled: true
    min_edge_percent: 5.0      # Notify on opportunities with >5% edge
    channels: ['desktop', 'telegram']
  
  daily_loss_limit:
    enabled: true
    threshold_percent: 80      # Notify at 80% of daily loss limit
    channels: ['desktop', 'email', 'telegram']
  
  test_complete:
    enabled: true
    channels: ['desktop', 'email']
```

### Security Best Practices

1. **Never commit credentials** - `config.yaml` is git-ignored
2. **Use app-specific passwords** - Never use your main email password
3. **Copy from example** - Start from `config.example.yaml`
4. **Protect your config** - Keep `config.yaml` secure with proper file permissions

```bash
# Set secure permissions on your config
chmod 600 config.yaml
```

---

## 📊 Data Sources - Hybrid System

The bot supports **multiple data sources** with automatic fallback - start completely free, upgrade when ready!

### 🎯 How It Works: Priority-Based Fallback

The bot tries data sources in order of priority. If one fails, it automatically tries the next:

1. **Free Web Scraping** (default) → 2. **The Odds API** (paid, optional) → 3. **ESPN API** (free stats)

```yaml
data_sources:
  priority_order:
    - "odds_scraping"    # Try free scraping first
    - "the_odds_api"     # Fall back to paid API if scraping fails
    - "espn_api"         # Supplementary stats
```

---

### 🆓 Option 1: Free Web Scraping (Default)

**Zero setup required!** The bot automatically scrapes odds from free public websites.

#### ✅ Pros:
- ✅ **Completely free** - No API keys or subscriptions needed
- ✅ **Works out of the box** - Default configuration, just run the bot
- ✅ **Multiple sources** - OddsPortal + OddsChecker for reliability
- ✅ **All sportsbooks** - FanDuel, DraftKings, BetMGM, Caesars, PointsBet
- ✅ **Built-in rate limiting** - Respects website limits (10 req/min default)
- ✅ **Smart caching** - 5-minute cache reduces requests

#### ⚠️ Cons:
- ⚠️ Slower than paid APIs (rate limiting required)
- ⚠️ May break if websites change their HTML structure
- ⚠️ Slightly less fresh data (5-minute cache vs 1-minute for paid)

#### Configuration:

```yaml
data_sources:
  odds_scraping:
    enabled: true  # ✓ Enabled by default
    sources:
      - "oddsportal"     # OddsPortal.com
      - "oddschecker"    # OddsChecker.com
    rate_limiting:
      enabled: true
      requests_per_minute: 10
      delay_between_requests: 6  # 6 seconds between requests
    cache:
      enabled: true
      ttl_minutes: 5     # Cache odds for 5 minutes
    user_agents:
      rotate: true       # Rotate user agents to avoid blocks
```

**No setup required!** This is the default configuration.

---

### 💰 Option 2: The Odds API (Paid, Fallback)

**Optional paid API** for faster, more reliable odds data. The bot automatically falls back to this if scraping fails.

#### ✅ Pros:
- ✅ **Faster** - Direct API access, no rate limiting delays
- ✅ **More reliable** - Professional API, no website changes
- ✅ **Fresher data** - 1-minute cache vs 5-minute for scraping
- ✅ **Official odds** - Direct from sportsbooks' data feeds
- ✅ **Free tier available** - 500 requests/month (~16/day)

#### ⚠️ Cons:
- ⚠️ Requires API key setup
- ⚠️ Free tier limited to 500 requests/month
- ⚠️ Paid plans needed for high-frequency use

#### Setup Instructions:

**1. Get Your Free API Key:**
- Visit [theoddsapi.com](https://the-odds-api.com/)
- Sign up for a free account
- Get 500 API requests per month (free tier)
- Copy your API key

**2. Add to `config.yaml`:**
```yaml
data_sources:
  the_odds_api:
    enabled: true              # Enable The Odds API
    api_key: "YOUR_KEY_HERE"   # Paste your API key
    regions: ["us"]
    markets: ["h2h", "spreads", "totals"]
    odds_format: "american"
    rate_limit:
      requests_per_month: 500   # Free tier limit
      requests_per_day: 25      # Self-imposed daily limit
      min_interval_seconds: 1   # Minimum 1 second between calls
    cache:
      enabled: true
      ttl_minutes: 1     # Cache for 1 minute (fresher data)
```

**3. Restart the bot** - It will now use The Odds API as fallback!

---

### 📈 Option 3: ESPN API (Free Stats)

**Supplementary data source** for game schedules, scores, and team statistics. Always free!

#### Configuration:

```yaml
data_sources:
  espn_api:
    enabled: true
    use_mock: true       # Set to false for real ESPN data
    cache_ttl_minutes: 15
```

**What You Get:**
- ✅ Live game schedules and scores
- ✅ Team records and standings
- ✅ Real game times and venues
- ✅ All 7 sports supported
- ✅ No API key required!

---

### 🎮 Recommended Configurations

#### For Learning / Testing (Default):
```yaml
data_sources:
  priority_order:
    - "odds_scraping"    # Free scraping only
    - "espn_api"
  
  odds_scraping:
    enabled: true        # ✓ Free scraping
  
  the_odds_api:
    enabled: false       # ✗ No API key needed
    api_key: ""
```

**Best for:** Getting started, learning the bot, testing strategies without any setup.

#### For Production (Paid API First):
```yaml
data_sources:
  priority_order:
    - "the_odds_api"     # Try paid API first
    - "odds_scraping"    # Fall back to free scraping
    - "espn_api"
  
  odds_scraping:
    enabled: true        # ✓ Backup free scraping
  
  the_odds_api:
    enabled: true        # ✓ Primary paid API
    api_key: "YOUR_KEY"
```

**Best for:** Live trading with fastest, most reliable data, with free scraping as backup.

#### For Hybrid (Best of Both):
```yaml
data_sources:
  priority_order:
    - "odds_scraping"    # Try free first
    - "the_odds_api"     # Fall back to paid
    - "espn_api"
  
  odds_scraping:
    enabled: true        # ✓ Free primary
  
  the_odds_api:
    enabled: true        # ✓ Paid fallback
    api_key: "YOUR_KEY"
```

**Best for:** Start free, only use paid API when scraping fails. Maximize free tier, minimize costs.

---

### 🔍 Monitoring Data Sources

The bot shows which data source is being used in the dashboard and logs:

**Dashboard Display:**
```
📊 DATA SOURCES
  Priority: odds_scraping → the_odds_api → espn_api
  ✓ Free Scraping: oddsportal, oddschecker
  ✗ The Odds API: Disabled
```

**Log Messages:**
```
✓ Got odds from free scraping for game_123
✓ Got odds from The Odds API for game_456 (fallback)
```

---

### 📦 Installation

**Free Scraping (Default):**
```bash
pip install beautifulsoup4 lxml fake-useragent
```

**All Dependencies:**
```bash
pip install -r requirements.txt
```

---

### 🆘 Troubleshooting

**Issue: "ImportError: No module named 'bs4'"**
```bash
pip install beautifulsoup4 lxml
```

**Issue: "Failed to initialize scrapers"**
- Install dependencies: `pip install beautifulsoup4 lxml fake-useragent`
- Bot will automatically fall back to The Odds API if available

**Issue: "No odds available"**
- Check internet connection
- Verify at least one data source is enabled
- Check logs for specific error messages

**Issue: "API quota exceeded"**
- You've used all 500 free requests this month
- Enable free scraping as primary: `priority_order: ["odds_scraping", "the_odds_api"]`
- Wait for next month's quota reset
- Or upgrade to paid API plan

---

## 📦 Installation

### Requirements

- Python 3.8 or higher
- pip (Python package manager)

### Setup

```bash
# Clone the repository
git clone https://github.com/AlexMeisenzahl/Sport-Betting-Bot.git
cd Sport-Betting-Bot

# Install dependencies
pip install -r requirements.txt

# Run the bot
python bot.py
```

---

## 🚀 Quick Start

### 1. Configure Your Settings

Edit `config.yaml` to enable/disable strategies and sports:

```yaml
paper_trading:
  enabled: true
  starting_bankroll: 500

strategies:
  arbitrage:
    enabled: true
  clv_model:
    enabled: true
  sharp_tracker:
    enabled: true
  prop_analyzer:
    enabled: true
  live_betting:
    enabled: true

sports:
  nba:
    enabled: true
    strategies: ['arbitrage', 'clv_model', 'sharp_tracker', 'props', 'live']
  nfl:
    enabled: true
  # ... etc
```

### 2. Run Paper Trading Test

```bash
python bot.py
```

The bot will run for 30 days (configurable) testing all enabled strategy × sport combinations.

### 3. Review Results

After 30 days, the bot provides clear recommendations:

```
✅ STRATEGIES TO DEPLOY:
   • clv_model + nba → +10.5% ROI (42 bets)
   • arbitrage + soccer → +3.8% ROI (28 bets)

❌ STRATEGIES TO AVOID:
   • clv_model + ncaaf → -2.1% ROI (35 bets)

📈 OVERALL CLOSING LINE VALUE: +1.8 points
   Status: ✓ BEATING THE CLOSING LINE

💰 FINAL BANKROLL: $578.50
   Total Return: +15.70%
```

---

## 🎓 Strategy Explanations

### 1. Sports Arbitrage

**How it works:**
- Monitor odds across multiple sportsbooks
- Find games where betting both sides guarantees profit
- Execute both bets simultaneously

**Example:**
```
FanDuel:    Lakers -110 (risk $110 to win $100)
DraftKings: Celtics +115 (risk $100 to win $115)
Total risk: $210
Guaranteed return: $215
Profit: $5 (2.38% risk-free)
```

### 2. CLV (Closing Line Value) Strategy

**How it works:**
- Build statistical models to predict game outcomes
- Bet when model shows edge vs current line
- Track if bets beat closing line (THE key metric)

**Why it works:**
- Closing line is the "wisest" line (all information priced in)
- If you consistently beat it, you WILL profit long-term (proven)

**Example:**
```
Model predicts: Lakers -7.5
Current line:   Lakers -5.5
Edge: 2 points → BET Lakers -5.5

Game time:
Your bet:       Lakers -5.5
Closing line:   Lakers -8.0
CLV: +2.5 points ✓ (Even if you lose, this was +EV)
```

### 3. Sharp Money Tracker

**How it works:**
- Detect when professional bettors place large bets
- Follow their action before line fully adjusts
- Look for "Reverse Line Movement"

**Example:**
```
Opening: Lakers -6
Public: 75% of bets on Lakers
Current: Lakers -4 (line moved TOWARD Celtics)

Signal: Sharp money on Celtics
Action: BET Celtics +4
```

### 4. Prop Bet Analyzer

**How it works:**
- Find mispriced player props
- Sportsbooks focus on main lines → props get less attention
- Compare player projections to offered lines

**Example:**
```
Player: LeBron James
Prop: Over/Under 27.5 points

Analysis:
- Season average: 29.2 ppg
- Last 10 games: 31.4 ppg
- vs Opponent: 32.8 ppg

Expected: 31.5 points
Prop line: 27.5
Edge: 4.0 points
Action: BET Over 27.5
```

### 5. Live Betting Engine

**How it works:**
- Live lines lag real-time game state
- Detect overreactions and value
- Create hedging opportunities

---

## 📊 Key Metrics

### Closing Line Value (CLV)
- **Most important metric**
- Goal: Average +1.0 to +2.0 points
- Positive CLV = beating the market = profitable long-term

### ROI (Return on Investment)
- Target: +2% to +5% per strategy
- Anything above +2% with positive CLV is deployable

### Win Rate
- Must beat 52.4% to overcome -110 vig
- But CLV matters more than win rate

---

## 🎯 Expected Returns

**Conservative estimate: +3-5% monthly ROI**  
**Aggressive estimate: +8-12% monthly ROI**

*Key: Deploy only profitable combinations after testing*

---

## ⚠️ Warnings

- Sportsbooks WILL limit winning players
- Even +EV betting has variance
- Paper trading uses mock data; real deployment needs live feeds
- Check local laws (sports betting not legal everywhere)
- This is not get-rich-quick - requires discipline

---

## 📈 Next Steps After Testing

### If Results Are Positive (CLV > 0, ROI > 2%)

1. Start small with real money ($500-$1000)
2. Deploy only winning strategy × sport combinations
3. Continue tracking CLV and performance
4. Scale up slowly

### If Results Are Negative

1. **DO NOT deploy real money**
2. Analyze what went wrong
3. Improve and retest

---

## 🎨 Enhanced Dashboard

The bot includes both a **terminal dashboard** and a **web dashboard** for monitoring performance.

### Terminal Dashboard (Rich UI)

The bot displays a real-time terminal dashboard with color-coded metrics:

```bash
python bot.py
```

**Features:**
- 💰 **Bankroll Tracking** - Current balance, P&L, ROI
- 📊 **Betting Statistics** - Win rate, total bets, pending bets
- 📈 **CLV Analysis** - Real-time closing line value tracking
- 🎯 **Strategy Performance** - ROI breakdown by strategy
- 🎨 **Color Coding** - Green for wins, red for losses, yellow for warnings

**Terminal UI powered by Rich library** - Automatically falls back to basic display if Rich is not available.

### Web Dashboard

Launch the web dashboard for a full-featured interface:

```bash
python start_dashboard.py
# or
cd dashboard && python app.py
```

Access at: `http://localhost:5000`

**New Enhanced Endpoints:**

| Endpoint | Description |
|----------|-------------|
| `/api/overview` | Dashboard summary with live data |
| `/api/charts/pnl` | Cumulative P&L chart data |
| `/api/charts/strategy` | Strategy performance comparison |
| `/api/trades/history` | Paginated trade history |
| `/api/export/trades` | CSV export of all trades |
| `/api/bot/status` | Bot status and API connections |

**Features:**
- 📈 **Interactive Charts** - Visualize P&L and performance trends
- 📊 **Trade History** - Filter, search, and export trades
- 🎮 **Bot Control Panel** - Monitor API status and bot health
- 📁 **CSV Export** - Download trade data for external analysis
- 🔄 **Real-Time Updates** - Live data from running bot

### API Integration Status

Monitor your API connections through the dashboard:

```json
{
  "odds_api": {
    "connected": true,
    "mode": "live",  // or "mock"
    "requests_remaining": 450
  },
  "espn_api": {
    "connected": true,
    "mode": "live"
  }
}
```

---

## 🛠️ Technical Details

### Project Structure

```
Sport-Betting-Bot/
├── bot.py                    # Main bot with dashboard
├── config.yaml               # Configuration
├── strategies/              # 5 betting strategies
├── models/                  # Predictive models for 7 sports
├── sports/                  # Sport handlers
├── sportsbooks/            # Sportsbook integrations
├── analytics/              # Performance tracking
└── utils/                  # Utilities
```

---

## 📄 License

MIT License

---

## ⚖️ Disclaimer

**This software is for educational purposes only.**

- Not financial advice
- Sports betting involves risk of loss
- Only bet what you can afford to lose
- Check local laws before using
- The authors are not responsible for any losses

---

**Good luck, and bet responsibly!** 🍀
