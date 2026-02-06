"""MLB Sport Handler"""
from typing import Dict, List
from datetime import datetime
from utils.logger import setup_logger
import random

logger = setup_logger("mlb_handler")

class MLBHandler:
    """Handle MLB-specific data"""
    
    def __init__(self):
        logger.info("MLB Handler initialized")
    
    def fetch_games_today(self) -> List[Dict]:
        """Get MLB games"""
        games = [
            {
                'game_id': 'mlb_001',
                'home': 'Yankees',
                'away': 'Red Sox',
                'start_time': datetime.now(),
                'home_pitcher': {'name': 'Gerrit Cole', 'era': 2.95},
                'away_pitcher': {'name': 'Chris Sale', 'era': 3.45}
            }
        ]
        logger.info(f"Fetched {len(games)} MLB games")
        return games
    
    def get_team_stats(self, team_name: str) -> Dict:
        """Get team stats"""
        return {
            'team': team_name,
            'woba': random.uniform(0.310, 0.350),
            'runs_per_game': random.uniform(3.8, 5.2)
        }
    
    def get_injury_report(self) -> List[Dict]:
        return []
    
    def get_player_props(self, game: Dict) -> List[Dict]:
        return []
