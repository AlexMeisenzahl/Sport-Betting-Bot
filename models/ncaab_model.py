"""NCAAB (College Basketball) Predictive Model"""
from typing import Dict
import random
from utils.logger import setup_logger

logger = setup_logger("ncaab_model")

class NCAABModel:
    """NCAAB model - Similar to NBA but with more variance"""
    
    def __init__(self):
        logger.info("NCAAB Model initialized")
        self.home_advantage = 4.0  # Slightly higher than NBA
    
    def predict(self, game: Dict) -> Dict:
        """Predict college basketball game"""
        # More variance in college
        kenpom_diff = random.uniform(-15, 15)
        
        predicted_spread = kenpom_diff * 0.5 + self.home_advantage
        
        return {'predicted_spread': round(predicted_spread, 1), 'confidence': 0.64}
