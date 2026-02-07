"""
Game Results Tracker
Track game results and settle bets automatically

Data sources (in priority order):
1. The Odds API results endpoint
2. ESPN API (free, no auth required)
3. Manual entry via CLI

Features:
- Fetch final scores
- Determine bet outcomes (win/loss/push)
- Auto-settle bets in PaperTrader
- Store historical results
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from utils.logger import setup_logger

logger = setup_logger("results_tracker")


class GameResultTracker:
    """
    Track game results and settle bets automatically
    """
    
    def __init__(self, odds_api_key: Optional[str] = None, data_dir: str = "data"):
        """
        Initialize results tracker
        
        Args:
            odds_api_key: The Odds API key (optional)
            data_dir: Directory to store results data
        """
        self.odds_api_key = odds_api_key or os.environ.get('THE_ODDS_API_KEY')
        self.data_dir = data_dir
        self.results_file = os.path.join(data_dir, 'results.json')
        self.results_cache = {}
        
        # Load cached results
        self._load_results_cache()
        
        logger.info("GameResultTracker initialized")
    
    def get_game_result(self, sport: str, game_id: str, use_cache: bool = True) -> Optional[Dict]:
        """
        Get final result for a game
        
        Args:
            sport: Sport name (NBA, NFL, etc.)
            game_id: Game identifier
            use_cache: Whether to use cached results
            
        Returns:
            Dictionary with game result or None if not available
        """
        # Check cache first
        if use_cache and game_id in self.results_cache:
            logger.debug(f"Using cached result for game {game_id}")
            return self.results_cache[game_id]
        
        # Try The Odds API first
        if self.odds_api_key:
            result = self._fetch_from_odds_api(sport, game_id)
            if result:
                self._cache_result(game_id, result)
                return result
        
        # Try ESPN API as backup
        result = self._fetch_from_espn(sport, game_id)
        if result:
            self._cache_result(game_id, result)
            return result
        
        logger.warning(f"Could not fetch result for game {game_id}")
        return None
    
    def settle_bets_for_game(self, game_id: str, game_result: Dict, paper_trader) -> int:
        """
        Automatically settle all bets for a completed game
        
        Args:
            game_id: Game identifier
            game_result: Game result dictionary
            paper_trader: PaperTrader instance
            
        Returns:
            Number of bets settled
        """
        # Get all pending bets for this game
        pending_bets = paper_trader.get_bet_history({
            'status': 'pending'
        })
        
        game_bets = [b for b in pending_bets if b.get('game_id') == game_id]
        
        if not game_bets:
            logger.debug(f"No pending bets for game {game_id}")
            return 0
        
        logger.info(f"Settling {len(game_bets)} bets for game {game_id}")
        
        settled_count = 0
        for bet in game_bets:
            result = self._determine_bet_result(bet, game_result)
            if result:
                paper_trader.settle_bet(bet['id'], result)
                settled_count += 1
        
        logger.info(f"Settled {settled_count} bets for game {game_id}")
        return settled_count
    
    def check_and_settle_pending(self, paper_trader, max_age_hours: int = 24) -> Dict:
        """
        Check all pending bets and settle any completed games
        
        Args:
            paper_trader: PaperTrader instance
            max_age_hours: Maximum age of pending bets to check (hours)
            
        Returns:
            Dictionary with settlement statistics
        """
        pending_bets = paper_trader.get_bet_history({'status': 'pending'})
        
        if not pending_bets:
            logger.info("No pending bets to settle")
            return {'total_checked': 0, 'settled': 0, 'errors': 0}
        
        # Filter by age
        cutoff = datetime.now() - timedelta(hours=max_age_hours)
        recent_bets = [b for b in pending_bets 
                      if datetime.fromisoformat(b['timestamp']) > cutoff]
        
        logger.info(f"Checking {len(recent_bets)} pending bets for completed games")
        
        settled = 0
        errors = 0
        checked_games = set()
        
        for bet in recent_bets:
            game_id = bet.get('game_id')
            sport = bet.get('sport')
            
            # Skip if we already checked this game
            if game_id in checked_games:
                continue
            
            checked_games.add(game_id)
            
            # Get game result
            try:
                result = self.get_game_result(sport, game_id)
                if result and result.get('status') == 'final':
                    count = self.settle_bets_for_game(game_id, result, paper_trader)
                    settled += count
            except Exception as e:
                logger.error(f"Error settling game {game_id}: {e}")
                errors += 1
        
        stats = {
            'total_checked': len(recent_bets),
            'games_checked': len(checked_games),
            'settled': settled,
            'errors': errors
        }
        
        logger.info(f"Settlement complete: {settled} bets settled, {errors} errors")
        return stats
    
    def manual_entry(self, game_info: Dict) -> bool:
        """
        Manually enter a game result
        
        Args:
            game_info: Dictionary with game result information
                {
                    'game_id': str,
                    'sport': str,
                    'home_team': str,
                    'away_team': str,
                    'home_score': int,
                    'away_score': int,
                    'status': 'final'
                }
        
        Returns:
            True if successful
        """
        required_fields = ['game_id', 'sport', 'home_team', 'away_team', 'home_score', 'away_score']
        for field in required_fields:
            if field not in game_info:
                logger.error(f"Missing required field: {field}")
                return False
        
        game_info['status'] = 'final'
        game_info['date'] = datetime.now().isoformat()
        game_info['source'] = 'manual'
        
        # Cache the result
        self._cache_result(game_info['game_id'], game_info)
        
        logger.info(f"Manually entered result for {game_info['home_team']} vs {game_info['away_team']}")
        return True
    
    def _fetch_from_odds_api(self, sport: str, game_id: str) -> Optional[Dict]:
        """Fetch result from The Odds API"""
        try:
            from sportsbooks.odds_api import TheOddsAPI
            
            api = TheOddsAPI(api_key=self.odds_api_key)
            sport_key = api.SPORT_KEYS.get(sport.upper())
            
            if not sport_key:
                return None
            
            # The Odds API includes scores in the odds endpoint
            # We need to fetch recent games and check for final status
            url = f"{api.BASE_URL}/sports/{sport_key}/scores"
            params = {
                'apiKey': self.odds_api_key,
                'daysFrom': 3  # Look back 3 days
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            games = response.json()
            
            # Find the specific game
            for game in games:
                if game.get('id') == game_id:
                    if game.get('completed'):
                        return {
                            'game_id': game_id,
                            'home_team': game.get('home_team'),
                            'away_team': game.get('away_team'),
                            'home_score': game.get('scores', [{}])[0].get('score'),
                            'away_score': game.get('scores', [{}])[1].get('score'),
                            'status': 'final',
                            'date': game.get('commence_time'),
                            'source': 'odds_api'
                        }
            
            return None
            
        except Exception as e:
            logger.debug(f"Could not fetch from Odds API: {e}")
            return None
    
    def _fetch_from_espn(self, sport: str, game_id: str) -> Optional[Dict]:
        """Fetch result from ESPN API (free, no auth)"""
        # ESPN API is more complex and would require sport-specific implementations
        # This is a placeholder for the structure
        logger.debug(f"ESPN API fetch not yet implemented for {sport}")
        return None
    
    def _determine_bet_result(self, bet: Dict, game_result: Dict) -> Optional[str]:
        """
        Determine if a bet won, lost, or pushed
        
        Args:
            bet: Bet dictionary
            game_result: Game result dictionary
            
        Returns:
            'win', 'loss', 'push', or None if cannot determine
        """
        bet_type = bet.get('bet_type')
        selection = bet.get('selection')
        
        home_team = game_result.get('home_team')
        away_team = game_result.get('away_team')
        home_score = game_result.get('home_score')
        away_score = game_result.get('away_score')
        
        if home_score is None or away_score is None:
            logger.warning(f"Missing scores for game {game_result.get('game_id')}")
            return None
        
        # Moneyline
        if bet_type == 'moneyline':
            if home_score > away_score and selection == home_team:
                return 'win'
            elif away_score > home_score and selection == away_team:
                return 'win'
            elif home_score == away_score:
                return 'push'
            else:
                return 'loss'
        
        # Spread
        elif bet_type == 'spread':
            # Extract team and point from selection (e.g., "Lakers -5.5")
            parts = selection.split()
            if len(parts) < 2:
                logger.error(f"Invalid spread selection: {selection}")
                return None
            
            team = ' '.join(parts[:-1])
            try:
                point = float(parts[-1])
            except ValueError:
                logger.error(f"Invalid point value in selection: {selection}")
                return None
            
            # Calculate spread result
            if team == home_team:
                result = home_score + point - away_score
            else:
                result = away_score + point - home_score
            
            if result > 0:
                return 'win'
            elif result < 0:
                return 'loss'
            else:
                return 'push'
        
        # Total
        elif bet_type == 'total':
            # Extract over/under and point from selection (e.g., "Over 215.5")
            parts = selection.split()
            if len(parts) < 2:
                logger.error(f"Invalid total selection: {selection}")
                return None
            
            over_under = parts[0].lower()
            try:
                point = float(parts[1])
            except ValueError:
                logger.error(f"Invalid point value in selection: {selection}")
                return None
            
            total = home_score + away_score
            
            if over_under == 'over':
                if total > point:
                    return 'win'
                elif total < point:
                    return 'loss'
                else:
                    return 'push'
            elif over_under == 'under':
                if total < point:
                    return 'win'
                elif total > point:
                    return 'loss'
                else:
                    return 'push'
        
        logger.error(f"Unknown bet type: {bet_type}")
        return None
    
    def _cache_result(self, game_id: str, result: Dict):
        """Cache a game result"""
        self.results_cache[game_id] = result
        self._save_results_cache()
    
    def _load_results_cache(self):
        """Load cached results from file"""
        if not os.path.exists(self.results_file):
            return
        
        try:
            with open(self.results_file, 'r') as f:
                self.results_cache = json.load(f)
            logger.debug(f"Loaded {len(self.results_cache)} cached results")
        except Exception as e:
            logger.error(f"Error loading results cache: {e}")
    
    def _save_results_cache(self):
        """Save cached results to file"""
        try:
            with open(self.results_file, 'w') as f:
                json.dump(self.results_cache, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving results cache: {e}")
