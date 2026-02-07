"""
Line Shopping Strategy
Always get the best available odds

Logic:
- Compare same bet across all sportsbooks
- Find best odds for each side
- Calculate CLV potential

Example:
Lakers ML: FanDuel -110, DraftKings -105, BetMGM -108
-> Recommend DraftKings -105 (best value)
"""

from typing import Dict, List
from utils.logger import setup_logger

logger = setup_logger("line_shopping")


class LineShoppingStrategy:
    """
    Always get the best available odds
    """
    
    def __init__(self, min_difference: int = 5):
        """
        Initialize line shopping strategy
        
        Args:
            min_difference: Minimum odds difference to recommend (in cents, e.g., 5 = 5 cents)
        """
        self.min_difference = min_difference
        logger.info(f"LineShoppingStrategy initialized with min difference: {min_difference} cents")
    
    def find_best_odds(self, game: Dict, odds: Dict) -> Dict:
        """
        Find best odds across all sportsbooks for each bet type
        
        Args:
            game: Game information
            odds: Odds from all bookmakers
            
        Returns:
            Dictionary with best odds for each bet type
        """
        best_odds = {
            'game_id': game.get('id'),
            'sport': game.get('sport'),
            'home_team': game.get('home_team'),
            'away_team': game.get('away_team'),
            'moneyline': self._find_best_moneyline(game, odds),
            'spread': self._find_best_spread(game, odds),
            'totals': self._find_best_totals(game, odds)
        }
        
        return best_odds
    
    def get_recommendations(self, game: Dict, odds: Dict) -> List[Dict]:
        """
        Get line shopping recommendations with significant differences
        
        Args:
            game: Game information
            odds: Odds from all bookmakers
            
        Returns:
            List of recommendations where there's meaningful line shopping value
        """
        recommendations = []
        
        # Find best odds for each bet type
        best_odds = self.find_best_odds(game, odds)
        
        # Check moneyline
        ml_recs = self._check_moneyline_recommendations(game, odds, best_odds['moneyline'])
        recommendations.extend(ml_recs)
        
        # Check spread
        spread_recs = self._check_spread_recommendations(game, odds, best_odds['spread'])
        recommendations.extend(spread_recs)
        
        # Check totals
        totals_recs = self._check_totals_recommendations(game, odds, best_odds['totals'])
        recommendations.extend(totals_recs)
        
        if recommendations:
            logger.info(f"Found {len(recommendations)} line shopping opportunities")
        
        return recommendations
    
    def _find_best_moneyline(self, game: Dict, odds: Dict) -> Dict:
        """Find best moneyline odds"""
        best = {
            'home': {'odds': None, 'bookmaker': None},
            'away': {'odds': None, 'bookmaker': None}
        }
        
        home_team = game.get('home_team')
        away_team = game.get('away_team')
        
        for bookmaker in odds.get('bookmakers', []):
            bookmaker_name = bookmaker.get('name')
            h2h_market = bookmaker.get('markets', {}).get('h2h')
            
            if not h2h_market:
                continue
            
            for outcome in h2h_market.get('outcomes', []):
                team = outcome.get('name')
                odds_value = outcome.get('price')
                
                # For moneyline, higher odds are better (more payout)
                if team == home_team:
                    if best['home']['odds'] is None or self._is_better_odds(odds_value, best['home']['odds']):
                        best['home'] = {'odds': odds_value, 'bookmaker': bookmaker_name}
                elif team == away_team:
                    if best['away']['odds'] is None or self._is_better_odds(odds_value, best['away']['odds']):
                        best['away'] = {'odds': odds_value, 'bookmaker': bookmaker_name}
        
        return best
    
    def _find_best_spread(self, game: Dict, odds: Dict) -> Dict:
        """Find best spread odds"""
        best = {
            'home': {'odds': None, 'point': None, 'bookmaker': None},
            'away': {'odds': None, 'point': None, 'bookmaker': None}
        }
        
        home_team = game.get('home_team')
        away_team = game.get('away_team')
        
        for bookmaker in odds.get('bookmakers', []):
            bookmaker_name = bookmaker.get('name')
            spread_market = bookmaker.get('markets', {}).get('spreads')
            
            if not spread_market:
                continue
            
            for outcome in spread_market.get('outcomes', []):
                team = outcome.get('name')
                odds_value = outcome.get('price')
                point = outcome.get('point')
                
                if team == home_team:
                    if best['home']['odds'] is None or self._is_better_odds(odds_value, best['home']['odds']):
                        best['home'] = {
                            'odds': odds_value,
                            'point': point,
                            'bookmaker': bookmaker_name
                        }
                elif team == away_team:
                    if best['away']['odds'] is None or self._is_better_odds(odds_value, best['away']['odds']):
                        best['away'] = {
                            'odds': odds_value,
                            'point': point,
                            'bookmaker': bookmaker_name
                        }
        
        return best
    
    def _find_best_totals(self, game: Dict, odds: Dict) -> Dict:
        """Find best totals odds"""
        best = {
            'over': {'odds': None, 'point': None, 'bookmaker': None},
            'under': {'odds': None, 'point': None, 'bookmaker': None}
        }
        
        for bookmaker in odds.get('bookmakers', []):
            bookmaker_name = bookmaker.get('name')
            totals_market = bookmaker.get('markets', {}).get('totals')
            
            if not totals_market:
                continue
            
            for outcome in totals_market.get('outcomes', []):
                name = outcome.get('name')  # 'Over' or 'Under'
                odds_value = outcome.get('price')
                point = outcome.get('point')
                
                if name == 'Over':
                    if best['over']['odds'] is None or self._is_better_odds(odds_value, best['over']['odds']):
                        best['over'] = {
                            'odds': odds_value,
                            'point': point,
                            'bookmaker': bookmaker_name
                        }
                elif name == 'Under':
                    if best['under']['odds'] is None or self._is_better_odds(odds_value, best['under']['odds']):
                        best['under'] = {
                            'odds': odds_value,
                            'point': point,
                            'bookmaker': bookmaker_name
                        }
        
        return best
    
    def _check_moneyline_recommendations(self, game: Dict, all_odds: Dict, best: Dict) -> List[Dict]:
        """Check if there's meaningful line shopping value in moneyline"""
        recommendations = []
        
        for side in ['home', 'away']:
            best_odds_value = best[side].get('odds')
            best_bookmaker = best[side].get('bookmaker')
            
            if not best_odds_value or not best_bookmaker:
                continue
            
            # Find worst odds for comparison
            worst_odds_value = None
            worst_bookmaker = None
            
            team = game.get('home_team') if side == 'home' else game.get('away_team')
            
            for bookmaker in all_odds.get('bookmakers', []):
                h2h_market = bookmaker.get('markets', {}).get('h2h')
                if not h2h_market:
                    continue
                
                for outcome in h2h_market.get('outcomes', []):
                    if outcome.get('name') == team:
                        odds_value = outcome.get('price')
                        if worst_odds_value is None or self._is_worse_odds(odds_value, worst_odds_value):
                            worst_odds_value = odds_value
                            worst_bookmaker = bookmaker.get('name')
            
            # Calculate difference
            if worst_odds_value and self._odds_difference(best_odds_value, worst_odds_value) >= self.min_difference:
                recommendations.append({
                    'game_id': game.get('id'),
                    'sport': game.get('sport'),
                    'home_team': game.get('home_team'),
                    'away_team': game.get('away_team'),
                    'bet_type': 'moneyline',
                    'selection': team,
                    'best_odds': best_odds_value,
                    'best_bookmaker': best_bookmaker,
                    'worst_odds': worst_odds_value,
                    'worst_bookmaker': worst_bookmaker,
                    'difference': self._odds_difference(best_odds_value, worst_odds_value),
                    'strategy': 'line_shopping'
                })
        
        return recommendations
    
    def _check_spread_recommendations(self, game: Dict, all_odds: Dict, best: Dict) -> List[Dict]:
        """Check if there's meaningful line shopping value in spread"""
        recommendations = []
        
        for side in ['home', 'away']:
            best_odds_value = best[side].get('odds')
            best_point = best[side].get('point')
            best_bookmaker = best[side].get('bookmaker')
            
            if not best_odds_value or not best_bookmaker:
                continue
            
            # Find worst odds at same point
            worst_odds_value = None
            worst_bookmaker = None
            
            team = game.get('home_team') if side == 'home' else game.get('away_team')
            
            for bookmaker in all_odds.get('bookmakers', []):
                spread_market = bookmaker.get('markets', {}).get('spreads')
                if not spread_market:
                    continue
                
                for outcome in spread_market.get('outcomes', []):
                    if outcome.get('name') == team and outcome.get('point') == best_point:
                        odds_value = outcome.get('price')
                        if worst_odds_value is None or self._is_worse_odds(odds_value, worst_odds_value):
                            worst_odds_value = odds_value
                            worst_bookmaker = bookmaker.get('name')
            
            if worst_odds_value and self._odds_difference(best_odds_value, worst_odds_value) >= self.min_difference:
                recommendations.append({
                    'game_id': game.get('id'),
                    'sport': game.get('sport'),
                    'home_team': game.get('home_team'),
                    'away_team': game.get('away_team'),
                    'bet_type': 'spread',
                    'selection': f"{team} {best_point}",
                    'best_odds': best_odds_value,
                    'best_bookmaker': best_bookmaker,
                    'worst_odds': worst_odds_value,
                    'worst_bookmaker': worst_bookmaker,
                    'difference': self._odds_difference(best_odds_value, worst_odds_value),
                    'strategy': 'line_shopping'
                })
        
        return recommendations
    
    def _check_totals_recommendations(self, game: Dict, all_odds: Dict, best: Dict) -> List[Dict]:
        """Check if there's meaningful line shopping value in totals"""
        recommendations = []
        
        for side in ['over', 'under']:
            best_odds_value = best[side].get('odds')
            best_point = best[side].get('point')
            best_bookmaker = best[side].get('bookmaker')
            
            if not best_odds_value or not best_bookmaker:
                continue
            
            # Find worst odds at same point
            worst_odds_value = None
            worst_bookmaker = None
            
            for bookmaker in all_odds.get('bookmakers', []):
                totals_market = bookmaker.get('markets', {}).get('totals')
                if not totals_market:
                    continue
                
                for outcome in totals_market.get('outcomes', []):
                    if outcome.get('name') == side.title() and outcome.get('point') == best_point:
                        odds_value = outcome.get('price')
                        if worst_odds_value is None or self._is_worse_odds(odds_value, worst_odds_value):
                            worst_odds_value = odds_value
                            worst_bookmaker = bookmaker.get('name')
            
            if worst_odds_value and self._odds_difference(best_odds_value, worst_odds_value) >= self.min_difference:
                recommendations.append({
                    'game_id': game.get('id'),
                    'sport': game.get('sport'),
                    'home_team': game.get('home_team'),
                    'away_team': game.get('away_team'),
                    'bet_type': 'total',
                    'selection': f"{side.title()} {best_point}",
                    'best_odds': best_odds_value,
                    'best_bookmaker': best_bookmaker,
                    'worst_odds': worst_odds_value,
                    'worst_bookmaker': worst_bookmaker,
                    'difference': self._odds_difference(best_odds_value, worst_odds_value),
                    'strategy': 'line_shopping'
                })
        
        return recommendations
    
    def _is_better_odds(self, odds1: int, odds2: int) -> bool:
        """Check if odds1 is better than odds2 (higher payout)"""
        # For positive odds, higher is better
        # For negative odds, closer to 0 is better (less risk)
        if odds1 > 0 and odds2 > 0:
            return odds1 > odds2
        elif odds1 < 0 and odds2 < 0:
            return odds1 > odds2  # -105 is better than -110
        elif odds1 > 0:
            return True  # Positive odds always better than negative
        else:
            return False
    
    def _is_worse_odds(self, odds1: int, odds2: int) -> bool:
        """Check if odds1 is worse than odds2"""
        return not self._is_better_odds(odds1, odds2) and odds1 != odds2
    
    def _odds_difference(self, better_odds: int, worse_odds: int) -> int:
        """Calculate the difference between odds in cents"""
        return abs(better_odds - worse_odds)
