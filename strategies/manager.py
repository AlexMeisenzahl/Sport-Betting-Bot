"""
Strategy Manager
Manage and run all strategies

Features:
- Run all strategies on current games
- Rank opportunities by confidence/edge
- Track which strategies perform best
- Allow enabling/disabling strategies
"""

from typing import Dict, List
from utils.logger import setup_logger

logger = setup_logger("strategy_manager")


class StrategyManager:
    """
    Manage and run all strategies
    """
    
    def __init__(self, config: Dict = None):
        """
        Initialize strategy manager
        
        Args:
            config: Configuration dictionary with strategy settings
        """
        self.config = config or {}
        self.strategies = {}
        self.enabled_strategies = {}
        
        # Initialize strategies
        self._initialize_strategies()
        
        logger.info(f"StrategyManager initialized with {len(self.enabled_strategies)} enabled strategies")
    
    def _initialize_strategies(self):
        """Initialize all available strategies"""
        from strategies.value_betting import ValueBettingStrategy
        from strategies.line_shopping import LineShoppingStrategy
        from strategies.arbitrage import ArbitrageStrategy
        
        # Get strategy configs
        strategies_config = self.config.get('strategies', {})
        
        # Value Betting
        value_config = strategies_config.get('value_betting', {})
        if value_config.get('enabled', True):
            min_edge = value_config.get('min_edge', 0.05)
            self.strategies['value_betting'] = ValueBettingStrategy(min_edge=min_edge)
            self.enabled_strategies['value_betting'] = True
            logger.info("✓ Value Betting strategy enabled")
        
        # Line Shopping
        line_config = strategies_config.get('line_shopping', {})
        if line_config.get('enabled', True):
            min_diff = line_config.get('min_difference', 5)
            self.strategies['line_shopping'] = LineShoppingStrategy(min_difference=min_diff)
            self.enabled_strategies['line_shopping'] = True
            logger.info("✓ Line Shopping strategy enabled")
        
        # Arbitrage
        arb_config = strategies_config.get('arbitrage', {})
        if arb_config.get('enabled', True):
            min_profit = arb_config.get('min_profit_margin', 0.01)
            self.strategies['arbitrage'] = ArbitrageStrategy(min_profit_margin=min_profit)
            self.enabled_strategies['arbitrage'] = True
            logger.info("✓ Arbitrage strategy enabled")
    
    def analyze_all(self, sport: str, odds_data: Dict) -> List[Dict]:
        """
        Run all enabled strategies and return ranked opportunities
        
        Args:
            sport: Sport name
            odds_data: Odds data from SportsbookManager
            
        Returns:
            List of opportunities ranked by confidence/edge
        """
        all_opportunities = []
        
        games = odds_data.get('games', [])
        if not games:
            logger.warning(f"No games found for {sport}")
            return []
        
        logger.info(f"Analyzing {len(games)} {sport} games with {len(self.enabled_strategies)} strategies")
        
        for game in games:
            # Run each enabled strategy
            if 'value_betting' in self.enabled_strategies:
                try:
                    value_opps = self.strategies['value_betting'].analyze(game, game)
                    all_opportunities.extend(value_opps)
                except Exception as e:
                    logger.error(f"Value betting strategy error: {e}")
            
            if 'line_shopping' in self.enabled_strategies:
                try:
                    line_opps = self.strategies['line_shopping'].get_recommendations(game, game)
                    all_opportunities.extend(line_opps)
                except Exception as e:
                    logger.error(f"Line shopping strategy error: {e}")
            
            if 'arbitrage' in self.enabled_strategies:
                try:
                    arb_opps = self.strategies['arbitrage'].find_arbitrage(game, game)
                    all_opportunities.extend(arb_opps)
                except Exception as e:
                    logger.error(f"Arbitrage strategy error: {e}")
        
        # Rank opportunities
        ranked_opportunities = self._rank_opportunities(all_opportunities)
        
        logger.info(f"Found {len(ranked_opportunities)} total opportunities")
        
        return ranked_opportunities
    
    def _rank_opportunities(self, opportunities: List[Dict]) -> List[Dict]:
        """
        Rank opportunities by quality
        
        Ranking priority:
        1. Arbitrage (guaranteed profit)
        2. High edge value bets
        3. Line shopping opportunities
        
        Args:
            opportunities: List of opportunities from all strategies
            
        Returns:
            Sorted list of opportunities
        """
        def get_priority_score(opp: Dict) -> float:
            """Calculate priority score for sorting"""
            strategy = opp.get('strategy')
            
            if strategy == 'arbitrage':
                # Highest priority, sort by profit margin
                return 1000 + opp.get('profit_margin', 0) * 100
            elif strategy == 'value_betting':
                # Sort by edge
                return 500 + opp.get('edge', 0) * 100
            elif strategy == 'line_shopping':
                # Sort by difference
                return 100 + opp.get('difference', 0)
            else:
                return 0
        
        # Sort by priority score (highest first)
        opportunities.sort(key=get_priority_score, reverse=True)
        
        return opportunities
    
    def enable_strategy(self, strategy_name: str) -> bool:
        """
        Enable a strategy
        
        Args:
            strategy_name: Name of strategy to enable
            
        Returns:
            True if successful
        """
        if strategy_name in self.strategies:
            self.enabled_strategies[strategy_name] = True
            logger.info(f"Enabled strategy: {strategy_name}")
            return True
        else:
            logger.warning(f"Strategy not found: {strategy_name}")
            return False
    
    def disable_strategy(self, strategy_name: str) -> bool:
        """
        Disable a strategy
        
        Args:
            strategy_name: Name of strategy to disable
            
        Returns:
            True if successful
        """
        if strategy_name in self.enabled_strategies:
            del self.enabled_strategies[strategy_name]
            logger.info(f"Disabled strategy: {strategy_name}")
            return True
        else:
            logger.warning(f"Strategy not enabled: {strategy_name}")
            return False
    
    def get_strategy_status(self) -> Dict:
        """
        Get status of all strategies
        
        Returns:
            Dictionary with strategy status
        """
        return {
            'total_strategies': len(self.strategies),
            'enabled_strategies': list(self.enabled_strategies.keys()),
            'disabled_strategies': [s for s in self.strategies.keys() if s not in self.enabled_strategies]
        }
    
    def get_strategy_performance(self, paper_trader) -> Dict:
        """
        Get performance metrics for each strategy
        
        Args:
            paper_trader: PaperTrader instance
            
        Returns:
            Dictionary with performance by strategy
        """
        performance = {}
        
        for strategy_name in self.strategies.keys():
            bets = paper_trader.get_bet_history({'strategy': strategy_name, 'status': 'settled'})
            
            if not bets:
                performance[strategy_name] = {
                    'total_bets': 0,
                    'wins': 0,
                    'losses': 0,
                    'win_rate': 0,
                    'total_profit': 0,
                    'roi': 0
                }
                continue
            
            wins = sum(1 for b in bets if b.get('result') == 'win')
            losses = sum(1 for b in bets if b.get('result') == 'loss')
            total_staked = sum(b.get('stake', 0) for b in bets)
            total_profit = sum(b.get('profit', 0) for b in bets)
            
            performance[strategy_name] = {
                'total_bets': len(bets),
                'wins': wins,
                'losses': losses,
                'win_rate': wins / (wins + losses) if (wins + losses) > 0 else 0,
                'total_profit': total_profit,
                'roi': (total_profit / total_staked) if total_staked > 0 else 0
            }
        
        return performance
