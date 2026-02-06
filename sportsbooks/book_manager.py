"""
Sportsbook Manager
Coordinates connections to multiple sportsbooks and aggregates odds
"""

from typing import Dict, List, Optional
from utils.logger import setup_logger
import random


logger = setup_logger("sportsbook_manager")


class SportsbookManager:
    """
    Manages connections to multiple sportsbooks
    Aggregates odds for comparison and arbitrage detection
    """
    
    def __init__(self, enabled_books: Dict[str, bool]):
        """
        Initialize sportsbook manager
        
        Args:
            enabled_books: Dict of book names to enabled status
        """
        self.books = {}
        
        # Initialize enabled sportsbooks
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
        
        logger.info(f"Initialized {len(self.books)} sportsbooks: {list(self.books.keys())}")
    
    def get_all_odds(self, sport: str, game: str) -> Dict[str, Dict]:
        """
        Get odds from all books for a specific game
        
        Args:
            sport: Sport name
            game: Game identifier
            
        Returns:
            Dict of sportsbook -> odds dict
        """
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
        return list(self.books.keys())
