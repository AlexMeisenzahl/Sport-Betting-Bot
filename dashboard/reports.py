"""
Report Generator
Generate text/CSV reports of performance
"""

import csv
from datetime import datetime
from typing import Optional
from utils.logger import setup_logger

logger = setup_logger("reports")


class ReportGenerator:
    """
    Generate text/CSV reports of performance
    """
    
    def __init__(self):
        """Initialize report generator"""
        pass
    
    def daily_summary(self, paper_trader) -> str:
        """
        Generate daily summary report
        
        Args:
            paper_trader: PaperTrader instance
            
        Returns:
            Daily summary as formatted string
        """
        stats = paper_trader.get_performance(days=1)
        
        report = []
        report.append("=" * 60)
        report.append(f"DAILY SUMMARY - {datetime.now().strftime('%Y-%m-%d')}")
        report.append("=" * 60)
        report.append("")
        
        # Bankroll
        report.append("BANKROLL:")
        report.append(f"  Current: ${paper_trader.bankroll:,.2f}")
        report.append(f"  Starting: ${paper_trader.starting_bankroll:,.2f}")
        net_profit = paper_trader.bankroll - paper_trader.starting_bankroll
        roi = net_profit / paper_trader.starting_bankroll if paper_trader.starting_bankroll > 0 else 0
        report.append(f"  Net P&L: ${net_profit:+,.2f} ({roi * 100:+.2f}%)")
        report.append("")
        
        # Today's activity
        report.append("TODAY'S ACTIVITY:")
        report.append(f"  Total Bets: {stats['total_bets']}")
        report.append(f"  Wins: {stats['wins']}")
        report.append(f"  Losses: {stats['losses']}")
        report.append(f"  Pushes: {stats['pushes']}")
        
        if stats['total_bets'] > 0:
            report.append(f"  Win Rate: {stats['win_rate'] * 100:.1f}%")
            report.append(f"  Total Staked: ${stats['total_staked']:,.2f}")
            report.append(f"  Total Profit: ${stats['total_profit']:+,.2f}")
            
            if stats['avg_clv'] != 0:
                report.append(f"  Avg CLV: {stats['avg_clv']:+.2f}%")
        else:
            report.append("  No bets placed today")
        
        report.append("")
        report.append("=" * 60)
        
        return "\n".join(report)
    
    def weekly_summary(self, paper_trader) -> str:
        """
        Generate weekly summary report
        
        Args:
            paper_trader: PaperTrader instance
            
        Returns:
            Weekly summary as formatted string
        """
        stats = paper_trader.get_performance(days=7)
        
        report = []
        report.append("=" * 60)
        report.append(f"WEEKLY SUMMARY - Week ending {datetime.now().strftime('%Y-%m-%d')}")
        report.append("=" * 60)
        report.append("")
        
        # Bankroll
        report.append("BANKROLL:")
        report.append(f"  Current: ${paper_trader.bankroll:,.2f}")
        report.append(f"  Starting: ${paper_trader.starting_bankroll:,.2f}")
        net_profit = paper_trader.bankroll - paper_trader.starting_bankroll
        roi = net_profit / paper_trader.starting_bankroll if paper_trader.starting_bankroll > 0 else 0
        report.append(f"  Net P&L: ${net_profit:+,.2f} ({roi * 100:+.2f}%)")
        report.append("")
        
        # Week's performance
        report.append("WEEK'S PERFORMANCE:")
        report.append(f"  Total Bets: {stats['total_bets']}")
        report.append(f"  Record: {stats['wins']}-{stats['losses']}-{stats['pushes']}")
        
        if stats['total_bets'] > 0:
            report.append(f"  Win Rate: {stats['win_rate'] * 100:.1f}%")
            report.append(f"  Total Staked: ${stats['total_staked']:,.2f}")
            report.append(f"  Total Profit: ${stats['total_profit']:+,.2f}")
            report.append(f"  Avg Stake: ${stats['total_staked'] / stats['total_bets']:.2f}")
            
            if stats['avg_clv'] != 0:
                report.append(f"  Avg CLV: {stats['avg_clv']:+.2f}%")
        
        report.append("")
        
        # Strategy breakdown
        report.append("BY STRATEGY:")
        bets = paper_trader.get_bet_history({'status': 'settled'})
        strategies = {}
        
        for bet in bets:
            strategy = bet.get('strategy', 'unknown')
            if strategy not in strategies:
                strategies[strategy] = {'wins': 0, 'losses': 0, 'profit': 0}
            
            if bet['result'] == 'win':
                strategies[strategy]['wins'] += 1
            elif bet['result'] == 'loss':
                strategies[strategy]['losses'] += 1
            
            strategies[strategy]['profit'] += bet.get('profit', 0)
        
        for strategy, data in strategies.items():
            total = data['wins'] + data['losses']
            win_rate = (data['wins'] / total * 100) if total > 0 else 0
            report.append(f"  {strategy}: {data['wins']}-{data['losses']} ({win_rate:.1f}%) - ${data['profit']:+.2f}")
        
        report.append("")
        report.append("=" * 60)
        
        return "\n".join(report)
    
    def monthly_summary(self, paper_trader) -> str:
        """
        Generate monthly summary report
        
        Args:
            paper_trader: PaperTrader instance
            
        Returns:
            Monthly summary as formatted string
        """
        stats = paper_trader.get_performance(days=30)
        
        report = []
        report.append("=" * 60)
        report.append(f"MONTHLY SUMMARY - {datetime.now().strftime('%B %Y')}")
        report.append("=" * 60)
        report.append("")
        
        # Bankroll
        report.append("BANKROLL:")
        report.append(f"  Current: ${paper_trader.bankroll:,.2f}")
        report.append(f"  Starting: ${paper_trader.starting_bankroll:,.2f}")
        net_profit = paper_trader.bankroll - paper_trader.starting_bankroll
        roi = net_profit / paper_trader.starting_bankroll if paper_trader.starting_bankroll > 0 else 0
        report.append(f"  Net P&L: ${net_profit:+,.2f} ({roi * 100:+.2f}%)")
        report.append("")
        
        # Month's performance
        report.append("MONTH'S PERFORMANCE:")
        report.append(f"  Total Bets: {stats['total_bets']}")
        report.append(f"  Record: {stats['wins']}-{stats['losses']}-{stats['pushes']}")
        
        if stats['total_bets'] > 0:
            report.append(f"  Win Rate: {stats['win_rate'] * 100:.1f}%")
            report.append(f"  Total Staked: ${stats['total_staked']:,.2f}")
            report.append(f"  Total Profit: ${stats['total_profit']:+,.2f}")
            report.append(f"  Avg Stake: ${stats['total_staked'] / stats['total_bets']:.2f}")
            report.append(f"  Best Day: [Calculate from daily data]")
            report.append(f"  Worst Day: [Calculate from daily data]")
            
            if stats['avg_clv'] != 0:
                report.append(f"  Avg CLV: {stats['avg_clv']:+.2f}%")
        
        report.append("")
        report.append("=" * 60)
        
        return "\n".join(report)
    
    def export_to_csv(self, paper_trader, filename: Optional[str] = None) -> str:
        """
        Export bet history to CSV
        
        Args:
            paper_trader: PaperTrader instance
            filename: Optional filename
            
        Returns:
            Path to exported file
        """
        # Use PaperTrader's built-in CSV export
        filepath = paper_trader.export_to_csv(filename)
        
        if filepath:
            logger.info(f"Exported bet history to {filepath}")
        
        return filepath
    
    def strategy_performance_report(self, paper_trader, strategy_manager) -> str:
        """
        Generate detailed strategy performance report
        
        Args:
            paper_trader: PaperTrader instance
            strategy_manager: StrategyManager instance
            
        Returns:
            Strategy performance report as formatted string
        """
        performance = strategy_manager.get_strategy_performance(paper_trader)
        
        report = []
        report.append("=" * 60)
        report.append("STRATEGY PERFORMANCE REPORT")
        report.append("=" * 60)
        report.append("")
        
        for strategy, stats in performance.items():
            report.append(f"STRATEGY: {strategy.replace('_', ' ').upper()}")
            report.append("-" * 60)
            report.append(f"  Total Bets: {stats['total_bets']}")
            
            if stats['total_bets'] > 0:
                report.append(f"  Record: {stats['wins']}-{stats['losses']}")
                report.append(f"  Win Rate: {stats['win_rate'] * 100:.1f}%")
                report.append(f"  Total Profit: ${stats['total_profit']:+,.2f}")
                report.append(f"  ROI: {stats['roi'] * 100:+.2f}%")
            else:
                report.append("  No bets placed with this strategy")
            
            report.append("")
        
        report.append("=" * 60)
        
        return "\n".join(report)
    
    def opportunity_report(self, opportunities: list) -> str:
        """
        Generate report of current opportunities
        
        Args:
            opportunities: List of opportunity dictionaries
            
        Returns:
            Opportunities report as formatted string
        """
        report = []
        report.append("=" * 60)
        report.append(f"CURRENT OPPORTUNITIES - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("=" * 60)
        report.append("")
        
        if not opportunities:
            report.append("No opportunities found")
            report.append("")
            report.append("=" * 60)
            return "\n".join(report)
        
        # Group by strategy
        by_strategy = {}
        for opp in opportunities:
            strategy = opp.get('strategy', 'unknown')
            if strategy not in by_strategy:
                by_strategy[strategy] = []
            by_strategy[strategy].append(opp)
        
        # Report each strategy's opportunities
        for strategy, opps in by_strategy.items():
            report.append(f"{strategy.replace('_', ' ').upper()} ({len(opps)} opportunities):")
            report.append("-" * 60)
            
            for i, opp in enumerate(opps[:5], 1):  # Show top 5 per strategy
                report.append(f"  {i}. {opp.get('away_team', 'Unknown')} @ {opp.get('home_team', 'Unknown')}")
                report.append(f"     Selection: {opp.get('selection', 'N/A')}")
                
                if strategy == 'arbitrage':
                    report.append(f"     Profit Margin: {opp.get('profit_margin', 0) * 100:.2f}%")
                    report.append(f"     Guaranteed Profit: ${opp.get('guaranteed_profit', 0):.2f}")
                elif strategy == 'value_betting':
                    report.append(f"     Edge: +{opp.get('edge', 0) * 100:.1f}%")
                    report.append(f"     Odds: {opp.get('odds', 'N/A')}")
                elif strategy == 'line_shopping':
                    report.append(f"     Best Odds: {opp.get('best_odds', 'N/A')} @ {opp.get('best_bookmaker', 'N/A')}")
                    report.append(f"     Difference: {opp.get('difference', 0)} points")
                
                report.append("")
            
            if len(opps) > 5:
                report.append(f"  ... and {len(opps) - 5} more")
                report.append("")
        
        report.append("=" * 60)
        
        return "\n".join(report)
