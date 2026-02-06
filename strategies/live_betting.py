"""
Live Betting Engine Strategy
In-game betting opportunities

Theory: Live lines lag reality. If watching with a model,
you can beat sportsbook adjustments.
"""

from typing import Dict, List, Optional
from datetime import datetime
from utils.logger import setup_logger
import random


logger = setup_logger("live_betting")


class LiveBettingEngine:
    """
    In-game betting opportunities
    
    Look for:
    1. Overreactions
    2. Momentum Shifts
    3. Situational advantages
    4. Hedging opportunities
    """
    
    def __init__(self, min_edge_percent: float = 5.0):
        """
        Initialize live betting engine
        
        Args:
            min_edge_percent: Minimum edge percentage for live bets
        """
        self.min_edge_percent = min_edge_percent
        self.live_games = {}  # Track games in progress
        logger.info(f"Live Betting Engine initialized with min edge: {min_edge_percent}%")
    
    def monitor_live_games(self, sport: str) -> List[Dict]:
        """
        Track all games in progress:
        - Real-time score
        - Time remaining
        - Current live line
        - Game flow (momentum, pace)
        
        Returns:
            List of live game states
        """
        # In production, fetch real-time game data
        # For now, return mock live games
        
        live_games = []
        
        # Mock live games
        if sport == 'nba':
            live_games = [
                {
                    'game_id': 'nba_live_1',
                    'home': 'Lakers',
                    'away': 'Celtics',
                    'home_score': 65,
                    'away_score': 58,
                    'period': 3,
                    'time_remaining': '8:42',
                    'live_line': -8.5,
                    'pregame_line': -5.5
                }
            ]
        
        # Update internal tracking
        for game in live_games:
            self.live_games[game['game_id']] = game
        
        return live_games
    
    def detect_live_opportunities(self, game: Dict) -> Optional[Dict]:
        """
        Look for:
        
        1. Overreactions
           - Team goes up 10 early
           - Live line moves to -15
           - Model: Should only be -8
           - Bet: Underdog +15
           
        2. Momentum Shifts
           - Team down 8 at halftime
           - Comes out strong in 3Q
           - Line hasn't adjusted yet
           
        3. Situational
           - Star player fouls out
           - Line doesn't adjust immediately
           
        4. Hedging
           - You bet Lakers -6 pregame
           - Lakers up 15 at halftime
           - Live line: Lakers -20
           - Bet: Opponent +20 (middle)
        """
        
        # Calculate expected live line based on game state
        expected_live_line = self.calculate_live_expected_value(game)
        current_live_line = game.get('live_line', 0)
        
        # Check for overreaction
        edge = abs(expected_live_line - current_live_line)
        edge_percent = (edge / abs(current_live_line)) * 100 if current_live_line != 0 else 0
        
        if edge_percent >= self.min_edge_percent:
            # Determine which side to bet
            if expected_live_line < current_live_line:
                side = 'home'
                bet_line = current_live_line
            else:
                side = 'away'
                bet_line = current_live_line
            
            opportunity = {
                'game': game,
                'type': 'overreaction',
                'side': side,
                'live_line': current_live_line,
                'expected_line': expected_live_line,
                'edge': edge,
                'edge_percent': edge_percent
            }
            
            logger.info(f"Live opportunity: {game['home']} vs {game['away']}")
            logger.info(f"  Live line: {current_live_line:.1f}, Expected: {expected_live_line:.1f}, Edge: {edge:.1f}")
            
            return opportunity
        
        return None
    
    def calculate_live_expected_value(self, game_state: Dict) -> float:
        """
        Real-time win probability model:
        - Current score
        - Time remaining
        - Possession
        - Timeouts
        - Momentum indicators
        
        Compare to implied probability from live line
        
        Args:
            game_state: Current game state
            
        Returns:
            Expected live line
        """
        home_score = game_state.get('home_score', 0)
        away_score = game_state.get('away_score', 0)
        period = game_state.get('period', 1)
        pregame_line = game_state.get('pregame_line', 0)
        
        # Calculate score differential
        score_diff = home_score - away_score
        
        # Estimate time remaining (as fraction of game)
        sport = 'nba'  # Simplified - would pass sport in production
        if sport == 'nba':
            total_periods = 4
            time_remaining_pct = (total_periods - period + 0.5) / total_periods
        else:
            time_remaining_pct = 0.5
        
        # Expected live line formula:
        # Live line ≈ Score differential + (Pregame line * time_remaining_pct)
        
        # If home team up 10 with half game left, and pregame was -5:
        # Expected: 10 + (-5 * 0.5) = 10 - 2.5 = -7.5
        
        expected_live_line = score_diff + (pregame_line * time_remaining_pct)
        
        # Add small random variance for realism
        expected_live_line += random.uniform(-1, 1)
        
        return round(expected_live_line, 1)
    
    def check_hedging_opportunity(self, pregame_bet: Dict, live_game: Dict) -> Optional[Dict]:
        """
        Check if should hedge a pregame bet
        
        You bet Lakers -6 pregame
        Lakers up 15 at halftime
        Live line: Lakers -20
        Bet: Opponent +20 (middle opportunity)
        
        Args:
            pregame_bet: Original pregame bet
            live_game: Current live game state
            
        Returns:
            Hedge opportunity if it exists
        """
        
        pregame_side = pregame_bet.get('side')
        pregame_line = pregame_bet.get('line')
        live_line = live_game.get('live_line')
        
        # Check for middle opportunity
        # If bet Lakers -6, and live is -20, can bet Celtics +20
        # Win both if Lakers win by 7-19 points
        
        if pregame_side == 'home':
            # Bet home pregame
            middle_width = abs(live_line) - abs(pregame_line)
            if middle_width >= 10:  # At least 10 point middle
                return {
                    'type': 'hedge_middle',
                    'pregame_bet': pregame_bet,
                    'live_bet_side': 'away',
                    'live_line': live_line,
                    'middle_width': middle_width
                }
        else:
            # Bet away pregame
            middle_width = abs(pregame_line) - abs(live_line)
            if middle_width >= 10:
                return {
                    'type': 'hedge_middle',
                    'pregame_bet': pregame_bet,
                    'live_bet_side': 'home',
                    'live_line': live_line,
                    'middle_width': middle_width
                }
        
        return None
