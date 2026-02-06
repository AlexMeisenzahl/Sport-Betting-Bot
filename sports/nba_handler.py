"""
NBA Sport Handler
Fetches games, stats, injuries, and props for NBA
"""

from typing import Dict, List
from datetime import datetime
from utils.logger import setup_logger
import random


logger = setup_logger("nba_handler")


class NBAHandler:
    """Handle NBA-specific data and game fetching"""
    
    def __init__(self):
        logger.info("NBA Handler initialized")
    
    def fetch_games_today(self) -> List[Dict]:
        """
        Get all NBA games scheduled today
        
        In production: Use nba_api or ESPN API
        For now: Generate mock games
        """
        # Mock NBA games
        games = [
            {
                'game_id': 'nba_001',
                'home': 'Lakers',
                'away': 'Celtics',
                'start_time': datetime.now(),
                'home_rest_days': 1,
                'away_rest_days': 2,
                'home_back_to_back': False,
                'away_back_to_back': False
            },
            {
                'game_id': 'nba_002',
                'home': 'Warriors',
                'away': 'Nets',
                'start_time': datetime.now(),
                'home_rest_days': 2,
                'away_rest_days': 0,
                'home_back_to_back': False,
                'away_back_to_back': True
            }
        ]
        
        logger.info(f"Fetched {len(games)} NBA games for today")
        return games
    
    def get_team_stats(self, team_name: str) -> Dict:
        """
        Get team statistics
        Off/def rating, pace, net rating, home/road splits
        
        In production: Fetch from nba_api
        """
        # Mock stats
        stats = {
            'team': team_name,
            'offensive_rating': random.uniform(108, 118),
            'defensive_rating': random.uniform(108, 118),
            'net_rating': random.uniform(-3, 8),
            'pace': random.uniform(96, 103),
            'home_record': (random.randint(15, 30), random.randint(5, 15)),
            'away_record': (random.randint(12, 28), random.randint(8, 18)),
            'last_10': (random.randint(4, 8), random.randint(2, 6))
        }
        
        logger.debug(f"Fetched stats for {team_name}")
        return stats
    
    def get_injury_report(self) -> List[Dict]:
        """
        Current injuries with impact ratings
        
        In production: Fetch from official NBA injury report
        """
        injuries = [
            {
                'player': 'LeBron James',
                'team': 'Lakers',
                'status': 'out',
                'tier': 'star',
                'impact_points': -6.5
            }
        ]
        
        logger.info(f"Fetched {len(injuries)} injuries")
        return injuries
    
    def get_player_props(self, game: Dict) -> List[Dict]:
        """
        Available prop bets for this game
        
        In production: Fetch from sportsbook APIs
        """
        props = [
            {
                'player': 'Stephen Curry',
                'team': game['away'],
                'prop_type': 'points',
                'line': 28.5,
                'over_odds': -110,
                'under_odds': -110
            },
            {
                'player': 'Anthony Davis',
                'team': game['home'],
                'prop_type': 'rebounds',
                'line': 11.5,
                'over_odds': -110,
                'under_odds': -110
            }
        ]
        
        return props
