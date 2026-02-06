"""
DraftKings Sportsbook API
Mock implementation for paper trading
"""

from typing import Dict, Optional
import random
from utils.logger import setup_logger


logger = setup_logger("draftkings_api")


class DraftKingsAPI:
    """DraftKings sportsbook API interface"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.connected = True
        logger.info("DraftKings API initialized (mock mode)")
    
    def get_odds(self, sport: str, game: str) -> Dict:
        """Get odds for a specific game"""
        # Generate slightly different odds than FanDuel for arbitrage opportunities
        spread_line = random.uniform(-10, 10)
        total_line = random.uniform(190, 240) if sport == 'nba' else random.uniform(40, 55)
        
        # Add small variance to create arbitrage opportunities
        variance = random.uniform(-0.3, 0.3)
        
        odds = {
            'spread': {
                'home': round(spread_line + variance, 1),
                'away': round(-(spread_line + variance), 1)
            },
            'spread_odds': {
                'home': random.choice([-110, -115, -105]),
                'away': random.choice([-110, -115, -105])
            },
            'total': {
                'over': round(total_line + variance, 1),
                'under': round(total_line + variance, 1)
            },
            'total_odds': {
                'over': random.choice([-110, -115, -105]),
                'under': random.choice([-110, -115, -105])
            },
            'moneyline': self._generate_moneyline(spread_line)
        }
        
        return odds
    
    def _generate_moneyline(self, spread: float) -> Dict[str, int]:
        """Generate realistic moneyline from spread"""
        if spread < -7:
            return {'home': -320, 'away': +250}
        elif spread < -3:
            return {'home': -190, 'away': +160}
        elif spread < -1:
            return {'home': -140, 'away': +120}
        elif spread < 1:
            return {'home': -110, 'away': -110}
        elif spread < 3:
            return {'home': +120, 'away': -140}
        elif spread < 7:
            return {'home': +160, 'away': -190}
        else:
            return {'home': +250, 'away': -320}
    
    def get_status(self) -> Dict:
        """Get API connection status"""
        return {
            'connected': self.connected,
            'rate_limit_remaining': 1000,
            'response_time_ms': random.randint(50, 200)
        }
