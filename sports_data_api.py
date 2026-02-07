"""
Live Sports Data API Integration
Using ESPN API for game schedules, scores, stats
"""

import requests
from typing import Dict, List, Optional
from datetime import datetime
from utils.logger import setup_logger


logger = setup_logger("sports_data_api")


class SportsDataClient:
    """ESPN API client for game schedules and scores"""
    
    ESPN_BASE = "https://site.api.espn.com/apis/site/v2/sports"
    
    def __init__(self):
        """Initialize the ESPN API client"""
        self.session = requests.Session()
        logger.info("Sports Data API client initialized")
    
    def get_nba_games(self, date: str = None) -> List[Dict]:
        """
        Get today's NBA games
        
        Args:
            date: Optional date in YYYYMMDD format
            
        Returns: List of game dictionaries
        """
        url = f"{self.ESPN_BASE}/basketball/nba/scoreboard"
        params = {}
        if date:
            params['dates'] = date
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data.get('events', [])
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching NBA games from ESPN: {e}")
            return []
    
    def get_nfl_games(self, date: str = None) -> List[Dict]:
        """
        Get NFL games
        
        Args:
            date: Optional date in YYYYMMDD format
            
        Returns: List of game dictionaries
        """
        url = f"{self.ESPN_BASE}/football/nfl/scoreboard"
        params = {}
        if date:
            params['dates'] = date
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data.get('events', [])
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching NFL games from ESPN: {e}")
            return []
    
    def get_mlb_games(self, date: str = None) -> List[Dict]:
        """
        Get MLB games
        
        Args:
            date: Optional date in YYYYMMDD format
            
        Returns: List of game dictionaries
        """
        url = f"{self.ESPN_BASE}/baseball/mlb/scoreboard"
        params = {}
        if date:
            params['dates'] = date
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data.get('events', [])
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching MLB games from ESPN: {e}")
            return []
    
    def get_nhl_games(self, date: str = None) -> List[Dict]:
        """
        Get NHL games
        
        Args:
            date: Optional date in YYYYMMDD format
            
        Returns: List of game dictionaries
        """
        url = f"{self.ESPN_BASE}/hockey/nhl/scoreboard"
        params = {}
        if date:
            params['dates'] = date
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data.get('events', [])
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching NHL games from ESPN: {e}")
            return []
    
    def get_ncaaf_games(self, date: str = None) -> List[Dict]:
        """
        Get NCAAF (College Football) games
        
        Args:
            date: Optional date in YYYYMMDD format
            
        Returns: List of game dictionaries
        """
        url = f"{self.ESPN_BASE}/football/college-football/scoreboard"
        params = {}
        if date:
            params['dates'] = date
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data.get('events', [])
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching NCAAF games from ESPN: {e}")
            return []
    
    def get_ncaab_games(self, date: str = None) -> List[Dict]:
        """
        Get NCAAB (College Basketball) games
        
        Args:
            date: Optional date in YYYYMMDD format
            
        Returns: List of game dictionaries
        """
        url = f"{self.ESPN_BASE}/basketball/mens-college-basketball/scoreboard"
        params = {}
        if date:
            params['dates'] = date
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data.get('events', [])
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching NCAAB games from ESPN: {e}")
            return []
    
    def get_soccer_games(self, league: str = "usa.1", date: str = None) -> List[Dict]:
        """
        Get Soccer games
        
        Args:
            league: League identifier (e.g., 'usa.1' for MLS, 'eng.1' for Premier League)
            date: Optional date in YYYYMMDD format
            
        Returns: List of game dictionaries
        """
        url = f"{self.ESPN_BASE}/soccer/{league}/scoreboard"
        params = {}
        if date:
            params['dates'] = date
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data.get('events', [])
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching soccer games from ESPN: {e}")
            return []
