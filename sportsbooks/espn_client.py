"""
ESPN Free API Client
Access ESPN's public API endpoints for game schedules, scores, and team stats
No API key required
"""

import requests
from typing import Dict, List, Optional
from utils.logger import setup_logger


logger = setup_logger("espn_client")


class ESPNClient:
    """
    ESPN free public API client
    
    Provides access to:
    - Game schedules
    - Live scores
    - Team statistics
    - Player data
    
    All endpoints are public and require no authentication
    """
    
    BASE_URL = "https://site.api.espn.com/apis/site/v2/sports"
    
    # Sport mappings
    SPORTS = {
        'nba': 'basketball/nba',
        'nfl': 'football/nfl',
        'mlb': 'baseball/mlb',
        'nhl': 'hockey/nhl',
        'ncaaf': 'football/college-football',
        'ncaab': 'basketball/mens-college-basketball',
        'soccer': 'soccer'  # Multiple leagues available
    }
    
    def __init__(self):
        """Initialize ESPN client"""
        self.session = requests.Session()
        logger.info("ESPN client initialized")
    
    def get_scoreboard(self, sport: str, date: Optional[str] = None) -> Optional[Dict]:
        """
        Get scoreboard for a sport
        
        Args:
            sport: Sport name (nba, nfl, mlb, nhl, ncaaf, ncaab)
            date: Optional date in YYYYMMDD format (defaults to today)
            
        Returns:
            Scoreboard data dict or None on error
        """
        if sport not in self.SPORTS:
            logger.error(f"Unsupported sport: {sport}")
            return None
        
        sport_path = self.SPORTS[sport]
        url = f"{self.BASE_URL}/{sport_path}/scoreboard"
        
        params = {}
        if date:
            params['dates'] = date
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            logger.debug(f"Retrieved scoreboard for {sport}")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching scoreboard for {sport}: {e}")
            return None
    
    def get_teams(self, sport: str) -> Optional[List[Dict]]:
        """
        Get teams for a sport
        
        Args:
            sport: Sport name
            
        Returns:
            List of team dicts or None on error
        """
        if sport not in self.SPORTS:
            logger.error(f"Unsupported sport: {sport}")
            return None
        
        sport_path = self.SPORTS[sport]
        url = f"{self.BASE_URL}/{sport_path}/teams"
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if 'sports' in data and len(data['sports']) > 0:
                leagues = data['sports'][0].get('leagues', [])
                if leagues:
                    teams = leagues[0].get('teams', [])
                    logger.debug(f"Retrieved {len(teams)} teams for {sport}")
                    return teams
            
            return []
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching teams for {sport}: {e}")
            return None
    
    def get_game_details(self, sport: str, game_id: str) -> Optional[Dict]:
        """
        Get detailed information for a specific game
        
        Args:
            sport: Sport name
            game_id: ESPN game ID
            
        Returns:
            Game details dict or None on error
        """
        if sport not in self.SPORTS:
            logger.error(f"Unsupported sport: {sport}")
            return None
        
        sport_path = self.SPORTS[sport]
        url = f"{self.BASE_URL}/{sport_path}/summary"
        
        try:
            response = self.session.get(
                url,
                params={'event': game_id},
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            logger.debug(f"Retrieved game details for {game_id}")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching game {game_id}: {e}")
            return None
    
    def get_standings(self, sport: str) -> Optional[Dict]:
        """
        Get standings for a sport
        
        Args:
            sport: Sport name
            
        Returns:
            Standings data dict or None on error
        """
        if sport not in self.SPORTS:
            logger.error(f"Unsupported sport: {sport}")
            return None
        
        sport_path = self.SPORTS[sport]
        url = f"{self.BASE_URL}/{sport_path}/standings"
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            logger.debug(f"Retrieved standings for {sport}")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching standings for {sport}: {e}")
            return None
    
    def close(self):
        """Close the session"""
        self.session.close()
        logger.debug("ESPN client session closed")
