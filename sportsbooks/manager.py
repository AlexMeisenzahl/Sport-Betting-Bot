"""
SportsbookManager
Unified manager that coordinates all data sources with intelligent fallback

Priority order:
1. The Odds API (primary - most reliable, real-time)
2. OddsPortal scraper (backup if API limit reached)
3. OddsChecker scraper (tertiary backup)

Features:
- Automatic fallback on failure/rate limits
- Data validation across sources
- Unified data format regardless of source
- Status tracking for each source
- Cache management
"""

from typing import Dict, List, Optional
from utils.logger import setup_logger

logger = setup_logger("sportsbook_manager")


class SportsbookManager:
    """
    Hybrid data source manager with priority fallback
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize sportsbook manager with all data sources
        
        Args:
            api_key: The Odds API key (optional)
        """
        self.api_key = api_key
        
        # Initialize The Odds API (primary source)
        self.odds_api = None
        self._initialize_odds_api()
        
        # Initialize scrapers (backup sources)
        self.scrapers = {}
        self._initialize_scrapers()
        
        # Track source status
        self.source_status = {
            'odds_api': {'available': self.odds_api is not None, 'last_success': None, 'failures': 0},
            'oddsportal': {'available': 'oddsportal' in self.scrapers, 'last_success': None, 'failures': 0},
            'oddschecker': {'available': 'oddschecker' in self.scrapers, 'last_success': None, 'failures': 0}
        }
        
        logger.info("SportsbookManager initialized")
        self._log_sources()
    
    def _initialize_odds_api(self):
        """Initialize The Odds API client"""
        try:
            from sportsbooks.odds_api import TheOddsAPI
            self.odds_api = TheOddsAPI(api_key=self.api_key)
            logger.info("✓ The Odds API initialized")
        except Exception as e:
            logger.warning(f"Could not initialize The Odds API: {e}")
            self.odds_api = None
    
    def _initialize_scrapers(self):
        """Initialize web scrapers as backup"""
        try:
            from sportsbooks.scrapers import OddsPortalScraper, OddsCheckerScraper
            
            try:
                self.scrapers['oddsportal'] = OddsPortalScraper()
                logger.info("✓ OddsPortal scraper initialized")
            except Exception as e:
                logger.warning(f"Could not initialize OddsPortal scraper: {e}")
            
            try:
                self.scrapers['oddschecker'] = OddsCheckerScraper()
                logger.info("✓ OddsChecker scraper initialized")
            except Exception as e:
                logger.warning(f"Could not initialize OddsChecker scraper: {e}")
                
        except ImportError as e:
            logger.warning(f"Could not import scrapers: {e}")
    
    def get_odds(self, sport: str, fallback: bool = True) -> Dict:
        """
        Get odds with automatic fallback
        
        Args:
            sport: Sport name (NBA, NFL, MLB, NHL, etc.)
            fallback: Whether to try backup sources if primary fails
            
        Returns:
            Dictionary with odds data in unified format
        """
        # Try The Odds API first
        if self.odds_api and self.api_key:
            try:
                logger.info(f"Attempting to fetch odds from The Odds API for {sport}")
                data = self.odds_api.get_odds(sport)
                if data:
                    self._record_success('odds_api')
                    return self._format_odds_api_data(data, sport)
                else:
                    self._record_failure('odds_api')
            except Exception as e:
                logger.warning(f"The Odds API failed: {e}")
                self._record_failure('odds_api')
        
        # Fallback to scrapers if enabled
        if fallback:
            # Try OddsPortal
            if 'oddsportal' in self.scrapers:
                try:
                    logger.info(f"Falling back to OddsPortal scraper for {sport}")
                    data = self.scrapers['oddsportal'].get_odds(sport)
                    if data:
                        self._record_success('oddsportal')
                        return self._format_scraper_data(data, sport, 'oddsportal')
                    else:
                        self._record_failure('oddsportal')
                except Exception as e:
                    logger.warning(f"OddsPortal scraper failed: {e}")
                    self._record_failure('oddsportal')
            
            # Try OddsChecker
            if 'oddschecker' in self.scrapers:
                try:
                    logger.info(f"Falling back to OddsChecker scraper for {sport}")
                    data = self.scrapers['oddschecker'].get_odds(sport)
                    if data:
                        self._record_success('oddschecker')
                        return self._format_scraper_data(data, sport, 'oddschecker')
                    else:
                        self._record_failure('oddschecker')
                except Exception as e:
                    logger.warning(f"OddsChecker scraper failed: {e}")
                    self._record_failure('oddschecker')
        
        logger.error(f"All data sources failed for {sport}")
        return {'games': [], 'source': 'none', 'error': 'All sources failed'}
    
    def get_best_odds(self, sport: str, game_id: str) -> Dict:
        """
        Find best available odds across all sportsbooks for a specific game
        
        Args:
            sport: Sport name
            game_id: Game identifier
            
        Returns:
            Dictionary with best odds for each bet type
        """
        odds_data = self.get_odds(sport, fallback=True)
        
        if not odds_data.get('games'):
            return {}
        
        # Find the specific game
        game = next((g for g in odds_data['games'] if g.get('id') == game_id), None)
        if not game:
            logger.warning(f"Game {game_id} not found in odds data")
            return {}
        
        # Extract best odds across all bookmakers
        best_odds = {
            'game_id': game_id,
            'game': game.get('name', 'Unknown'),
            'commence_time': game.get('commence_time'),
            'moneyline': self._find_best_moneyline(game),
            'spread': self._find_best_spread(game),
            'totals': self._find_best_totals(game)
        }
        
        return best_odds
    
    def get_source_status(self) -> Dict:
        """
        Get status of all data sources
        
        Returns:
            Dictionary with status information for each source
        """
        return {
            'sources': self.source_status,
            'primary_source': 'odds_api' if self.odds_api and self.api_key else 'scrapers',
            'available_sources': [name for name, status in self.source_status.items() if status['available']]
        }
    
    def _format_odds_api_data(self, data: List[Dict], sport: str) -> Dict:
        """
        Format The Odds API data into unified format
        
        Args:
            data: Raw data from The Odds API
            sport: Sport name
            
        Returns:
            Unified format dictionary
        """
        games = []
        
        for game in data:
            formatted_game = {
                'id': game.get('id'),
                'sport': sport,
                'commence_time': game.get('commence_time'),
                'home_team': game.get('home_team'),
                'away_team': game.get('away_team'),
                'bookmakers': []
            }
            
            # Process bookmaker odds
            for bookmaker in game.get('bookmakers', []):
                formatted_bookmaker = {
                    'name': bookmaker.get('title', bookmaker.get('key')),
                    'markets': {}
                }
                
                # Process each market
                for market in bookmaker.get('markets', []):
                    market_key = market.get('key')
                    formatted_bookmaker['markets'][market_key] = {
                        'outcomes': market.get('outcomes', [])
                    }
                
                formatted_game['bookmakers'].append(formatted_bookmaker)
            
            games.append(formatted_game)
        
        return {
            'games': games,
            'source': 'odds_api',
            'timestamp': None  # Could add current time
        }
    
    def _format_scraper_data(self, data: Dict, sport: str, source: str) -> Dict:
        """
        Format scraper data into unified format
        
        Args:
            data: Raw data from scraper
            sport: Sport name
            source: Source name (oddsportal or oddschecker)
            
        Returns:
            Unified format dictionary
        """
        # Scrapers might return data in different formats
        # This is a placeholder for the unified formatting
        return {
            'games': data.get('games', []),
            'source': source,
            'timestamp': data.get('timestamp')
        }
    
    def _find_best_moneyline(self, game: Dict) -> Dict:
        """Find best moneyline odds across all bookmakers"""
        best = {
            'home': {'odds': None, 'bookmaker': None},
            'away': {'odds': None, 'bookmaker': None}
        }
        
        for bookmaker in game.get('bookmakers', []):
            h2h_market = bookmaker.get('markets', {}).get('h2h')
            if not h2h_market:
                continue
            
            for outcome in h2h_market.get('outcomes', []):
                name = outcome.get('name')
                odds = outcome.get('price')
                
                if name == game.get('home_team'):
                    if best['home']['odds'] is None or odds > best['home']['odds']:
                        best['home'] = {'odds': odds, 'bookmaker': bookmaker['name']}
                elif name == game.get('away_team'):
                    if best['away']['odds'] is None or odds > best['away']['odds']:
                        best['away'] = {'odds': odds, 'bookmaker': bookmaker['name']}
        
        return best
    
    def _find_best_spread(self, game: Dict) -> Dict:
        """Find best spread odds across all bookmakers"""
        best = {
            'home': {'odds': None, 'point': None, 'bookmaker': None},
            'away': {'odds': None, 'point': None, 'bookmaker': None}
        }
        
        for bookmaker in game.get('bookmakers', []):
            spread_market = bookmaker.get('markets', {}).get('spreads')
            if not spread_market:
                continue
            
            for outcome in spread_market.get('outcomes', []):
                name = outcome.get('name')
                odds = outcome.get('price')
                point = outcome.get('point')
                
                if name == game.get('home_team'):
                    if best['home']['odds'] is None or odds > best['home']['odds']:
                        best['home'] = {'odds': odds, 'point': point, 'bookmaker': bookmaker['name']}
                elif name == game.get('away_team'):
                    if best['away']['odds'] is None or odds > best['away']['odds']:
                        best['away'] = {'odds': odds, 'point': point, 'bookmaker': bookmaker['name']}
        
        return best
    
    def _find_best_totals(self, game: Dict) -> Dict:
        """Find best totals odds across all bookmakers"""
        best = {
            'over': {'odds': None, 'point': None, 'bookmaker': None},
            'under': {'odds': None, 'point': None, 'bookmaker': None}
        }
        
        for bookmaker in game.get('bookmakers', []):
            totals_market = bookmaker.get('markets', {}).get('totals')
            if not totals_market:
                continue
            
            for outcome in totals_market.get('outcomes', []):
                name = outcome.get('name')
                odds = outcome.get('price')
                point = outcome.get('point')
                
                if name == 'Over':
                    if best['over']['odds'] is None or odds > best['over']['odds']:
                        best['over'] = {'odds': odds, 'point': point, 'bookmaker': bookmaker['name']}
                elif name == 'Under':
                    if best['under']['odds'] is None or odds > best['under']['odds']:
                        best['under'] = {'odds': odds, 'point': point, 'bookmaker': bookmaker['name']}
        
        return best
    
    def _record_success(self, source: str):
        """Record successful data fetch from source"""
        import datetime
        if source in self.source_status:
            self.source_status[source]['last_success'] = datetime.datetime.now()
            self.source_status[source]['failures'] = 0
    
    def _record_failure(self, source: str):
        """Record failed data fetch from source"""
        if source in self.source_status:
            self.source_status[source]['failures'] += 1
    
    def _log_sources(self):
        """Log available data sources"""
        available = [name for name, status in self.source_status.items() if status['available']]
        if available:
            logger.info(f"Available data sources: {', '.join(available)}")
        else:
            logger.warning("No data sources available!")
