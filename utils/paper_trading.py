"""
Paper Trading Engine
Simulates betting with realistic vig, delays, and market conditions
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import random
from utils.logger import setup_logger


logger = setup_logger("paper_trading")


class PaperTradingEngine:
    """
    Paper trading engine that simulates real betting conditions
    
    Features:
    - Realistic vig simulation (-110 standard)
    - Order execution delays
    - Line movement simulation
    - Bankroll management
    """
    
    def __init__(self, starting_bankroll: float = 500, realistic_mode: bool = True):
        self.starting_bankroll = starting_bankroll
        self.current_bankroll = starting_bankroll
        self.realistic_mode = realistic_mode
        self.bets: List[Dict] = []
        self.completed_bets: List[Dict] = []
        
        logger.info(f"Paper Trading Engine initialized with ${starting_bankroll}")
    
    def place_bet(self, 
                  sport: str,
                  game: str,
                  bet_type: str,
                  side: str,
                  odds: float,
                  stake: float,
                  strategy: str,
                  sportsbook: str = "paper") -> Optional[Dict]:
        """
        Place a paper bet
        
        Args:
            sport: Sport name (nba, nfl, etc.)
            game: Game identifier
            bet_type: Type of bet (spread, total, moneyline, prop)
            side: Which side of the bet
            odds: American odds (e.g., -110)
            stake: Amount to bet
            strategy: Strategy name that generated this bet
            sportsbook: Sportsbook name
            
        Returns:
            Bet dict if successful, None if failed
        """
        
        # Validate stake
        if stake > self.current_bankroll:
            logger.warning(f"Insufficient bankroll: ${stake} > ${self.current_bankroll}")
            return None
        
        if stake <= 0:
            logger.warning(f"Invalid stake: ${stake}")
            return None
        
        # Simulate execution delay in realistic mode
        if self.realistic_mode:
            # 1-3 second delay simulation
            execution_delay = random.uniform(1, 3)
            
            # Small chance odds have moved
            if random.random() < 0.1:  # 10% chance odds moved
                odds_movement = random.choice([-5, -10, 5, 10])
                original_odds = odds
                odds += odds_movement
                logger.info(f"Line moved from {original_odds} to {odds}")
        
        bet = {
            'id': f"BET-{len(self.bets) + 1:05d}",
            'timestamp': datetime.now(),
            'sport': sport,
            'game': game,
            'bet_type': bet_type,
            'side': side,
            'odds': odds,
            'stake': stake,
            'strategy': strategy,
            'sportsbook': sportsbook,
            'status': 'pending',
            'result': None,
            'profit': 0,
            'closing_line': None,  # To be filled later for CLV tracking
        }
        
        self.bets.append(bet)
        self.current_bankroll -= stake
        
        logger.info(f"Placed bet: {bet['id']} - {sport} {side} {odds} ${stake} via {strategy}")
        logger.info(f"Remaining bankroll: ${self.current_bankroll:.2f}")
        
        return bet
    
    def settle_bet(self, bet_id: str, won: bool, closing_line: Optional[float] = None):
        """
        Settle a bet with result
        
        Args:
            bet_id: Bet identifier
            won: Whether bet won
            closing_line: Closing line for CLV calculation
        """
        bet = next((b for b in self.bets if b['id'] == bet_id), None)
        
        if not bet:
            logger.error(f"Bet not found: {bet_id}")
            return
        
        if bet['status'] != 'pending':
            logger.warning(f"Bet already settled: {bet_id}")
            return
        
        # Calculate profit/loss
        if won:
            profit = self._calculate_payout(bet['stake'], bet['odds'])
            bet['result'] = 'win'
            bet['profit'] = profit
            self.current_bankroll += profit
        else:
            bet['result'] = 'loss'
            bet['profit'] = -bet['stake']
            # Stake already deducted when bet was placed
        
        bet['status'] = 'settled'
        bet['settled_at'] = datetime.now()
        
        if closing_line:
            bet['closing_line'] = closing_line
        
        self.completed_bets.append(bet)
        self.bets.remove(bet)
        
        logger.info(f"Settled bet {bet_id}: {bet['result']} - Profit: ${bet['profit']:.2f}")
        logger.info(f"New bankroll: ${self.current_bankroll:.2f}")
    
    def _calculate_payout(self, stake: float, odds: float) -> float:
        """
        Calculate payout from stake and American odds
        
        Args:
            stake: Amount bet
            odds: American odds (e.g., -110, +150)
            
        Returns:
            Total payout including stake
        """
        if odds > 0:
            # Positive odds: win = stake * (odds / 100)
            return stake + (stake * (odds / 100))
        else:
            # Negative odds: win = stake * (100 / abs(odds))
            return stake + (stake * (100 / abs(odds)))
    
    def get_pending_bets(self) -> List[Dict]:
        """Get all pending bets"""
        return self.bets.copy()
    
    def get_completed_bets(self) -> List[Dict]:
        """Get all completed bets"""
        return self.completed_bets.copy()
    
    def get_bankroll(self) -> float:
        """Get current bankroll"""
        return self.current_bankroll
    
    def get_total_profit(self) -> float:
        """Get total profit/loss"""
        return self.current_bankroll - self.starting_bankroll
    
    def get_roi(self) -> float:
        """Get return on investment"""
        if self.starting_bankroll == 0:
            return 0
        return (self.current_bankroll - self.starting_bankroll) / self.starting_bankroll
    
    def get_stats(self) -> Dict:
        """Get comprehensive stats"""
        total_bets = len(self.completed_bets)
        wins = sum(1 for b in self.completed_bets if b['result'] == 'win')
        losses = sum(1 for b in self.completed_bets if b['result'] == 'loss')
        
        total_staked = sum(b['stake'] for b in self.completed_bets)
        total_profit = sum(b['profit'] for b in self.completed_bets)
        
        return {
            'starting_bankroll': self.starting_bankroll,
            'current_bankroll': self.current_bankroll,
            'total_profit': self.get_total_profit(),
            'roi': self.get_roi(),
            'total_bets': total_bets,
            'wins': wins,
            'losses': losses,
            'win_rate': wins / total_bets if total_bets > 0 else 0,
            'pending_bets': len(self.bets),
            'total_staked': total_staked,
            'avg_stake': total_staked / total_bets if total_bets > 0 else 0,
        }
