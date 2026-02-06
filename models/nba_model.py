"""
NBA Predictive Model
Predicts game outcomes using team statistics and situational factors
"""

from typing import Dict
import random
from utils.logger import setup_logger


logger = setup_logger("nba_model")


class NBAModel:
    """
    NBA game prediction model
    
    Factors:
    - Team Stats (40%): Off/Def rating, pace, net rating
    - Situational (30%): Home court (+3.5), rest, B2B, travel
    - Injuries (20%): Star out (-5 to -8), starter out (-2 to -3)
    - Matchup History (10%): H2H, style compatibility
    """
    
    def __init__(self):
        logger.info("NBA Model initialized")
        # In production, would load historical data and trained model
        self.home_court_advantage = 3.5
    
    def predict(self, game: Dict) -> Dict:
        """
        Predict NBA game outcome
        
        Args:
            game: Dict with 'home' and 'away' team names and stats
            
        Returns:
            Dict with predicted_spread and confidence
        """
        home_team = game.get('home', 'Home Team')
        away_team = game.get('away', 'Away Team')
        
        # Get team stats (in production, fetch real stats)
        home_stats = self._get_team_stats(home_team)
        away_stats = self._get_team_stats(away_team)
        
        # Calculate components
        team_stats_component = self._calculate_team_stats_component(home_stats, away_stats)
        situational_component = self._calculate_situational_component(game)
        injury_component = self._calculate_injury_component(game)
        matchup_component = self._calculate_matchup_component(home_team, away_team)
        
        # Weighted combination
        predicted_spread = (
            team_stats_component * 0.40 +
            situational_component * 0.30 +
            injury_component * 0.20 +
            matchup_component * 0.10
        )
        
        # Calculate confidence based on data quality and consistency
        confidence = self._calculate_confidence(game, home_stats, away_stats)
        
        logger.debug(f"NBA Prediction: {home_team} vs {away_team} = {predicted_spread:.1f} (confidence: {confidence:.2f})")
        
        return {
            'predicted_spread': round(predicted_spread, 1),
            'confidence': confidence,
            'components': {
                'team_stats': team_stats_component,
                'situational': situational_component,
                'injury': injury_component,
                'matchup': matchup_component
            }
        }
    
    def _get_team_stats(self, team: str) -> Dict:
        """
        Get team statistics
        
        In production: Fetch from nba_api or database
        For now: Generate realistic mock stats
        """
        # Mock stats - in production, fetch real data
        return {
            'offensive_rating': random.uniform(105, 120),
            'defensive_rating': random.uniform(105, 120),
            'net_rating': random.uniform(-5, 10),
            'pace': random.uniform(95, 105),
            'home_record': (random.randint(15, 35), random.randint(5, 25)),
            'away_record': (random.randint(10, 30), random.randint(10, 30))
        }
    
    def _calculate_team_stats_component(self, home_stats: Dict, away_stats: Dict) -> float:
        """
        Calculate spread component from team statistics
        
        Uses offensive and defensive ratings to predict point differential
        """
        # Net rating difference
        home_net = home_stats['net_rating']
        away_net = away_stats['net_rating']
        
        net_rating_diff = home_net - away_net
        
        # Offensive/defensive rating difference
        home_expected_points = home_stats['offensive_rating'] - away_stats['defensive_rating']
        away_expected_points = away_stats['offensive_rating'] - home_stats['defensive_rating']
        
        matchup_diff = home_expected_points - away_expected_points
        
        # Combine
        component = (net_rating_diff + matchup_diff * 0.5) / 1.5
        
        return component
    
    def _calculate_situational_component(self, game: Dict) -> float:
        """
        Calculate spread component from situational factors
        
        - Home court advantage: +3.5 points
        - Rest days: Well-rested team +1-2 points
        - Back-to-back: Team on B2B -3 to -4 points
        - Travel: Long road trip -1 to -2 points
        """
        component = self.home_court_advantage
        
        # Rest advantage
        home_rest = game.get('home_rest_days', 1)
        away_rest = game.get('away_rest_days', 1)
        
        if home_rest > away_rest:
            component += 1.0
        elif away_rest > home_rest:
            component -= 1.0
        
        # Back-to-back disadvantage
        if game.get('home_back_to_back', False):
            component -= 3.5
        if game.get('away_back_to_back', False):
            component += 3.5
        
        return component
    
    def _calculate_injury_component(self, game: Dict) -> float:
        """
        Calculate impact of injuries
        
        - Star player out: -5 to -8 points
        - Starter out: -2 to -3 points
        - Bench player out: -0.5 to -1 point
        """
        component = 0
        
        home_injuries = game.get('home_injuries', [])
        away_injuries = game.get('away_injuries', [])
        
        for injury in home_injuries:
            if injury.get('tier') == 'star':
                component -= 6.5
            elif injury.get('tier') == 'starter':
                component -= 2.5
            else:
                component -= 0.75
        
        for injury in away_injuries:
            if injury.get('tier') == 'star':
                component += 6.5
            elif injury.get('tier') == 'starter':
                component += 2.5
            else:
                component += 0.75
        
        return component
    
    def _calculate_matchup_component(self, home_team: str, away_team: str) -> float:
        """
        Calculate matchup-specific factors
        
        - Historical H2H record
        - Style matchups (pace, 3pt shooting, etc.)
        """
        # Simplified - in production, analyze actual matchup history
        return random.uniform(-1, 1)
    
    def _calculate_confidence(self, game: Dict, home_stats: Dict, away_stats: Dict) -> float:
        """
        Calculate model confidence based on data quality
        
        Higher confidence when:
        - Complete injury information
        - Recent stats available
        - Consistent team performance
        """
        confidence = 0.65  # Base confidence
        
        # Boost confidence if injury info available
        if 'home_injuries' in game and 'away_injuries' in game:
            confidence += 0.05
        
        # Boost if situational data available
        if 'home_rest_days' in game:
            confidence += 0.05
        
        # Cap at 0.85 (never fully certain)
        confidence = min(confidence, 0.85)
        
        return confidence
