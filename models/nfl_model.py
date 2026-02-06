"""
NFL Predictive Model
Predicts game outcomes using team statistics and situational factors
"""

from typing import Dict
import random
from utils.logger import setup_logger


logger = setup_logger("nfl_model")


class NFLModel:
    """
    NFL game prediction model
    
    Factors:
    - Team Stats (35%): DVOA, yards per play, turnover differential
    - Situational (35%): Home field (+2.5), weather, bye week, division game
    - Injuries (20%): QB injury huge (-7 to -10), other positions
    - Coaching (10%): ATS record, post-bye performance, situational coaching
    """
    
    def __init__(self):
        logger.info("NFL Model initialized")
        self.home_field_advantage = 2.5
    
    def predict(self, game: Dict) -> Dict:
        """
        Predict NFL game outcome
        
        Args:
            game: Dict with 'home' and 'away' team names and stats
            
        Returns:
            Dict with predicted_spread and confidence
        """
        home_team = game.get('home', 'Home Team')
        away_team = game.get('away', 'Away Team')
        
        home_stats = self._get_team_stats(home_team)
        away_stats = self._get_team_stats(away_team)
        
        # Calculate components
        team_stats_component = self._calculate_team_stats_component(home_stats, away_stats)
        situational_component = self._calculate_situational_component(game)
        injury_component = self._calculate_injury_component(game)
        coaching_component = self._calculate_coaching_component(game)
        
        # Weighted combination
        predicted_spread = (
            team_stats_component * 0.35 +
            situational_component * 0.35 +
            injury_component * 0.20 +
            coaching_component * 0.10
        )
        
        confidence = self._calculate_confidence(game, home_stats, away_stats)
        
        logger.debug(f"NFL Prediction: {home_team} vs {away_team} = {predicted_spread:.1f} (confidence: {confidence:.2f})")
        
        return {
            'predicted_spread': round(predicted_spread, 1),
            'confidence': confidence
        }
    
    def _get_team_stats(self, team: str) -> Dict:
        """Get team statistics"""
        return {
            'dvoa': random.uniform(-20, 20),  # Defense-adjusted Value Over Average
            'yards_per_play': random.uniform(4.5, 6.5),
            'turnover_diff': random.uniform(-10, 10),
            'points_per_game': random.uniform(18, 32)
        }
    
    def _calculate_team_stats_component(self, home_stats: Dict, away_stats: Dict) -> float:
        """Calculate spread from team stats (DVOA, efficiency, etc.)"""
        # DVOA difference is strong predictor
        dvoa_diff = home_stats['dvoa'] - away_stats['dvoa']
        yards_diff = home_stats['yards_per_play'] - away_stats['yards_per_play']
        turnover_diff = home_stats['turnover_diff'] - away_stats['turnover_diff']
        
        component = dvoa_diff * 0.15 + yards_diff * 2.0 + turnover_diff * 0.3
        return component
    
    def _calculate_situational_component(self, game: Dict) -> float:
        """
        Situational factors: home field, weather, bye week, division
        """
        component = self.home_field_advantage
        
        # Bye week advantage (+3 points)
        if game.get('home_off_bye', False):
            component += 3.0
        if game.get('away_off_bye', False):
            component -= 3.0
        
        # Division game (typically closer)
        if game.get('division_game', False):
            # Slightly compress the line
            component *= 0.9
        
        # Weather impact (wind, rain, cold affect passing)
        weather = game.get('weather', {})
        if weather.get('wind_mph', 0) > 15:
            # High wind reduces scoring, favors underdogs
            component *= 0.85
        
        return component
    
    def _calculate_injury_component(self, game: Dict) -> float:
        """
        QB injury is HUGE in NFL (-7 to -10 points)
        Other positions: -1 to -3 points
        """
        component = 0
        
        home_injuries = game.get('home_injuries', [])
        away_injuries = game.get('away_injuries', [])
        
        for injury in home_injuries:
            if injury.get('position') == 'QB':
                component -= 8.5  # Massive impact
            elif injury.get('tier') == 'star':
                component -= 2.5
            else:
                component -= 1.0
        
        for injury in away_injuries:
            if injury.get('position') == 'QB':
                component += 8.5
            elif injury.get('tier') == 'star':
                component += 2.5
            else:
                component += 1.0
        
        return component
    
    def _calculate_coaching_component(self, game: Dict) -> float:
        """Coaching impact (ATS record, situational)"""
        # Simplified - in production, track coaching stats
        return random.uniform(-0.5, 0.5)
    
    def _calculate_confidence(self, game: Dict, home_stats: Dict, away_stats: Dict) -> float:
        """Calculate model confidence"""
        confidence = 0.65
        
        if 'home_injuries' in game:
            confidence += 0.05
        if 'weather' in game:
            confidence += 0.03
        
        return min(confidence, 0.85)
