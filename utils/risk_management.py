"""
Risk Management System
Enforces bankroll limits, position sizing, and risk controls
"""

from typing import Dict, Optional
from utils.logger import setup_logger


logger = setup_logger("risk_management")


class RiskManager:
    """
    Manages risk across all betting activity
    
    Features:
    - Kelly Criterion position sizing
    - Daily loss limits
    - Maximum drawdown controls
    - Concurrent bet limits
    """
    
    def __init__(self, 
                 starting_bankroll: float,
                 max_daily_loss_percent: float = 0.10,
                 max_total_drawdown_percent: float = 0.20,
                 max_concurrent_bets: int = 10,
                 kelly_fraction: float = 0.25):
        """
        Initialize risk manager
        
        Args:
            starting_bankroll: Initial bankroll
            max_daily_loss_percent: Max daily loss as % of bankroll (e.g., 0.10 = 10%)
            max_total_drawdown_percent: Max total drawdown from peak
            max_concurrent_bets: Maximum number of simultaneous open bets
            kelly_fraction: Fraction of Kelly Criterion to use (0.25 = quarter Kelly)
        """
        self.starting_bankroll = starting_bankroll
        self.peak_bankroll = starting_bankroll
        self.max_daily_loss_percent = max_daily_loss_percent
        self.max_total_drawdown_percent = max_total_drawdown_percent
        self.max_concurrent_bets = max_concurrent_bets
        self.kelly_fraction = kelly_fraction
        
        self.daily_losses = {}  # Track daily P&L
        
        logger.info(f"Risk Manager initialized with ${starting_bankroll}")
        logger.info(f"Max daily loss: {max_daily_loss_percent*100}%")
        logger.info(f"Max drawdown: {max_total_drawdown_percent*100}%")
    
    def calculate_position_size(self, 
                                current_bankroll: float,
                                win_probability: float,
                                odds: float) -> float:
        """
        Calculate optimal bet size using Kelly Criterion
        
        Args:
            current_bankroll: Current bankroll amount
            win_probability: Estimated probability of winning (0-1)
            odds: American odds
            
        Returns:
            Recommended bet size
        """
        
        # Convert American odds to decimal
        if odds > 0:
            decimal_odds = (odds / 100) + 1
        else:
            decimal_odds = (100 / abs(odds)) + 1
        
        # Kelly Criterion: f = (bp - q) / b
        # where: f = fraction to bet
        #        b = decimal odds - 1 (net odds)
        #        p = probability of win
        #        q = probability of loss (1 - p)
        
        b = decimal_odds - 1
        p = win_probability
        q = 1 - p
        
        kelly_fraction_full = (b * p - q) / b
        
        # Apply fractional Kelly for safety
        kelly_fraction_adjusted = kelly_fraction_full * self.kelly_fraction
        
        # Ensure non-negative
        if kelly_fraction_adjusted < 0:
            logger.warning(f"Negative Kelly fraction: {kelly_fraction_adjusted:.4f} - No edge detected")
            return 0
        
        # Cap at 5% of bankroll for safety
        kelly_fraction_adjusted = min(kelly_fraction_adjusted, 0.05)
        
        bet_size = current_bankroll * kelly_fraction_adjusted
        
        logger.debug(f"Kelly sizing: P={p:.3f}, Odds={odds}, Size=${bet_size:.2f} ({kelly_fraction_adjusted*100:.2f}% of bankroll)")
        
        return bet_size
    
    def check_bet_allowed(self, 
                         current_bankroll: float,
                         proposed_stake: float,
                         pending_bet_count: int,
                         today_pnl: float) -> tuple[bool, str]:
        """
        Check if a bet should be allowed based on risk parameters
        
        Args:
            current_bankroll: Current bankroll
            proposed_stake: Proposed bet amount
            pending_bet_count: Number of currently pending bets
            today_pnl: Today's profit/loss so far
            
        Returns:
            (allowed, reason) tuple
        """
        
        # Check concurrent bet limit
        if pending_bet_count >= self.max_concurrent_bets:
            return False, f"Max concurrent bets reached ({self.max_concurrent_bets})"
        
        # Check if stake exceeds bankroll
        if proposed_stake > current_bankroll:
            return False, f"Insufficient bankroll: ${proposed_stake:.2f} > ${current_bankroll:.2f}"
        
        # Check daily loss limit
        max_daily_loss = self.starting_bankroll * self.max_daily_loss_percent
        if today_pnl < 0 and abs(today_pnl) >= max_daily_loss:
            return False, f"Daily loss limit reached: ${abs(today_pnl):.2f} >= ${max_daily_loss:.2f}"
        
        # Check if new bet would exceed daily loss limit
        if today_pnl - proposed_stake < -max_daily_loss:
            return False, f"Bet would exceed daily loss limit"
        
        # Check drawdown from peak
        current_drawdown = (self.peak_bankroll - current_bankroll) / self.peak_bankroll
        if current_drawdown >= self.max_total_drawdown_percent:
            return False, f"Max drawdown reached: {current_drawdown*100:.1f}%"
        
        # Update peak if needed
        if current_bankroll > self.peak_bankroll:
            self.peak_bankroll = current_bankroll
            logger.info(f"New peak bankroll: ${self.peak_bankroll:.2f}")
        
        return True, "OK"
    
    def get_current_drawdown(self, current_bankroll: float) -> float:
        """Calculate current drawdown from peak"""
        if self.peak_bankroll == 0:
            return 0
        return (self.peak_bankroll - current_bankroll) / self.peak_bankroll
    
    def should_halt_trading(self, current_bankroll: float) -> bool:
        """Determine if trading should be halted due to excessive losses"""
        drawdown = self.get_current_drawdown(current_bankroll)
        return drawdown >= self.max_total_drawdown_percent
