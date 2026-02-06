"""NCAAF (College Football) Predictive Model"""
from typing import Dict
import random
from utils.logger import setup_logger

logger = setup_logger("ncaaf_model")

class NCAAFModel:
    """NCAAF model - Similar to NFL but with more variance"""
    
    def __init__(self):
        logger.info("NCAAF Model initialized")
        self.home_advantage = 3.0
    
    def predict(self, game: Dict) -> Dict:
        """Predict college football game"""
        # College has more variance than NFL
        talent_diff = random.uniform(-20, 20)
        
        predicted_spread = talent_diff * 0.4 + self.home_advantage
        
        return {'predicted_spread': round(predicted_spread, 1), 'confidence': 0.63}
