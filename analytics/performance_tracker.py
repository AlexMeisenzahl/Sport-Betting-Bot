"""
Performance Tracker
Track performance across all strategies and sports
Generate strategy x sport performance matrix
"""

from typing import Dict, List
from collections import defaultdict
from utils.logger import setup_logger


logger = setup_logger("performance_tracker")


class PerformanceTracker:
    """
    Track performance across all strategies and sports
    """
    
    def __init__(self):
        self.bets = []
        self.completed_bets = []
        logger.info("Performance Tracker initialized")
    
    def track_bet_result(self, bet: Dict, outcome: str):
        """
        Record every bet:
        - Strategy used
        - Sport
        - Bet type
        - Odds
        - Stake
        - Result
        - CLV (if applicable)
        
        Args:
            bet: Bet dict
            outcome: 'win' or 'loss'
        """
        bet['outcome'] = outcome
        self.completed_bets.append(bet)
        
        logger.info(f"Tracked bet result: {bet['id']} - {outcome}")
    
    def calculate_strategy_performance(self, strategy_name: str) -> Dict:
        """
        For each strategy:
        - Total bets
        - Win rate
        - Total profit/loss
        - ROI
        - Sharpe ratio
        - Max drawdown
        
        Args:
            strategy_name: Strategy name
            
        Returns:
            Performance metrics dict
        """
        strategy_bets = [b for b in self.completed_bets if b.get('strategy') == strategy_name]
        
        if not strategy_bets:
            return {
                'total_bets': 0,
                'wins': 0,
                'losses': 0,
                'win_rate': 0,
                'total_profit': 0,
                'roi': 0,
                'sharpe_ratio': 0,
                'max_drawdown': 0
            }
        
        total_bets = len(strategy_bets)
        wins = sum(1 for b in strategy_bets if b.get('result') == 'win')
        losses = sum(1 for b in strategy_bets if b.get('result') == 'loss')
        
        total_staked = sum(b.get('stake', 0) for b in strategy_bets)
        total_profit = sum(b.get('profit', 0) for b in strategy_bets)
        
        win_rate = wins / total_bets if total_bets > 0 else 0
        roi = total_profit / total_staked if total_staked > 0 else 0
        
        # Simplified Sharpe ratio calculation
        sharpe_ratio = self._calculate_sharpe_ratio(strategy_bets)
        max_drawdown = self._calculate_max_drawdown(strategy_bets)
        
        return {
            'strategy': strategy_name,
            'total_bets': total_bets,
            'wins': wins,
            'losses': losses,
            'win_rate': win_rate,
            'total_staked': total_staked,
            'total_profit': total_profit,
            'roi': roi,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown
        }
    
    def calculate_sport_performance(self, sport: str) -> Dict:
        """Calculate performance for a specific sport"""
        sport_bets = [b for b in self.completed_bets if b.get('sport') == sport]
        
        if not sport_bets:
            return {'total_bets': 0, 'roi': 0}
        
        total_staked = sum(b.get('stake', 0) for b in sport_bets)
        total_profit = sum(b.get('profit', 0) for b in sport_bets)
        
        return {
            'sport': sport,
            'total_bets': len(sport_bets),
            'total_profit': total_profit,
            'roi': total_profit / total_staked if total_staked > 0 else 0
        }
    
    def generate_performance_matrix(self) -> Dict[str, Dict[str, float]]:
        """
        Strategy x Sport matrix showing ROI for each combination
        
        Identifies:
        - Best strategy overall
        - Best strategy per sport
        - Which strategies to deploy
        - Which to avoid
        
        Returns:
            Nested dict: matrix[strategy][sport] = ROI
        """
        matrix = defaultdict(lambda: defaultdict(float))
        
        strategies = set(b.get('strategy') for b in self.completed_bets if b.get('strategy'))
        sports = set(b.get('sport') for b in self.completed_bets if b.get('sport'))
        
        for strategy in strategies:
            for sport in sports:
                combo_bets = [
                    b for b in self.completed_bets
                    if b.get('strategy') == strategy and b.get('sport') == sport
                ]
                
                if combo_bets:
                    total_staked = sum(b.get('stake', 0) for b in combo_bets)
                    total_profit = sum(b.get('profit', 0) for b in combo_bets)
                    roi = total_profit / total_staked if total_staked > 0 else 0
                    matrix[strategy][sport] = roi
        
        logger.info("Generated performance matrix")
        return dict(matrix)
    
    def generate_recommendations(self, min_sample_size: int = 20) -> Dict:
        """
        After 30 days testing:
        
        Recommendations:
        1. Deploy: NBA CLV Model (+10.5% ROI)
        2. Deploy: Soccer Arbitrage (+3.8% ROI)
        3. AVOID: NCAAF CLV (-2.1% ROI)
        
        Suggested capital allocation
        
        Args:
            min_sample_size: Minimum bets required for recommendation
            
        Returns:
            Recommendations dict
        """
        matrix = self.generate_performance_matrix()
        
        deploy = []
        avoid = []
        
        for strategy, sports in matrix.items():
            for sport, roi in sports.items():
                # Count bets for this combo
                combo_bets = [
                    b for b in self.completed_bets
                    if b.get('strategy') == strategy and b.get('sport') == sport
                ]
                
                if len(combo_bets) < min_sample_size:
                    continue  # Not enough data
                
                if roi > 0.02:  # +2% ROI threshold
                    deploy.append({
                        'strategy': strategy,
                        'sport': sport,
                        'roi': roi,
                        'bets': len(combo_bets)
                    })
                elif roi < -0.01:  # -1% ROI threshold
                    avoid.append({
                        'strategy': strategy,
                        'sport': sport,
                        'roi': roi,
                        'bets': len(combo_bets)
                    })
        
        # Sort by ROI
        deploy.sort(key=lambda x: x['roi'], reverse=True)
        avoid.sort(key=lambda x: x['roi'])
        
        logger.info(f"Generated recommendations: {len(deploy)} to deploy, {len(avoid)} to avoid")
        
        return {
            'deploy': deploy,
            'avoid': avoid,
            'total_combos_tested': len([
                (s, sp) for s in matrix for sp in matrix[s]
            ])
        }
    
    def _calculate_sharpe_ratio(self, bets: List[Dict]) -> float:
        """Calculate Sharpe ratio (risk-adjusted return)"""
        if len(bets) < 2:
            return 0
        
        returns = [b.get('profit', 0) / b.get('stake', 1) for b in bets]
        
        import statistics
        mean_return = statistics.mean(returns)
        std_return = statistics.stdev(returns) if len(returns) > 1 else 1
        
        # Simplified Sharpe (assuming 0 risk-free rate)
        sharpe = mean_return / std_return if std_return > 0 else 0
        
        return round(sharpe, 2)
    
    def _calculate_max_drawdown(self, bets: List[Dict]) -> float:
        """Calculate maximum drawdown from peak"""
        if not bets:
            return 0
        
        cumulative = 0
        peak = 0
        max_dd = 0
        
        for bet in sorted(bets, key=lambda x: x.get('timestamp', 0)):
            cumulative += bet.get('profit', 0)
            peak = max(peak, cumulative)
            drawdown = peak - cumulative
            max_dd = max(max_dd, drawdown)
        
        return round(max_dd, 2)
    
    def get_overall_stats(self) -> Dict:
        """Get overall performance statistics"""
        if not self.completed_bets:
            return {'total_bets': 0, 'roi': 0}
        
        total_bets = len(self.completed_bets)
        wins = sum(1 for b in self.completed_bets if b.get('result') == 'win')
        
        total_staked = sum(b.get('stake', 0) for b in self.completed_bets)
        total_profit = sum(b.get('profit', 0) for b in self.completed_bets)
        
        return {
            'total_bets': total_bets,
            'wins': wins,
            'losses': total_bets - wins,
            'win_rate': wins / total_bets if total_bets > 0 else 0,
            'total_staked': total_staked,
            'total_profit': total_profit,
            'roi': total_profit / total_staked if total_staked > 0 else 0
        }
