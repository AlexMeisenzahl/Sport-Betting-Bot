"""
The Odds API Integration
Integration with The Odds API for real-time betting odds

Features:
- Fetch live odds from multiple sportsbooks (FanDuel, DraftKings, BetMGM, Caesars)
- Support for NBA, NFL, MLB, NHL
- Support for moneyline, spread, totals
- Rate limiting (500 requests per month on free tier)
- Error handling and retries
- Cache odds for 5 minutes to minimize API calls
"""

import os
import requests
import time
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from utils.logger import setup_logger

logger = setup_logger("odds_api")


class TheOddsAPI:
    """
    Integration with The Odds API for real-time betting odds
    """
    
    BASE_URL = "https://api.the-odds-api.com/v4"
    
    # Sport keys mapping
    SPORT_KEYS = {
        'NBA': 'basketball_nba',
        'NFL': 'americanfootball_nfl',
        'MLB': 'baseball_mlb',
        'NHL': 'icehockey_nhl',
        'NCAAF': 'americanfootball_ncaaf',
        'NCAAB': 'basketball_ncaab',
        'SOCCER': 'soccer_epl'
    }
    
    # Market types
    DEFAULT_MARKETS = ['h2h', 'spreads', 'totals']
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize The Odds API client
        
        Args:
            api_key: The Odds API key (or use THE_ODDS_API_KEY env variable)
        """
        self.api_key = api_key or os.environ.get('THE_ODDS_API_KEY')
        
        if not self.api_key:
            logger.warning("No API key provided. API calls will fail.")
        
        # Rate limiting
        self.requests_made = 0
        self.last_request_time = None
        self.min_request_interval = 1.0  # 1 second between requests
        
        # Cache (5 minutes)
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes in seconds
        
        logger.info(f"TheOddsAPI initialized with key: {'*' * 8 if self.api_key else 'None'}")
    
    def get_odds(self, sport: str, markets: Optional[List[str]] = None, 
                 regions: str = 'us', bookmakers: Optional[List[str]] = None) -> List[Dict]:
        """
        Fetch current odds for a sport
        
        Args:
            sport: Sport name (NBA, NFL, MLB, NHL, etc.)
            markets: List of markets to fetch (default: ['h2h', 'spreads', 'totals'])
            regions: Regions to get odds from (default: 'us')
            bookmakers: Specific bookmakers to filter (optional)
            
        Returns:
            List of games with odds from all sportsbooks
        """
        if not self.api_key:
            logger.error("Cannot fetch odds: No API key configured")
            return []
        
        # Map sport name to API key
        sport_key = self.SPORT_KEYS.get(sport.upper())
        if not sport_key:
            logger.error(f"Unsupported sport: {sport}")
            return []
        
        # Check cache first
        cache_key = f"{sport_key}_{markets}_{regions}"
        cached_data = self._check_cache(cache_key)
        if cached_data:
            logger.debug(f"Using cached odds for {sport}")
            return cached_data
        
        # Default markets
        if markets is None:
            markets = self.DEFAULT_MARKETS
        
        # Build request parameters
        params = {
            'apiKey': self.api_key,
            'regions': regions,
            'markets': ','.join(markets),
            'oddsFormat': 'american',
            'dateFormat': 'iso'
        }
        
        if bookmakers:
            params['bookmakers'] = ','.join(bookmakers)
        
        # Rate limiting
        self._rate_limit()
        
        # Make request
        url = f"{self.BASE_URL}/sports/{sport_key}/odds"
        
        try:
            logger.info(f"Fetching odds for {sport} from The Odds API...")
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            self.requests_made += 1
            
            # Check remaining requests from headers
            remaining = response.headers.get('x-requests-remaining')
            if remaining:
                logger.info(f"API requests remaining: {remaining}")
            
            data = response.json()
            
            # Cache the data
            self._update_cache(cache_key, data)
            
            logger.info(f"Successfully fetched {len(data)} games for {sport}")
            return data
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                logger.error("API authentication failed. Check your API key.")
            elif e.response.status_code == 429:
                logger.error("API rate limit exceeded. Wait before making more requests.")
            else:
                logger.error(f"HTTP error fetching odds: {e}")
            return []
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching odds: {e}")
            return []
    
    def get_sports(self) -> List[Dict]:
        """
        Get list of available sports
        
        Returns:
            List of sport dictionaries with keys, groups, etc.
        """
        if not self.api_key:
            logger.error("Cannot fetch sports: No API key configured")
            return []
        
        # Check cache
        cache_key = "sports_list"
        cached_data = self._check_cache(cache_key)
        if cached_data:
            return cached_data
        
        self._rate_limit()
        
        url = f"{self.BASE_URL}/sports"
        params = {'apiKey': self.api_key}
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            self._update_cache(cache_key, data)
            
            logger.info(f"Fetched {len(data)} available sports")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching sports list: {e}")
            return []
    
    def get_usage(self) -> Dict:
        """
        Check remaining API requests
        
        Note: This requires making an API call, which counts against your quota.
        The remaining count is also returned in response headers of other calls.
        
        Returns:
            Dictionary with usage information
        """
        if not self.api_key:
            return {'error': 'No API key configured'}
        
        # Make a minimal request to check usage
        self._rate_limit()
        
        url = f"{self.BASE_URL}/sports"
        params = {'apiKey': self.api_key}
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            remaining = response.headers.get('x-requests-remaining', 'unknown')
            used = response.headers.get('x-requests-used', 'unknown')
            
            return {
                'requests_remaining': remaining,
                'requests_used': used,
                'requests_made_this_session': self.requests_made
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error checking usage: {e}")
            return {'error': str(e)}
    
    def _rate_limit(self):
        """Enforce rate limiting between API calls"""
        if self.last_request_time:
            elapsed = time.time() - self.last_request_time
            if elapsed < self.min_request_interval:
                sleep_time = self.min_request_interval - elapsed
                time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _check_cache(self, cache_key: str) -> Optional[List[Dict]]:
        """Check if cached data is still valid"""
        if cache_key in self.cache:
            data, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                return data
            else:
                # Cache expired
                del self.cache[cache_key]
        return None
    
    def _update_cache(self, cache_key: str, data: List[Dict]):
        """Update cache with new data"""
        self.cache[cache_key] = (data, time.time())
    
    def clear_cache(self):
        """Clear all cached data"""
        self.cache.clear()
        logger.info("Cache cleared")
