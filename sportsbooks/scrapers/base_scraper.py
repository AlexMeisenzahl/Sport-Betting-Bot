"""
Base scraper class with rate limiting, caching, and user agent rotation
"""

import time
import requests
from typing import Dict, Optional
from datetime import datetime, timedelta
from utils.logger import setup_logger

try:
    from fake_useragent import UserAgent
    HAS_FAKE_USERAGENT = True
except ImportError:
    HAS_FAKE_USERAGENT = False

logger = setup_logger("base_scraper")


class BaseScraper:
    """
    Base class for web scrapers with common functionality
    - Rate limiting
    - Caching
    - User agent rotation
    - Error handling
    """
    
    def __init__(self, rate_limit_delay: float = 6.0, cache_ttl_minutes: int = 5, rotate_user_agents: bool = True):
        """
        Initialize base scraper
        
        Args:
            rate_limit_delay: Seconds to wait between requests (default: 6 = 10 req/min)
            cache_ttl_minutes: Cache time-to-live in minutes
            rotate_user_agents: Whether to rotate user agents
        """
        self.rate_limit_delay = rate_limit_delay
        self.cache_ttl = timedelta(minutes=cache_ttl_minutes)
        self.rotate_user_agents = rotate_user_agents and HAS_FAKE_USERAGENT
        
        # Initialize user agent rotator
        if self.rotate_user_agents:
            try:
                self.ua = UserAgent()
            except Exception as e:
                logger.warning(f"Failed to initialize UserAgent: {e}")
                self.rotate_user_agents = False
        
        # Rate limiting
        self.last_request_time = None
        
        # Simple cache: {url: (data, timestamp)}
        self.cache = {}
        
        # Session for connection pooling
        self.session = requests.Session()
        
        logger.info(f"Scraper initialized with rate limit: {rate_limit_delay}s, cache TTL: {cache_ttl_minutes}min")
    
    def _rate_limit(self):
        """Enforce rate limiting between requests"""
        if self.last_request_time:
            elapsed = time.time() - self.last_request_time
            if elapsed < self.rate_limit_delay:
                sleep_time = self.rate_limit_delay - elapsed
                logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s")
                time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers with optional user agent rotation"""
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        if self.rotate_user_agents:
            try:
                headers['User-Agent'] = self.ua.random
            except Exception:
                headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        else:
            headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        
        return headers
    
    def _check_cache(self, url: str) -> Optional[str]:
        """Check if cached data is still valid"""
        if url in self.cache:
            data, timestamp = self.cache[url]
            if datetime.now() - timestamp < self.cache_ttl:
                logger.debug(f"Cache hit for {url}")
                return data
            else:
                del self.cache[url]
        return None
    
    def _update_cache(self, url: str, data: str):
        """Update cache with new data"""
        self.cache[url] = (data, datetime.now())
    
    def _fetch_page(self, url: str, use_cache: bool = True) -> Optional[str]:
        """
        Fetch a web page with rate limiting and caching
        
        Args:
            url: URL to fetch
            use_cache: Whether to use cached data if available
            
        Returns:
            Page HTML or None on error
        """
        # Check cache first
        if use_cache:
            cached = self._check_cache(url)
            if cached:
                return cached
        
        # Rate limit
        self._rate_limit()
        
        # Fetch page
        try:
            headers = self._get_headers()
            response = self.session.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            html = response.text
            
            # Cache the result
            if use_cache:
                self._update_cache(url, html)
            
            return html
            
        except requests.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
    
    def clear_cache(self):
        """Clear the cache"""
        self.cache = {}
        logger.debug("Cache cleared")
    
    def close(self):
        """Close the session"""
        self.session.close()
