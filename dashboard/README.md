# Sports Betting Alerts Dashboard

A professional, modern web dashboard for viewing and managing betting alerts from the Sport-Betting-Bot.

![Dashboard](https://img.shields.io/badge/status-production%20ready-brightgreen)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![Flask](https://img.shields.io/badge/flask-latest-lightgrey)

## ✨ Features

### 📊 Alerts Feed
- **Real-time alerts display** with auto-refresh capability
- **Advanced filtering** by sport, time range, confidence level, and more
- **Beautiful alert cards** with color-coded confidence scores
- **Responsive design** that works on desktop, tablet, and mobile

### 📜 Alert History
- **Comprehensive table** of all past alerts
- **Pagination** for easy navigation (25/50/100 per page)
- **Export to CSV** for external analysis
- **Date range filtering** for custom time periods

### 📈 Analytics Dashboard
- **Key metrics cards**:
  - Total alerts generated
  - Alerts today
  - Average confidence score
  - Alerts per day trend
- **Interactive charts** using Chart.js:
  - Alerts over time (line chart)
  - Alerts by sport (bar chart)
  - Confidence distribution (histogram)
  - Alert frequency by day of week

### ⚙️ Settings Panel
- **Notification preferences**:
  - Toggle desktop, email, and Telegram notifications
  - Test notification buttons for each channel
  - Safe credential management
- **Display preferences**:
  - Auto-refresh interval configuration
  - Default alerts per page
- **Configuration backups** (automatic before changes)

## 🚀 Quick Start

### Option 1: One-Command Start (Recommended)

```bash
python3 start_dashboard.py
```

The dashboard will:
1. Check and install dependencies if needed
2. Start the Flask server
3. Automatically open in your browser at http://localhost:5000

### Option 2: Manual Start

```bash
# Install dependencies
pip install flask flask-cors pyyaml

# Run the dashboard
cd dashboard
python3 app.py
```

Then open http://localhost:5000 in your browser.

## 📋 Requirements

- Python 3.8 or higher
- Flask and dependencies (automatically installed by start script)

### Python Packages
- `flask` - Web framework
- `flask-cors` - CORS support for API
- `pyyaml` - Configuration management

## 📁 Architecture

```
Sport-Betting-Bot/
├── dashboard/
│   ├── app.py                    # Main Flask application
│   ├── services/
│   │   ├── __init__.py
│   │   ├── alerts_parser.py      # Parse alert logs and history
│   │   ├── analytics.py          # Calculate alert statistics
│   │   └── config_manager.py     # Manage config with backups
│   ├── static/
│   │   ├── css/custom.css        # Custom styles
│   │   └── js/dashboard.js       # Frontend interactivity
│   └── templates/
│       └── index.html            # Main dashboard template
├── start_dashboard.py            # Quick start script
└── dashboard/README.md           # This file
```

## 🔧 Configuration

The dashboard reads from your existing `config.yaml` file. No additional configuration needed!

### Port Configuration

Change the port by setting the `PORT` environment variable:

```bash
PORT=8080 python3 start_dashboard.py
```

### Host Configuration

By default, the dashboard binds to `127.0.0.1` (localhost only). To allow external access:

```bash
HOST=0.0.0.0 python3 start_dashboard.py
```

⚠️ **Security Note**: Only expose to external networks if you understand the security implications.

## 🔌 API Endpoints

### Alerts
- `GET /api/alerts` - Get filtered alerts
  - Query params: `sport`, `league`, `min_confidence`, `time_range`, `status`, `limit`
- `GET /api/alerts/history` - Get paginated alert history
  - Query params: `page`, `per_page`, `sport`, `start_date`, `end_date`
- `POST /api/alerts/:id/action` - Perform action on alert
  - Body: `{ "action": "mark_read" | "dismiss" | "favorite" }`

### Analytics
- `GET /api/analytics/overview` - Get dashboard overview statistics
- `GET /api/analytics/charts` - Get chart data for visualizations
- `GET /api/analytics/summary` - Get alert summary for date range

### Settings
- `GET /api/settings` - Get current bot settings
- `PUT /api/settings` - Update bot settings (with automatic backup)
- `GET /api/settings/notification` - Get notification settings
- `PUT /api/settings/notification` - Update notification settings

### Notifications
- `POST /api/notifications/test` - Test notification channels
  - Body: `{ "channel": "desktop" | "email" | "telegram" | "all" }`

### Metadata
- `GET /api/metadata/sports` - Get list of available sports
- `GET /api/metadata/leagues` - Get list of available leagues

## 🎨 User Interface

### Dark Theme
The dashboard features a professional dark theme optimized for extended viewing:
- Reduced eye strain during long sessions
- High contrast for important information
- Color-coded confidence scores (green/yellow/red)

### Responsive Design
Works seamlessly across devices:
- **Desktop**: Full feature set with side-by-side layouts
- **Tablet**: Optimized column layouts
- **Mobile**: Stacked cards for easy scrolling

### Interactive Elements
- **Auto-refresh**: Configure automatic data updates (30s, 1m, 5m)
- **Smooth animations**: Polished transitions and hover effects
- **Toast notifications**: User feedback for all actions
- **Loading states**: Clear indicators during data fetching

## 🔒 Security

### Built-in Security Features
- ✅ Debug mode disabled by default
- ✅ CORS properly configured for API endpoints
- ✅ Input validation on all endpoints
- ✅ Automatic config backups before changes
- ✅ No hardcoded credentials
- ✅ Safe error handling (no sensitive data in errors)

### Best Practices
1. **Never commit** `config.yaml` (already in .gitignore)
2. **Use strong passwords** for email/Telegram configuration
3. **Keep dependencies updated**: `pip install --upgrade flask flask-cors pyyaml`
4. **Review config backups** in `config_backups/` directory
5. **Limit network access** - use localhost (127.0.0.1) unless necessary

## 🐛 Troubleshooting

### Dashboard won't start
**Error**: `ModuleNotFoundError: No module named 'flask'`
```bash
pip install flask flask-cors pyyaml
```

**Error**: Port already in use
```bash
# Use a different port
PORT=5001 python3 start_dashboard.py
```

### No alerts showing
**Check**: Are there any log files?
```bash
ls -la betting_bot_*.log
```

The dashboard reads alerts from log files created by the betting bot. Run the bot first to generate alerts:
```bash
python3 bot.py
```

### Charts not rendering
**Check**: Browser console for errors (F12 → Console tab)

**Solution**: Ensure Chart.js is loading from CDN. Check internet connection.

### Notifications not working
**Desktop**: Verify `plyer` is installed
```bash
pip install plyer
```

**Email**: Check credentials in `config.yaml` and test with:
```bash
python3 test_notifications.py
```

**Telegram**: Verify `bot_token` and `chat_id` in `config.yaml`

## 📊 Log Format

The dashboard parses logs that contain alert keywords:
- `OPPORTUNITY`
- `ALERT`
- `ARBITRAGE`
- `CLV`
- `SHARP`
- `PROP`
- `LIVE`

Example log format:
```
2024-02-07 15:30:45 - betting_bot - INFO - ARBITRAGE OPPORTUNITY: Lakers vs Celtics, profit: 3.2%
```

## 🔄 Integration with Bot

The dashboard **reads** from:
- Log files (`betting_bot_*.log`)
- Configuration file (`config.yaml`)
- Alert history

The dashboard **does not modify**:
- Bot behavior
- Alert generation logic
- Trading strategies

This ensures **zero conflicts** with existing bot functionality.

## 🚧 Future Enhancements

Planned features for future releases:
- [ ] Bet tracking and outcome monitoring
- [ ] Performance metrics and ROI calculation
- [ ] Multi-user support with authentication
- [ ] Mobile app (React Native)
- [ ] Alert webhooks for custom integrations
- [ ] Advanced filtering with saved presets
- [ ] Real-time WebSocket updates
- [ ] Dark/Light theme toggle

## 📝 Development

### Running in Development Mode

```python
# In dashboard/app.py, change:
app.config['DEBUG'] = True

# Then run:
python3 app.py
```

⚠️ **Never run with DEBUG=True in production!**

### Adding New Features

1. **Backend**: Add endpoints in `dashboard/app.py`
2. **Services**: Add logic in `dashboard/services/`
3. **Frontend**: Update `templates/index.html` and `static/js/dashboard.js`
4. **Test**: Verify with sample data before deploying

### Code Style
- Follow PEP 8 for Python code
- Use meaningful variable names
- Add docstrings to functions
- Comment complex logic

## 🤝 Contributing

Contributions are welcome! Please:
1. Test your changes thoroughly
2. Follow existing code style
3. Update documentation
4. Ensure no breaking changes to bot functionality

## 📄 License

This dashboard is part of the Sport-Betting-Bot project. See main repository for license information.

## 🆘 Support

Having issues? 
1. Check the [Troubleshooting](#-troubleshooting) section
2. Review the [API documentation](#-api-endpoints)
3. Check bot logs for errors
4. Open an issue on GitHub

## 🎯 Key Design Principles

1. **Non-invasive**: Reads from bot, never modifies it
2. **Secure by default**: Debug off, backups enabled, credentials protected
3. **User-friendly**: One command to start, intuitive interface
4. **Professional**: Clean design, smooth animations, responsive layout
5. **Extensible**: Easy to add features without breaking existing code

---

**Built with ❤️ for the Sport-Betting-Bot community**

*Dashboard Version 1.0.0 - Production Ready*
