"""
Configuration loader for the sports betting bot
Loads and validates configuration from config.yaml
"""

import yaml
import os
from typing import Dict, Any


class ConfigLoader:
    """Loads and manages bot configuration"""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
            
        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)
            
        return config
    
    def get(self, *keys, default=None) -> Any:
        """Get configuration value by nested keys"""
        value = self.config
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
                if value is None:
                    return default
            else:
                return default
        return value
    
    def is_paper_trading(self) -> bool:
        """Check if paper trading mode is enabled"""
        return self.get('paper_trading', 'enabled', default=True)
    
    def get_starting_bankroll(self) -> float:
        """Get starting bankroll for paper trading"""
        return float(self.get('paper_trading', 'starting_bankroll', default=500))
    
    def is_strategy_enabled(self, strategy_name: str) -> bool:
        """Check if a strategy is enabled"""
        return self.get('strategies', strategy_name, 'enabled', default=False)
    
    def is_sport_enabled(self, sport_name: str) -> bool:
        """Check if a sport is enabled"""
        return self.get('sports', sport_name, 'enabled', default=False)
    
    def get_sport_strategies(self, sport_name: str) -> list:
        """Get enabled strategies for a sport"""
        return self.get('sports', sport_name, 'strategies', default=[])
    
    def get_max_concurrent_bets(self) -> int:
        """Get maximum concurrent bets allowed"""
        return self.get('risk_management', 'max_concurrent_bets', default=10)
    
    def get_kelly_fraction(self) -> float:
        """Get Kelly fraction for position sizing"""
        return self.get('risk_management', 'kelly_fraction', default=0.25)
