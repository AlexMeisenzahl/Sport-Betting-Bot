"""
Generic Web Scraper Utilities
Provides reusable scraping functionality with rate limiting and error handling
"""

import time
import requests
from typing import Optional, Dict
from fake_useragent import UserAgent
from utils.logger import setup_logger


logger = setup_logger("web_scraper")


class WebScraper:
    """
    Generic web scraper with anti-detection features
    - User-agent rotation
    - Rate limiting
    - Session management
    - Error handling
    """
    
    def __init__(self, rate_limit_seconds: int = 5):
        """
        Initialize web scraper
        
        Args:
            rate_limit_seconds: Minimum seconds between requests
        """
        self.rate_limit = rate_limit_seconds
        self.last_request_time = 0
        self.session = requests.Session()
        self.ua = UserAgent()
        
        logger.info(f"Web scraper initialized with {rate_limit_seconds}s rate limit")
    
    def get_headers(self) -> Dict[str, str]:
        """
        Get random headers with rotating user agent
        
        Returns:
            Headers dict
        """
        return {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
    
    def fetch_page(self, url: str, timeout: int = 10) -> Optional[str]:
        """
        Fetch a web page with rate limiting and error handling
        
        Args:
            url: URL to fetch
            timeout: Request timeout in seconds
            
        Returns:
            Page HTML content or None on error
        """
        # Enforce rate limiting
        time_since_last = time.time() - self.last_request_time
        if time_since_last < self.rate_limit:
            sleep_time = self.rate_limit - time_since_last
            logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s")
            time.sleep(sleep_time)
        
        try:
            response = self.session.get(
                url,
                headers=self.get_headers(),
                timeout=timeout
            )
            self.last_request_time = time.time()
            
            response.raise_for_status()
            logger.debug(f"Successfully fetched: {url}")
            return response.text
            
        except requests.exceptions.Timeout:
            logger.error(f"Timeout fetching {url}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
    
    def close(self):
        """Close the session"""
        self.session.close()
        logger.debug("Web scraper session closed")
