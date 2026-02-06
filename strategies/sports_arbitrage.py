"""
Sports Arbitrage Strategy
Find guaranteed profit opportunities between sportsbooks

How it works:
- Monitor odds across multiple sportsbooks
- Find games where betting both sides guarantees profit
- Calculate optimal stake sizing
- Execute both bets

Example:
FanDuel: Lakers -110 (bet $110 to win $100)
DraftKings: Celtics +115 (bet $100 to win $115)
Total risk: $210, Guaranteed return: $215
Profit: $5 (2.38% risk-free)
"""

from typing import Dict, List, Optional
from utils.logger import setup_logger


logger = setup_logger("arbitrage_strategy")


class SportsArbitrageStrategy:
    """
    Find guaranteed profit opportunities between sportsbooks
    """
    
    def __init__(self, min_profit_percent: float = 0.5):
        """
        Initialize arbitrage strategy
        
        Args:
            min_profit_percent: Minimum profit percentage to consider (e.g., 0.5 = 0.5%)
        """
        self.min_profit_percent = min_profit_percent
        logger.info(f"Arbitrage strategy initialized with min profit: {min_profit_percent}%")
    
    def scan_all_books(self, sportsbook_manager, sport: str, game: str) -> Dict[str, Dict]:
        """
        Check odds across all sportsbooks
        
        Args:
            sportsbook_manager: SportsbookManager instance
            sport: Sport name
            game: Game identifier
            
        Returns:
            Dict of sportsbook -> odds
        """
        return sportsbook_manager.get_all_odds(sport, game)
    
    def find_arbitrage_opportunities(self, 
                                     sportsbook_manager,
                                     sport: str,
                                     games: List[str]) -> List[Dict]:
        """
        For each game, check if arbitrage exists
        
        Calculate break-even: 1 / (1 + odds_decimal)
        If sum of both sides < 1.0 → arbitrage exists
        
        Args:
            sportsbook_manager: SportsbookManager instance
            sport: Sport name
            games: List of game identifiers
            
        Returns:
            List of arbitrage opportunities
        """
        opportunities = []
        
        for game in games:
            all_odds = self.scan_all_books(sportsbook_manager, sport, game)
            
            if len(all_odds) < 2:
                continue  # Need at least 2 books to compare
            
            # Check spread arbitrage
            spread_arb = self._check_spread_arbitrage(game, all_odds)
            if spread_arb:
                opportunities.append(spread_arb)
            
            # Check total arbitrage
            total_arb = self._check_total_arbitrage(game, all_odds)
            if total_arb:
                opportunities.append(total_arb)
            
            # Check moneyline arbitrage
            moneyline_arb = self._check_moneyline_arbitrage(game, all_odds)
            if moneyline_arb:
                opportunities.append(moneyline_arb)
        
        logger.info(f"Found {len(opportunities)} arbitrage opportunities in {sport}")
        return opportunities
    
    def _check_spread_arbitrage(self, game: str, all_odds: Dict) -> Optional[Dict]:
        """Check for arbitrage in spread betting"""
        best_home = None
        best_away = None
        
        # Find best odds for each side
        for book, odds in all_odds.items():
            if 'spread_odds' in odds:
                home_odds = odds['spread_odds'].get('home')
                away_odds = odds['spread_odds'].get('away')
                
                if home_odds and (not best_home or home_odds > best_home['odds']):
                    best_home = {'book': book, 'odds': home_odds, 'line': odds['spread']['home']}
                
                if away_odds and (not best_away or away_odds > best_away['odds']):
                    best_away = {'book': book, 'odds': away_odds, 'line': odds['spread']['away']}
        
        if not best_home or not best_away:
            return None
        
        # Calculate if arbitrage exists
        arb = self._calculate_arbitrage(best_home['odds'], best_away['odds'])
        
        if arb and arb['profit_percent'] >= self.min_profit_percent:
            return {
                'game': game,
                'type': 'spread',
                'side_a': {'book': best_home['book'], 'side': 'home', 'odds': best_home['odds'], 'line': best_home['line']},
                'side_b': {'book': best_away['book'], 'side': 'away', 'odds': best_away['odds'], 'line': best_away['line']},
                'profit_percent': arb['profit_percent'],
                'stake_ratio': arb['stake_ratio']
            }
        
        return None
    
    def _check_total_arbitrage(self, game: str, all_odds: Dict) -> Optional[Dict]:
        """Check for arbitrage in totals betting"""
        best_over = None
        best_under = None
        
        for book, odds in all_odds.items():
            if 'total_odds' in odds:
                over_odds = odds['total_odds'].get('over')
                under_odds = odds['total_odds'].get('under')
                
                if over_odds and (not best_over or over_odds > best_over['odds']):
                    best_over = {'book': book, 'odds': over_odds, 'line': odds['total']['over']}
                
                if under_odds and (not best_under or under_odds > best_under['odds']):
                    best_under = {'book': book, 'odds': under_odds, 'line': odds['total']['under']}
        
        if not best_over or not best_under:
            return None
        
        arb = self._calculate_arbitrage(best_over['odds'], best_under['odds'])
        
        if arb and arb['profit_percent'] >= self.min_profit_percent:
            return {
                'game': game,
                'type': 'total',
                'side_a': {'book': best_over['book'], 'side': 'over', 'odds': best_over['odds'], 'line': best_over['line']},
                'side_b': {'book': best_under['book'], 'side': 'under', 'odds': best_under['odds'], 'line': best_under['line']},
                'profit_percent': arb['profit_percent'],
                'stake_ratio': arb['stake_ratio']
            }
        
        return None
    
    def _check_moneyline_arbitrage(self, game: str, all_odds: Dict) -> Optional[Dict]:
        """Check for arbitrage in moneyline betting"""
        best_home = None
        best_away = None
        
        for book, odds in all_odds.items():
            if 'moneyline' in odds:
                home_odds = odds['moneyline'].get('home')
                away_odds = odds['moneyline'].get('away')
                
                if home_odds and (not best_home or home_odds > best_home['odds']):
                    best_home = {'book': book, 'odds': home_odds}
                
                if away_odds and (not best_away or away_odds > best_away['odds']):
                    best_away = {'book': book, 'odds': away_odds}
        
        if not best_home or not best_away:
            return None
        
        arb = self._calculate_arbitrage(best_home['odds'], best_away['odds'])
        
        if arb and arb['profit_percent'] >= self.min_profit_percent:
            return {
                'game': game,
                'type': 'moneyline',
                'side_a': {'book': best_home['book'], 'side': 'home', 'odds': best_home['odds']},
                'side_b': {'book': best_away['book'], 'side': 'away', 'odds': best_away['odds']},
                'profit_percent': arb['profit_percent'],
                'stake_ratio': arb['stake_ratio']
            }
        
        return None
    
    def _calculate_arbitrage(self, odds_a: float, odds_b: float) -> Optional[Dict]:
        """
        Calculate if arbitrage exists between two odds
        
        Args:
            odds_a: American odds for side A
            odds_b: American odds for side B
            
        Returns:
            Dict with profit_percent and stake_ratio, or None if no arb
        """
        # Convert American odds to decimal
        decimal_a = self._american_to_decimal(odds_a)
        decimal_b = self._american_to_decimal(odds_b)
        
        # Calculate implied probabilities
        implied_prob_a = 1 / decimal_a
        implied_prob_b = 1 / decimal_b
        
        # Sum of probabilities < 1.0 means arbitrage exists
        total_prob = implied_prob_a + implied_prob_b
        
        if total_prob < 1.0:
            profit_percent = ((1 / total_prob) - 1) * 100
            
            # Calculate stake ratio (how to split total bankroll)
            # Stake A / Stake B = implied_prob_a / implied_prob_b
            stake_ratio = implied_prob_a / implied_prob_b
            
            return {
                'profit_percent': profit_percent,
                'stake_ratio': stake_ratio,
                'total_prob': total_prob
            }
        
        return None
    
    def _american_to_decimal(self, american_odds: float) -> float:
        """Convert American odds to decimal odds"""
        if american_odds > 0:
            return (american_odds / 100) + 1
        else:
            return (100 / abs(american_odds)) + 1
    
    def calculate_optimal_stakes(self, 
                                opportunity: Dict,
                                bankroll: float) -> Dict[str, float]:
        """
        Calculate how much to bet on each side
        
        Formula:
        Total stake = bankroll * kelly_fraction
        Stake A = Total * (Odds B / (Odds A + Odds B))
        Stake B = Total * (Odds A / (Odds A + Odds B))
        
        Args:
            opportunity: Arbitrage opportunity dict
            bankroll: Available bankroll
            
        Returns:
            Dict with stake_a and stake_b
        """
        # For arbitrage, use conservative sizing (e.g., 10% of bankroll)
        # Since it's risk-free, could use more, but be conservative
        total_stake = bankroll * 0.10
        
        stake_ratio = opportunity['stake_ratio']
        
        # Calculate individual stakes
        stake_a = total_stake / (1 + stake_ratio)
        stake_b = total_stake - stake_a
        
        return {
            'stake_a': round(stake_a, 2),
            'stake_b': round(stake_b, 2),
            'total_stake': round(total_stake, 2),
            'expected_profit': round(total_stake * (opportunity['profit_percent'] / 100), 2)
        }
    
    def validate_opportunity(self, arb: Dict) -> tuple[bool, str]:
        """
        Validate arbitrage opportunity
        
        Check:
        - Both books still offering these odds?
        - Sufficient liquidity?
        - Profit > minimum threshold?
        - Execution time < opportunity lifespan?
        
        Args:
            arb: Arbitrage opportunity
            
        Returns:
            (valid, reason) tuple
        """
        # Check profit threshold
        if arb['profit_percent'] < self.min_profit_percent:
            return False, f"Profit too low: {arb['profit_percent']:.2f}% < {self.min_profit_percent}%"
        
        # Check if books are different (can't arb same book)
        if arb['side_a']['book'] == arb['side_b']['book']:
            return False, "Cannot arbitrage same sportsbook"
        
        # In production, would check:
        # - Books still offering these odds
        # - Sufficient liquidity
        # - Account limits
        
        return True, "Valid arbitrage opportunity"
