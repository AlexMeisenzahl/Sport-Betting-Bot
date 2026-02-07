"""MLB Sport Handler"""
from typing import Dict, List, Optional
from datetime import datetime
from utils.logger import setup_logger
import random

logger = setup_logger("mlb_handler")

class MLBHandler:
    """Handle MLB-specific data"""
    
    def __init__(self, sports_data_api=None):
        """
        Initialize MLB handler
        
        Args:
            sports_data_api: Optional SportsDataAPI instance for live data
        """
        self.sports_data_api = sports_data_api
        self.use_live_api = sports_data_api is not None and not sports_data_api.use_mock
        
        mode = "LIVE ESPN API" if self.use_live_api else "MOCK"
        logger.info(f"MLB Handler initialized in {mode} mode")
    
    def fetch_games_today(self) -> List[Dict]:
        """
        Get all MLB games scheduled today
        
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
            games_data = self.sports_data_api.get_todays_games('mlb')
            
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
                    'venue': game_data.get('venue', ''),
                    'home_pitcher': {'name': 'TBD', 'era': 0.0},
                    'away_pitcher': {'name': 'TBD', 'era': 0.0}
                }
                games.append(game)
            
            logger.info(f"Fetched {len(games)} MLB games from ESPN API")
            return games
            
        except Exception as e:
            logger.error(f"Error fetching live MLB games: {e}")
            return self._fetch_mock_games()
    
    def _fetch_mock_games(self) -> List[Dict]:
        """Generate mock MLB games"""
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
        
        logger.info(f"Generated {len(games)} mock MLB games")
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
                stats = self.sports_data_api.get_team_stats('mlb', team_id)
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
            'woba': random.uniform(0.310, 0.350),  # ESPN API doesn't provide wOBA
            'runs_per_game': random.uniform(3.8, 5.2)  # Would need game-by-game data
        }
    
    def _get_mock_team_stats(self, team_name: str) -> Dict:
        """Generate mock team stats"""
        stats = {
            'team': team_name,
            'woba': random.uniform(0.310, 0.350),
            'runs_per_game': random.uniform(3.8, 5.2)
        }
        
        logger.debug(f"Generated mock stats for {team_name}")
        return stats
    
    def get_injury_report(self) -> List[Dict]:
        return []
    
    def get_player_props(self, game: Dict) -> List[Dict]:
        return []
