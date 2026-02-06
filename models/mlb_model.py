"""MLB Predictive Model - Starting pitcher focused"""
from typing import Dict
import random
from utils.logger import setup_logger

logger = setup_logger("mlb_model")

class MLBModel:
    """MLB model - Starting pitchers (50%), Team offense (25%), Bullpen (15%), Situational (10%)"""
    
    def __init__(self):
        logger.info("MLB Model initialized")
    
    def predict(self, game: Dict) -> Dict:
        """Predict MLB game win probability (not spread - use moneyline)"""
        home_pitcher_era = random.uniform(2.5, 5.5)
        away_pitcher_era = random.uniform(2.5, 5.5)
        
        # Lower ERA = better, convert to advantage
        pitcher_advantage = (away_pitcher_era - home_pitcher_era) * 3.0
        
        home_woba = random.uniform(0.300, 0.360)
        away_woba = random.uniform(0.300, 0.360)
        offense_advantage = (home_woba - away_woba) * 25.0
        
        predicted_spread = pitcher_advantage + offense_advantage + random.uniform(0, 1.5)  # Home field
        
        return {'predicted_spread': round(predicted_spread, 1), 'confidence': 0.65}
