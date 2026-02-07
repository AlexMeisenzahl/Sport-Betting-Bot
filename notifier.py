"""
Multi-channel notification system for betting opportunities
Supports desktop notifications, Telegram, and email alerts
"""

import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class Notifier:
    """
    Handles multi-channel notifications for betting opportunities
    
    Supports:
    - Desktop notifications (cross-platform)
    - Telegram bot notifications
    - Email alerts
    """
    
    def __init__(self, config):
        """
        Initialize the notifier with configuration
        
        Args:
            config: ConfigLoader instance with notification settings
        """
        self.config = config
        self.desktop_enabled = config.get('desktop_notifications', 'enabled', default=True)
        self.telegram_enabled = config.get('telegram', 'enabled', default=False)
        self.email_enabled = config.get('email', 'enabled', default=False)
        self.alert_on_opportunities = config.get('alert_on_opportunities', default=True)
        
        # Initialize notification channels
        self._init_desktop()
        self._init_telegram()
        self._init_email()
        
        logger.info(f"Notifier initialized - Desktop: {self.desktop_enabled}, "
                   f"Telegram: {self.telegram_enabled}, Email: {self.email_enabled}")
    
    def _init_desktop(self):
        """Initialize desktop notification system"""
        if not self.desktop_enabled:
            return
        
        try:
            # Try to import plyer for cross-platform notifications
            from plyer import notification as plyer_notification
            self.plyer_notification = plyer_notification
            self.desktop_available = True
            logger.info("Desktop notifications available (plyer)")
        except ImportError:
            # Fallback: try to use platform-specific methods
            try:
                import platform
                system = platform.system()
                
                if system == "Darwin":  # macOS
                    self.desktop_method = "osascript"
                    self.desktop_available = True
                    logger.info("Desktop notifications available (macOS osascript)")
                elif system == "Linux":
                    # Check if notify-send is available
                    import subprocess
                    result = subprocess.run(['which', 'notify-send'], 
                                          capture_output=True, text=True)
                    if result.returncode == 0:
                        self.desktop_method = "notify-send"
                        self.desktop_available = True
                        logger.info("Desktop notifications available (Linux notify-send)")
                    else:
                        self.desktop_available = False
                        logger.warning("notify-send not found on Linux")
                elif system == "Windows":
                    # Try Windows toast notifications
                    try:
                        from win10toast import ToastNotifier
                        self.toast_notifier = ToastNotifier()
                        self.desktop_method = "win10toast"
                        self.desktop_available = True
                        logger.info("Desktop notifications available (Windows)")
                    except ImportError:
                        self.desktop_available = False
                        logger.warning("win10toast not available on Windows")
                else:
                    self.desktop_available = False
                    logger.warning(f"Desktop notifications not supported on {system}")
            except Exception as e:
                self.desktop_available = False
                logger.warning(f"Could not initialize desktop notifications: {e}")
    
    def _init_telegram(self):
        """Initialize Telegram bot"""
        if not self.telegram_enabled:
            return
        
        try:
            self.telegram_token = self.config.get('telegram', 'bot_token', default='')
            self.telegram_chat_id = self.config.get('telegram', 'chat_id', default='')
            
            if self.telegram_token and self.telegram_chat_id:
                import requests
                self.telegram_available = True
                logger.info("Telegram notifications configured")
            else:
                self.telegram_available = False
                logger.warning("Telegram enabled but token/chat_id not configured")
        except Exception as e:
            self.telegram_available = False
            logger.warning(f"Could not initialize Telegram: {e}")
    
    def _init_email(self):
        """Initialize email notifications"""
        if not self.email_enabled:
            return
        
        try:
            self.email_from = self.config.get('email', 'from_email', default='')
            self.email_to = self.config.get('email', 'to_email', default='')
            self.email_smtp_server = self.config.get('email', 'smtp_server', default='smtp.gmail.com')
            self.email_smtp_port = self.config.get('email', 'smtp_port', default=587)
            self.email_password = self.config.get('email', 'password', default='')
            
            if self.email_from and self.email_to and self.email_password:
                self.email_available = True
                logger.info("Email notifications configured")
            else:
                self.email_available = False
                logger.warning("Email enabled but credentials not fully configured")
        except Exception as e:
            self.email_available = False
            logger.warning(f"Could not initialize email: {e}")
    
    def alert_opportunity_found(self, market_name: str, profit_margin: float):
        """
        Send alert when an arbitrage opportunity is found
        
        Args:
            market_name: Name of the market/game
            profit_margin: Profit margin as a percentage (e.g., 2.3 for 2.3%)
        """
        if not self.alert_on_opportunities:
            return
        
        title = "💰 Arbitrage Opportunity Found!"
        message = f"{market_name}\nProfit: {profit_margin:.2f}%"
        
        # Send notifications to all enabled channels
        self._send_desktop(title, message)
        self._send_telegram(title, message)
        self._send_email(title, message)
    
    def alert_high_value(self, opportunity_type: str, details: str, edge_percent: float):
        """
        Send alert for high-value opportunities
        
        Args:
            opportunity_type: Type of opportunity (e.g., "CLV", "Sharp Signal")
            details: Details about the opportunity
            edge_percent: Expected edge in percentage
        """
        if not self.alert_on_opportunities:
            return
        
        title = f"🎯 High Value {opportunity_type}!"
        message = f"{details}\nEdge: {edge_percent:.1f}%"
        
        self._send_desktop(title, message)
        self._send_telegram(title, message)
        self._send_email(title, message)
    
    def alert_warning(self, warning_type: str, message: str):
        """
        Send warning alert
        
        Args:
            warning_type: Type of warning
            message: Warning message
        """
        title = f"⚠️ Warning: {warning_type}"
        
        self._send_desktop(title, message)
        self._send_telegram(title, message)
        self._send_email(title, message)
    
    def _send_desktop(self, title: str, message: str):
        """Send desktop notification"""
        if not self.desktop_enabled or not self.desktop_available:
            return
        
        try:
            if hasattr(self, 'plyer_notification'):
                # Use plyer for cross-platform support
                self.plyer_notification.notify(
                    title=title,
                    message=message,
                    app_name='Sports Betting Bot',
                    timeout=10
                )
            elif hasattr(self, 'desktop_method'):
                if self.desktop_method == "osascript":
                    # macOS notification - properly escape strings to prevent injection
                    import subprocess
                    # Use list form to avoid shell injection
                    script = f'display notification "{message}" with title "{title}"'
                    # Escape quotes in the strings
                    safe_message = message.replace('"', '\\"').replace('$', '\\$')
                    safe_title = title.replace('"', '\\"').replace('$', '\\$')
                    script = f'display notification "{safe_message}" with title "{safe_title}"'
                    subprocess.run(['osascript', '-e', script], check=False)
                elif self.desktop_method == "notify-send":
                    # Linux notification - use list arguments to avoid shell injection
                    import subprocess
                    subprocess.run(['notify-send', title, message], check=False)
                elif self.desktop_method == "win10toast":
                    # Windows notification
                    self.toast_notifier.show_toast(title, message, duration=10)
            
            logger.debug(f"Desktop notification sent: {title}")
        except Exception as e:
            logger.debug(f"Failed to send desktop notification: {e}")
    
    def _send_telegram(self, title: str, message: str):
        """Send Telegram notification"""
        if not self.telegram_enabled or not self.telegram_available:
            return
        
        try:
            import requests
            
            full_message = f"<b>{title}</b>\n{message}"
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            
            payload = {
                'chat_id': self.telegram_chat_id,
                'text': full_message,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, data=payload, timeout=5)
            
            if response.status_code == 200:
                logger.debug(f"Telegram notification sent: {title}")
            else:
                logger.debug(f"Telegram notification failed: {response.status_code} - {response.text}")
        except Exception as e:
            logger.debug(f"Failed to send Telegram notification: {e}")
    
    def _send_email(self, title: str, message: str):
        """Send email notification"""
        if not self.email_enabled or not self.email_available:
            return
        
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            msg = MIMEMultipart()
            msg['From'] = self.email_from
            msg['To'] = self.email_to
            msg['Subject'] = title
            
            body = f"{message}\n\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP(self.email_smtp_server, self.email_smtp_port) as server:
                server.starttls()
                server.login(self.email_from, self.email_password)
                server.send_message(msg)
            
            logger.debug(f"Email notification sent: {title}")
        except Exception as e:
            logger.debug(f"Failed to send email notification: {e}")
