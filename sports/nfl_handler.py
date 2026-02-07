"""NFL Sport Handler"""
from typing import Dict, List, Optional
from datetime import datetime
from utils.logger import setup_logger
import random

logger = setup_logger("nfl_handler")

class NFLHandler:
    """Handle NFL-specific data"""
    
    def __init__(self, sports_data_api=None):
        """
        Initialize NFL handler
        
        Args:
            sports_data_api: Optional SportsDataAPI instance for live data
        """
        self.sports_data_api = sports_data_api
        self.use_live_api = sports_data_api is not None and not sports_data_api.use_mock
        
        mode = "LIVE ESPN API" if self.use_live_api else "MOCK"
        logger.info(f"NFL Handler initialized in {mode} mode")
    
    def fetch_games_today(self) -> List[Dict]:
        """
        Get all NFL games scheduled today
        
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
            games_data = self.sports_data_api.get_todays_games('nfl')
            
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
                    # ESPN API doesn't provide bye week, division game, or weather data
                    'home_off_bye': False,
                    'away_off_bye': False,
                    'division_game': False,
                    'weather': {'temp_f': 45, 'wind_mph': 10, 'condition': 'clear'}
                }
                games.append(game)
            
            logger.info(f"Fetched {len(games)} NFL games from ESPN API")
            return games
            
        except Exception as e:
            logger.error(f"Error fetching live NFL games: {e}")
            return self._fetch_mock_games()
    
    def _fetch_mock_games(self) -> List[Dict]:
        """Generate mock NFL games"""
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
        
        logger.info(f"Generated {len(games)} mock NFL games")
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
                stats = self.sports_data_api.get_team_stats('nfl', team_id)
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
            'dvoa': random.uniform(-15, 15),  # ESPN API doesn't provide DVOA
            'yards_per_play': random.uniform(5.0, 6.5),  # Would need game-by-game data
            'points_per_game': random.uniform(20, 30)  # Would need game-by-game data
        }
    
    def _get_mock_team_stats(self, team_name: str) -> Dict:
        """Generate mock team stats"""
        stats = {
            'team': team_name,
            'dvoa': random.uniform(-15, 15),
            'yards_per_play': random.uniform(5.0, 6.5),
            'points_per_game': random.uniform(20, 30),
            'record': (random.randint(6, 12), random.randint(2, 8))
        }
        
        logger.debug(f"Generated mock stats for {team_name}")
        return stats
    
    def get_injury_report(self) -> List[Dict]:
        """Get injuries"""
        return []
    
    def get_player_props(self, game: Dict) -> List[Dict]:
        """Get props"""
        return []
