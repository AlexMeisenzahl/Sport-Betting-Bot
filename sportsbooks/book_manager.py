"""
Hybrid Sportsbook Manager
Coordinates multiple data sources (free scraping + paid APIs) with automatic fallback
Supports priority-based data source selection
"""

from typing import Dict, List, Optional
from utils.logger import setup_logger
import random

logger = setup_logger("sportsbook_manager")


class SportsbookManager:
    """
    Hybrid sportsbook manager supporting multiple data sources:
    - Free web scraping (OddsPortal, OddsChecker)
    - Paid APIs (The Odds API)
    - Free stats APIs (ESPN)
    
    Features:
    - Priority-based fallback: Try sources in configured order
    - Automatic failover: If one source fails, try the next
    - Clear logging: Shows which source was used
    - Status reporting: Get data source availability status
    """
    
    def __init__(self, config: Dict, odds_api_client=None):
        """
        Initialize hybrid sportsbook manager
        
        Args:
            config: Full configuration dict with data_sources section
            odds_api_client: Optional OddsAPIClient instance (legacy support)
        """
        self.config = config
        self.data_sources_config = config.get('data_sources', {})
        self.priority_order = self.data_sources_config.get('priority_order', ['odds_scraping', 'the_odds_api'])
        
        # Initialize scrapers (free)
        self.scrapers = {}
        self._initialize_scrapers()
        
        # Initialize The Odds API client (paid)
        self.odds_api_client = None
        self._initialize_odds_api(odds_api_client)
        
        # Store enabled books configuration
        sportsbooks_config = config.get('sportsbooks', {})
        self.enabled_books = {
            book: sportsbooks_config.get(book, {}).get('enabled', False)
            for book in ['fanduel', 'draftkings', 'betmgm', 'caesars', 'pointsbet']
        }
        
        # Initialize legacy mock APIs (backward compatibility)
        self.books = {}
        if not self.scrapers and not self.odds_api_client:
            # Fallback to mock APIs if no data sources available
            self._initialize_mock_apis()
        
        # Log initialization
        self._log_initialization()
    
    def _initialize_scrapers(self):
        """Initialize free web scraping data sources"""
        scraping_config = self.data_sources_config.get('odds_scraping', {})
        
        if not scraping_config.get('enabled', False):
            logger.info("Free web scraping disabled in config")
            return
        
        try:
            from sportsbooks.scrapers import OddsPortalScraper, OddsCheckerScraper
            
            # Get scraper settings
            sources = scraping_config.get('sources', ['oddsportal', 'oddschecker'])
            rate_config = scraping_config.get('rate_limiting', {})
            cache_config = scraping_config.get('cache', {})
            ua_config = scraping_config.get('user_agents', {})
            
            # Scraper initialization parameters
            scraper_kwargs = {
                'rate_limit_delay': rate_config.get('delay_between_requests', 6.0),
                'cache_ttl_minutes': cache_config.get('ttl_minutes', 5),
                'rotate_user_agents': ua_config.get('rotate', True)
            }
            
            # Initialize enabled scrapers
            if 'oddsportal' in sources:
                try:
                    self.scrapers['oddsportal'] = OddsPortalScraper(**scraper_kwargs)
                    logger.info("✓ OddsPortal scraper initialized")
                except Exception as e:
                    logger.warning(f"Failed to initialize OddsPortal scraper: {e}")
            
            if 'oddschecker' in sources:
                try:
                    self.scrapers['oddschecker'] = OddsCheckerScraper(**scraper_kwargs)
                    logger.info("✓ OddsChecker scraper initialized")
                except Exception as e:
                    logger.warning(f"Failed to initialize OddsChecker scraper: {e}")
        
        except ImportError as e:
            logger.warning(f"Scraping dependencies not available: {e}")
            logger.warning("Install with: pip install beautifulsoup4 lxml fake-useragent")
    
    def _initialize_odds_api(self, odds_api_client=None):
        """Initialize The Odds API client (paid)"""
        # Use provided client (legacy) or create new one
        if odds_api_client:
            self.odds_api_client = odds_api_client
            logger.info("Using provided Odds API client")
            return
        
        # Check if The Odds API is enabled in config
        api_config = self.data_sources_config.get('the_odds_api', {})
        
        if not api_config.get('enabled', False):
            logger.info("The Odds API disabled in config")
            return
        
        api_key = api_config.get('api_key', '')
        
        if not api_key:
            logger.info("The Odds API key not provided - API disabled")
            return
        
        try:
            from odds_api_client import OddsAPIClient
            
            # Initialize with live mode (since API key is provided)
            self.odds_api_client = OddsAPIClient(
                api_key=api_key,
                use_mock=False
            )
            
            # Configure cache and rate limiting
            cache_config = api_config.get('cache', {})
            if cache_config.get('enabled', True):
                cache_ttl_min = cache_config.get('ttl_minutes', 1)
                self.odds_api_client.cache_ttl = cache_ttl_min * 60
            
            rate_limit = api_config.get('rate_limit', {})
            if 'min_interval_seconds' in rate_limit:
                self.odds_api_client.min_request_interval = rate_limit['min_interval_seconds']
            
            logger.info("✓ The Odds API client initialized (LIVE mode)")
            
        except Exception as e:
            logger.error(f"Failed to initialize The Odds API client: {e}")
    
    def _initialize_mock_apis(self):
        """Initialize mock book APIs (fallback/backward compatibility)"""
        for book_name, enabled in self.enabled_books.items():
            if enabled:
                try:
                    if book_name == 'fanduel':
                        from sportsbooks.fanduel import FanDuelAPI
                        self.books[book_name] = FanDuelAPI()
                    elif book_name == 'draftkings':
                        from sportsbooks.draftkings import DraftKingsAPI
                        self.books[book_name] = DraftKingsAPI()
                    elif book_name == 'betmgm':
                        from sportsbooks.betmgm import BetMGMAPI
                        self.books[book_name] = BetMGMAPI()
                    elif book_name == 'caesars':
                        from sportsbooks.caesars import CaesarsAPI
                        self.books[book_name] = CaesarsAPI()
                    elif book_name == 'pointsbet':
                        from sportsbooks.pointsbet import PointsBetAPI
                        self.books[book_name] = PointsBetAPI()
                except Exception as e:
                    logger.error(f"Failed to initialize {book_name}: {e}")
        
        if self.books:
            logger.info(f"Mock APIs initialized for {len(self.books)} books (fallback mode)")
    
    def _log_initialization(self):
        """Log initialization summary"""
        logger.info("=" * 60)
        logger.info("SPORTSBOOK MANAGER - Hybrid Data Sources")
        logger.info("=" * 60)
        logger.info(f"Priority Order: {' → '.join(self.priority_order)}")
        logger.info(f"Free Scraping: {'✓ Enabled' if self.scrapers else '✗ Disabled'}")
        if self.scrapers:
            logger.info(f"  Scrapers: {', '.join(self.scrapers.keys())}")
        logger.info(f"The Odds API: {'✓ Enabled' if self.odds_api_client else '✗ Disabled'}")
        if self.odds_api_client:
            mode = "MOCK" if getattr(self.odds_api_client, 'use_mock', True) else "LIVE"
            logger.info(f"  Mode: {mode}")
        logger.info("=" * 60)
    
    def get_odds(self, sport: str, game_id: str) -> Dict[str, Dict]:
        """
        Get odds for a specific game using priority fallback
        
        Args:
            sport: Sport name (nba, nfl, etc.)
            game_id: Game identifier
            
        Returns:
            Dict of sportsbook -> odds dict
        """
        # Try each source in priority order
        for source in self.priority_order:
            try:
                if source == 'odds_scraping' and self.scrapers:
                    odds = self._get_odds_from_scrapers(sport, game_id)
                    if odds:
                        logger.info(f"✓ Got odds from free scraping for {game_id}")
                        return odds
                
                elif source == 'the_odds_api' and self.odds_api_client:
                    odds = self._get_odds_from_api(sport, game_id)
                    if odds:
                        logger.info(f"✓ Got odds from The Odds API for {game_id}")
                        return odds
                
            except Exception as e:
                logger.warning(f"Failed to get odds from {source}: {e}")
                continue  # Try next source
        
        # All sources failed, try legacy mock APIs
        if self.books:
            logger.debug(f"Falling back to mock APIs for {game_id}")
            return self._get_mock_odds(sport, game_id)
        
        logger.warning(f"No odds available for {sport} game {game_id}")
        return {}
    
    def get_all_odds(self, sport: str, game: str) -> Dict[str, Dict]:
        """
        Get odds from all books for a specific game (legacy method)
        
        Args:
            sport: Sport name
            game: Game identifier
            
        Returns:
            Dict of sportsbook -> odds dict
        """
        return self.get_odds(sport, game)
    
    def get_all_games_today(self, sport: str) -> List[Dict]:
        """
        Get all games for a sport today from available sources
        
        Args:
            sport: Sport name
            
        Returns:
            List of game dicts
        """
        # Try each source in priority order
        for source in self.priority_order:
            try:
                if source == 'odds_scraping' and self.scrapers:
                    games = self._get_games_from_scrapers(sport)
                    if games:
                        logger.info(f"✓ Got {len(games)} games from free scraping for {sport}")
                        return games
                
                elif source == 'the_odds_api' and self.odds_api_client:
                    games = self._get_games_from_api(sport)
                    if games:
                        logger.info(f"✓ Got {len(games)} games from The Odds API for {sport}")
                        return games
                
            except Exception as e:
                logger.warning(f"Failed to get games from {source}: {e}")
                continue
        
        logger.warning(f"No games available for {sport}")
        return []
    
    def _get_odds_from_scrapers(self, sport: str, game_id: str) -> Dict[str, Dict]:
        """Get odds using free web scrapers"""
        all_odds = {}
        
        # Try each scraper
        for scraper_name, scraper in self.scrapers.items():
            try:
                odds = scraper.get_odds(sport, game_id)
                if odds:
                    # Merge odds from this scraper
                    for book, book_odds in odds.items():
                        if book not in all_odds:
                            all_odds[book] = book_odds
            except Exception as e:
                logger.debug(f"Scraper {scraper_name} failed: {e}")
        
        return all_odds
    
    def _get_odds_from_api(self, sport: str, game_id: str) -> Dict[str, Dict]:
        """Get odds using The Odds API"""
        try:
            # Fetch all odds for the sport
            odds_data = self.odds_api_client.get_odds(sport)
            
            # Format odds
            formatted_odds = self.odds_api_client.format_odds_for_strategy(odds_data)
            
            # Find the specific game
            if game_id in formatted_odds:
                return formatted_odds[game_id]
            
            # Try partial match
            game_id_lower = game_id.lower()
            for game_key, odds in formatted_odds.items():
                if game_id_lower in game_key.lower() or game_key.lower() in game_id_lower:
                    return odds
            
            return {}
            
        except Exception as e:
            logger.error(f"Error fetching odds from API: {e}")
            return {}
    
    def _get_games_from_scrapers(self, sport: str) -> List[Dict]:
        """Get games using free web scrapers"""
        all_games = []
        seen_game_ids = set()
        
        # Try each scraper
        for scraper_name, scraper in self.scrapers.items():
            try:
                games = scraper.get_games_today(sport)
                # Deduplicate by game_id
                for game in games:
                    game_id = game.get('game_id')
                    if game_id and game_id not in seen_game_ids:
                        all_games.append(game)
                        seen_game_ids.add(game_id)
            except Exception as e:
                logger.debug(f"Scraper {scraper_name} failed: {e}")
        
        return all_games
    
    def _get_games_from_api(self, sport: str) -> List[Dict]:
        """Get games using The Odds API"""
        try:
            odds_data = self.odds_api_client.get_odds(sport)
            
            # Convert to game list
            games = []
            for event in odds_data:
                games.append({
                    'game_id': event.get('id', ''),
                    'home': event.get('home_team', ''),
                    'away': event.get('away_team', ''),
                    'sport': sport,
                    'start_time': event.get('commence_time', ''),
                    'source': 'the_odds_api'
                })
            
            return games
            
        except Exception as e:
            logger.error(f"Error fetching games from API: {e}")
            return []
    
    def _get_mock_odds(self, sport: str, game: str) -> Dict[str, Dict]:
        """Get odds from mock book APIs (fallback)"""
        all_odds = {}
        
        for book_name, book_api in self.books.items():
            try:
                odds = book_api.get_odds(sport, game)
                if odds:
                    all_odds[book_name] = odds
            except Exception as e:
                logger.error(f"Error fetching odds from {book_name}: {e}")
        
        return all_odds
    
    def get_all_games_odds(self, sport: str) -> Dict[str, Dict[str, Dict]]:
        """
        Get odds for all games in a sport
        
        Args:
            sport: Sport name
            
        Returns:
            Dict of game -> sportsbook -> odds
        """
        if self.odds_api_client and not getattr(self.odds_api_client, 'use_mock', True):
            try:
                odds_data = self.odds_api_client.get_odds(sport)
                return self.odds_api_client.format_odds_for_strategy(odds_data)
            except Exception as e:
                logger.error(f"Error fetching all games odds: {e}")
                return {}
        else:
            # For scrapers and mock mode, return empty (need individual calls)
            return {}
    
    def find_best_odds(self, sport: str, game: str, bet_type: str, side: str) -> Optional[tuple]:
        """
        Find which book offers best odds for a specific bet
        
        Args:
            sport: Sport name
            game: Game identifier
            bet_type: 'spread', 'total', 'moneyline', 'prop'
            side: Which side of the bet
            
        Returns:
            (book_name, odds) tuple or None
        """
        all_odds = self.get_odds(sport, game)
        
        best_book = None
        best_odds = None
        
        for book_name, odds in all_odds.items():
            if bet_type in odds and side in odds[bet_type]:
                current_odds = odds[bet_type][side]
                
                # Handle both simple odds (number) and complex odds (dict with 'price')
                if isinstance(current_odds, dict):
                    current_odds = current_odds.get('price', current_odds.get('odds', 0))
                
                # Higher is better for American odds
                if best_odds is None or current_odds > best_odds:
                    best_odds = current_odds
                    best_book = book_name
        
        if best_book:
            logger.debug(f"Best odds for {game} {bet_type} {side}: {best_book} at {best_odds}")
            return (best_book, best_odds)
        
        return None
    
    def get_data_source_status(self) -> Dict:
        """
        Get status of all data sources
        
        Returns:
            Dict with data source status information
        """
        return {
            'priority_order': self.priority_order,
            'free_scraping': {
                'enabled': bool(self.scrapers),
                'scrapers': list(self.scrapers.keys()) if self.scrapers else []
            },
            'the_odds_api': {
                'enabled': self.odds_api_client is not None,
                'mode': 'LIVE' if self.odds_api_client and not getattr(self.odds_api_client, 'use_mock', True) else 'MOCK'
            },
            'mock_apis': {
                'enabled': bool(self.books),
                'books': list(self.books.keys()) if self.books else []
            }
        }
    
    def track_line_movement(self, sport: str, game: str, bet_type: str) -> List[Dict]:
        """
        Track line movements across sportsbooks
        
        Args:
            sport: Sport name
            game: Game identifier
            bet_type: Type of bet to track
            
        Returns:
            List of line movement data points
        """
        all_odds = self.get_odds(sport, game)
        
        movements = []
        for book_name, odds in all_odds.items():
            if bet_type in odds:
                movements.append({
                    'book': book_name,
                    'timestamp': 'current',
                    'odds': odds[bet_type]
                })
        
        return movements
    
    def check_book_status(self, book_name: str) -> Dict:
        """
        Check status of a specific sportsbook
        
        Args:
            book_name: Sportsbook name
            
        Returns:
            Status dict with connection info
        """
        # Check if using API
        if self.odds_api_client and not getattr(self.odds_api_client, 'use_mock', True):
            return {
                'connected': True,
                'mode': 'live_api',
                'book': book_name,
                'enabled': book_name in self.enabled_books and self.enabled_books[book_name]
            }
        
        # Check scrapers
        if self.scrapers:
            return {
                'connected': True,
                'mode': 'free_scraping',
                'book': book_name,
                'available': True
            }
        
        # Check mock APIs
        if book_name not in self.books:
            return {
                'connected': False,
                'error': 'Book not enabled'
            }
        
        book = self.books[book_name]
        return book.get_status()
    
    def get_available_books(self) -> List[str]:
        """Get list of available sportsbook names"""
        if self.odds_api_client and not getattr(self.odds_api_client, 'use_mock', True):
            return [book for book, enabled in self.enabled_books.items() if enabled]
        elif self.scrapers:
            # Scrapers typically support major books
            return ['fanduel', 'draftkings', 'betmgm', 'caesars', 'pointsbet']
        else:
            return list(self.books.keys())
