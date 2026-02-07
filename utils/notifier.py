"""
Multi-Channel Notification System for Sports Betting Bot

Provides comprehensive notification support across multiple channels:
- Desktop notifications (cross-platform via plyer)
- Email notifications (SMTP with validation)
- Telegram bot notifications (via HTTP API)
- Sound alerts (platform-specific)

Features:
- Granular enabled flags per channel and event type
- Rate limiting to prevent spam
- Quiet hours support
- Test notification endpoints
- Email validation
- Secure credential handling
"""

import re
import smtplib
import platform
from typing import Dict, Any, Optional, List
from datetime import datetime, time as dt_time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from collections import deque


class Notifier:
    """
    Multi-channel notification system with advanced features
    
    Supports desktop, email, Telegram, and sound notifications with
    granular controls, rate limiting, and quiet hours.
    """
    
    def __init__(self, config: Dict[str, Any], logger=None):
        """
        Initialize notifier
        
        Args:
            config: Configuration dictionary from config.yaml
            logger: Optional logger instance
        """
        self.config = config
        self.logger = logger
        
        # Load notification settings
        notif_config = config.get('notifications', {})
        
        # Desktop notifications
        desktop_config = notif_config.get('desktop', {})
        self.desktop_enabled = desktop_config.get('enabled', False)
        self.desktop_event_types = desktop_config.get('event_types', {})
        
        # Email notifications
        email_config = notif_config.get('email', {})
        self.email_enabled = email_config.get('enabled', False)
        self.email_from = email_config.get('from_email', '')
        self.email_to = email_config.get('to_email', '')
        self.smtp_server = email_config.get('smtp_server', 'smtp.gmail.com')
        self.smtp_port = email_config.get('smtp_port', 587)
        self.email_password = email_config.get('password', '')
        self.email_event_types = email_config.get('event_types', {})
        
        # Telegram notifications
        telegram_config = notif_config.get('telegram', {})
        self.telegram_enabled = telegram_config.get('enabled', False)
        self.telegram_token = telegram_config.get('bot_token', '')
        self.telegram_chat_id = telegram_config.get('chat_id', '')
        self.telegram_event_types = telegram_config.get('event_types', {})
        
        # Sound alerts
        sound_config = notif_config.get('sound', {})
        self.sound_enabled = sound_config.get('enabled', False)
        self.sound_event_types = sound_config.get('event_types', {})
        
        # Rate limiting
        rate_limit_config = notif_config.get('rate_limiting', {})
        self.rate_limiting_enabled = rate_limit_config.get('enabled', True)
        self.max_per_hour = rate_limit_config.get('max_per_hour', 20)
        self.max_per_minute = rate_limit_config.get('max_per_minute', 5)
        self.cooldown_seconds = rate_limit_config.get('cooldown_seconds', 30)
        
        # Quiet hours
        quiet_hours_config = notif_config.get('quiet_hours', {})
        self.quiet_hours_enabled = quiet_hours_config.get('enabled', False)
        self.quiet_start = quiet_hours_config.get('start_time', '23:00')
        self.quiet_end = quiet_hours_config.get('end_time', '07:00')
        
        # Notification history for rate limiting
        self.notification_timestamps = deque(maxlen=100)
        self.last_notification_by_type = {}
        
        # Statistics
        self.notification_count = 0
        self.last_notification = None
        
        # Validate configuration
        self._validate_config()
        
        # Try to import plyer for desktop notifications
        self.plyer_available = False
        if self.desktop_enabled:
            try:
                from plyer import notification
                self.plyer_notification = notification
                self.plyer_available = True
            except ImportError:
                if self.logger:
                    self.logger.warning(
                        "plyer not installed - desktop notifications disabled. "
                        "Install with: pip install plyer"
                    )
        
        if self.logger:
            self.logger.info(
                f"Notifier initialized - "
                f"Desktop: {self.desktop_enabled}, Email: {self.email_enabled}, "
                f"Telegram: {self.telegram_enabled}, Sound: {self.sound_enabled}"
            )
    
    def _validate_config(self):
        """Validate notification configuration"""
        
        # Validate email configuration if enabled
        if self.email_enabled:
            errors = []
            
            # Check required fields
            if not self.email_from:
                errors.append("email.from_email is required")
            elif not self._is_valid_email(self.email_from):
                errors.append(f"email.from_email is invalid: {self.email_from}")
            
            if not self.email_to:
                errors.append("email.to_email is required")
            elif not self._is_valid_email(self.email_to):
                errors.append(f"email.to_email is invalid: {self.email_to}")
            
            if not self.email_password:
                errors.append("email.password is required")
            elif self.email_password == "YOUR_APP_PASSWORD_HERE":
                errors.append("email.password must be replaced with actual password")
            
            if not self.smtp_server:
                errors.append("email.smtp_server is required")
            
            if not isinstance(self.smtp_port, int) or self.smtp_port < 1:
                errors.append("email.smtp_port must be a positive integer")
            
            if errors:
                error_msg = "Email notification configuration errors:\n  - " + "\n  - ".join(errors)
                if self.logger:
                    self.logger.error(error_msg)
                # Disable email if configuration is invalid
                self.email_enabled = False
                if self.logger:
                    self.logger.warning("Email notifications disabled due to configuration errors")
        
        # Validate Telegram configuration if enabled
        if self.telegram_enabled:
            errors = []
            
            if not self.telegram_token:
                errors.append("telegram.bot_token is required")
            elif self.telegram_token == "YOUR_BOT_TOKEN_HERE":
                errors.append("telegram.bot_token must be replaced with actual token")
            
            if not self.telegram_chat_id:
                errors.append("telegram.chat_id is required")
            elif self.telegram_chat_id == "YOUR_CHAT_ID_HERE":
                errors.append("telegram.chat_id must be replaced with actual chat ID")
            
            if errors:
                error_msg = "Telegram notification configuration errors:\n  - " + "\n  - ".join(errors)
                if self.logger:
                    self.logger.error(error_msg)
                # Disable Telegram if configuration is invalid
                self.telegram_enabled = False
                if self.logger:
                    self.logger.warning("Telegram notifications disabled due to configuration errors")
    
    @staticmethod
    def _is_valid_email(email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _is_quiet_hours(self) -> bool:
        """Check if current time is within quiet hours"""
        if not self.quiet_hours_enabled:
            return False
        
        now = datetime.now().time()
        start = datetime.strptime(self.quiet_start, '%H:%M').time()
        end = datetime.strptime(self.quiet_end, '%H:%M').time()
        
        # Handle overnight quiet hours (e.g., 23:00 to 07:00)
        if start <= end:
            return start <= now <= end
        else:
            return now >= start or now <= end
    
    def _check_rate_limit(self, event_type: str) -> bool:
        """
        Check if notification should be rate limited
        
        Args:
            event_type: Type of event (trade, opportunity, error, etc.)
            
        Returns:
            True if notification is allowed, False if rate limited
        """
        if not self.rate_limiting_enabled:
            return True
        
        now = datetime.now()
        
        # Check cooldown for this specific event type
        if event_type in self.last_notification_by_type:
            last_time = self.last_notification_by_type[event_type]
            if (now - last_time).total_seconds() < self.cooldown_seconds:
                return False
        
        # Check per-minute rate limit
        one_minute_ago = datetime.now().timestamp() - 60
        recent_minute = sum(1 for ts in self.notification_timestamps if ts > one_minute_ago)
        if recent_minute >= self.max_per_minute:
            return False
        
        # Check per-hour rate limit
        one_hour_ago = datetime.now().timestamp() - 3600
        recent_hour = sum(1 for ts in self.notification_timestamps if ts > one_hour_ago)
        if recent_hour >= self.max_per_hour:
            return False
        
        return True
    
    def _record_notification(self, event_type: str):
        """Record notification for rate limiting"""
        now = datetime.now()
        self.notification_timestamps.append(now.timestamp())
        self.last_notification_by_type[event_type] = now
        self.notification_count += 1
        self.last_notification = now
    
    def notify(self, title: str, message: str, event_type: str = "info", 
               priority: str = "INFO") -> Dict[str, bool]:
        """
        Send notification through appropriate channels based on event type
        
        Args:
            title: Notification title
            message: Notification message
            event_type: Event type (trade, opportunity, error, summary, status_change)
            priority: Priority level (CRITICAL, WARNING, INFO) - for backward compatibility
            
        Returns:
            Dictionary with success status for each channel
        """
        results = {}
        
        # Check quiet hours
        if self._is_quiet_hours():
            if self.logger:
                self.logger.debug(f"Skipping notification during quiet hours: {title}")
            return results
        
        # Check rate limiting
        if not self._check_rate_limit(event_type):
            if self.logger:
                self.logger.debug(f"Notification rate limited: {title}")
            return results
        
        # Record this notification
        self._record_notification(event_type)
        
        # Send through each enabled channel for this event type
        if self.desktop_enabled and self.desktop_event_types.get(event_type, True):
            results['desktop'] = self.send_desktop_notification(title, message)
        
        if self.email_enabled and self.email_event_types.get(event_type, True):
            results['email'] = self.send_email_notification(title, message)
        
        if self.telegram_enabled and self.telegram_event_types.get(event_type, True):
            results['telegram'] = self.send_telegram_notification(title, message)
        
        if self.sound_enabled and self.sound_event_types.get(event_type, True):
            results['sound'] = self.play_alert_sound(priority)
        
        return results
    
    def send_desktop_notification(self, title: str, message: str) -> bool:
        """
        Send desktop notification via OS notification system
        
        Args:
            title: Notification title
            message: Notification message
            
        Returns:
            True if successful
        """
        if not self.desktop_enabled:
            return False
        
        if not self.plyer_available:
            # Fallback: just print to console
            print(f"\n[NOTIFICATION] {title}\n{message}\n")
            return True
        
        try:
            # Try plyer first
            self.plyer_notification.notify(
                title=title,
                message=message,
                app_name="Sports Betting Bot",
                timeout=10
            )
            return True
        except Exception as e:
            # Fallback to platform-specific methods
            try:
                if platform.system() == 'Darwin':  # macOS
                    import subprocess
                    # Properly escape strings for shell
                    escaped_title = title.replace('"', '\\"').replace('$', '\\$')
                    escaped_message = message.replace('"', '\\"').replace('$', '\\$')
                    subprocess.run([
                        'osascript', '-e',
                        f'display notification "{escaped_message}" with title "{escaped_title}"'
                    ], check=True)
                    return True
                elif platform.system() == 'Linux':
                    import subprocess
                    subprocess.run(['notify-send', title, message], check=True)
                    return True
                elif platform.system() == 'Windows':
                    # Try win10toast as a fallback
                    from win10toast import ToastNotifier
                    toaster = ToastNotifier()
                    toaster.show_toast(title, message, duration=10, threaded=True)
                    return True
            except Exception as fallback_error:
                if self.logger:
                    self.logger.error(f"Desktop notification failed: {fallback_error}")
                return False
        
        return False
    
    def send_email_notification(self, title: str, message: str) -> bool:
        """
        Send email notification via SMTP
        
        Args:
            title: Email subject
            message: Email body
            
        Returns:
            True if successful
        """
        if not self.email_enabled:
            return False
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_from
            msg['To'] = self.email_to
            msg['Subject'] = f"🏈 Sports Betting Bot: {title}"
            
            # Create formatted email body
            body = f"""
Sports Betting Bot Notification
================================

{title}

{message}

--------------------------------
Sent: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Bot: Sports Betting Bot (Paper Trading)
"""
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_from, self.email_password)
            server.send_message(msg)
            server.quit()
            
            if self.logger:
                self.logger.info(f"Email sent: {title}")
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Email notification failed: {str(e)}")
            return False
    
    def send_telegram_notification(self, title: str, message: str) -> bool:
        """
        Send push notification via Telegram
        
        Args:
            title: Notification title
            message: Notification message
        
        Returns:
            True if successful
        """
        if not self.telegram_enabled:
            return False
        
        try:
            import requests
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            payload = {
                'chat_id': self.telegram_chat_id,
                'text': f"🏈 *{title}*\n\n{message}",
                'parse_mode': 'Markdown'
            }
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                if self.logger:
                    self.logger.info(f"Telegram sent: {title}")
                return True
            else:
                if self.logger:
                    self.logger.error(f"Telegram failed: {response.text}")
                return False
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Telegram notification failed: {str(e)}")
            return False
    
    def play_alert_sound(self, priority: str = "INFO") -> bool:
        """
        Play alert sound based on priority
        
        Args:
            priority: Priority level (CRITICAL, WARNING, INFO)
            
        Returns:
            True if successful
        """
        if not self.sound_enabled:
            return False
        
        try:
            if platform.system() == 'Windows':
                import winsound
                if priority == "CRITICAL":
                    # Three urgent beeps
                    for _ in range(3):
                        winsound.Beep(1000, 200)
                elif priority == "WARNING":
                    # Two warning beeps
                    for _ in range(2):
                        winsound.Beep(800, 150)
                else:
                    # Single info beep
                    winsound.Beep(600, 100)
            else:
                # Unix/Linux/Mac - use system bell
                if priority == "CRITICAL":
                    print('\a\a\a', end='', flush=True)
                elif priority == "WARNING":
                    print('\a\a', end='', flush=True)
                else:
                    print('\a', end='', flush=True)
            
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Sound alert failed: {str(e)}")
            return False
    
    # Convenience methods for specific events
    
    def alert_opportunity_found(self, sport: str, game: str, edge_percent: float) -> Dict[str, bool]:
        """Alert when high-value opportunity is found"""
        title = "High Value Opportunity"
        message = f"{sport}: {game}\n{edge_percent:.1f}% edge detected"
        return self.notify(title, message, event_type="opportunity", priority="CRITICAL")
    
    def alert_trade_executed(self, sport: str, game: str, stake: float, expected_profit: float) -> Dict[str, bool]:
        """Alert when trade is executed"""
        title = "Trade Executed"
        message = f"{sport}: {game}\nStake: ${stake:.2f}\nExpected Profit: ${expected_profit:.2f}"
        return self.notify(title, message, event_type="trade", priority="CRITICAL")
    
    def alert_daily_loss_limit(self, current_loss: float, limit: float, percent: float) -> Dict[str, bool]:
        """Alert when approaching daily loss limit"""
        title = "⚠️ Daily Loss Limit Warning"
        message = f"Current Loss: ${current_loss:.2f}\nLimit: ${limit:.2f}\n{percent:.0f}% of limit reached"
        return self.notify(title, message, event_type="error", priority="CRITICAL")
    
    def alert_test_complete(self, duration_days: int, final_roi: float, total_bets: int) -> Dict[str, bool]:
        """Alert when testing period completes"""
        title = "🎉 Testing Period Complete"
        message = f"{duration_days}-day test finished\nROI: {final_roi:.2f}%\nTotal Bets: {total_bets}"
        return self.notify(title, message, event_type="summary", priority="INFO")
    
    def alert_strategy_status_change(self, strategy: str, sport: str, enabled: bool, reason: str) -> Dict[str, bool]:
        """Alert when strategy status changes"""
        status = "ENABLED" if enabled else "DISABLED"
        title = f"Strategy {status}"
        message = f"{strategy} for {sport}\nReason: {reason}"
        return self.notify(title, message, event_type="status_change", priority="WARNING")
    
    def alert_error(self, error_type: str, details: str) -> Dict[str, bool]:
        """Alert when critical error occurs"""
        title = f"⚠️ Error: {error_type}"
        return self.notify(title, details, event_type="error", priority="CRITICAL")
    
    def test_notifications(self) -> Dict[str, bool]:
        """
        Test all notification channels
        
        Returns:
            Dictionary with test results for each channel
        """
        results = {}
        
        # Test desktop
        if self.desktop_enabled:
            results['desktop'] = self.send_desktop_notification(
                "Test Notification",
                "This is a test of the desktop notification system"
            )
        
        # Test email
        if self.email_enabled:
            results['email'] = self.send_email_notification(
                "Test Notification",
                "This is a test of the email notification system"
            )
        
        # Test Telegram
        if self.telegram_enabled:
            results['telegram'] = self.send_telegram_notification(
                "Test Notification",
                "This is a test of the Telegram notification system"
            )
        
        # Test sound
        if self.sound_enabled:
            results['sound'] = self.play_alert_sound("INFO")
        
        if self.logger:
            self.logger.info(f"Notification test results: {results}")
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get notification statistics
        
        Returns:
            Dictionary with notification stats
        """
        return {
            'total_notifications': self.notification_count,
            'last_notification': self.last_notification.isoformat() if self.last_notification else None,
            'channels_enabled': {
                'desktop': self.desktop_enabled,
                'email': self.email_enabled,
                'telegram': self.telegram_enabled,
                'sound': self.sound_enabled
            },
            'rate_limiting': {
                'enabled': self.rate_limiting_enabled,
                'recent_count': len(self.notification_timestamps)
            },
            'quiet_hours': {
                'enabled': self.quiet_hours_enabled,
                'currently_quiet': self._is_quiet_hours()
            }
        }
