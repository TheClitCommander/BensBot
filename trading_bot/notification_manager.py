"""
Notification Manager

Provides a comprehensive notification system for trading alerts and system status updates.
Supports desktop notifications, email alerts, and Slack messaging.
"""

import os
import json
import logging
import time
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, Any, List, Optional, Union

# Try to import optional dependencies
# Desktop notifications
try:
    from plyer import notification as desktop_notification
    DESKTOP_AVAILABLE = True
except ImportError:
    DESKTOP_AVAILABLE = False

# Slack integration
try:
    from slack_sdk import WebClient
    from slack_sdk.errors import SlackApiError
    SLACK_AVAILABLE = True
except ImportError:
    SLACK_AVAILABLE = False

class NotificationManager:
    """
    Manages notifications across multiple channels (desktop, email, Slack)
    
    This class provides a unified interface for sending notifications about
    trading events, alerts, and system status through various channels.
    """
    
    # Notification levels and corresponding colors
    LEVELS = {
        "INFO": {"color": "#36a64f", "emoji": "ℹ️", "importance": 0},
        "SUCCESS": {"color": "#2eb886", "emoji": "✅", "importance": 1},
        "WARNING": {"color": "#daa038", "emoji": "⚠️", "importance": 2},
        "ERROR": {"color": "#cc0000", "emoji": "❌", "importance": 3},
        "CRITICAL": {"color": "#ff0000", "emoji": "🚨", "importance": 4}
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the notification manager with configuration.
        
        Args:
            config_path: Path to configuration file (JSON format)
        """
        self.logger = logging.getLogger("NotificationManager")
        self.logger.setLevel(logging.INFO)
        
        # Default configuration
        self.config = {
            "enabled": True,
            "min_level": "INFO",
            "rate_limit": {
                "enabled": True,
                "max_notifications": 10,  # Max notifications per time window
                "time_window": 60,       # Time window in seconds
                "cooldown": 300          # Cooldown period after rate limit is hit
            },
            "desktop": {
                "enabled": DESKTOP_AVAILABLE,
                "timeout": 10            # Notification timeout in seconds
            },
            "email": {
                "enabled": False,
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "sender_email": "",
                "sender_password": "",
                "recipients": [],
                "min_level": "WARNING"   # Only send emails for warnings or higher
            },
            "slack": {
                "enabled": SLACK_AVAILABLE,
                "token": "",
                "channel": "#trading-alerts",
                "username": "Trading Bot",
                "min_level": "INFO"
            }
        }
        
        # Load configuration if provided
        if config_path:
            self._load_config(config_path)
        
        # Initialize notification history and rate limiting
        self.notification_history = []
        self.rate_limit_active = False
        self.rate_limit_start_time = 0
        
        # Initialize Slack client if available and enabled
        self.slack_client = None
        if SLACK_AVAILABLE and self.config["slack"]["enabled"] and self.config["slack"]["token"]:
            try:
                self.slack_client = WebClient(token=self.config["slack"]["token"])
                self.logger.info("Slack integration initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize Slack client: {e}")
        
        self.logger.info("Notification Manager initialized")
    
    def _load_config(self, config_path: str) -> None:
        """
        Load configuration from a JSON file.
        
        Args:
            config_path: Path to the configuration file
        """
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                
                # Update configuration with user settings
                self._update_nested_dict(self.config, user_config)
                self.logger.info(f"Loaded configuration from {config_path}")
            else:
                self.logger.warning(f"Configuration file not found at {config_path}, using defaults")
        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")
    
    def _update_nested_dict(self, d: Dict, u: Dict) -> Dict:
        """
        Recursively update a nested dictionary.
        
        Args:
            d: Base dictionary to update
            u: Dictionary with updates
            
        Returns:
            Updated dictionary
        """
        for k, v in u.items():
            if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                d[k] = self._update_nested_dict(d[k], v)
            else:
                d[k] = v
        return d
    
    def send_notification(self, 
                         title: str, 
                         message: str, 
                         level: str = "INFO", 
                         channels: List[str] = None,
                         metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Send a notification through specified channels.
        
        Args:
            title: Notification title
            message: Notification body
            level: Notification importance level (INFO, SUCCESS, WARNING, ERROR, CRITICAL)
            channels: List of channels to use (desktop, email, slack) or None for all
            metadata: Additional metadata to include with the notification
            
        Returns:
            Dictionary with notification result
        """
        # Standardize level
        level = level.upper()
        if level not in self.LEVELS:
            level = "INFO"
        
        # Check if notifications are enabled
        if not self.config["enabled"]:
            return {"success": False, "message": "Notifications are disabled"}
        
        # Check minimum notification level
        if self.LEVELS[level]["importance"] < self.LEVELS[self.config["min_level"]]["importance"]:
            return {"success": False, "message": f"Notification level {level} below minimum threshold"}
        
        # Check rate limiting
        if not self._check_rate_limiting():
            return {"success": False, "message": "Rate limit exceeded, notification suppressed"}
        
        # Default to all channels if none specified
        if not channels:
            channels = ["desktop", "email", "slack"]
        
        # Create notification record
        notification = {
            "id": self._generate_id(),
            "timestamp": datetime.now().isoformat(),
            "title": title,
            "message": message,
            "level": level,
            "emoji": self.LEVELS[level]["emoji"],
            "metadata": metadata or {},
            "results": {}
        }
        
        # Send through each channel
        for channel in channels:
            if channel == "desktop" and self.config["desktop"]["enabled"]:
                notification["results"]["desktop"] = self._send_desktop(title, message, level)
            
            elif channel == "email" and self.config["email"]["enabled"]:
                # Only send email if level meets threshold
                if self.LEVELS[level]["importance"] >= self.LEVELS[self.config["email"]["min_level"]]["importance"]:
                    notification["results"]["email"] = self._send_email(title, message, level)
                else:
                    notification["results"]["email"] = {"success": False, "message": "Level below email threshold"}
            
            elif channel == "slack" and self.config["slack"]["enabled"] and self.slack_client:
                # Only send slack if level meets threshold
                if self.LEVELS[level]["importance"] >= self.LEVELS[self.config["slack"]["min_level"]]["importance"]:
                    notification["results"]["slack"] = self._send_slack(title, message, level, metadata)
                else:
                    notification["results"]["slack"] = {"success": False, "message": "Level below slack threshold"}
        
        # Record notification
        self.notification_history.append(notification)
        if len(self.notification_history) > 100:
            self.notification_history = self.notification_history[-100:]
        
        # Log notification
        self.logger.info(f"Sent {level} notification: {title}")
        
        return {
            "success": any(result.get("success", False) for result in notification["results"].values()),
            "notification_id": notification["id"],
            "results": notification["results"]
        }
    
    def _generate_id(self) -> str:
        """Generate a unique notification ID."""
        import uuid
        return str(uuid.uuid4())
    
    def _check_rate_limiting(self) -> bool:
        """
        Check if notification should be suppressed due to rate limiting.
        
        Returns:
            True if notification can be sent, False if rate limited
        """
        # If rate limiting is disabled, always allow
        if not self.config["rate_limit"]["enabled"]:
            return True
        
        current_time = time.time()
        
        # If in cooldown period, suppress notification
        if self.rate_limit_active:
            if current_time - self.rate_limit_start_time > self.config["rate_limit"]["cooldown"]:
                # Cooldown period over
                self.rate_limit_active = False
                self.logger.info("Notification rate limit cooldown period ended")
                # Reset the history when cooldown ends
                self.notification_history = []
            else:
                # Still in cooldown, suppress notification
                return False
        
        # Count recent notifications in time window
        recent_count = sum(1 for n in self.notification_history 
                         if current_time - datetime.fromisoformat(n["timestamp"]).timestamp() < 
                         self.config["rate_limit"]["time_window"])
        
        # Check if rate limit exceeded
        if recent_count >= self.config["rate_limit"]["max_notifications"]:
            self.rate_limit_active = True
            self.rate_limit_start_time = current_time
            self.logger.warning(f"Notification rate limit exceeded ({recent_count} in {self.config['rate_limit']['time_window']}s). "
                              f"Entering cooldown for {self.config['rate_limit']['cooldown']}s")
            return False
        
        return True
    
    def _send_desktop(self, title: str, message: str, level: str) -> Dict[str, Any]:
        """
        Send a desktop notification.
        
        Args:
            title: Notification title
            message: Notification message
            level: Notification level
            
        Returns:
            Dictionary with result
        """
        if not DESKTOP_AVAILABLE:
            return {"success": False, "message": "Desktop notifications not available"}
        
        try:
            # Create a level-prefixed title
            prefixed_title = f"{self.LEVELS[level]['emoji']} {title}"
            
            # Send notification
            desktop_notification.notify(
                title=prefixed_title,
                message=message,
                app_name="Trading Bot",
                timeout=self.config["desktop"]["timeout"]
            )
            return {"success": True, "message": "Desktop notification sent"}
        except Exception as e:
            self.logger.error(f"Failed to send desktop notification: {e}")
            return {"success": False, "message": str(e)}
    
    def _send_email(self, title: str, message: str, level: str) -> Dict[str, Any]:
        """
        Send an email notification.
        
        Args:
            title: Email subject
            message: Email body
            level: Notification level
            
        Returns:
            Dictionary with result
        """
        email_config = self.config["email"]
        
        if not email_config["sender_email"] or not email_config["sender_password"] or not email_config["recipients"]:
            return {"success": False, "message": "Email configuration incomplete"}
        
        try:
            # Create a multipart message
            msg = MIMEMultipart()
            msg["Subject"] = f"{self.LEVELS[level]['emoji']} {title}"
            msg["From"] = email_config["sender_email"]
            msg["To"] = ", ".join(email_config["recipients"])
            
            # Format the body with HTML
            html = f"""
            <html>
              <body>
                <h2>{title}</h2>
                <p style="white-space: pre-wrap;">{message}</p>
                <p style="color: #666; font-size: 0.8em;">
                  Sent by Trading Bot at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                </p>
              </body>
            </html>
            """
            msg.attach(MIMEText(html, "html"))
            
            # Connect to the server
            context = ssl.create_default_context()
            with smtplib.SMTP(email_config["smtp_server"], email_config["smtp_port"]) as server:
                server.starttls(context=context)
                server.login(email_config["sender_email"], email_config["sender_password"])
                server.send_message(msg)
            
            self.logger.info(f"Email notification sent to {len(email_config['recipients'])} recipients")
            return {"success": True, "message": f"Email sent to {len(email_config['recipients'])} recipients"}
        
        except Exception as e:
            self.logger.error(f"Failed to send email notification: {e}")
            return {"success": False, "message": str(e)}
    
    def _send_slack(self, title: str, message: str, level: str, 
                   metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Send a Slack notification.
        
        Args:
            title: Message title
            message: Message body
            level: Notification level
            metadata: Additional metadata for enhanced messages
            
        Returns:
            Dictionary with result
        """
        if not SLACK_AVAILABLE:
            return {"success": False, "message": "Slack SDK not available"}
        
        if not self.slack_client:
            return {"success": False, "message": "Slack client not initialized"}
        
        try:
            slack_config = self.config["slack"]
            color = self.LEVELS[level]["color"]
            
            # Build attachments for rich formatting
            attachments = [
                {
                    "color": color,
                    "title": f"{self.LEVELS[level]['emoji']} {title}",
                    "text": message,
                    "footer": f"Trading Bot • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    "mrkdwn_in": ["text"]
                }
            ]
            
            # Add fields from metadata if provided
            if metadata and isinstance(metadata, dict):
                fields = []
                for key, value in metadata.items():
                    if isinstance(value, (str, int, float, bool)):
                        fields.append({
                            "title": key,
                            "value": str(value),
                            "short": len(str(value)) < 20  # Short field if value is short
                        })
                
                if fields:
                    attachments[0]["fields"] = fields
            
            # Send the message
            response = self.slack_client.chat_postMessage(
                channel=slack_config["channel"],
                text=f"{self.LEVELS[level]['emoji']} {title}",  # Fallback text
                attachments=attachments,
                username=slack_config.get("username", "Trading Bot")
            )
            
            return {
                "success": True, 
                "message": "Slack notification sent",
                "timestamp": response["ts"],
                "channel": response["channel"]
            }
            
        except SlackApiError as e:
            self.logger.error(f"Failed to send Slack notification: {e.response['error']}")
            return {"success": False, "message": e.response["error"]}
        except Exception as e:
            self.logger.error(f"Failed to send Slack notification: {e}")
            return {"success": False, "message": str(e)}
    
    def get_notification_history(self, limit: int = 10, 
                                min_level: str = None) -> List[Dict[str, Any]]:
        """
        Get recent notification history.
        
        Args:
            limit: Maximum number of notifications to return
            min_level: Minimum level to include
            
        Returns:
            List of recent notifications
        """
        if not min_level:
            filtered = self.notification_history
        else:
            min_importance = self.LEVELS.get(min_level.upper(), {"importance": 0})["importance"]
            filtered = [n for n in self.notification_history 
                       if self.LEVELS[n["level"]]["importance"] >= min_importance]
        
        # Return most recent notifications first
        return sorted(filtered, key=lambda x: x["timestamp"], reverse=True)[:limit]
    
    def is_rate_limited(self) -> bool:
        """Check if notifications are currently rate limited."""
        return self.rate_limit_active
    
    def get_config(self) -> Dict[str, Any]:
        """Get current configuration."""
        return self.config
    
    def update_config(self, new_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update configuration with new settings.
        
        Args:
            new_config: Dictionary with new configuration values
            
        Returns:
            Updated configuration
        """
        self._update_nested_dict(self.config, new_config)
        self.logger.info("Notification configuration updated")
        
        # Reinitialize Slack if settings changed
        if SLACK_AVAILABLE and self.config["slack"]["enabled"] and self.config["slack"]["token"]:
            try:
                self.slack_client = WebClient(token=self.config["slack"]["token"])
            except Exception as e:
                self.logger.error(f"Failed to reinitialize Slack client: {e}")
        
        return self.config

# Example usage
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Create notification manager
    manager = NotificationManager()
    
    # Send a test notification
    result = manager.send_notification(
        title="Test Notification",
        message="This is a test notification from the Trading Bot",
        level="INFO"
    )
    
    print(f"Notification result: {result}") 