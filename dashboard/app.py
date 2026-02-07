"""
Professional Sports Betting Alerts Dashboard

A clean, modern web interface for viewing and managing betting alerts
from the Sport-Betting-Bot.
"""

import os
import sys
from pathlib import Path
from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_cors import CORS

# Add parent directory to path to import from utils
sys.path.insert(0, str(Path(__file__).parent.parent))

from dashboard.services.alerts_parser import AlertsParser
from dashboard.services.analytics import Analytics
from dashboard.services.config_manager import ConfigManager
from utils.notifier import Notifier
from utils.logger import setup_logger

# Initialize logger
logger = setup_logger("dashboard", level=20)  # INFO level

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
app.config['DEBUG'] = False  # Security: Debug disabled by default

# Enable CORS for API endpoints
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Initialize services
alerts_parser = AlertsParser(log_dir=".")
analytics = Analytics(alerts_parser)
config_manager = ConfigManager(config_path="config.yaml")

logger.info("Dashboard services initialized")


# ============================================================================
# WEB ROUTES
# ============================================================================

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')


@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    return send_from_directory('static', filename)


# ============================================================================
# API ENDPOINTS - ALERTS
# ============================================================================

@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    """
    Get filtered alerts
    
    Query parameters:
        - sport: Filter by sport
        - league: Filter by league
        - min_confidence: Minimum confidence (0-100)
        - time_range: Hours to look back
        - status: Alert status (new, viewed, dismissed)
        - limit: Max results (default 100)
    """
    try:
        sport = request.args.get('sport')
        league = request.args.get('league')
        min_confidence = request.args.get('min_confidence', type=float)
        time_range = request.args.get('time_range', type=int)
        status = request.args.get('status')
        limit = request.args.get('limit', 100, type=int)
        
        alerts = alerts_parser.get_alerts(
            sport=sport,
            league=league,
            min_confidence=min_confidence,
            time_range=time_range,
            status=status,
            limit=limit
        )
        
        return jsonify({
            'success': True,
            'alerts': alerts,
            'count': len(alerts)
        })
    
    except Exception as e:
        logger.error(f"Error fetching alerts: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/alerts/history', methods=['GET'])
def get_alert_history():
    """
    Get paginated alert history
    
    Query parameters:
        - page: Page number (default 1)
        - per_page: Items per page (default 25)
        - sport: Filter by sport
        - start_date: Start date (ISO format)
        - end_date: End date (ISO format)
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 25, type=int)
        sport = request.args.get('sport')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        result = alerts_parser.get_alert_history(
            page=page,
            per_page=per_page,
            sport=sport,
            start_date=start_date,
            end_date=end_date
        )
        
        return jsonify({
            'success': True,
            **result
        })
    
    except Exception as e:
        logger.error(f"Error fetching alert history: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/alerts/<int:alert_id>/action', methods=['POST'])
def alert_action(alert_id):
    """
    Perform action on alert
    
    Body:
        - action: 'mark_read', 'dismiss', 'favorite'
    """
    try:
        data = request.get_json()
        action = data.get('action')
        
        if action not in ['mark_read', 'dismiss', 'favorite']:
            return jsonify({
                'success': False,
                'error': 'Invalid action'
            }), 400
        
        # TODO: Implement alert state management
        # For now, just acknowledge the action
        
        return jsonify({
            'success': True,
            'message': f'Alert {alert_id} {action} successfully'
        })
    
    except Exception as e:
        logger.error(f"Error performing alert action: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# API ENDPOINTS - ANALYTICS
# ============================================================================

@app.route('/api/analytics/overview', methods=['GET'])
def get_analytics_overview():
    """Get dashboard overview statistics"""
    try:
        stats = analytics.get_overview_stats()
        
        return jsonify({
            'success': True,
            'stats': stats
        })
    
    except Exception as e:
        logger.error(f"Error fetching overview stats: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/analytics/charts', methods=['GET'])
def get_chart_data():
    """Get data for dashboard charts"""
    try:
        chart_data = analytics.get_chart_data()
        
        return jsonify({
            'success': True,
            'data': chart_data
        })
    
    except Exception as e:
        logger.error(f"Error fetching chart data: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/analytics/summary', methods=['GET'])
def get_alert_summary():
    """
    Get alert summary statistics
    
    Query parameters:
        - start_date: Start date (ISO format)
        - end_date: End date (ISO format)
    """
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        summary = analytics.get_alert_summary(
            start_date=start_date,
            end_date=end_date
        )
        
        return jsonify({
            'success': True,
            'summary': summary
        })
    
    except Exception as e:
        logger.error(f"Error fetching summary: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# API ENDPOINTS - SETTINGS
# ============================================================================

@app.route('/api/settings', methods=['GET'])
def get_settings():
    """Get current bot settings"""
    try:
        config = config_manager.get_config()
        
        return jsonify({
            'success': True,
            'settings': config
        })
    
    except Exception as e:
        logger.error(f"Error fetching settings: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/settings', methods=['PUT'])
def update_settings():
    """
    Update bot settings
    
    Body: Settings dictionary to update
    """
    try:
        updates = request.get_json()
        
        if not updates:
            return jsonify({
                'success': False,
                'error': 'No updates provided'
            }), 400
        
        # Update config with automatic backup
        updated_config = config_manager.update_config(updates, backup=True)
        
        return jsonify({
            'success': True,
            'message': 'Settings updated successfully',
            'settings': updated_config
        })
    
    except Exception as e:
        logger.error(f"Error updating settings: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/settings/notification', methods=['GET'])
def get_notification_settings():
    """Get notification settings"""
    try:
        settings = config_manager.get_notification_settings()
        
        return jsonify({
            'success': True,
            'settings': settings
        })
    
    except Exception as e:
        logger.error(f"Error fetching notification settings: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/settings/notification', methods=['PUT'])
def update_notification_settings():
    """Update notification settings"""
    try:
        settings = request.get_json()
        
        if not settings:
            return jsonify({
                'success': False,
                'error': 'No settings provided'
            }), 400
        
        updated_settings = config_manager.update_notification_settings(settings)
        
        return jsonify({
            'success': True,
            'message': 'Notification settings updated successfully',
            'settings': updated_settings
        })
    
    except Exception as e:
        logger.error(f"Error updating notification settings: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# API ENDPOINTS - NOTIFICATIONS
# ============================================================================

@app.route('/api/notifications/test', methods=['POST'])
def test_notifications():
    """
    Test notification channels
    
    Body:
        - channel: 'desktop', 'email', 'telegram', or 'all'
    """
    try:
        data = request.get_json()
        channel = data.get('channel', 'all')
        
        # Get config and initialize notifier
        config = config_manager.get_config()
        notifier = Notifier(config, logger)
        
        # Test the specified channel
        if channel == 'all':
            notifier.test_notifications()
            message = 'Test notifications sent to all enabled channels'
        elif channel == 'desktop':
            notifier.send_desktop_notification('Test', 'Dashboard test notification')
            message = 'Test desktop notification sent'
        elif channel == 'email':
            notifier.send_email_notification(
                'Dashboard Test',
                'This is a test email from the Sports Betting Dashboard'
            )
            message = 'Test email sent'
        elif channel == 'telegram':
            notifier.send_telegram_notification('🧪 Dashboard test notification')
            message = 'Test Telegram notification sent'
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid channel'
            }), 400
        
        return jsonify({
            'success': True,
            'message': message
        })
    
    except Exception as e:
        logger.error(f"Error testing notifications: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# API ENDPOINTS - METADATA
# ============================================================================

@app.route('/api/metadata/sports', methods=['GET'])
def get_sports():
    """Get list of available sports"""
    try:
        sports = alerts_parser.get_sports_list()
        
        return jsonify({
            'success': True,
            'sports': sports
        })
    
    except Exception as e:
        logger.error(f"Error fetching sports: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/metadata/leagues', methods=['GET'])
def get_leagues():
    """Get list of available leagues"""
    try:
        leagues = alerts_parser.get_leagues_list()
        
        return jsonify({
            'success': True,
            'leagues': leagues
        })
    
    except Exception as e:
        logger.error(f"Error fetching leagues: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# ENHANCED API ENDPOINTS - TRADING DATA
# ============================================================================

@app.route('/api/overview', methods=['GET'])
def get_dashboard_overview():
    """
    Get comprehensive dashboard overview with live data
    
    Returns:
        - Current bankroll and P&L
        - Active bets count
        - Today's performance
        - Strategy breakdown
        - Recent opportunities
    """
    try:
        # This would connect to the running bot instance in production
        # For now, return mock data structure
        overview = {
            'bankroll': {
                'current': 0,
                'starting': 500,
                'profit_loss': 0,
                'roi_percent': 0
            },
            'stats': {
                'total_bets': 0,
                'wins': 0,
                'losses': 0,
                'pending': 0,
                'win_rate': 0
            },
            'today': {
                'bets_placed': 0,
                'profit_loss': 0,
                'opportunities_found': 0
            },
            'strategies': [],
            'recent_opportunities': []
        }
        
        return jsonify({
            'success': True,
            'overview': overview
        })
    
    except Exception as e:
        logger.error(f"Error fetching dashboard overview: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/charts/pnl', methods=['GET'])
def get_pnl_chart_data():
    """
    Get cumulative P&L chart data
    
    Query parameters:
        - period: '7d', '30d', '90d', 'all' (default: '30d')
    """
    try:
        period = request.args.get('period', '30d')
        
        # Mock chart data structure
        chart_data = {
            'labels': [],  # Dates
            'datasets': [{
                'label': 'Cumulative P&L',
                'data': [],  # P&L values
                'borderColor': 'rgb(75, 192, 192)',
                'tension': 0.1
            }]
        }
        
        return jsonify({
            'success': True,
            'data': chart_data
        })
    
    except Exception as e:
        logger.error(f"Error fetching P&L chart data: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/charts/strategy', methods=['GET'])
def get_strategy_chart_data():
    """
    Get strategy performance comparison chart data
    
    Returns:
        Bar chart data comparing ROI across strategies
    """
    try:
        chart_data = {
            'labels': [],  # Strategy names
            'datasets': [{
                'label': 'ROI %',
                'data': [],  # ROI percentages
                'backgroundColor': [
                    'rgba(255, 99, 132, 0.5)',
                    'rgba(54, 162, 235, 0.5)',
                    'rgba(255, 206, 86, 0.5)',
                    'rgba(75, 192, 192, 0.5)',
                    'rgba(153, 102, 255, 0.5)',
                ]
            }]
        }
        
        return jsonify({
            'success': True,
            'data': chart_data
        })
    
    except Exception as e:
        logger.error(f"Error fetching strategy chart data: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/trades/history', methods=['GET'])
def get_trades_history():
    """
    Get paginated trade history
    
    Query parameters:
        - page: Page number (default 1)
        - per_page: Items per page (default 25, max 100)
        - status: Filter by status ('pending', 'won', 'lost', 'all')
        - strategy: Filter by strategy name
        - sport: Filter by sport
        - start_date: Filter start date (ISO format)
        - end_date: Filter end date (ISO format)
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 25, type=int), 100)
        status = request.args.get('status', 'all')
        strategy = request.args.get('strategy')
        sport = request.args.get('sport')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Mock trade history structure
        trades = {
            'items': [],
            'total': 0,
            'page': page,
            'per_page': per_page,
            'pages': 0
        }
        
        return jsonify({
            'success': True,
            'trades': trades
        })
    
    except Exception as e:
        logger.error(f"Error fetching trade history: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/export/trades', methods=['GET'])
def export_trades_csv():
    """
    Export trade history as CSV file
    
    Query parameters:
        - status: Filter by status
        - strategy: Filter by strategy
        - sport: Filter by sport
        - start_date: Filter start date
        - end_date: Filter end date
    """
    try:
        from flask import Response
        import io
        import csv
        
        # Get filter parameters
        status = request.args.get('status', 'all')
        strategy = request.args.get('strategy')
        sport = request.args.get('sport')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Mock CSV data
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Date', 'Sport', 'Game', 'Strategy', 'Bet Type', 
            'Side', 'Stake', 'Odds', 'Result', 'Profit/Loss'
        ])
        
        # In production, would fetch actual trade data and write rows
        # writer.writerow([...])
        
        # Create response
        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={
                'Content-Disposition': 'attachment; filename=trades_export.csv'
            }
        )
    
    except Exception as e:
        logger.error(f"Error exporting trades: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/bot/status', methods=['GET'])
def get_bot_status():
    """
    Get current bot status
    
    Returns:
        - Running status
        - Uptime
        - API connection status
        - Last update time
    """
    try:
        status = {
            'running': False,
            'uptime_seconds': 0,
            'api_connections': {
                'odds_api': {
                    'connected': False,
                    'mode': 'mock',
                    'requests_remaining': 500
                },
                'espn_api': {
                    'connected': False,
                    'mode': 'mock'
                }
            },
            'last_update': None
        }
        
        return jsonify({
            'success': True,
            'status': status
        })
    
    except Exception as e:
        logger.error(f"Error fetching bot status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'success': False,
        'error': 'Not found'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {error}")
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '127.0.0.1')
    
    logger.info(f"Starting Sports Betting Dashboard on {host}:{port}")
    logger.info(f"Access dashboard at: http://{host}:{port}")
    
    app.run(host=host, port=port, debug=False)
