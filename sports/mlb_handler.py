"""MLB Sport Handler"""
from typing import Dict, List
from datetime import datetime
from utils.logger import setup_logger
import random

logger = setup_logger("mlb_handler")

class MLBHandler:
    """Handle MLB-specific data"""
    
    def __init__(self, use_live_api: bool = False):
        """
        Initialize MLB handler
        
        Args:
            use_live_api: Whether to use live ESPN API or mock data
        """
        self.use_live_api = use_live_api
        self.sports_data = None
        
        if self.use_live_api:
            try:
                from sports_data_api import SportsDataClient
                self.sports_data = SportsDataClient()
                logger.info("MLB Handler initialized with live ESPN API")
            except Exception as e:
                logger.warning(f"Failed to initialize live API, using mock data: {e}")
                self.use_live_api = False
        else:
            logger.info("MLB Handler initialized with mock data")
    
    def fetch_games_today(self) -> List[Dict]:
        """
        Get all MLB games scheduled today
        
        Uses ESPN API if enabled, otherwise generates mock games
        """
        if self.use_live_api and self.sports_data:
            try:
                games_data = self.sports_data.get_mlb_games()
                
                formatted_games = []
                for game in games_data:
                    try:
                        competitors = game.get('competitions', [{}])[0].get('competitors', [])
                        if len(competitors) >= 2:
                            home_team = competitors[0].get('team', {}).get('displayName', 'Unknown')
                            away_team = competitors[1].get('team', {}).get('displayName', 'Unknown')
                            
                            formatted_games.append({
                                'game_id': game.get('id', f'mlb_{len(formatted_games)}'),
                                'home': home_team,
                                'away': away_team,
                                'start_time': game.get('date', datetime.now().isoformat()),
                                'commence_time': game.get('date', datetime.now().isoformat())
                            })
                    except Exception as e:
                        logger.debug(f"Error parsing game data: {e}")
                        continue
                
                if formatted_games:
                    logger.info(f"Fetched {len(formatted_games)} live MLB games from ESPN")
                    return formatted_games
                else:
                    logger.info("No live MLB games found, using mock data")
            
            except Exception as e:
                logger.error(f"Error fetching live MLB games: {e}")
        
        # Fallback to mock games
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
        logger.info(f"Using {len(games)} mock MLB games")
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
