"""NHL Sport Handler"""
from typing import Dict, List
from datetime import datetime
from utils.logger import setup_logger

logger = setup_logger("nhl_handler")

class NHLHandler:
    """Handle NHL-specific data"""
    
    def __init__(self, use_live_api: bool = False):
        """
        Initialize NHL handler
        
        Args:
            use_live_api: Whether to use live ESPN API or mock data
        """
        self.use_live_api = use_live_api
        self.sports_data = None
        
        if self.use_live_api:
            try:
                from sports_data_api import SportsDataClient
                self.sports_data = SportsDataClient()
                logger.info("NHL Handler initialized with live ESPN API")
            except Exception as e:
                logger.warning(f"Failed to initialize live API, using mock data: {e}")
                self.use_live_api = False
        else:
            logger.info("NHL Handler initialized with mock data")
    
    def fetch_games_today(self) -> List[Dict]:
        """
        Get all NHL games scheduled today
        
        Uses ESPN API if enabled, otherwise generates mock games
        """
        if self.use_live_api and self.sports_data:
            try:
                games_data = self.sports_data.get_nhl_games()
                
                formatted_games = []
                for game in games_data:
                    try:
                        competitors = game.get('competitions', [{}])[0].get('competitors', [])
                        if len(competitors) >= 2:
                            home_team = competitors[0].get('team', {}).get('displayName', 'Unknown')
                            away_team = competitors[1].get('team', {}).get('displayName', 'Unknown')
                            
                            formatted_games.append({
                                'game_id': game.get('id', f'nhl_{len(formatted_games)}'),
                                'home': home_team,
                                'away': away_team,
                                'start_time': game.get('date', datetime.now().isoformat()),
                                'commence_time': game.get('date', datetime.now().isoformat())
                            })
                    except Exception as e:
                        logger.debug(f"Error parsing game data: {e}")
                        continue
                
                if formatted_games:
                    logger.info(f"Fetched {len(formatted_games)} live NHL games from ESPN")
                    return formatted_games
                else:
                    logger.info("No live NHL games found, using mock data")
            
            except Exception as e:
                logger.error(f"Error fetching live NHL games: {e}")
        
        # Fallback to mock games
        return [{'game_id': 'nhl_001', 'home': 'Bruins', 'away': 'Maple Leafs', 'start_time': datetime.now()}]
    
    def get_team_stats(self, team_name: str) -> Dict:
        return {'team': team_name, 'goals_per_game': 3.2, 'goals_against': 2.8}
    
    def get_injury_report(self) -> List[Dict]:
        return []
    
    def get_player_props(self, game: Dict) -> List[Dict]:
        return []
