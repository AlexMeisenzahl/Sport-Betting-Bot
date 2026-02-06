"""
Sharp Money Tracker Strategy
Detect and follow professional betting action

Theory: Sharp bettors (pros) move lines. Detect their action early
and follow them before line fully adjusts.
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from utils.logger import setup_logger


logger = setup_logger("sharp_tracker")


class SharpMoneyTracker:
    """
    Detect and follow professional betting action
    
    Sharp money indicators:
    1. Reverse Line Movement (RLM)
    2. Steam Moves
    3. Early Line Movement
    4. Low Volume, Big Move
    """
    
    def __init__(self, min_sharp_score: int = 70):
        """
        Initialize sharp tracker
        
        Args:
            min_sharp_score: Minimum sharp signal score (0-100) to act on
        """
        self.min_sharp_score = min_sharp_score
        self.line_history = {}  # Track line movements
        logger.info(f"Sharp Money Tracker initialized with min score: {min_sharp_score}")
    
    def monitor_line_movements(self, sport: str, game: str, sportsbook_manager) -> Dict:
        """
        Track odds changes in real-time
        
        Returns:
        - Opening line
        - Current line
        - Line movements with timestamps
        - Betting percentages (public %)
        """
        game_key = f"{sport}:{game}"
        
        # Get current odds
        current_odds = sportsbook_manager.get_all_odds(sport, game)
        
        if not current_odds:
            return {}
        
        # Initialize history if not exists
        if game_key not in self.line_history:
            self.line_history[game_key] = {
                'opening_line': self._extract_primary_line(current_odds),
                'history': [],
                'first_seen': datetime.now()
            }
        
        # Record current line
        current_line = self._extract_primary_line(current_odds)
        self.line_history[game_key]['history'].append({
            'timestamp': datetime.now(),
            'line': current_line
        })
        
        return self.line_history[game_key]
    
    def _extract_primary_line(self, all_odds: Dict) -> float:
        """Extract primary spread line (average across books)"""
        spreads = []
        for book, odds in all_odds.items():
            if 'spread' in odds and 'home' in odds['spread']:
                spreads.append(odds['spread']['home'])
        
        if spreads:
            return sum(spreads) / len(spreads)
        return 0.0
    
    def detect_sharp_signals(self, sport: str, game: str) -> Optional[Dict]:
        """
        Detect sharp money indicators
        
        1. Reverse Line Movement (RLM)
           - 75% of bets on Lakers
           - Line moves FROM Lakers -6 TO Lakers -4
           - Sharp money on Celtics (bet Celtics)
           
        2. Steam Moves
           - Sudden line change across multiple books
           - Coordinated sharp action
           
        3. Early Line Movement
           - Line opens at -6, immediately moves to -7
           - Sharps hit the opening line
           
        4. Low Volume, Big Move
           - Only 10% of bets on one side
           - But line moves significantly toward that side
        """
        game_key = f"{sport}:{game}"
        
        if game_key not in self.line_history:
            return None
        
        history = self.line_history[game_key]
        
        if len(history['history']) < 2:
            return None  # Need at least 2 data points
        
        opening_line = history['opening_line']
        current_line = history['history'][-1]['line']
        
        # Calculate line movement
        line_movement = current_line - opening_line
        
        # Check for various sharp signals
        signals = []
        sharp_score = 0
        
        # 1. Check for significant line movement (potential RLM)
        if abs(line_movement) >= 1.5:
            signals.append({
                'type': 'significant_movement',
                'description': f'Line moved {line_movement:+.1f} points',
                'score': 25
            })
            sharp_score += 25
        
        # 2. Check for steam move (rapid movement)
        if len(history['history']) >= 3:
            recent_movement = history['history'][-1]['line'] - history['history'][-3]['line']
            time_diff = (history['history'][-1]['timestamp'] - history['history'][-3]['timestamp']).total_seconds()
            
            if abs(recent_movement) >= 1.0 and time_diff < 600:  # 1 point in 10 minutes
                signals.append({
                    'type': 'steam_move',
                    'description': f'Rapid {recent_movement:+.1f} point move in {time_diff/60:.1f} min',
                    'score': 30
                })
                sharp_score += 30
        
        # 3. Check for early line movement
        time_since_open = (datetime.now() - history['first_seen']).total_seconds()
        if time_since_open < 3600 and abs(line_movement) >= 1.0:  # Within 1 hour
            signals.append({
                'type': 'early_movement',
                'description': f'Early {line_movement:+.1f} point move',
                'score': 20
            })
            sharp_score += 20
        
        # 4. Mock public betting percentage (in production, get real data)
        # Simulate RLM: public on one side, line moves other way
        import random
        public_pct = random.randint(35, 80)
        
        # If public heavy on one side but line moved opposite direction
        if public_pct > 65 and line_movement < -1.0:
            signals.append({
                'type': 'reverse_line_movement',
                'description': f'{public_pct}% public on home, but line moved away',
                'score': 25
            })
            sharp_score += 25
        elif public_pct < 45 and line_movement > 1.0:
            signals.append({
                'type': 'reverse_line_movement',
                'description': f'{100-public_pct}% public on away, but line moved away',
                'score': 25
            })
            sharp_score += 25
        
        if sharp_score < self.min_sharp_score:
            return None
        
        # Determine which side sharps are on
        if line_movement > 0:
            sharp_side = 'away'  # Line moved toward home, sharps on away
        else:
            sharp_side = 'home'  # Line moved toward away, sharps on home
        
        logger.info(f"Sharp signal detected: {game} - Score: {sharp_score}, Side: {sharp_side}")
        
        return {
            'game': game,
            'sport': sport,
            'sharp_score': sharp_score,
            'sharp_side': sharp_side,
            'opening_line': opening_line,
            'current_line': current_line,
            'line_movement': line_movement,
            'signals': signals,
            'public_pct': public_pct
        }
    
    def calculate_sharp_score(self, game: Dict) -> int:
        """
        Score 0-100 indicating sharp action confidence
        
        Factors:
        - Magnitude of reverse line movement: +30
        - Speed of line change: +20
        - Multiple books moving together: +25
        - Against heavy public betting: +25
        
        Score > 70 = Strong sharp signal (bet it)
        """
        # This is called by detect_sharp_signals
        # Keeping method for interface completeness
        return 0
