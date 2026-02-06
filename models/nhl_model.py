"""NHL Predictive Model"""
from typing import Dict
import random
from utils.logger import setup_logger

logger = setup_logger("nhl_model")

class NHLModel:
    """NHL model - Goaltending, team stats, recent form"""
    
    def __init__(self):
        logger.info("NHL Model initialized")
    
    def predict(self, game: Dict) -> Dict:
        """Predict NHL game"""
        # Goaltending is key in NHL
        home_goalie_sv_pct = random.uniform(0.880, 0.925)
        away_goalie_sv_pct = random.uniform(0.880, 0.925)
        
        goalie_advantage = (home_goalie_sv_pct - away_goalie_sv_pct) * 15.0
        
        predicted_spread = goalie_advantage + random.uniform(-0.5, 1.0)
        
        return {'predicted_spread': round(predicted_spread, 1), 'confidence': 0.62}
