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
