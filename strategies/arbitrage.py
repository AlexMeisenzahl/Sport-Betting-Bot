"""
Arbitrage Strategy
Find risk-free betting opportunities

Logic:
- Find mismatched odds across books
- Calculate if guaranteed profit exists
- Suggest bet sizing for both sides

Example:
FanDuel: Team A -105
DraftKings: Team B +120
-> Arb opportunity! Bet both for guaranteed profit

Note: Rare but extremely valuable when found
"""

from typing import Dict, List, Optional
from utils.logger import setup_logger

logger = setup_logger("arbitrage")


class ArbitrageStrategy:
    """
    Find risk-free betting opportunities
    """
    
    def __init__(self, min_profit_margin: float = 0.01):
        """
        Initialize arbitrage strategy
        
        Args:
            min_profit_margin: Minimum profit margin required (default: 1%)
        """
        self.min_profit_margin = min_profit_margin
        logger.info(f"ArbitrageStrategy initialized with min profit margin: {min_profit_margin * 100}%")
    
    def find_arbitrage(self, game: Dict, odds: Dict) -> List[Dict]:
        """
        Find arbitrage opportunities in a game
        
        Args:
            game: Game information
            odds: Odds from all bookmakers
            
        Returns:
            List of arbitrage opportunities (if any)
        """
        opportunities = []
        
        # Check moneyline arbitrage
        ml_arbs = self._check_moneyline_arbitrage(game, odds)
        opportunities.extend(ml_arbs)
        
        # Check spread arbitrage (rare but possible)
        spread_arbs = self._check_spread_arbitrage(game, odds)
        opportunities.extend(spread_arbs)
        
        # Check totals arbitrage (rare but possible)
        totals_arbs = self._check_totals_arbitrage(game, odds)
        opportunities.extend(totals_arbs)
        
        if opportunities:
            logger.info(f"🎯 Found {len(opportunities)} ARBITRAGE opportunities!")
        
        return opportunities
    
    def _check_moneyline_arbitrage(self, game: Dict, odds: Dict) -> List[Dict]:
        """Check for moneyline arbitrage"""
        opportunities = []
        
        home_team = game.get('home_team')
        away_team = game.get('away_team')
        
        # Find best odds for each side across all bookmakers
        best_home = {'odds': None, 'bookmaker': None}
        best_away = {'odds': None, 'bookmaker': None}
        
        for bookmaker in odds.get('bookmakers', []):
            bookmaker_name = bookmaker.get('name')
            h2h_market = bookmaker.get('markets', {}).get('h2h')
            
            if not h2h_market:
                continue
            
            for outcome in h2h_market.get('outcomes', []):
                team = outcome.get('name')
                odds_value = outcome.get('price')
                
                if team == home_team:
                    if best_home['odds'] is None or odds_value > best_home['odds']:
                        best_home = {'odds': odds_value, 'bookmaker': bookmaker_name}
                elif team == away_team:
                    if best_away['odds'] is None or odds_value > best_away['odds']:
                        best_away = {'odds': odds_value, 'bookmaker': bookmaker_name}
        
        # Check if arbitrage exists
        if best_home['odds'] and best_away['odds']:
            arb_result = self._calculate_arbitrage(
                best_home['odds'], best_away['odds']
            )
            
            if arb_result['is_arbitrage'] and arb_result['profit_margin'] >= self.min_profit_margin:
                # Calculate bet sizes for $100 total stake
                total_stake = 100
                bet_sizes = self._calculate_bet_sizes(
                    best_home['odds'], best_away['odds'], total_stake
                )
                
                opportunities.append({
                    'game_id': game.get('id'),
                    'sport': game.get('sport'),
                    'home_team': home_team,
                    'away_team': away_team,
                    'bet_type': 'moneyline',
                    'leg1': {
                        'selection': home_team,
                        'odds': best_home['odds'],
                        'bookmaker': best_home['bookmaker'],
                        'stake': bet_sizes['bet1']
                    },
                    'leg2': {
                        'selection': away_team,
                        'odds': best_away['odds'],
                        'bookmaker': best_away['bookmaker'],
                        'stake': bet_sizes['bet2']
                    },
                    'profit_margin': arb_result['profit_margin'],
                    'total_stake': total_stake,
                    'guaranteed_profit': arb_result['profit_margin'] * total_stake,
                    'strategy': 'arbitrage'
                })
        
        return opportunities
    
    def _check_spread_arbitrage(self, game: Dict, odds: Dict) -> List[Dict]:
        """Check for spread arbitrage"""
        opportunities = []
        
        home_team = game.get('home_team')
        away_team = game.get('away_team')
        
        # Group spreads by point value
        spreads_by_point = {}
        
        for bookmaker in odds.get('bookmakers', []):
            bookmaker_name = bookmaker.get('name')
            spread_market = bookmaker.get('markets', {}).get('spreads')
            
            if not spread_market:
                continue
            
            for outcome in spread_market.get('outcomes', []):
                team = outcome.get('name')
                odds_value = outcome.get('price')
                point = outcome.get('point')
                
                # Key by the point value (should be opposite for home/away)
                if point not in spreads_by_point:
                    spreads_by_point[point] = {}
                
                if team == home_team:
                    if 'home' not in spreads_by_point[point] or odds_value > spreads_by_point[point]['home']['odds']:
                        spreads_by_point[point]['home'] = {
                            'odds': odds_value,
                            'bookmaker': bookmaker_name,
                            'team': team
                        }
                elif team == away_team:
                    if 'away' not in spreads_by_point[point] or odds_value > spreads_by_point[point]['away']['odds']:
                        spreads_by_point[point]['away'] = {
                            'odds': odds_value,
                            'bookmaker': bookmaker_name,
                            'team': team
                        }
        
        # Check each spread for arbitrage
        for point, data in spreads_by_point.items():
            if 'home' in data and 'away' in data:
                arb_result = self._calculate_arbitrage(
                    data['home']['odds'], data['away']['odds']
                )
                
                if arb_result['is_arbitrage'] and arb_result['profit_margin'] >= self.min_profit_margin:
                    total_stake = 100
                    bet_sizes = self._calculate_bet_sizes(
                        data['home']['odds'], data['away']['odds'], total_stake
                    )
                    
                    opportunities.append({
                        'game_id': game.get('id'),
                        'sport': game.get('sport'),
                        'home_team': home_team,
                        'away_team': away_team,
                        'bet_type': 'spread',
                        'leg1': {
                            'selection': f"{data['home']['team']} {point}",
                            'odds': data['home']['odds'],
                            'bookmaker': data['home']['bookmaker'],
                            'stake': bet_sizes['bet1']
                        },
                        'leg2': {
                            'selection': f"{data['away']['team']} {-point}",
                            'odds': data['away']['odds'],
                            'bookmaker': data['away']['bookmaker'],
                            'stake': bet_sizes['bet2']
                        },
                        'profit_margin': arb_result['profit_margin'],
                        'total_stake': total_stake,
                        'guaranteed_profit': arb_result['profit_margin'] * total_stake,
                        'strategy': 'arbitrage'
                    })
        
        return opportunities
    
    def _check_totals_arbitrage(self, game: Dict, odds: Dict) -> List[Dict]:
        """Check for totals arbitrage"""
        opportunities = []
        
        # Group totals by point value
        totals_by_point = {}
        
        for bookmaker in odds.get('bookmakers', []):
            bookmaker_name = bookmaker.get('name')
            totals_market = bookmaker.get('markets', {}).get('totals')
            
            if not totals_market:
                continue
            
            for outcome in totals_market.get('outcomes', []):
                name = outcome.get('name')  # 'Over' or 'Under'
                odds_value = outcome.get('price')
                point = outcome.get('point')
                
                if point not in totals_by_point:
                    totals_by_point[point] = {}
                
                side = name.lower()
                if side not in totals_by_point[point] or odds_value > totals_by_point[point][side]['odds']:
                    totals_by_point[point][side] = {
                        'odds': odds_value,
                        'bookmaker': bookmaker_name
                    }
        
        # Check each total for arbitrage
        for point, data in totals_by_point.items():
            if 'over' in data and 'under' in data:
                arb_result = self._calculate_arbitrage(
                    data['over']['odds'], data['under']['odds']
                )
                
                if arb_result['is_arbitrage'] and arb_result['profit_margin'] >= self.min_profit_margin:
                    total_stake = 100
                    bet_sizes = self._calculate_bet_sizes(
                        data['over']['odds'], data['under']['odds'], total_stake
                    )
                    
                    opportunities.append({
                        'game_id': game.get('id'),
                        'sport': game.get('sport'),
                        'home_team': game.get('home_team'),
                        'away_team': game.get('away_team'),
                        'bet_type': 'total',
                        'leg1': {
                            'selection': f"Over {point}",
                            'odds': data['over']['odds'],
                            'bookmaker': data['over']['bookmaker'],
                            'stake': bet_sizes['bet1']
                        },
                        'leg2': {
                            'selection': f"Under {point}",
                            'odds': data['under']['odds'],
                            'bookmaker': data['under']['bookmaker'],
                            'stake': bet_sizes['bet2']
                        },
                        'profit_margin': arb_result['profit_margin'],
                        'total_stake': total_stake,
                        'guaranteed_profit': arb_result['profit_margin'] * total_stake,
                        'strategy': 'arbitrage'
                    })
        
        return opportunities
    
    def _calculate_arbitrage(self, odds1: int, odds2: int) -> Dict:
        """
        Calculate if arbitrage opportunity exists
        
        Args:
            odds1: American odds for side 1
            odds2: American odds for side 2
            
        Returns:
            Dictionary with arbitrage calculation results
        """
        # Convert American odds to decimal
        decimal1 = self._american_to_decimal(odds1)
        decimal2 = self._american_to_decimal(odds2)
        
        # Calculate implied probabilities
        implied_prob1 = 1 / decimal1
        implied_prob2 = 1 / decimal2
        
        # Sum of implied probabilities
        total_prob = implied_prob1 + implied_prob2
        
        # If total < 1.0, arbitrage exists
        is_arbitrage = total_prob < 1.0
        
        # Profit margin
        profit_margin = (1 - total_prob) if is_arbitrage else 0
        
        return {
            'is_arbitrage': is_arbitrage,
            'profit_margin': profit_margin,
            'total_implied_prob': total_prob
        }
    
    def _calculate_bet_sizes(self, odds1: int, odds2: int, total_stake: float) -> Dict:
        """
        Calculate optimal bet sizes for arbitrage
        
        Args:
            odds1: American odds for side 1
            odds2: American odds for side 2
            total_stake: Total amount to bet
            
        Returns:
            Dictionary with bet sizes for each side
        """
        decimal1 = self._american_to_decimal(odds1)
        decimal2 = self._american_to_decimal(odds2)
        
        # Optimal stake calculation
        stake1 = total_stake / (1 + (decimal1 / decimal2))
        stake2 = total_stake - stake1
        
        return {
            'bet1': round(stake1, 2),
            'bet2': round(stake2, 2)
        }
    
    def _american_to_decimal(self, odds: int) -> float:
        """Convert American odds to decimal odds"""
        if odds > 0:
            return (odds / 100) + 1
        else:
            return (100 / abs(odds)) + 1
