"""
Sportsbook Manager
Coordinates connections to multiple sportsbooks and aggregates odds
Integrates with The Odds API for live odds data
"""

from typing import Dict, List, Optional
from utils.logger import setup_logger
import random

logger = setup_logger("sportsbook_manager")


class SportsbookManager:
    """
    Manages connections to multiple sportsbooks
    Aggregates odds for comparison and arbitrage detection
    Now supports both mock (paper trading) and live API data
    """
    
    def __init__(self, enabled_books: Dict[str, bool], odds_api_client=None):
        """
        Initialize sportsbook manager
        
        Args:
            enabled_books: Dict of book names to enabled status
            odds_api_client: Optional OddsAPIClient instance for live data
        """
        self.books = {}
        self.odds_api_client = odds_api_client
        self.use_live_api = odds_api_client is not None and not odds_api_client.use_mock
        
        # Store enabled books configuration
        self.enabled_books = enabled_books
        
        # If using live API, we don't need individual book APIs
        if not self.use_live_api:
            # Initialize enabled sportsbooks with mock APIs
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
        
        mode = "LIVE API" if self.use_live_api else "MOCK"
        logger.info(f"SportsbookManager initialized in {mode} mode with {len(enabled_books)} enabled books")
    
    def get_all_odds(self, sport: str, game: str) -> Dict[str, Dict]:
        """
        Get odds from all books for a specific game
        
        Args:
            sport: Sport name
            game: Game identifier (format: "Away @ Home")
            
        Returns:
            Dict of sportsbook -> odds dict
        """
        if self.use_live_api:
            return self._get_live_odds(sport, game)
        else:
            return self._get_mock_odds(sport, game)
    
    def _get_live_odds(self, sport: str, game: str) -> Dict[str, Dict]:
        """Get odds from live API"""
        try:
            # Fetch all odds for the sport
            odds_data = self.odds_api_client.get_odds(sport)
            
            # Format odds
            formatted_odds = self.odds_api_client.format_odds_for_strategy(odds_data)
            
            # Find the specific game
            if game in formatted_odds:
                return formatted_odds[game]
            
            # Try to match by team names (case-insensitive partial match)
            game_lower = game.lower()
            for game_key, odds in formatted_odds.items():
                if game_lower in game_key.lower() or game_key.lower() in game_lower:
                    return odds
            
            logger.warning(f"No odds found for game: {game}")
            return {}
            
        except Exception as e:
            logger.error(f"Error fetching live odds: {e}")
            return {}
    
    def _get_mock_odds(self, sport: str, game: str) -> Dict[str, Dict]:
        """Get odds from mock book APIs"""
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
        if self.use_live_api:
            try:
                odds_data = self.odds_api_client.get_odds(sport)
                return self.odds_api_client.format_odds_for_strategy(odds_data)
            except Exception as e:
                logger.error(f"Error fetching all games odds: {e}")
                return {}
        else:
            # For mock mode, return empty (individual calls needed)
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
        all_odds = self.get_all_odds(sport, game)
        
        best_book = None
        best_odds = None
        
        for book_name, odds in all_odds.items():
            if bet_type in odds and side in odds[bet_type]:
                current_odds = odds[bet_type][side]
                
                # Handle both simple odds (number) and complex odds (dict with 'price')
                if isinstance(current_odds, dict):
                    current_odds = current_odds.get('price', current_odds.get('odds', 0))
                
                # Higher is better for American odds (both positive and negative)
                if best_odds is None or current_odds > best_odds:
                    best_odds = current_odds
                    best_book = book_name
        
        if best_book:
            logger.debug(f"Best odds for {game} {bet_type} {side}: {best_book} at {best_odds}")
            return (best_book, best_odds)
        
        return None
    
    def track_line_movement(self, sport: str, game: str, bet_type: str) -> List[Dict]:
        """
        Track line movements across sportsbooks for sharp money detection
        
        Args:
            sport: Sport name
            game: Game identifier
            bet_type: Type of bet to track
            
        Returns:
            List of line movement data points
        """
        # This would require historical data tracking
        # For now, return current snapshot
        all_odds = self.get_all_odds(sport, game)
        
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
        if self.use_live_api:
            return {
                'connected': True,
                'mode': 'live_api',
                'book': book_name,
                'enabled': book_name in self.enabled_books and self.enabled_books[book_name]
            }
        
        if book_name not in self.books:
            return {
                'connected': False,
                'error': 'Book not enabled'
            }
        
        book = self.books[book_name]
        return book.get_status()
    
    def get_available_books(self) -> List[str]:
        """Get list of available sportsbook names"""
        if self.use_live_api:
            return [book for book, enabled in self.enabled_books.items() if enabled]
        return list(self.books.keys())

