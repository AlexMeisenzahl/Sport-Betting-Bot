"""
The Odds API Client
Fetches live sports betting odds from The Odds API (theoddsapi.com)
"""

import requests
import time
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from utils.logger import setup_logger

logger = setup_logger("odds_api_client")


class OddsAPIClient:
    """
    Client for The Odds API
    Free tier: 500 requests/month
    """
    
    BASE_URL = "https://api.the-odds-api.com/v4"
    
    # Sport keys mapping
    SPORT_KEYS = {
        'nba': 'basketball_nba',
        'nfl': 'americanfootball_nfl',
        'mlb': 'baseball_mlb',
        'nhl': 'icehockey_nhl',
        'soccer': 'soccer_epl',  # English Premier League as default
        'ncaaf': 'americanfootball_ncaaf',
        'ncaab': 'basketball_ncaab'
    }
    
    # Bookmaker keys
    BOOKMAKERS = [
        'fanduel',
        'draftkings',
        'betmgm',
        'williamhill_us',  # Caesars
        'pointsbetus'
    ]
    
    def __init__(self, api_key: Optional[str] = None, use_mock: bool = True):
        """
        Initialize The Odds API client
        
        Args:
            api_key: The Odds API key (get from theoddsapi.com)
            use_mock: If True, use mock data instead of real API calls
        """
        self.api_key = api_key
        self.use_mock = use_mock or not api_key
        
        # Rate limiting
        self.requests_made = 0
        self.last_request_time = None
        self.min_request_interval = 1.0  # Minimum 1 second between requests
        
        # Simple cache
        self.cache = {}
        self.cache_ttl = 60  # 60 seconds cache
        
        if self.use_mock:
            logger.info("Odds API Client initialized in MOCK mode (paper trading)")
        else:
            logger.info("Odds API Client initialized with LIVE data")
            
    def _rate_limit(self):
        """Enforce rate limiting between API calls"""
        if self.last_request_time:
            elapsed = time.time() - self.last_request_time
            if elapsed < self.min_request_interval:
                sleep_time = self.min_request_interval - elapsed
                time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _get_cache_key(self, endpoint: str, params: Dict) -> str:
        """Generate cache key from endpoint and params"""
        param_str = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
        return f"{endpoint}?{param_str}"
    
    def _check_cache(self, cache_key: str) -> Optional[Dict]:
        """Check if cached data is still valid"""
        if cache_key in self.cache:
            data, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                logger.debug(f"Cache hit for {cache_key}")
                return data
            else:
                del self.cache[cache_key]
        return None
    
    def _update_cache(self, cache_key: str, data: Dict):
        """Update cache with new data"""
        self.cache[cache_key] = (data, time.time())
    
    def _make_request(self, endpoint: str, params: Dict) -> Optional[Dict]:
        """
        Make API request with rate limiting and caching
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            
        Returns:
            Response data or None on error
        """
        # Check cache first
        cache_key = self._get_cache_key(endpoint, params)
        cached_data = self._check_cache(cache_key)
        if cached_data:
            return cached_data
        
        # Rate limit
        self._rate_limit()
        
        # Make request
        url = f"{self.BASE_URL}/{endpoint}"
        params['apiKey'] = self.api_key
        
        try:
            response = requests.get(url, params=params, timeout=10)
            self.requests_made += 1
            
            # Check remaining requests from headers
            if 'x-requests-remaining' in response.headers:
                remaining = response.headers['x-requests-remaining']
                logger.debug(f"API requests remaining: {remaining}")
            
            response.raise_for_status()
            data = response.json()
            
            # Update cache
            self._update_cache(cache_key, data)
            
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            return None
    
    def get_sports(self) -> List[Dict]:
        """
        Get list of available sports
        
        Returns:
            List of sport dictionaries
        """
        if self.use_mock:
            return self._get_mock_sports()
        
        endpoint = "sports"
        params = {}
        
        data = self._make_request(endpoint, params)
        return data if data else []
    
    def get_odds(self, sport: str, regions: str = 'us', markets: str = 'h2h,spreads,totals') -> List[Dict]:
        """
        Get odds for a specific sport
        
        Args:
            sport: Sport key (nba, nfl, mlb, etc.)
            regions: Bookmaker regions (us, uk, eu, au)
            markets: Bet types to fetch (h2h=moneyline, spreads, totals)
            
        Returns:
            List of game odds
        """
        if self.use_mock:
            return self._get_mock_odds(sport)
        
        sport_key = self.SPORT_KEYS.get(sport.lower(), sport)
        
        endpoint = f"sports/{sport_key}/odds"
        params = {
            'regions': regions,
            'markets': markets,
            'oddsFormat': 'american',
            'dateFormat': 'iso'
        }
        
        data = self._make_request(endpoint, params)
        return data if data else []
    
    def get_event_odds(self, sport: str, event_id: str) -> Optional[Dict]:
        """
        Get odds for a specific event
        
        Args:
            sport: Sport key
            event_id: Event ID from The Odds API
            
        Returns:
            Event odds data
        """
        if self.use_mock:
            mock_odds = self._get_mock_odds(sport)
            for game in mock_odds:
                if game.get('id') == event_id:
                    return game
            return None
        
        sport_key = self.SPORT_KEYS.get(sport.lower(), sport)
        
        endpoint = f"sports/{sport_key}/odds/{event_id}"
        params = {
            'regions': 'us',
            'markets': 'h2h,spreads,totals',
            'oddsFormat': 'american',
            'dateFormat': 'iso'
        }
        
        return self._make_request(endpoint, params)
    
    def get_bookmaker_odds(self, sport: str, bookmaker: str) -> List[Dict]:
        """
        Get odds from a specific bookmaker
        
        Args:
            sport: Sport key
            bookmaker: Bookmaker key (fanduel, draftkings, etc.)
            
        Returns:
            List of odds from that bookmaker
        """
        all_odds = self.get_odds(sport)
        
        filtered_odds = []
        for game in all_odds:
            game_filtered = game.copy()
            game_filtered['bookmakers'] = [
                b for b in game.get('bookmakers', [])
                if b.get('key') == bookmaker
            ]
            if game_filtered['bookmakers']:
                filtered_odds.append(game_filtered)
        
        return filtered_odds
    
    def format_odds_for_strategy(self, odds_data: List[Dict]) -> Dict[str, Dict]:
        """
        Format API odds data into format expected by strategies
        
        Args:
            odds_data: Raw odds data from API
            
        Returns:
            Dict of game_id -> sportsbook -> odds
        """
        formatted = {}
        
        for game in odds_data:
            game_id = game.get('id', '')
            home_team = game.get('home_team', '')
            away_team = game.get('away_team', '')
            
            game_key = f"{away_team} @ {home_team}"
            formatted[game_key] = {}
            
            for bookmaker in game.get('bookmakers', []):
                book_name = bookmaker.get('key', '').replace('_us', '')
                book_odds = {}
                
                for market in bookmaker.get('markets', []):
                    market_key = market.get('key')
                    
                    if market_key == 'h2h':  # Moneyline
                        book_odds['moneyline'] = {}
                        for outcome in market.get('outcomes', []):
                            team = outcome.get('name')
                            price = outcome.get('price')
                            side = 'home' if team == home_team else 'away'
                            book_odds['moneyline'][side] = price
                    
                    elif market_key == 'spreads':
                        book_odds['spread'] = {}
                        for outcome in market.get('outcomes', []):
                            team = outcome.get('name')
                            price = outcome.get('price')
                            point = outcome.get('point')
                            side = 'home' if team == home_team else 'away'
                            book_odds['spread'][side] = {
                                'price': price,
                                'line': point
                            }
                    
                    elif market_key == 'totals':
                        book_odds['total'] = {}
                        for outcome in market.get('outcomes', []):
                            name = outcome.get('name')
                            price = outcome.get('price')
                            point = outcome.get('point')
                            book_odds['total'][name.lower()] = {
                                'price': price,
                                'line': point
                            }
                
                formatted[game_key][book_name] = book_odds
        
        return formatted
    
    # ========== Mock Data Methods (for paper trading) ==========
    
    def _get_mock_sports(self) -> List[Dict]:
        """Get mock sports list"""
        import random
        return [
            {'key': 'basketball_nba', 'title': 'NBA', 'active': True},
            {'key': 'americanfootball_nfl', 'title': 'NFL', 'active': True},
            {'key': 'baseball_mlb', 'title': 'MLB', 'active': True},
            {'key': 'icehockey_nhl', 'title': 'NHL', 'active': True},
            {'key': 'soccer_epl', 'title': 'EPL', 'active': True},
            {'key': 'americanfootball_ncaaf', 'title': 'NCAAF', 'active': True},
            {'key': 'basketball_ncaab', 'title': 'NCAAB', 'active': True},
        ]
    
    def _get_mock_odds(self, sport: str) -> List[Dict]:
        """Generate mock odds data for testing"""
        import random
        
        # Mock team names by sport
        teams = {
            'nba': [
                ('Lakers', 'Celtics'), ('Warriors', 'Nets'), 
                ('Bucks', 'Heat'), ('Suns', 'Nuggets')
            ],
            'nfl': [
                ('Chiefs', 'Bills'), ('Cowboys', 'Eagles'),
                ('49ers', 'Seahawks'), ('Packers', 'Vikings')
            ],
            'mlb': [
                ('Yankees', 'Red Sox'), ('Dodgers', 'Giants'),
                ('Astros', 'Rangers'), ('Braves', 'Mets')
            ],
            'nhl': [
                ('Maple Leafs', 'Bruins'), ('Avalanche', 'Golden Knights'),
                ('Lightning', 'Panthers'), ('Rangers', 'Devils')
            ],
            'soccer': [
                ('Arsenal', 'Chelsea'), ('Man City', 'Liverpool'),
                ('Man United', 'Tottenham'), ('Newcastle', 'Brighton')
            ],
            'ncaaf': [
                ('Alabama', 'Georgia'), ('Ohio State', 'Michigan'),
                ('Texas', 'Oklahoma'), ('USC', 'Oregon')
            ],
            'ncaab': [
                ('Duke', 'North Carolina'), ('Kansas', 'Kentucky'),
                ('Gonzaga', 'Villanova'), ('UCLA', 'Arizona')
            ]
        }
        
        sport_teams = teams.get(sport.lower(), teams['nba'])
        mock_games = []
        
        for i, (home, away) in enumerate(sport_teams[:2]):  # Just 2 games for testing
            # Generate random but realistic odds
            home_ml = random.randint(-200, 200)
            away_ml = -home_ml if abs(home_ml) > 110 else random.randint(-150, 150)
            
            spread = random.uniform(-10, 10)
            total = random.uniform(200, 230) if sport == 'nba' else random.uniform(40, 55)
            
            game = {
                'id': f"mock_{sport}_{i}",
                'sport_key': self.SPORT_KEYS.get(sport, 'basketball_nba'),
                'commence_time': datetime.now().isoformat(),
                'home_team': home,
                'away_team': away,
                'bookmakers': []
            }
            
            # Add odds from multiple bookmakers
            for bookmaker in self.BOOKMAKERS[:3]:  # Use 3 bookmakers
                book_data = {
                    'key': bookmaker,
                    'title': bookmaker.title().replace('_', ' '),
                    'markets': [
                        {
                            'key': 'h2h',
                            'outcomes': [
                                {'name': home, 'price': home_ml + random.randint(-5, 5)},
                                {'name': away, 'price': away_ml + random.randint(-5, 5)}
                            ]
                        },
                        {
                            'key': 'spreads',
                            'outcomes': [
                                {
                                    'name': home,
                                    'price': -110 + random.randint(-5, 5),
                                    'point': round(spread + random.uniform(-0.5, 0.5), 1)
                                },
                                {
                                    'name': away,
                                    'price': -110 + random.randint(-5, 5),
                                    'point': round(-spread + random.uniform(-0.5, 0.5), 1)
                                }
                            ]
                        },
                        {
                            'key': 'totals',
                            'outcomes': [
                                {
                                    'name': 'Over',
                                    'price': -110 + random.randint(-5, 5),
                                    'point': round(total + random.uniform(-1, 1), 1)
                                },
                                {
                                    'name': 'Under',
                                    'price': -110 + random.randint(-5, 5),
                                    'point': round(total + random.uniform(-1, 1), 1)
                                }
                            ]
                        }
                    ]
                }
                game['bookmakers'].append(book_data)
            
            mock_games.append(game)
        
        return mock_games
    
    def get_remaining_requests(self) -> int:
        """
        Get approximate remaining API requests
        Note: This is an estimate, real count comes from API headers
        """
        return 500 - self.requests_made
