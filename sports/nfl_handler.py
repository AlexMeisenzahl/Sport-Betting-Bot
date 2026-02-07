"""NFL Sport Handler"""
from typing import Dict, List
from datetime import datetime
from utils.logger import setup_logger
import random

logger = setup_logger("nfl_handler")

class NFLHandler:
    """Handle NFL-specific data"""
    
    def __init__(self, use_live_api: bool = False):
        """
        Initialize NFL handler
        
        Args:
            use_live_api: Whether to use live ESPN API or mock data
        """
        self.use_live_api = use_live_api
        self.sports_data = None
        
        if self.use_live_api:
            try:
                from sports_data_api import SportsDataClient
                self.sports_data = SportsDataClient()
                logger.info("NFL Handler initialized with live ESPN API")
            except Exception as e:
                logger.warning(f"Failed to initialize live API, using mock data: {e}")
                self.use_live_api = False
        else:
            logger.info("NFL Handler initialized with mock data")
    
    def fetch_games_today(self) -> List[Dict]:
        """
        Get all NFL games scheduled today
        
        Uses ESPN API if enabled, otherwise generates mock games
        """
        if self.use_live_api and self.sports_data:
            try:
                games_data = self.sports_data.get_nfl_games()
                
                formatted_games = []
                for idx, game in enumerate(games_data):
                    try:
                        competitors = game.get('competitions', [{}])[0].get('competitors', [])
                        if len(competitors) >= 2:
                            home_team = competitors[0].get('team', {}).get('displayName', 'Unknown')
                            away_team = competitors[1].get('team', {}).get('displayName', 'Unknown')
                            
                            formatted_games.append({
                                'game_id': game.get('id', f'nfl_{idx}'),
                                'home': home_team,
                                'away': away_team,
                                'start_time': game.get('date', datetime.now().isoformat()),
                                'commence_time': game.get('date', datetime.now().isoformat())
                            })
                    except Exception as e:
                        logger.debug(f"Error parsing game data: {e}")
                        continue
                
                if formatted_games:
                    logger.info(f"Fetched {len(formatted_games)} live NFL games from ESPN")
                    return formatted_games
                else:
                    logger.info("No live NFL games found, using mock data")
            
            except Exception as e:
                logger.error(f"Error fetching live NFL games: {e}")
        
        # Fallback to mock games
        games = [
            {
                'game_id': 'nfl_001',
                'home': 'Chiefs',
                'away': 'Bills',
                'start_time': datetime.now(),
                'home_off_bye': False,
                'away_off_bye': False,
                'division_game': False,
                'weather': {'temp_f': 45, 'wind_mph': 10, 'condition': 'clear'}
            }
        ]
        logger.info(f"Using {len(games)} mock NFL games")
        return games
    
    def get_team_stats(self, team_name: str) -> Dict:
        """Get team stats"""
        return {
            'team': team_name,
            'dvoa': random.uniform(-15, 15),
            'yards_per_play': random.uniform(5.0, 6.5),
            'points_per_game': random.uniform(20, 30),
            'record': (random.randint(6, 12), random.randint(2, 8))
        }
    
    def get_injury_report(self) -> List[Dict]:
        """Get injuries"""
        return []
    
    def get_player_props(self, game: Dict) -> List[Dict]:
        """Get props"""
        return []
