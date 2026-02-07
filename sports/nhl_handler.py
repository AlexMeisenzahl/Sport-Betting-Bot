"""NHL Sport Handler"""
from typing import Dict, List, Optional
from datetime import datetime
from utils.logger import setup_logger
import random

logger = setup_logger("nhl_handler")

class NHLHandler:
    """Handle NHL-specific data"""
    
    def __init__(self, sports_data_api=None):
        """
        Initialize NHL handler
        
        Args:
            sports_data_api: Optional SportsDataAPI instance for live data
        """
        self.sports_data_api = sports_data_api
        self.use_live_api = sports_data_api is not None and not sports_data_api.use_mock
        
        mode = "LIVE ESPN API" if self.use_live_api else "MOCK"
        logger.info(f"NHL Handler initialized in {mode} mode")
    
    def fetch_games_today(self) -> List[Dict]:
        """
        Get all NHL games scheduled today
        
        Returns:
            List of game dictionaries
        """
        if self.use_live_api:
            return self._fetch_live_games()
        else:
            return self._fetch_mock_games()
    
    def _fetch_live_games(self) -> List[Dict]:
        """Fetch games from ESPN API"""
        try:
            games_data = self.sports_data_api.get_todays_games('nhl')
            
            games = []
            for game_data in games_data:
                game = {
                    'game_id': game_data['game_id'],
                    'home': game_data['home']['name'],
                    'away': game_data['away']['name'],
                    'start_time': game_data['start_time'],
                    'home_record': game_data['home'].get('record', '0-0'),
                    'away_record': game_data['away'].get('record', '0-0'),
                    'status': game_data.get('status', 'pre'),
                    'venue': game_data.get('venue', '')
                }
                games.append(game)
            
            logger.info(f"Fetched {len(games)} NHL games from ESPN API")
            return games
            
        except Exception as e:
            logger.error(f"Error fetching live NHL games: {e}")
            return self._fetch_mock_games()
    
    def _fetch_mock_games(self) -> List[Dict]:
        """Generate mock NHL games"""
        games = [
            {
                'game_id': 'nhl_001',
                'home': 'Bruins',
                'away': 'Maple Leafs',
                'start_time': datetime.now()
            }
        ]
        
        logger.info(f"Generated {len(games)} mock NHL games")
        return games
    
    def get_team_stats(self, team_name: str, team_id: Optional[str] = None) -> Dict:
        """
        Get team statistics
        
        Args:
            team_name: Team name
            team_id: Optional team ID for live API
            
        Returns:
            Team statistics dictionary
        """
        if self.use_live_api and team_id:
            try:
                stats = self.sports_data_api.get_team_stats('nhl', team_id)
                if stats:
                    return self._format_team_stats(stats)
            except Exception as e:
                logger.error(f"Error fetching live team stats: {e}")
        
        return self._get_mock_team_stats(team_name)
    
    def _format_team_stats(self, api_stats: Dict) -> Dict:
        """Format ESPN API stats to our format"""
        return {
            'team': api_stats.get('name', ''),
            'record': api_stats.get('record', '0-0'),
            'standings': api_stats.get('standings', ''),
            'goals_per_game': random.uniform(2.5, 3.5),  # Would need game-by-game data
            'goals_against': random.uniform(2.5, 3.5)  # Would need game-by-game data
        }
    
    def _get_mock_team_stats(self, team_name: str) -> Dict:
        """Generate mock team stats"""
        stats = {
            'team': team_name,
            'goals_per_game': 3.2,
            'goals_against': 2.8
        }
        
        logger.debug(f"Generated mock stats for {team_name}")
        return stats
    
    def get_injury_report(self) -> List[Dict]:
        return []
    
    def get_player_props(self, game: Dict) -> List[Dict]:
        return []
