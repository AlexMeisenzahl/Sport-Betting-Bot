"""
Terminal Dashboard
Rich terminal dashboard showing bot performance

Display sections:
1. Current bankroll and P&L
2. 30-day performance metrics
3. Recent bets (last 10)
4. Pending bets
5. Strategy performance comparison
6. Live odds for upcoming games
7. Active opportunities

Uses rich.live for real-time updates
"""

from rich.console import Console
from rich.table import Table
from rich.layout import Layout
from rich.panel import Panel
from rich.live import Live
from rich.text import Text
from datetime import datetime
from typing import Optional
import time

console = Console()


class TerminalDashboard:
    """
    Live terminal dashboard showing bot performance
    """
    
    def __init__(self, refresh_interval: int = 5):
        """
        Initialize terminal dashboard
        
        Args:
            refresh_interval: Refresh interval in seconds
        """
        self.refresh_interval = refresh_interval
        self.console = Console()
    
    def start(self, paper_trader, manager, strategy_manager=None, 
              opportunities: list = None, duration: Optional[int] = None):
        """
        Start live dashboard with auto-refresh
        
        Args:
            paper_trader: PaperTrader instance
            manager: SportsbookManager instance
            strategy_manager: StrategyManager instance (optional)
            opportunities: List of current opportunities (optional)
            duration: How long to run (seconds), None for indefinite
        """
        start_time = time.time()
        
        with Live(self._generate_dashboard(paper_trader, manager, strategy_manager, opportunities), 
                  refresh_per_second=1/self.refresh_interval, console=self.console) as live:
            
            try:
                while True:
                    time.sleep(self.refresh_interval)
                    live.update(self._generate_dashboard(paper_trader, manager, strategy_manager, opportunities))
                    
                    # Stop after duration if specified
                    if duration and (time.time() - start_time) > duration:
                        break
                        
            except KeyboardInterrupt:
                console.print("\n[yellow]Dashboard stopped by user[/yellow]")
    
    def display_once(self, paper_trader, manager, strategy_manager=None, opportunities: list = None):
        """
        Display dashboard once (no auto-refresh)
        
        Args:
            paper_trader: PaperTrader instance
            manager: SportsbookManager instance
            strategy_manager: StrategyManager instance (optional)
            opportunities: List of current opportunities (optional)
        """
        self.console.print(self._generate_dashboard(paper_trader, manager, strategy_manager, opportunities))
    
    def _generate_dashboard(self, paper_trader, manager, strategy_manager, opportunities):
        """Generate complete dashboard layout"""
        layout = Layout()
        
        # Split into sections
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=3)
        )
        
        # Split main into left and right
        layout["main"].split_row(
            Layout(name="left"),
            Layout(name="right")
        )
        
        # Header
        layout["header"].update(self._generate_header())
        
        # Left column
        layout["left"].split_column(
            Layout(self._generate_bankroll_panel(paper_trader), name="bankroll"),
            Layout(self._generate_performance_panel(paper_trader), name="performance"),
            Layout(self._generate_recent_bets_panel(paper_trader), name="recent")
        )
        
        # Right column
        layout["right"].split_column(
            Layout(self._generate_pending_bets_panel(paper_trader), name="pending"),
            Layout(self._generate_strategy_panel(paper_trader, strategy_manager), name="strategies"),
            Layout(self._generate_opportunities_panel(opportunities), name="opportunities")
        )
        
        # Footer
        layout["footer"].update(self._generate_footer())
        
        return layout
    
    def _generate_header(self):
        """Generate header panel"""
        header_text = Text()
        header_text.append("🎯 Sports Betting Bot - Paper Trading Dashboard", style="bold cyan")
        return Panel(header_text, style="bold blue")
    
    def _generate_footer(self):
        """Generate footer panel"""
        footer_text = Text()
        footer_text.append(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", style="dim")
        footer_text.append(" | Press Ctrl+C to exit", style="dim yellow")
        return Panel(footer_text, style="dim")
    
    def _generate_bankroll_panel(self, paper_trader):
        """Generate bankroll and P&L panel"""
        stats = paper_trader.get_performance(days=None)
        
        bankroll = stats['current_bankroll']
        starting = stats['starting_bankroll']
        profit = stats['net_profit']
        roi = stats['roi'] * 100
        
        # Color based on profit/loss
        profit_color = "green" if profit >= 0 else "red"
        roi_color = "green" if roi >= 0 else "red"
        
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Label", style="cyan")
        table.add_column("Value", justify="right")
        
        table.add_row("Current Bankroll:", f"[bold]{bankroll:,.2f}[/bold]")
        table.add_row("Starting Bankroll:", f"{starting:,.2f}")
        table.add_row("Net Profit/Loss:", f"[{profit_color}]{profit:+,.2f}[/{profit_color}]")
        table.add_row("ROI:", f"[{roi_color}]{roi:+.2f}%[/{roi_color}]")
        
        return Panel(table, title="💰 Bankroll", border_style="green")
    
    def _generate_performance_panel(self, paper_trader):
        """Generate performance metrics panel"""
        stats = paper_trader.get_performance(days=30)
        
        win_rate = stats['win_rate'] * 100
        win_color = "green" if win_rate >= 52.4 else "yellow" if win_rate >= 50 else "red"
        
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Metric", style="cyan")
        table.add_column("Value", justify="right")
        
        table.add_row("Total Bets (30d):", f"{stats['total_bets']}")
        table.add_row("Wins:", f"[green]{stats['wins']}[/green]")
        table.add_row("Losses:", f"[red]{stats['losses']}[/red]")
        table.add_row("Pushes:", f"{stats['pushes']}")
        table.add_row("Win Rate:", f"[{win_color}]{win_rate:.1f}%[/{win_color}]")
        table.add_row("Total Staked:", f"${stats['total_staked']:,.2f}")
        table.add_row("Total Profit:", f"${stats['total_profit']:+,.2f}")
        
        if stats['avg_clv'] != 0:
            clv_color = "green" if stats['avg_clv'] > 0 else "red"
            table.add_row("Avg CLV:", f"[{clv_color}]{stats['avg_clv']:+.2f}%[/{clv_color}]")
        
        return Panel(table, title="📊 30-Day Performance", border_style="blue")
    
    def _generate_recent_bets_panel(self, paper_trader):
        """Generate recent bets panel"""
        bets = paper_trader.get_bet_history({'status': 'settled'})
        recent_bets = sorted(bets, key=lambda x: x['settled_at'] if x.get('settled_at') else '', reverse=True)[:10]
        
        table = Table(show_header=True, box=None)
        table.add_column("Sport", style="cyan", width=6)
        table.add_column("Selection", width=15)
        table.add_column("Odds", justify="right", width=6)
        table.add_column("Stake", justify="right", width=8)
        table.add_column("Result", justify="center", width=6)
        table.add_column("Profit", justify="right", width=10)
        
        for bet in recent_bets:
            result = bet.get('result', 'pending')
            result_emoji = "✅" if result == 'win' else "❌" if result == 'loss' else "⚖️"
            profit = bet.get('profit', 0)
            profit_color = "green" if profit > 0 else "red" if profit < 0 else "yellow"
            
            table.add_row(
                bet.get('sport', '')[:6],
                bet.get('selection', '')[:15],
                str(bet.get('odds', '')),
                f"${bet.get('stake', 0):.0f}",
                result_emoji,
                f"[{profit_color}]${profit:+.2f}[/{profit_color}]"
            )
        
        return Panel(table, title=f"📜 Recent Bets (Last {len(recent_bets)})", border_style="magenta")
    
    def _generate_pending_bets_panel(self, paper_trader):
        """Generate pending bets panel"""
        pending = paper_trader.get_bet_history({'status': 'pending'})
        
        table = Table(show_header=True, box=None)
        table.add_column("Sport", style="cyan", width=6)
        table.add_column("Selection", width=15)
        table.add_column("Odds", justify="right", width=6)
        table.add_column("Stake", justify="right", width=8)
        table.add_column("Strategy", width=10)
        
        for bet in pending[:10]:  # Show up to 10 pending
            table.add_row(
                bet.get('sport', '')[:6],
                bet.get('selection', '')[:15],
                str(bet.get('odds', '')),
                f"${bet.get('stake', 0):.0f}",
                bet.get('strategy', '')[:10]
            )
        
        title = f"⏳ Pending Bets ({len(pending)})"
        return Panel(table, title=title, border_style="yellow")
    
    def _generate_strategy_panel(self, paper_trader, strategy_manager):
        """Generate strategy performance comparison panel"""
        if not strategy_manager:
            return Panel("Strategy manager not available", title="🎯 Strategy Performance", border_style="blue")
        
        performance = strategy_manager.get_strategy_performance(paper_trader)
        
        table = Table(show_header=True, box=None)
        table.add_column("Strategy", style="cyan")
        table.add_column("Bets", justify="right", width=6)
        table.add_column("W-L", justify="center", width=8)
        table.add_column("Win%", justify="right", width=7)
        table.add_column("ROI", justify="right", width=8)
        
        for strategy, stats in performance.items():
            win_rate = stats['win_rate'] * 100
            roi = stats['roi'] * 100
            
            win_color = "green" if win_rate >= 52.4 else "yellow" if win_rate >= 50 else "red"
            roi_color = "green" if roi > 0 else "red" if roi < 0 else "yellow"
            
            table.add_row(
                strategy.replace('_', ' ').title()[:12],
                str(stats['total_bets']),
                f"{stats['wins']}-{stats['losses']}",
                f"[{win_color}]{win_rate:.1f}%[/{win_color}]",
                f"[{roi_color}]{roi:+.1f}%[/{roi_color}]"
            )
        
        return Panel(table, title="🎯 Strategy Performance", border_style="blue")
    
    def _generate_opportunities_panel(self, opportunities):
        """Generate active opportunities panel"""
        if not opportunities:
            return Panel("No opportunities currently", title="🔍 Active Opportunities", border_style="green")
        
        table = Table(show_header=True, box=None)
        table.add_column("Type", style="cyan", width=8)
        table.add_column("Game", width=20)
        table.add_column("Selection", width=15)
        table.add_column("Value", justify="right", width=10)
        
        for opp in opportunities[:10]:  # Show top 10
            strategy = opp.get('strategy', '')
            
            # Format value based on strategy
            if strategy == 'arbitrage':
                value = f"{opp.get('profit_margin', 0) * 100:.2f}%"
                value_style = "bold green"
            elif strategy == 'value_betting':
                value = f"+{opp.get('edge', 0) * 100:.1f}%"
                value_style = "green"
            elif strategy == 'line_shopping':
                value = f"{opp.get('difference', 0)}"
                value_style = "cyan"
            else:
                value = "N/A"
                value_style = ""
            
            game = f"{opp.get('away_team', '')} @ {opp.get('home_team', '')}"[:20]
            
            table.add_row(
                strategy[:8],
                game,
                opp.get('selection', '')[:15],
                f"[{value_style}]{value}[/{value_style}]"
            )
        
        title = f"🔍 Active Opportunities ({len(opportunities)})"
        return Panel(table, title=title, border_style="green")
    
    def generate_performance_table(self, paper_trader):
        """Generate standalone performance metrics table"""
        return self._generate_performance_panel(paper_trader)
    
    def generate_strategy_comparison(self, paper_trader, strategy_manager):
        """Generate standalone strategy comparison table"""
        return self._generate_strategy_panel(paper_trader, strategy_manager)
