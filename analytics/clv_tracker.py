"""
CLV (Closing Line Value) Tracker
Track THE KEY METRIC for long-term profitability
"""

from typing import Dict, List
from utils.logger import setup_logger


logger = setup_logger("clv_tracker")


class CLVTracker:
    """
    Track Closing Line Value - THE KEY METRIC
    
    If you consistently beat the closing line, you WILL be profitable long-term
    """
    
    def __init__(self):
        self.clv_records = []
        logger.info("CLV Tracker initialized")
    
    def track_bet_clv(self, bet: Dict, closing_line: float):
        """
        Your bet: Lakers -5.5 at 10am
        Closing line: Lakers -8 at game time
        CLV: +2.5 points ✓
        
        Even if you lose, +CLV means it was +EV
        
        Args:
            bet: Bet dict with bet_line and side
            closing_line: Final line at game time
        """
        bet_line = bet.get('bet_line', bet.get('odds', 0))
        side = bet.get('side', 'home')
        
        # Calculate CLV based on side
        if side == 'home':
            # For home bets, if closing line is more negative (moved away), CLV is positive
            clv = closing_line - bet_line
        else:
            # For away bets, if closing line is less negative (moved toward away), CLV is positive
            clv = bet_line - closing_line
        
        record = {
            'bet_id': bet.get('id'),
            'sport': bet.get('sport'),
            'strategy': bet.get('strategy'),
            'bet_line': bet_line,
            'closing_line': closing_line,
            'clv': clv,
            'side': side
        }
        
        self.clv_records.append(record)
        
        logger.info(f"CLV tracked: {bet.get('id')} - Bet: {bet_line:.1f}, Close: {closing_line:.1f}, CLV: {clv:+.1f}")
    
    def calculate_average_clv(self, strategy: str = None, sport: str = None) -> float:
        """
        Average CLV over last 50-100 bets
        
        +CLV average = Beating the market ✓
        -CLV average = Worse than closing line ✗
        
        Goal: +1.0 to +2.0 CLV average
        
        Args:
            strategy: Filter by strategy (optional)
            sport: Filter by sport (optional)
            
        Returns:
            Average CLV
        """
        records = self.clv_records
        
        if strategy:
            records = [r for r in records if r.get('strategy') == strategy]
        
        if sport:
            records = [r for r in records if r.get('sport') == sport]
        
        if not records:
            return 0.0
        
        avg_clv = sum(r['clv'] for r in records) / len(records)
        
        logger.info(f"Average CLV: {avg_clv:+.2f} ({len(records)} bets)")
        
        return round(avg_clv, 2)
    
    def correlate_clv_with_wins(self) -> Dict:
        """
        Analyze: Do higher CLV bets win more often?
        Expected: YES
        
        Returns:
            Correlation analysis
        """
        if not self.clv_records:
            return {'correlation': 0, 'sample_size': 0}
        
        # Bucket bets by CLV
        positive_clv = [r for r in self.clv_records if r['clv'] > 0]
        negative_clv = [r for r in self.clv_records if r['clv'] < 0]
        
        # In a real implementation, we'd track outcomes and calculate win rates
        # For now, return structure
        
        return {
            'positive_clv_bets': len(positive_clv),
            'negative_clv_bets': len(negative_clv),
            'positive_clv_rate': len(positive_clv) / len(self.clv_records) if self.clv_records else 0,
            'avg_positive_clv': sum(r['clv'] for r in positive_clv) / len(positive_clv) if positive_clv else 0,
            'avg_negative_clv': sum(r['clv'] for r in negative_clv) / len(negative_clv) if negative_clv else 0
        }
    
    def get_clv_by_strategy(self) -> Dict[str, float]:
        """Get average CLV for each strategy"""
        strategies = set(r.get('strategy') for r in self.clv_records if r.get('strategy'))
        
        clv_by_strategy = {}
        for strategy in strategies:
            clv_by_strategy[strategy] = self.calculate_average_clv(strategy=strategy)
        
        return clv_by_strategy
    
    def get_clv_by_sport(self) -> Dict[str, float]:
        """Get average CLV for each sport"""
        sports = set(r.get('sport') for r in self.clv_records if r.get('sport'))
        
        clv_by_sport = {}
        for sport in sports:
            clv_by_sport[sport] = self.calculate_average_clv(sport=sport)
        
        return clv_by_sport
    
    def get_clv_distribution(self) -> Dict:
        """Get distribution of CLV values"""
        if not self.clv_records:
            return {'buckets': {}}
        
        buckets = {
            'highly_positive': 0,  # CLV > 2.0
            'positive': 0,          # 0 < CLV <= 2.0
            'negative': 0,          # -2.0 <= CLV < 0
            'highly_negative': 0    # CLV < -2.0
        }
        
        for record in self.clv_records:
            clv = record['clv']
            if clv > 2.0:
                buckets['highly_positive'] += 1
            elif clv > 0:
                buckets['positive'] += 1
            elif clv >= -2.0:
                buckets['negative'] += 1
            else:
                buckets['highly_negative'] += 1
        
        return {
            'buckets': buckets,
            'total': len(self.clv_records)
        }
