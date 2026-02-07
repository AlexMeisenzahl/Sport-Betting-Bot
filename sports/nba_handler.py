"""
NBA Sport Handler
Fetches games, stats, injuries, and props for NBA
Now supports both mock data (paper trading) and live ESPN API data
"""

from typing import Dict, List, Optional
from datetime import datetime
from utils.logger import setup_logger
import random


logger = setup_logger("nba_handler")


class NBAHandler:
    """Handle NBA-specific data and game fetching"""
    
    def __init__(self, sports_data_api=None):
        """
        Initialize NBA handler
        
        Args:
            sports_data_api: Optional SportsDataAPI instance for live data
        """
        self.sports_data_api = sports_data_api
        self.use_live_api = sports_data_api is not None and not sports_data_api.use_mock
        
        mode = "LIVE ESPN API" if self.use_live_api else "MOCK"
        logger.info(f"NBA Handler initialized in {mode} mode")
    
    def fetch_games_today(self) -> List[Dict]:
        """
        Get all NBA games scheduled today
        
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
            games_data = self.sports_data_api.get_todays_games('nba')
            
            # Convert to our format
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
                    # Note: Rest days would require historical data tracking
                    'home_rest_days': 1,  # Default
                    'away_rest_days': 1,  # Default
                    'home_back_to_back': False,  # Would need to track
                    'away_back_to_back': False   # Would need to track
                }
                games.append(game)
            
            logger.info(f"Fetched {len(games)} NBA games from ESPN API")
            return games
            
        except Exception as e:
            logger.error(f"Error fetching live NBA games: {e}")
            return self._fetch_mock_games()
    
    def _fetch_mock_games(self) -> List[Dict]:
        """Generate mock NBA games"""
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
        
        logger.info(f"Generated {len(games)} mock NBA games")
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
                stats = self.sports_data_api.get_team_stats('nba', team_id)
                if stats:
                    return self._format_team_stats(stats)
            except Exception as e:
                logger.error(f"Error fetching live team stats: {e}")
        
        # Fall back to mock stats
        return self._get_mock_team_stats(team_name)
    
    def _format_team_stats(self, api_stats: Dict) -> Dict:
        """Format ESPN API stats to our format"""
        return {
            'team': api_stats.get('name', ''),
            'record': api_stats.get('record', '0-0'),
            'standings': api_stats.get('standings', ''),
            'offensive_rating': random.uniform(108, 118),  # Would need advanced stats
            'defensive_rating': random.uniform(108, 118),
            'net_rating': random.uniform(-3, 8),
            'pace': random.uniform(96, 103),
            'home_record': (25, 10),  # Would parse from record
            'away_record': (20, 15),
            'last_10': (6, 4)
        }
    
    def _get_mock_team_stats(self, team_name: str) -> Dict:
        """Generate mock team stats"""
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
        
        logger.debug(f"Generated mock stats for {team_name}")
        return stats
    
    def get_injury_report(self) -> List[Dict]:
        """
        Current injuries with impact ratings
        
        Note: ESPN API doesn't provide detailed injury data
        Would need a different source for production
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
        
        logger.info(f"Using mock injury data: {len(injuries)} injuries")
        return injuries
    
    def get_player_props(self, game: Dict) -> List[Dict]:
        """
        Available prop bets for this game
        
        Note: Would need sportsbook prop APIs for production
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

