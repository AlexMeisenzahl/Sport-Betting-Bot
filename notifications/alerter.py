"""
Bet Alerter
Send desktop notifications for important events

Notification triggers:
- High-value bet found (edge > 10%)
- Arbitrage opportunity detected
- Significant line movement (> 5 cents)
- Daily performance summary
- API rate limit warning
"""

from typing import Dict, Optional
from datetime import datetime
from utils.logger import setup_logger

logger = setup_logger("bet_alerter")


class BetAlerter:
    """
    Send desktop notifications for important events
    """
    
    def __init__(self, config: Dict = None):
        """
        Initialize bet alerter
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.notification_settings = self.config.get('notifications', {})
        self.enabled = self.notification_settings.get('enabled', True)
        
        # Initialize plyer for desktop notifications
        self.notifier = None
        if self.enabled:
            try:
                from plyer import notification
                self.notifier = notification
                logger.info("Desktop notifications enabled")
            except ImportError:
                logger.warning("plyer not installed, desktop notifications disabled")
                self.enabled = False
    
    def notify_opportunity(self, opportunity: Dict):
        """
        Notify about betting opportunity
        
        Args:
            opportunity: Opportunity dictionary
        """
        if not self.enabled or not self.notifier:
            return
        
        strategy = opportunity.get('strategy', 'unknown')
        
        # Check thresholds
        if strategy == 'arbitrage':
            if not self.notification_settings.get('arbitrage_alerts', True):
                return
            
            title = "🎯 Arbitrage Opportunity!"
            message = (f"{opportunity.get('home_team')} vs {opportunity.get('away_team')}\n"
                      f"Profit: {opportunity.get('profit_margin', 0) * 100:.2f}%")
            
        elif strategy == 'value_betting':
            edge = opportunity.get('edge', 0)
            threshold = self.notification_settings.get('high_value_threshold', 0.10)
            
            if edge < threshold:
                return  # Don't notify if below threshold
            
            title = "💰 High Value Bet!"
            message = (f"{opportunity.get('selection')}\n"
                      f"Edge: +{edge * 100:.1f}% @ {opportunity.get('odds')}")
            
        elif strategy == 'line_shopping':
            difference = opportunity.get('difference', 0)
            min_diff = self.notification_settings.get('line_shopping_min_diff', 10)
            
            if difference < min_diff:
                return
            
            title = "📊 Line Shopping Value"
            message = (f"{opportunity.get('selection')}\n"
                      f"{opportunity.get('best_odds')} @ {opportunity.get('best_bookmaker')}")
        else:
            return
        
        try:
            self.notifier.notify(
                title=title,
                message=message,
                app_name="Sports Betting Bot",
                timeout=10
            )
            logger.info(f"Notification sent: {title}")
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
    
    def notify_performance(self, metrics: Dict):
        """
        Send daily performance notification
        
        Args:
            metrics: Performance metrics dictionary
        """
        if not self.enabled or not self.notifier:
            return
        
        if not self.notification_settings.get('daily_summary', True):
            return
        
        title = "📊 Daily Performance Summary"
        
        profit = metrics.get('total_profit', 0)
        roi = metrics.get('roi', 0) * 100
        win_rate = metrics.get('win_rate', 0) * 100
        
        profit_emoji = "📈" if profit > 0 else "📉"
        
        message = (f"{profit_emoji} P&L: ${profit:+,.2f} ({roi:+.1f}%)\n"
                  f"Bets: {metrics.get('total_bets', 0)} "
                  f"({metrics.get('wins', 0)}W-{metrics.get('losses', 0)}L)\n"
                  f"Win Rate: {win_rate:.1f}%")
        
        try:
            self.notifier.notify(
                title=title,
                message=message,
                app_name="Sports Betting Bot",
                timeout=15
            )
            logger.info("Daily performance notification sent")
        except Exception as e:
            logger.error(f"Error sending performance notification: {e}")
    
    def notify_rate_limit_warning(self, remaining: int):
        """
        Notify about API rate limit warning
        
        Args:
            remaining: Number of requests remaining
        """
        if not self.enabled or not self.notifier:
            return
        
        # Only notify if below threshold
        if remaining > 50:
            return
        
        title = "⚠️ API Rate Limit Warning"
        message = f"Only {remaining} API requests remaining this month"
        
        try:
            self.notifier.notify(
                title=title,
                message=message,
                app_name="Sports Betting Bot",
                timeout=10
            )
            logger.warning(f"Rate limit warning sent: {remaining} requests remaining")
        except Exception as e:
            logger.error(f"Error sending rate limit warning: {e}")
    
    def notify_line_movement(self, game: str, old_line: int, new_line: int):
        """
        Notify about significant line movement
        
        Args:
            game: Game description
            old_line: Old odds
            new_line: New odds
        """
        if not self.enabled or not self.notifier:
            return
        
        movement = abs(new_line - old_line)
        min_movement = self.notification_settings.get('line_movement_threshold', 5)
        
        if movement < min_movement:
            return
        
        title = "📊 Significant Line Movement"
        direction = "↗️" if new_line > old_line else "↘️"
        message = f"{game}\n{direction} {old_line} → {new_line} ({movement:+})"
        
        try:
            self.notifier.notify(
                title=title,
                message=message,
                app_name="Sports Betting Bot",
                timeout=10
            )
            logger.info(f"Line movement notification sent for {game}")
        except Exception as e:
            logger.error(f"Error sending line movement notification: {e}")
    
    def notify_bet_settled(self, bet: Dict):
        """
        Notify when a bet is settled
        
        Args:
            bet: Bet dictionary
        """
        if not self.enabled or not self.notifier:
            return
        
        if not self.notification_settings.get('bet_settlement_alerts', False):
            return  # Disabled by default to avoid spam
        
        result = bet.get('result', 'unknown')
        profit = bet.get('profit', 0)
        
        if result == 'win':
            title = "✅ Bet Won!"
            emoji = "💰"
        elif result == 'loss':
            title = "❌ Bet Lost"
            emoji = "📉"
        else:
            title = "⚖️ Bet Pushed"
            emoji = "↔️"
        
        message = f"{emoji} {bet.get('selection', 'Unknown')}\nProfit: ${profit:+,.2f}"
        
        try:
            self.notifier.notify(
                title=title,
                message=message,
                app_name="Sports Betting Bot",
                timeout=5
            )
        except Exception as e:
            logger.error(f"Error sending bet settlement notification: {e}")
    
    def notify_error(self, error_message: str):
        """
        Notify about errors
        
        Args:
            error_message: Error message to display
        """
        if not self.enabled or not self.notifier:
            return
        
        if not self.notification_settings.get('error_alerts', True):
            return
        
        title = "⚠️ Bot Error"
        message = error_message[:200]  # Limit length
        
        try:
            self.notifier.notify(
                title=title,
                message=message,
                app_name="Sports Betting Bot",
                timeout=10
            )
            logger.info("Error notification sent")
        except Exception as e:
            logger.error(f"Error sending error notification: {e}")
    
    def test_notification(self):
        """Send a test notification"""
        if not self.enabled or not self.notifier:
            logger.error("Notifications are not enabled")
            return False
        
        try:
            self.notifier.notify(
                title="🧪 Test Notification",
                message="Desktop notifications are working correctly!",
                app_name="Sports Betting Bot",
                timeout=5
            )
            logger.info("Test notification sent successfully")
            return True
        except Exception as e:
            logger.error(f"Test notification failed: {e}")
            return False
