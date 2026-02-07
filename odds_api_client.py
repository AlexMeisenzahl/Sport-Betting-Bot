"""
Live Sports Betting Odds API Integration
Documentation: https://the-odds-api.com/
"""

import requests
from typing import Dict, List, Optional
import time
from utils.logger import setup_logger


logger = setup_logger("odds_api_client")


class OddsAPIClient:
    """The Odds API client for live sportsbook odds"""
    
    BASE_URL = "https://api.the-odds-api.com/v4"
    
    def __init__(self, api_key: str):
        """
        Initialize the Odds API client
        
        Args:
            api_key: API key from the-odds-api.com
        """
        self.api_key = api_key
        self.session = requests.Session()
        self.last_request_time = 0
        self.rate_limit_delay = 1.0  # Minimum seconds between requests
        logger.info("Odds API client initialized")
    
    def get_odds(self, sport_key: str, regions: List[str] = None, 
                 markets: List[str] = None, bookmakers: List[str] = None) -> List[Dict]:
        """
        Get live odds for a sport
        
        Parameters:
        - sport_key: 'basketball_nba', 'americanfootball_nfl', etc.
        - regions: ['us'] - geographic regions
        - markets: ['h2h', 'spreads', 'totals'] - bet types
        - bookmakers: ['fanduel', 'draftkings', 'betmgm'] - specific books
        
        Returns: List of games with odds from each bookmaker
        """
        # Rate limiting
        self._respect_rate_limit()
        
        endpoint = f"{self.BASE_URL}/sports/{sport_key}/odds"
        params = {
            'apiKey': self.api_key,
            'regions': ','.join(regions or ['us']),
            'markets': ','.join(markets or ['h2h', 'spreads']),
            'oddsFormat': 'american'
        }
        if bookmakers:
            params['bookmakers'] = ','.join(bookmakers)
        
        try:
            response = self.session.get(endpoint, params=params, timeout=10)
            response.raise_for_status()
            
            # Log remaining quota
            if 'x-requests-remaining' in response.headers:
                remaining = response.headers['x-requests-remaining']
                logger.debug(f"API requests remaining: {remaining}")
            
            return response.json()
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching odds from The Odds API: {e}")
            return []
    
    def get_sports(self) -> List[Dict]:
        """
        Get list of available sports
        
        Returns: List of sport objects with keys and titles
        """
        self._respect_rate_limit()
        
        endpoint = f"{self.BASE_URL}/sports"
        params = {'apiKey': self.api_key}
        
        try:
            response = self.session.get(endpoint, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching sports list: {e}")
            return []
    
    def _respect_rate_limit(self):
        """Implement rate limiting to avoid API throttling"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
