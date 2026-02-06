"""Caesars Sportsbook API - Mock implementation for paper trading"""

from typing import Dict, Optional
import random
from utils.logger import setup_logger

logger = setup_logger("caesars_api")

class CaesarsAPI:
    """Caesars sportsbook API interface"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.connected = True
        logger.info("Caesars API initialized (mock mode)")
    
    def get_odds(self, sport: str, game: str) -> Dict:
        """Get odds for a specific game"""
        spread_line = random.uniform(-10, 10)
        total_line = random.uniform(190, 240) if sport == 'nba' else random.uniform(40, 55)
        variance = random.uniform(-0.4, 0.4)
        
        return {
            'spread': {'home': round(spread_line + variance, 1), 'away': round(-(spread_line + variance), 1)},
            'spread_odds': {'home': random.choice([-110, -115, -108]), 'away': random.choice([-110, -115, -108])},
            'total': {'over': round(total_line + variance, 1), 'under': round(total_line + variance, 1)},
            'total_odds': {'over': -110, 'under': -110},
            'moneyline': self._generate_moneyline(spread_line)
        }
    
    def _generate_moneyline(self, spread: float) -> Dict[str, int]:
        if spread < -7: return {'home': -305, 'away': +235}
        elif spread < -3: return {'home': -175, 'away': +145}
        elif spread < -1: return {'home': -125, 'away': +105}
        elif spread < 1: return {'home': -110, 'away': -110}
        elif spread < 3: return {'home': +105, 'away': -125}
        elif spread < 7: return {'home': +145, 'away': -175}
        else: return {'home': +235, 'away': -305}
    
    def get_status(self) -> Dict:
        return {'connected': self.connected, 'rate_limit_remaining': 1000, 'response_time_ms': random.randint(50, 200)}
