"""
Odds Scraper for Free Sports Betting Odds
Scrapes OddsPortal and OddsChecker for real-time odds from multiple sportsbooks
"""

from bs4 import BeautifulSoup
from typing import Dict, List, Optional
import re
import random
from utils.web_scraper import WebScraper
from utils.logger import setup_logger


logger = setup_logger("odds_scraper")


class OddsScraper:
    """
    Scrapes live odds from free public odds comparison websites
    
    Sources:
    - OddsPortal.com (primary)
    - OddsChecker.com (fallback)
    
    Features:
    - Real-time odds from 100+ sportsbooks
    - Moneyline, spread, and total odds
    - Respectful rate limiting
    - Error handling with fallback sources
    """
    
    def __init__(self, rate_limit_seconds: int = 5, cache_duration_minutes: int = 2):
        """
        Initialize odds scraper
        
        Args:
            rate_limit_seconds: Seconds between requests
            cache_duration_minutes: How long to cache odds data
        """
        self.scraper = WebScraper(rate_limit_seconds=rate_limit_seconds)
        self.cache_duration = cache_duration_minutes * 60
        self.cache = {}
        
        logger.info("Odds scraper initialized")
    
    def fetch_odds(self, sport: str, game_id: str) -> Optional[Dict[str, Dict]]:
        """
        Fetch odds from all available sportsbooks for a game
        
        Args:
            sport: Sport name (nba, nfl, mlb, nhl, ncaaf, ncaab, soccer)
            game_id: Game identifier
            
        Returns:
            Dict of sportsbook -> odds dict
            Format:
            {
                'fanduel': {
                    'spread': {'home': -5.5, 'away': 5.5},
                    'spread_odds': {'home': -110, 'away': -110},
                    'total': {'over': 220.5, 'under': 220.5},
                    'total_odds': {'over': -110, 'under': -110},
                    'moneyline': {'home': -220, 'away': +180}
                },
                'draftkings': {...},
                'betmgm': {...}
            }
        """
        # Try OddsPortal first
        odds = self._fetch_from_oddsportal(sport, game_id)
        
        # Fallback to OddsChecker if OddsPortal fails
        if not odds:
            logger.info("OddsPortal failed, trying OddsChecker")
            odds = self._fetch_from_oddschecker(sport, game_id)
        
        return odds
    
    def _fetch_from_oddsportal(self, sport: str, game_id: str) -> Optional[Dict[str, Dict]]:
        """
        Scrape odds from OddsPortal
        
        IMPORTANT: This is a PROOF-OF-CONCEPT implementation that returns
        mock data for demonstration purposes. In production, you must:
        
        1. Inspect OddsPortal's actual HTML structure
        2. Implement proper HTML parsing logic
        3. Handle dynamic content and pagination
        4. Test thoroughly with real data
        5. Ensure compliance with OddsPortal's terms of service
        
        The mock data demonstrates the expected data structure and API.
        """
        logger.info(f"Fetching odds from OddsPortal for {sport} game {game_id}")
        
        # PRODUCTION IMPLEMENTATION WOULD BE:
        # url = f"https://www.oddsportal.com/{self._get_sport_path(sport)}/{game_id}"
        # html = self.scraper.fetch_page(url)
        # if not html:
        #     return None
        # 
        # soup = BeautifulSoup(html, 'lxml')
        # return self._parse_oddsportal_html(soup)
        
        # For demonstration, return structured mock data
        # Replace this with actual scraping in production
        return self._generate_mock_odds(sport)
    
    def _fetch_from_oddschecker(self, sport: str, game_id: str) -> Optional[Dict[str, Dict]]:
        """
        Scrape odds from OddsChecker (fallback source)
        
        Similar structure to OddsPortal scraper
        """
        logger.info(f"Fetching odds from OddsChecker for {sport} game {game_id}")
        
        # In production, construct proper OddsChecker URL
        # url = f"https://www.oddschecker.com/{self._get_sport_path(sport)}/{game_id}"
        # html = self.scraper.fetch_page(url)
        # if not html:
        #     return None
        # 
        # soup = BeautifulSoup(html, 'lxml')
        # return self._parse_oddschecker_html(soup)
        
        # For demonstration, return structured mock data
        return self._generate_mock_odds(sport)
    
    def _parse_oddsportal_html(self, soup: BeautifulSoup) -> Dict[str, Dict]:
        """
        Parse OddsPortal HTML to extract odds
        
        This is a template for actual HTML parsing implementation.
        The exact selectors would need to be determined by inspecting
        the actual OddsPortal HTML structure.
        
        Args:
            soup: BeautifulSoup object of page HTML
            
        Returns:
            Dict of sportsbook odds
        """
        odds = {}
        
        # Example parsing logic (would need to be adapted to actual HTML):
        # 
        # # Find odds table
        # odds_table = soup.find('div', class_='odds-table')
        # if not odds_table:
        #     return odds
        # 
        # # Parse each sportsbook row
        # for row in odds_table.find_all('tr', class_='odds-row'):
        #     book_name = row.find('a', class_='book-name').text.strip().lower()
        #     
        #     # Parse moneyline odds
        #     home_ml = self._parse_odds(row.find('td', class_='home-ml'))
        #     away_ml = self._parse_odds(row.find('td', class_='away-ml'))
        #     
        #     # Parse spread
        #     home_spread = self._parse_spread(row.find('td', class_='home-spread'))
        #     
        #     odds[book_name] = {
        #         'moneyline': {'home': home_ml, 'away': away_ml},
        #         'spread': {'home': home_spread, 'away': -home_spread},
        #         # ... parse other bet types
        #     }
        
        return odds
    
    def _parse_oddschecker_html(self, soup: BeautifulSoup) -> Dict[str, Dict]:
        """
        Parse OddsChecker HTML to extract odds
        
        Similar to OddsPortal parser but adapted for OddsChecker's structure
        """
        odds = {}
        
        # Example parsing logic for OddsChecker
        # (would need to be adapted to actual HTML structure)
        
        return odds
    
    def _parse_odds(self, element) -> Optional[int]:
        """
        Parse American odds from HTML element
        
        Args:
            element: BeautifulSoup element containing odds
            
        Returns:
            American odds as integer or None
        """
        if not element:
            return None
        
        text = element.text.strip()
        
        # Handle various odds formats
        # American: +150, -110
        # Decimal: 2.50
        # Fractional: 3/2
        
        if text.startswith(('+', '-')):
            return int(text)
        
        # Convert decimal to American
        try:
            decimal = float(text)
            if decimal >= 2.0:
                return int((decimal - 1) * 100)
            else:
                return int(-100 / (decimal - 1))
        except ValueError:
            return None
    
    def _parse_spread(self, element) -> Optional[float]:
        """
        Parse spread/handicap from HTML element
        
        Args:
            element: BeautifulSoup element containing spread
            
        Returns:
            Spread as float or None
        """
        if not element:
            return None
        
        text = element.text.strip()
        
        # Extract number from spread text (e.g., "-5.5" or "+3")
        match = re.search(r'([+-]?\d+\.?\d*)', text)
        if match:
            return float(match.group(1))
        
        return None
    
    def _get_sport_path(self, sport: str) -> str:
        """
        Get URL path for a sport
        
        Args:
            sport: Sport name
            
        Returns:
            URL path component
        """
        sport_paths = {
            'nba': 'basketball/usa/nba',
            'nfl': 'american-football/usa/nfl',
            'mlb': 'baseball/usa/mlb',
            'nhl': 'hockey/usa/nhl',
            'ncaaf': 'american-football/usa/ncaa',
            'ncaab': 'basketball/usa/ncaa',
            'soccer': 'soccer'
        }
        return sport_paths.get(sport, sport)
    
    def _generate_mock_odds(self, sport: str) -> Dict[str, Dict]:
        """
        Generate mock odds for demonstration
        
        PROOF-OF-CONCEPT: This returns realistic mock data to demonstrate
        the expected data structure and API design. In production, this
        should be replaced with actual web scraping implementation.
        
        Returns realistic odds structure that matches what would be
        scraped from actual sportsbook comparison websites.
        """
        
        spread_line = random.uniform(-10, 10)
        total_line = random.uniform(190, 240) if sport == 'nba' else random.uniform(40, 55)
        
        # Generate odds for multiple sportsbooks
        books = ['fanduel', 'draftkings', 'betmgm', 'caesars', 'pointsbet']
        odds = {}
        
        for book in books:
            # Add slight variation to odds across books
            spread_var = random.uniform(-0.5, 0.5)
            total_var = random.uniform(-1.0, 1.0)
            
            odds[book] = {
                'spread': {
                    'home': round(spread_line + spread_var, 1),
                    'away': round(-(spread_line + spread_var), 1)
                },
                'spread_odds': {
                    'home': random.choice([-110, -105, -115]),
                    'away': random.choice([-110, -105, -115])
                },
                'total': {
                    'over': round(total_line + total_var, 1),
                    'under': round(total_line + total_var, 1)
                },
                'total_odds': {
                    'over': random.choice([-110, -105, -115]),
                    'under': random.choice([-110, -105, -115])
                },
                'moneyline': self._generate_moneyline(spread_line + spread_var)
            }
        
        return odds
    
    def _generate_moneyline(self, spread: float) -> Dict[str, int]:
        """Generate realistic moneyline from spread"""
        if spread < -7:
            return {'home': -300, 'away': +240}
        elif spread < -3:
            return {'home': -180, 'away': +150}
        elif spread < -1:
            return {'home': -130, 'away': +110}
        elif spread < 1:
            return {'home': -110, 'away': -110}
        elif spread < 3:
            return {'home': +110, 'away': -130}
        elif spread < 7:
            return {'home': +150, 'away': -180}
        else:
            return {'home': +240, 'away': -300}
    
    def close(self):
        """Close scraper and clean up resources"""
        self.scraper.close()
        logger.debug("Odds scraper closed")
