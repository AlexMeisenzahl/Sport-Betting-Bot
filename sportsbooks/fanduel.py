"""
FanDuel Sportsbook API
Mock implementation for paper trading
"""

from typing import Dict, Optional
import random
from utils.logger import setup_logger


logger = setup_logger("fanduel_api")


class FanDuelAPI:
    """
    FanDuel sportsbook API interface
    
    In paper trading mode, generates realistic mock odds
    In live mode, would connect to actual FanDuel API
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.connected = True
        logger.info("FanDuel API initialized (mock mode)")
    
    def get_odds(self, sport: str, game: str) -> Dict:
        """
        Get odds for a specific game
        
        Returns odds in format:
        {
            'spread': {'home': -5.5, 'away': 5.5},
            'spread_odds': {'home': -110, 'away': -110},
            'total': {'over': 220.5, 'under': 220.5},
            'total_odds': {'over': -110, 'under': -110},
            'moneyline': {'home': -220, 'away': +180}
        }
        """
        # Generate realistic mock odds
        # In production, this would call actual FanDuel API
        
        spread_line = random.uniform(-10, 10)
        total_line = random.uniform(190, 240) if sport == 'nba' else random.uniform(40, 55)
        
        odds = {
            'spread': {
                'home': round(spread_line, 1),
                'away': round(-spread_line, 1)
            },
            'spread_odds': {
                'home': -110,
                'away': -110
            },
            'total': {
                'over': round(total_line, 1),
                'under': round(total_line, 1)
            },
            'total_odds': {
                'over': -110,
                'under': -110
            },
            'moneyline': self._generate_moneyline(spread_line)
        }
        
        return odds
    
    def _generate_moneyline(self, spread: float) -> Dict[str, int]:
        """Generate realistic moneyline from spread"""
        # Rough conversion: spread to moneyline
        if spread < -7:
            return {'home': -300, 'away': +240}
        elif spread < -3:
            return {'home': -180, 'away': +150}
        elif spread < -1:
            return {'home': -130, 'away': +110}
        elif spread < 1:
            return {'home': -110, 'away': -110}
        elif spread < 3:
            return {'home': +110, 'away': -130}
        elif spread < 7:
            return {'home': +150, 'away': -180}
        else:
            return {'home': +240, 'away': -300}
    
    def get_status(self) -> Dict:
        """Get API connection status"""
        return {
            'connected': self.connected,
            'rate_limit_remaining': 1000,
            'response_time_ms': random.randint(50, 200)
        }
