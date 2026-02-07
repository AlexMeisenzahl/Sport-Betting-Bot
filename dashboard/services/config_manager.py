"""
Configuration Manager Service

Manages bot configuration with automatic backups before changes.
"""

import os
import yaml
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigManager:
    """
    Manage bot configuration with backup functionality
    """
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize config manager
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = Path(config_path)
        self.backup_dir = Path("config_backups")
        self.backup_dir.mkdir(exist_ok=True)
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get current configuration
        
        Returns:
            Configuration dictionary
        """
        if not self.config_path.exists():
            return {}
        
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            print(f"Error loading config: {e}")
            return {}
    
    def update_config(self, updates: Dict[str, Any], backup: bool = True) -> Dict[str, Any]:
        """
        Update configuration with automatic backup
        
        Args:
            updates: Dictionary of configuration updates
            backup: Whether to create backup before updating
            
        Returns:
            Updated configuration
        """
        if backup:
            self._create_backup()
        
        config = self.get_config()
        
        # Deep merge updates into config
        config = self._deep_merge(config, updates)
        
        # Write updated config
        try:
            with open(self.config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        except Exception as e:
            print(f"Error saving config: {e}")
            raise
        
        return config
    
    def get_notification_settings(self) -> Dict[str, Any]:
        """
        Get notification configuration
        
        Returns:
            Notification settings
        """
        config = self.get_config()
        return config.get('notifications', {})
    
    def update_notification_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update notification settings
        
        Args:
            settings: Notification settings to update
            
        Returns:
            Updated notification settings
        """
        updates = {'notifications': settings}
        config = self.update_config(updates)
        return config.get('notifications', {})
    
    def _create_backup(self) -> Optional[Path]:
        """
        Create timestamped backup of current config
        
        Returns:
            Path to backup file or None if failed
        """
        if not self.config_path.exists():
            return None
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"config_backup_{timestamp}.yaml"
        backup_path = self.backup_dir / backup_name
        
        try:
            shutil.copy2(self.config_path, backup_path)
            print(f"Config backup created: {backup_path}")
            return backup_path
        except Exception as e:
            print(f"Error creating backup: {e}")
            return None
    
    def list_backups(self) -> list:
        """
        List all config backups
        
        Returns:
            List of backup file paths
        """
        if not self.backup_dir.exists():
            return []
        
        backups = sorted(
            self.backup_dir.glob("config_backup_*.yaml"),
            reverse=True
        )
        
        return [
            {
                'filename': b.name,
                'path': str(b),
                'created': datetime.fromtimestamp(b.stat().st_mtime).isoformat()
            }
            for b in backups
        ]
    
    def restore_backup(self, backup_filename: str) -> bool:
        """
        Restore configuration from backup
        
        Args:
            backup_filename: Name of backup file to restore
            
        Returns:
            True if successful, False otherwise
        """
        backup_path = self.backup_dir / backup_filename
        
        if not backup_path.exists():
            print(f"Backup not found: {backup_filename}")
            return False
        
        try:
            # Create backup of current config before restoring
            self._create_backup()
            
            # Restore from backup
            shutil.copy2(backup_path, self.config_path)
            print(f"Config restored from: {backup_filename}")
            return True
        except Exception as e:
            print(f"Error restoring backup: {e}")
            return False
    
    def _deep_merge(self, base: Dict, updates: Dict) -> Dict:
        """
        Deep merge two dictionaries
        
        Args:
            base: Base dictionary
            updates: Updates to merge in
            
        Returns:
            Merged dictionary
        """
        result = base.copy()
        
        for key, value in updates.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def validate_config(self) -> Dict[str, Any]:
        """
        Validate configuration
        
        Returns:
            Dictionary with validation results
        """
        config = self.get_config()
        errors = []
        warnings = []
        
        # Check for required sections
        required_sections = ['paper_trading', 'strategies', 'sports', 'notifications']
        for section in required_sections:
            if section not in config:
                errors.append(f"Missing required section: {section}")
        
        # Validate notification config
        if 'notifications' in config:
            notif = config['notifications']
            
            # Check email config if enabled
            if notif.get('email', {}).get('enabled', False):
                email_config = notif['email']
                if not email_config.get('from_email'):
                    warnings.append("Email notifications enabled but from_email not set")
                if not email_config.get('password'):
                    warnings.append("Email notifications enabled but password not set")
            
            # Check Telegram config if enabled
            if notif.get('telegram', {}).get('enabled', False):
                telegram_config = notif['telegram']
                if not telegram_config.get('bot_token'):
                    warnings.append("Telegram notifications enabled but bot_token not set")
                if not telegram_config.get('chat_id'):
                    warnings.append("Telegram notifications enabled but chat_id not set")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
