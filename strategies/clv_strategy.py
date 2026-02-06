"""
Closing Line Value (CLV) Strategy with Predictive Models
Build statistical models to predict game outcomes
Bet when model shows value vs current line
Track if bets beat closing line (key metric for long-term profit)
"""

from typing import Dict, Optional
from utils.logger import setup_logger


logger = setup_logger("clv_strategy")


class CLVStrategy:
    """
    Use predictive models to find value bets
    Track Closing Line Value - THE KEY METRIC for long-term profitability
    """
    
    def __init__(self, sport: str, min_edge_points: float = 1.5, confidence_threshold: float = 0.60):
        """
        Initialize CLV strategy
        
        Args:
            sport: Sport name (nba, nfl, mlb, etc.)
            min_edge_points: Minimum edge in points/goals to bet
            confidence_threshold: Minimum model confidence (0-1)
        """
        self.sport = sport
        self.min_edge_points = min_edge_points
        self.confidence_threshold = confidence_threshold
        self.model = self._load_sport_model(sport)
        
        logger.info(f"CLV Strategy initialized for {sport} with min edge: {min_edge_points} points")
    
    def _load_sport_model(self, sport: str):
        """Load sport-specific predictive model"""
        if sport == 'nba':
            from models.nba_model import NBAModel
            return NBAModel()
        elif sport == 'nfl':
            from models.nfl_model import NFLModel
            return NFLModel()
        elif sport == 'mlb':
            from models.mlb_model import MLBModel
            return MLBModel()
        elif sport == 'nhl':
            from models.nhl_model import NHLModel
            return NHLModel()
        elif sport == 'soccer':
            from models.soccer_model import SoccerModel
            return SoccerModel()
        elif sport == 'ncaaf':
            from models.ncaaf_model import NCAAFModel
            return NCAAFModel()
        elif sport == 'ncaab':
            from models.ncaab_model import NCAABModel
            return NCAABModel()
        else:
            logger.warning(f"No model available for {sport}")
            return None
    
    def predict_game(self, game: Dict) -> Optional[Dict]:
        """
        Use statistical model to predict outcome
        
        Inputs:
        - Team stats (offense, defense, pace)
        - Situational factors (home/away, rest, injuries)
        - Historical matchups
        - Advanced metrics
        
        Output:
        - Predicted spread
        - Confidence level
        
        Args:
            game: Game dict with teams and relevant data
            
        Returns:
            Prediction dict with spread and confidence
        """
        if not self.model:
            return None
        
        try:
            prediction = self.model.predict(game)
            logger.debug(f"Model prediction for {game['home']} vs {game['away']}: {prediction['predicted_spread']:.1f}")
            return prediction
        except Exception as e:
            logger.error(f"Error predicting game: {e}")
            return None
    
    def find_value_bets(self, game: Dict, current_line: float) -> Optional[Dict]:
        """
        Compare model prediction vs current line
        
        Model: Lakers -7.5
        Current: Lakers -5.5
        Edge: 2 points (bet Lakers)
        
        Only bet if edge > threshold (1.5-2 points)
        
        Args:
            game: Game dict
            current_line: Current spread line
            
        Returns:
            Value bet dict if edge exists, None otherwise
        """
        prediction = self.predict_game(game)
        
        if not prediction:
            return None
        
        predicted_spread = prediction['predicted_spread']
        confidence = prediction['confidence']
        
        # Check confidence threshold
        if confidence < self.confidence_threshold:
            logger.debug(f"Confidence too low: {confidence:.2f} < {self.confidence_threshold}")
            return None
        
        # Calculate edge
        edge = abs(predicted_spread - current_line)
        
        # Determine which side to bet
        if predicted_spread < current_line - self.min_edge_points:
            # Model predicts home team wins by more than line suggests
            side = 'home'
            bet_line = current_line
            edge_points = current_line - predicted_spread
        elif predicted_spread > current_line + self.min_edge_points:
            # Model predicts away team covers
            side = 'away'
            bet_line = current_line
            edge_points = predicted_spread - current_line
        else:
            # No significant edge
            return None
        
        logger.info(f"Value bet found: {game['home']} vs {game['away']}")
        logger.info(f"  Predicted: {predicted_spread:.1f}, Current: {current_line:.1f}, Edge: {edge_points:.1f}")
        
        return {
            'game': game,
            'side': side,
            'bet_line': bet_line,
            'predicted_spread': predicted_spread,
            'edge_points': edge_points,
            'confidence': confidence,
            'expected_value': edge_points * confidence  # Simple EV calculation
        }
    
    def calculate_clv(self, bet: Dict, closing_line: float) -> float:
        """
        Calculate Closing Line Value
        
        After game:
        Your bet: Lakers -5.5
        Closing line: Lakers -8.0
        CLV: +2.5 points ✓
        
        Track this metric - if consistently positive, 
        you WILL be profitable long-term (proven)
        
        Args:
            bet: Bet dict with bet_line
            closing_line: Final line at game time
            
        Returns:
            CLV in points (positive is good)
        """
        bet_line = bet['bet_line']
        side = bet['side']
        
        # Calculate CLV based on which side was bet
        if side == 'home':
            # Bet home team
            # If closing line moved away from home (became more negative), CLV is positive
            clv = closing_line - bet_line
        else:
            # Bet away team
            # If closing line moved toward away (became less negative), CLV is positive
            clv = bet_line - closing_line
        
        logger.info(f"CLV: Bet at {bet_line:.1f}, Closed at {closing_line:.1f}, CLV: {clv:+.1f} points")
        
        return clv
    
    def calculate_win_probability(self, predicted_spread: float) -> float:
        """
        Convert predicted spread to win probability
        
        Uses standard deviation of NFL spreads (~14 points)
        
        Args:
            predicted_spread: Predicted point spread
            
        Returns:
            Win probability (0-1)
        """
        # Simplified conversion - in production, use sport-specific std dev
        if self.sport in ['nba', 'ncaab']:
            std_dev = 12.0
        elif self.sport in ['nfl', 'ncaaf']:
            std_dev = 14.0
        elif self.sport == 'mlb':
            std_dev = 1.8
        elif self.sport == 'nhl':
            std_dev = 1.3
        else:
            std_dev = 10.0
        
        # Use normal distribution approximation
        import math
        z_score = predicted_spread / std_dev
        win_prob = 0.5 + 0.5 * math.erf(z_score / math.sqrt(2))
        
        return win_prob
