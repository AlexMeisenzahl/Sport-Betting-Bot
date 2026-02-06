"""BetMGM Sportsbook API - Mock implementation for paper trading"""

from typing import Dict, Optional
import random
from utils.logger import setup_logger

logger = setup_logger("betmgm_api")

class BetMGMAPI:
    """BetMGM sportsbook API interface"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.connected = True
        logger.info("BetMGM API initialized (mock mode)")
    
    def get_odds(self, sport: str, game: str) -> Dict:
        """Get odds for a specific game"""
        spread_line = random.uniform(-10, 10)
        total_line = random.uniform(190, 240) if sport == 'nba' else random.uniform(40, 55)
        variance = random.uniform(-0.5, 0.5)
        
        return {
            'spread': {'home': round(spread_line + variance, 1), 'away': round(-(spread_line + variance), 1)},
            'spread_odds': {'home': -110, 'away': -110},
            'total': {'over': round(total_line + variance, 1), 'under': round(total_line + variance, 1)},
            'total_odds': {'over': -110, 'under': -110},
            'moneyline': self._generate_moneyline(spread_line)
        }
    
    def _generate_moneyline(self, spread: float) -> Dict[str, int]:
        if spread < -7: return {'home': -310, 'away': +245}
        elif spread < -3: return {'home': -185, 'away': +155}
        elif spread < -1: return {'home': -135, 'away': +115}
        elif spread < 1: return {'home': -110, 'away': -110}
        elif spread < 3: return {'home': +115, 'away': -135}
        elif spread < 7: return {'home': +155, 'away': -185}
        else: return {'home': +245, 'away': -310}
    
    def get_status(self) -> Dict:
        return {'connected': self.connected, 'rate_limit_remaining': 1000, 'response_time_ms': random.randint(50, 200)}
