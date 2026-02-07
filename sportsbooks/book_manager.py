"""
Sportsbook Manager
Coordinates connections to multiple sportsbooks and aggregates odds
Now uses FREE web scraping - NO API KEYS REQUIRED
"""

from typing import Dict, List, Optional
from utils.logger import setup_logger
from sportsbooks.odds_scraper import OddsScraper
from sportsbooks.espn_client import ESPNClient
import random


logger = setup_logger("sportsbook_manager")


class SportsbookManager:
    """
    Manages connections to multiple sportsbooks
    Aggregates odds for comparison and arbitrage detection
    """
    
    def __init__(self, enabled_books: Dict[str, bool], use_free_odds: bool = True, 
                 rate_limit_seconds: int = 5, cache_duration_minutes: int = 2):
        """
        Initialize sportsbook manager
        
        Args:
            enabled_books: Dict of book names to enabled status
            use_free_odds: If True, use free web scraping instead of APIs (default)
            rate_limit_seconds: Seconds between scraping requests (default: 5)
            cache_duration_minutes: How long to cache odds data (default: 2)
        """
        self.books = {}
        self.use_free_odds = use_free_odds
        
        # Initialize free odds scraper (NO API KEYS REQUIRED)
        if use_free_odds:
            try:
                self.odds_scraper = OddsScraper(
                    rate_limit_seconds=rate_limit_seconds,
                    cache_duration_minutes=cache_duration_minutes
                )
                self.espn_client = ESPNClient()
                logger.info(f"Initialized FREE odds scraping - NO API KEYS REQUIRED")
                logger.info(f"Rate limit: {rate_limit_seconds}s, Cache: {cache_duration_minutes}min")
            except Exception as e:
                logger.warning(f"Failed to initialize free odds scraper: {e}")
                logger.warning("Falling back to mock sportsbook APIs")
                self.use_free_odds = False
                self.odds_scraper = None
                self.espn_client = None
        
        # Initialize mock sportsbook APIs (for paper trading fallback)
        if not use_free_odds:
            for book_name, enabled in enabled_books.items():
                if enabled:
                    # In paper trading mode, use mock APIs
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
        
        if use_free_odds:
            logger.info("SportsbookManager using FREE web scraping")
        else:
            logger.info(f"Initialized {len(self.books)} mock sportsbooks: {list(self.books.keys())}")
    
    def get_all_odds(self, sport: str, game: str) -> Dict[str, Dict]:
        """
        Get odds from all books for a specific game
        Uses FREE web scraping when enabled
        
        Args:
            sport: Sport name
            game: Game identifier
            
        Returns:
            Dict of sportsbook -> odds dict
        """
        # Use free odds scraper if enabled
        if self.use_free_odds and self.odds_scraper:
            try:
                all_odds = self.odds_scraper.fetch_odds(sport, game)
                if all_odds:
                    logger.debug(f"Retrieved odds from {len(all_odds)} sportsbooks via scraping")
                    return all_odds
                else:
                    logger.warning("Free odds scraper returned no data, falling back to mock")
            except Exception as e:
                logger.error(f"Error fetching odds from scraper: {e}")
                logger.warning("Falling back to mock data")
        
        # Fallback to mock APIs
        all_odds = {}
        for book_name, book_api in self.books.items():
            try:
                odds = book_api.get_odds(sport, game)
                if odds:
                    all_odds[book_name] = odds
            except Exception as e:
                logger.error(f"Error fetching odds from {book_name}: {e}")
        
        return all_odds
    
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
        all_odds = self.get_all_odds(sport, game)
        
        best_book = None
        best_odds = None
        
        for book_name, odds in all_odds.items():
            if bet_type in odds and side in odds[bet_type]:
                current_odds = odds[bet_type][side]
                
                # Higher is better for American odds (both positive and negative)
                if best_odds is None or current_odds > best_odds:
                    best_odds = current_odds
                    best_book = book_name
        
        if best_book:
            logger.debug(f"Best odds for {game} {bet_type} {side}: {best_book} at {best_odds}")
            return (best_book, best_odds)
        
        return None
    
    def check_book_status(self, book_name: str) -> Dict:
        """
        Check status of a specific sportsbook
        
        Args:
            book_name: Sportsbook name
            
        Returns:
            Status dict with connection info
        """
        if book_name not in self.books:
            return {
                'connected': False,
                'error': 'Book not enabled'
            }
        
        book = self.books[book_name]
        return book.get_status()
    
    def get_available_books(self) -> List[str]:
        """Get list of available sportsbook names"""
        if self.use_free_odds and self.odds_scraper:
            # When using free scraping, we can get odds from multiple books
            return ['fanduel', 'draftkings', 'betmgm', 'caesars', 'pointsbet']
        return list(self.books.keys())
    
    def get_espn_scoreboard(self, sport: str) -> Optional[Dict]:
        """
        Get ESPN scoreboard for a sport (FREE API)
        
        Args:
            sport: Sport name
            
        Returns:
            Scoreboard data dict or None
        """
        if self.use_free_odds and self.espn_client:
            try:
                return self.espn_client.get_scoreboard(sport)
            except Exception as e:
                logger.error(f"Error fetching ESPN scoreboard: {e}")
        return None
    
    def get_espn_teams(self, sport: str) -> Optional[List[Dict]]:
        """
        Get ESPN teams for a sport (FREE API)
        
        Args:
            sport: Sport name
            
        Returns:
            List of team dicts or None
        """
        if self.use_free_odds and self.espn_client:
            try:
                return self.espn_client.get_teams(sport)
            except Exception as e:
                logger.error(f"Error fetching ESPN teams: {e}")
        return None
