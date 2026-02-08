"""
Paper Trading Engine
Virtual betting system that tracks bets and performance

Features:
- Starting bankroll (default: $10,000)
- Multiple bet sizing strategies (flat, Kelly criterion, percentage)
- Track opening and closing lines
- Calculate CLV (Closing Line Value)
- Store bet history in JSON file
- Export results to CSV
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from utils.logger import setup_logger

logger = setup_logger("paper_trader")


class PaperTrader:
    """
    Paper trading engine for virtual betting
    """
    
    def __init__(self, starting_bankroll: float = 10000, 
                 data_dir: str = "data"):
        """
        Initialize paper trader
        
        Args:
            starting_bankroll: Starting bankroll amount
            data_dir: Directory to store data files
        """
        self.starting_bankroll = starting_bankroll
        self.bankroll = starting_bankroll
        self.data_dir = data_dir
        self.bets = []  # All bets (pending and settled)
        self.bet_counter = 0
        
        # Create data directory if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)
        
        # Try to load existing state
        self.load_state()
        
        logger.info(f"PaperTrader initialized with ${self.bankroll:.2f} bankroll")
    
    def place_bet(self, bet: Dict) -> Optional[str]:
        """
        Place a paper bet
        
        Args:
            bet: Dictionary with bet information:
                {
                    'game_id': str,
                    'sport': str,
                    'bet_type': str,  # 'moneyline', 'spread', 'total'
                    'selection': str,  # team name or 'over'/'under'
                    'odds': int,  # American odds (e.g., -110, +150)
                    'stake': float,  # amount to bet
                    'strategy': str,  # which strategy suggested this
                    'sportsbook': str
                }
        
        Returns:
            Bet ID if successful, None if failed
        """
        # Validate required fields
        required_fields = ['game_id', 'sport', 'bet_type', 'selection', 'odds', 'stake', 'strategy']
        for field in required_fields:
            if field not in bet:
                logger.error(f"Missing required field: {field}")
                return None
        
        # Validate stake
        if bet['stake'] > self.bankroll:
            logger.warning(f"Insufficient bankroll: ${bet['stake']} > ${self.bankroll}")
            return None
        
        if bet['stake'] <= 0:
            logger.error(f"Invalid stake: ${bet['stake']}")
            return None
        
        # Create bet record
        self.bet_counter += 1
        bet_id = f"BET-{self.bet_counter:06d}"
        
        bet_record = {
            'id': bet_id,
            'timestamp': datetime.now().isoformat(),
            'status': 'pending',
            'result': None,
            'profit': 0,
            'closing_line': None,
            'settled_at': None,
            **bet
        }
        
        # Deduct stake from bankroll
        self.bankroll -= bet['stake']
        
        # Add to bets list
        self.bets.append(bet_record)
        
        logger.info(f"Placed bet {bet_id}: {bet['sport']} {bet['selection']} {bet['bet_type']} "
                   f"@ {bet['odds']} for ${bet['stake']:.2f}")
        logger.info(f"Remaining bankroll: ${self.bankroll:.2f}")
        
        # Auto-save state
        self.save_state()
        
        return bet_id
    
    def settle_bet(self, bet_id: str, result: str, closing_line: Optional[int] = None) -> Dict:
        """
        Settle a bet as 'win', 'loss', or 'push'
        
        Args:
            bet_id: Bet identifier
            result: Result ('win', 'loss', or 'push')
            closing_line: Optional closing line for CLV calculation
            
        Returns:
            Dictionary with settlement information
        """
        if result not in ['win', 'loss', 'push']:
            logger.error(f"Invalid result: {result}")
            return {'error': 'Invalid result'}
        
        # Find bet
        bet = next((b for b in self.bets if b['id'] == bet_id), None)
        if not bet:
            logger.error(f"Bet not found: {bet_id}")
            return {'error': 'Bet not found'}
        
        if bet['status'] != 'pending':
            logger.warning(f"Bet already settled: {bet_id}")
            return {'error': 'Bet already settled'}
        
        # Calculate profit/loss
        profit = 0
        if result == 'win':
            profit = self._calculate_payout(bet['stake'], bet['odds']) - bet['stake']
            self.bankroll += bet['stake'] + profit  # Return stake + winnings
        elif result == 'loss':
            profit = -bet['stake']
            # Stake already deducted when bet was placed
        elif result == 'push':
            profit = 0
            self.bankroll += bet['stake']  # Return stake
        
        # Update bet
        bet['status'] = 'settled'
        bet['result'] = result
        bet['profit'] = profit
        bet['settled_at'] = datetime.now().isoformat()
        
        if closing_line:
            bet['closing_line'] = closing_line
            # Calculate CLV (Closing Line Value)
            bet['clv'] = self._calculate_clv(bet['odds'], closing_line)
        
        logger.info(f"Settled bet {bet_id}: {result.upper()} - Profit: ${profit:.2f}")
        logger.info(f"New bankroll: ${self.bankroll:.2f}")
        
        # Auto-save state
        self.save_state()
        
        return {
            'bet_id': bet_id,
            'result': result,
            'profit': profit,
            'bankroll': self.bankroll
        }
    
    def get_bankroll(self) -> float:
        """Get current bankroll"""
        return self.bankroll
    
    def get_performance(self, days: Optional[int] = 30) -> Dict:
        """
        Get performance metrics
        
        Args:
            days: Number of days to look back (None for all time)
            
        Returns:
            Dictionary with performance metrics
        """
        # Filter settled bets
        settled_bets = [b for b in self.bets if b['status'] == 'settled']
        
        # Filter by days if specified
        if days:
            from datetime import datetime, timedelta
            cutoff = datetime.now() - timedelta(days=days)
            settled_bets = [b for b in settled_bets 
                           if datetime.fromisoformat(b['timestamp']) > cutoff]
        
        if not settled_bets:
            return {
                'total_bets': 0,
                'wins': 0,
                'losses': 0,
                'pushes': 0,
                'win_rate': 0,
                'roi': 0,
                'total_staked': 0,
                'total_profit': 0,
                'avg_clv': 0
            }
        
        # Calculate metrics
        wins = sum(1 for b in settled_bets if b['result'] == 'win')
        losses = sum(1 for b in settled_bets if b['result'] == 'loss')
        pushes = sum(1 for b in settled_bets if b['result'] == 'push')
        
        total_staked = sum(b['stake'] for b in settled_bets)
        total_profit = sum(b['profit'] for b in settled_bets)
        
        # Calculate average CLV
        bets_with_clv = [b for b in settled_bets if b.get('clv') is not None]
        avg_clv = sum(b['clv'] for b in bets_with_clv) / len(bets_with_clv) if bets_with_clv else 0
        
        return {
            'total_bets': len(settled_bets),
            'wins': wins,
            'losses': losses,
            'pushes': pushes,
            'win_rate': wins / (wins + losses) if (wins + losses) > 0 else 0,
            'roi': (total_profit / total_staked) if total_staked > 0 else 0,
            'total_staked': total_staked,
            'total_profit': total_profit,
            'avg_clv': avg_clv,
            'current_bankroll': self.bankroll,
            'starting_bankroll': self.starting_bankroll,
            'net_profit': self.bankroll - self.starting_bankroll
        }
    
    def get_bet_history(self, filters: Optional[Dict] = None) -> List[Dict]:
        """
        Get bet history with optional filters
        
        Args:
            filters: Optional filters:
                {
                    'sport': str,
                    'strategy': str,
                    'status': str,  # 'pending' or 'settled'
                    'result': str  # 'win', 'loss', 'push'
                }
        
        Returns:
            List of bets matching filters
        """
        bets = self.bets.copy()
        
        if filters:
            if 'sport' in filters:
                bets = [b for b in bets if b.get('sport') == filters['sport']]
            if 'strategy' in filters:
                bets = [b for b in bets if b.get('strategy') == filters['strategy']]
            if 'status' in filters:
                bets = [b for b in bets if b.get('status') == filters['status']]
            if 'result' in filters:
                bets = [b for b in bets if b.get('result') == filters['result']]
        
        return bets
    
    def save_state(self):
        """Save current state to data/paper_trader_state.json"""
        state = {
            'bankroll': self.bankroll,
            'starting_bankroll': self.starting_bankroll,
            'bet_counter': self.bet_counter,
            'bets': self.bets,
            'last_updated': datetime.now().isoformat()
        }
        
        state_file = os.path.join(self.data_dir, 'paper_trader_state.json')
        try:
            with open(state_file, 'w') as f:
                json.dump(state, f, indent=2)
            logger.debug(f"State saved to {state_file}")
        except Exception as e:
            logger.error(f"Error saving state: {e}")
    
    def load_state(self):
        """Load previous state from file"""
        state_file = os.path.join(self.data_dir, 'paper_trader_state.json')
        
        if not os.path.exists(state_file):
            logger.info("No previous state found, starting fresh")
            return
        
        try:
            with open(state_file, 'r') as f:
                state = json.load(f)
            
            self.bankroll = state.get('bankroll', self.starting_bankroll)
            self.starting_bankroll = state.get('starting_bankroll', self.starting_bankroll)
            self.bet_counter = state.get('bet_counter', 0)
            self.bets = state.get('bets', [])
            
            logger.info(f"State loaded from {state_file}")
            logger.info(f"Loaded {len(self.bets)} bets, bankroll: ${self.bankroll:.2f}")
        except Exception as e:
            logger.error(f"Error loading state: {e}")
    
    def export_to_csv(self, filename: Optional[str] = None) -> str:
        """
        Export bet history to CSV
        
        Args:
            filename: Optional filename (default: bets_YYYY-MM-DD.csv)
            
        Returns:
            Path to exported file
        """
        import csv
        
        if not filename:
            timestamp = datetime.now().strftime('%Y-%m-%d')
            filename = f"bets_{timestamp}.csv"
        
        export_dir = os.path.join(self.data_dir, 'exports')
        os.makedirs(export_dir, exist_ok=True)
        
        filepath = os.path.join(export_dir, filename)
        
        # CSV headers
        headers = ['id', 'timestamp', 'sport', 'game_id', 'bet_type', 'selection', 
                  'odds', 'stake', 'strategy', 'sportsbook', 'status', 'result', 
                  'profit', 'closing_line', 'clv', 'settled_at']
        
        try:
            with open(filepath, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                
                for bet in self.bets:
                    # Extract only relevant fields
                    row = {k: bet.get(k, '') for k in headers}
                    writer.writerow(row)
            
            logger.info(f"Exported {len(self.bets)} bets to {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
            return ""
    
    def _calculate_payout(self, stake: float, odds: int) -> float:
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
    
    def _calculate_clv(self, opening_odds: int, closing_odds: int) -> float:
        """
        Calculate Closing Line Value (CLV)
        
        CLV is a measure of bet quality - positive CLV indicates
        you got better odds than the closing line
        
        Args:
            opening_odds: Odds when bet was placed
            closing_odds: Closing odds
            
        Returns:
            CLV as a percentage
        """
        # Convert American odds to implied probability
        def odds_to_prob(odds: int) -> float:
            if odds > 0:
                return 100 / (odds + 100)
            else:
                return abs(odds) / (abs(odds) + 100)
        
        opening_prob = odds_to_prob(opening_odds)
        closing_prob = odds_to_prob(closing_odds)
        
        # CLV = (Closing probability - Opening probability) / Opening probability
        clv = (closing_prob - opening_prob) / opening_prob
        
        return clv * 100  # Return as percentage
