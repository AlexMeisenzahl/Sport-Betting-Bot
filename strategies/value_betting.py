"""
Value Betting Strategy
Find positive expected value (+EV) bets

Logic:
- Calculate implied probability from odds
- Compare against estimated true probability
- Suggest bet if edge > minimum threshold (default 5%)

Example:
- Odds: +150 (implied prob: 40%)
- True prob estimate: 50%
- Edge: 10% -> BET!
"""

from typing import Dict, List, Optional
from utils.logger import setup_logger

logger = setup_logger("value_betting")


class ValueBettingStrategy:
    """
    Find positive expected value (+EV) bets
    """
    
    def __init__(self, min_edge: float = 0.05):
        """
        Initialize value betting strategy
        
        Args:
            min_edge: Minimum edge required (default: 5%)
        """
        self.min_edge = min_edge
        logger.info(f"ValueBettingStrategy initialized with min edge: {min_edge * 100}%")
    
    def analyze(self, game: Dict, odds: Dict, true_probabilities: Optional[Dict] = None) -> List[Dict]:
        """
        Analyze a game for value betting opportunities
        
        Args:
            game: Game information
            odds: Odds from all bookmakers
            true_probabilities: Estimated true probabilities (optional)
                               If not provided, will use simple model
        
        Returns:
            List of value bet opportunities
        """
        opportunities = []
        
        # If no true probabilities provided, estimate them
        if not true_probabilities:
            true_probabilities = self._estimate_true_probabilities(odds)
        
        # Check each bookmaker for value
        for bookmaker in odds.get('bookmakers', []):
            bookmaker_name = bookmaker.get('name')
            
            # Check moneyline value
            h2h_market = bookmaker.get('markets', {}).get('h2h')
            if h2h_market:
                ml_opportunities = self._check_moneyline_value(
                    game, bookmaker_name, h2h_market, true_probabilities
                )
                opportunities.extend(ml_opportunities)
            
            # Check spread value
            spread_market = bookmaker.get('markets', {}).get('spreads')
            if spread_market:
                spread_opportunities = self._check_spread_value(
                    game, bookmaker_name, spread_market, true_probabilities
                )
                opportunities.extend(spread_opportunities)
            
            # Check totals value
            totals_market = bookmaker.get('markets', {}).get('totals')
            if totals_market:
                totals_opportunities = self._check_totals_value(
                    game, bookmaker_name, totals_market, true_probabilities
                )
                opportunities.extend(totals_opportunities)
        
        # Filter by minimum edge
        opportunities = [opp for opp in opportunities if opp['edge'] >= self.min_edge]
        
        # Sort by edge (highest first)
        opportunities.sort(key=lambda x: x['edge'], reverse=True)
        
        if opportunities:
            logger.info(f"Found {len(opportunities)} value betting opportunities in {game.get('home_team')} vs {game.get('away_team')}")
        
        return opportunities
    
    def _check_moneyline_value(self, game: Dict, bookmaker: str, 
                               market: Dict, true_probs: Dict) -> List[Dict]:
        """Check moneyline for value"""
        opportunities = []
        
        home_team = game.get('home_team')
        away_team = game.get('away_team')
        
        for outcome in market.get('outcomes', []):
            team = outcome.get('name')
            odds = outcome.get('price')
            
            # Get implied probability from odds
            implied_prob = self._odds_to_probability(odds)
            
            # Get true probability
            true_prob = true_probs.get('moneyline', {}).get(team, 0)
            
            if true_prob == 0:
                continue
            
            # Calculate edge
            edge = true_prob - implied_prob
            
            if edge >= self.min_edge:
                opportunities.append({
                    'game_id': game.get('id'),
                    'sport': game.get('sport'),
                    'home_team': home_team,
                    'away_team': away_team,
                    'bet_type': 'moneyline',
                    'selection': team,
                    'odds': odds,
                    'implied_prob': implied_prob,
                    'true_prob': true_prob,
                    'edge': edge,
                    'bookmaker': bookmaker,
                    'strategy': 'value_betting',
                    'confidence': self._calculate_confidence(edge)
                })
        
        return opportunities
    
    def _check_spread_value(self, game: Dict, bookmaker: str,
                           market: Dict, true_probs: Dict) -> List[Dict]:
        """Check spread for value"""
        opportunities = []
        
        home_team = game.get('home_team')
        away_team = game.get('away_team')
        
        for outcome in market.get('outcomes', []):
            team = outcome.get('name')
            odds = outcome.get('price')
            point = outcome.get('point')
            
            implied_prob = self._odds_to_probability(odds)
            
            # For spreads, true probability depends on the line
            # This is simplified - a real model would consider the specific spread
            true_prob = true_probs.get('spread', {}).get(team, 0.5)
            
            edge = true_prob - implied_prob
            
            if edge >= self.min_edge:
                opportunities.append({
                    'game_id': game.get('id'),
                    'sport': game.get('sport'),
                    'home_team': home_team,
                    'away_team': away_team,
                    'bet_type': 'spread',
                    'selection': f"{team} {point}",
                    'odds': odds,
                    'point': point,
                    'implied_prob': implied_prob,
                    'true_prob': true_prob,
                    'edge': edge,
                    'bookmaker': bookmaker,
                    'strategy': 'value_betting',
                    'confidence': self._calculate_confidence(edge)
                })
        
        return opportunities
    
    def _check_totals_value(self, game: Dict, bookmaker: str,
                           market: Dict, true_probs: Dict) -> List[Dict]:
        """Check totals for value"""
        opportunities = []
        
        home_team = game.get('home_team')
        away_team = game.get('away_team')
        
        for outcome in market.get('outcomes', []):
            name = outcome.get('name')  # 'Over' or 'Under'
            odds = outcome.get('price')
            point = outcome.get('point')
            
            implied_prob = self._odds_to_probability(odds)
            
            # For totals, true probability depends on the line
            true_prob = true_probs.get('totals', {}).get(name.lower(), 0.5)
            
            edge = true_prob - implied_prob
            
            if edge >= self.min_edge:
                opportunities.append({
                    'game_id': game.get('id'),
                    'sport': game.get('sport'),
                    'home_team': home_team,
                    'away_team': away_team,
                    'bet_type': 'total',
                    'selection': f"{name} {point}",
                    'odds': odds,
                    'point': point,
                    'implied_prob': implied_prob,
                    'true_prob': true_prob,
                    'edge': edge,
                    'bookmaker': bookmaker,
                    'strategy': 'value_betting',
                    'confidence': self._calculate_confidence(edge)
                })
        
        return opportunities
    
    def _estimate_true_probabilities(self, odds: Dict) -> Dict:
        """
        Estimate true probabilities from market consensus
        
        This is a simplified approach - uses the best available odds
        as a proxy for true probability
        
        Args:
            odds: Odds from all bookmakers
            
        Returns:
            Dictionary with estimated true probabilities
        """
        # Find best odds for each outcome (highest = most value)
        best_odds = {}
        
        for bookmaker in odds.get('bookmakers', []):
            # Moneyline
            h2h_market = bookmaker.get('markets', {}).get('h2h')
            if h2h_market:
                for outcome in h2h_market.get('outcomes', []):
                    team = outcome.get('name')
                    odds_value = outcome.get('price')
                    
                    key = ('moneyline', team)
                    if key not in best_odds or odds_value > best_odds[key]:
                        best_odds[key] = odds_value
        
        # Convert best odds to probabilities
        # Remove vig by adjusting probabilities to sum to 1.0
        true_probs = {'moneyline': {}, 'spread': {}, 'totals': {}}
        
        # Moneyline probabilities
        ml_probs = {}
        total_ml_prob = 0
        for (bet_type, team), odds_value in best_odds.items():
            if bet_type == 'moneyline':
                prob = self._odds_to_probability(odds_value)
                ml_probs[team] = prob
                total_ml_prob += prob
        
        # Remove vig (normalize to 1.0)
        if total_ml_prob > 0:
            for team, prob in ml_probs.items():
                true_probs['moneyline'][team] = prob / total_ml_prob
        
        # For spread and totals, assume 50/50 as baseline
        # (A real model would use more sophisticated estimation)
        true_probs['spread'] = {}
        true_probs['totals'] = {'over': 0.5, 'under': 0.5}
        
        return true_probs
    
    def _odds_to_probability(self, odds: int) -> float:
        """
        Convert American odds to implied probability
        
        Args:
            odds: American odds (e.g., -110, +150)
            
        Returns:
            Implied probability (0-1)
        """
        if odds > 0:
            return 100 / (odds + 100)
        else:
            return abs(odds) / (abs(odds) + 100)
    
    def _calculate_confidence(self, edge: float) -> str:
        """
        Calculate confidence level based on edge size
        
        Args:
            edge: Edge percentage (0-1)
            
        Returns:
            Confidence level string
        """
        if edge >= 0.15:
            return 'very_high'
        elif edge >= 0.10:
            return 'high'
        elif edge >= 0.07:
            return 'medium'
        else:
            return 'low'
