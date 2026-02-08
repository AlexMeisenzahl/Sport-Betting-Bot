#!/usr/bin/env python3
"""
Paper Trading Bot CLI
Command-line interface for the paper trading system

Modes:
- 'live': Continuously monitor and suggest bets
- 'analyze': One-time analysis of current opportunities
- 'dashboard': Show performance dashboard
- 'settle': Settle completed games
- 'report': Generate performance reports
"""

import argparse
import sys
import os
from datetime import datetime
from utils.logger import setup_logger
from utils.config_loader import ConfigLoader

logger = setup_logger("paper_trading_cli")


class PaperTradingCLI:
    """
    Command-line interface for paper trading system
    """
    
    def __init__(self, config_path: str = "config.yaml", api_key: str = None):
        """
        Initialize the CLI
        
        Args:
            config_path: Path to configuration file
            api_key: The Odds API key (optional, can use env variable)
        """
        logger.info("Initializing Paper Trading System...")
        
        # Load configuration
        self.config = ConfigLoader(config_path)
        
        # Get API key
        self.api_key = api_key or os.environ.get('THE_ODDS_API_KEY')
        
        # Initialize components
        from sportsbooks.manager import SportsbookManager
        from betting.paper_trader import PaperTrader
        from strategies.manager import StrategyManager
        from results.tracker import GameResultTracker
        from notifications.alerter import BetAlerter
        from dashboard.terminal_dashboard import TerminalDashboard
        from dashboard.reports import ReportGenerator
        
        # Paper trader
        starting_bankroll = self.config.get('paper_trading', 'starting_bankroll', default=10000)
        self.paper_trader = PaperTrader(starting_bankroll=starting_bankroll)
        
        # Sportsbook manager
        self.sportsbook_manager = SportsbookManager(api_key=self.api_key)
        
        # Strategy manager
        self.strategy_manager = StrategyManager(config=self.config.config)
        
        # Results tracker
        self.results_tracker = GameResultTracker(odds_api_key=self.api_key)
        
        # Alerter
        self.alerter = BetAlerter(config=self.config.config)
        
        # Dashboard
        dashboard_config = self.config.get('dashboard', default={})
        refresh_interval = dashboard_config.get('terminal', {}).get('refresh_interval', 5)
        self.dashboard = TerminalDashboard(refresh_interval=refresh_interval)
        
        # Reports
        self.report_generator = ReportGenerator()
        
        logger.info("Paper Trading System initialized successfully")
    
    def run_live(self, sports: list = None):
        """
        Run bot continuously
        
        Args:
            sports: List of sports to monitor (default: from config)
        """
        import time
        
        if not sports:
            # Get enabled sports from config
            sports_config = self.config.get('sports', default={})
            sports = [sport.upper() for sport, cfg in sports_config.items() 
                     if cfg.get('enabled', False)]
        
        if not sports:
            logger.error("No sports enabled in configuration")
            return
        
        logger.info(f"Starting live monitoring for: {', '.join(sports)}")
        logger.info("Press Ctrl+C to stop")
        
        try:
            poll_interval = self.config.get('data_sources', 'poll_interval_seconds', default=300)
            
            while True:
                logger.info("\n" + "=" * 60)
                logger.info(f"Polling odds at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                logger.info("=" * 60)
                
                all_opportunities = []
                
                for sport in sports:
                    logger.info(f"\nAnalyzing {sport}...")
                    
                    # Fetch odds
                    odds_data = self.sportsbook_manager.get_odds(sport, fallback=True)
                    
                    if not odds_data.get('games'):
                        logger.warning(f"No games found for {sport}")
                        continue
                    
                    # Run strategies
                    opportunities = self.strategy_manager.analyze_all(sport, odds_data)
                    
                    if opportunities:
                        logger.info(f"Found {len(opportunities)} opportunities in {sport}")
                        all_opportunities.extend(opportunities)
                        
                        # Send notifications for top opportunities
                        for opp in opportunities[:3]:  # Top 3
                            self.alerter.notify_opportunity(opp)
                    else:
                        logger.info(f"No opportunities found in {sport}")
                
                # Display summary
                if all_opportunities:
                    print(self.report_generator.opportunity_report(all_opportunities))
                
                # Wait before next poll
                logger.info(f"\nWaiting {poll_interval} seconds until next poll...")
                time.sleep(poll_interval)
                
        except KeyboardInterrupt:
            logger.info("\nStopped by user")
    
    def analyze_now(self, sport: str):
        """
        Run one-time analysis
        
        Args:
            sport: Sport to analyze (NBA, NFL, etc.)
        """
        logger.info(f"Analyzing {sport}...")
        
        # Fetch odds
        odds_data = self.sportsbook_manager.get_odds(sport, fallback=True)
        
        if not odds_data.get('games'):
            logger.error(f"No games found for {sport}")
            return
        
        logger.info(f"Found {len(odds_data['games'])} games")
        
        # Run strategies
        opportunities = self.strategy_manager.analyze_all(sport, odds_data)
        
        if opportunities:
            logger.info(f"\nFound {len(opportunities)} opportunities!")
            print(self.report_generator.opportunity_report(opportunities))
        else:
            logger.info("No opportunities found")
    
    def show_dashboard(self, duration: int = None):
        """
        Display performance dashboard
        
        Args:
            duration: How long to show dashboard (seconds), None for indefinite
        """
        logger.info("Starting dashboard...")
        
        # Get current opportunities
        opportunities = []
        # Could fetch latest opportunities here
        
        self.dashboard.start(
            self.paper_trader,
            self.sportsbook_manager,
            self.strategy_manager,
            opportunities,
            duration
        )
    
    def settle_games(self):
        """Check and settle completed games"""
        logger.info("Checking for completed games to settle...")
        
        stats = self.results_tracker.check_and_settle_pending(
            self.paper_trader,
            max_age_hours=24
        )
        
        logger.info(f"Settlement complete:")
        logger.info(f"  Games checked: {stats['games_checked']}")
        logger.info(f"  Bets settled: {stats['settled']}")
        logger.info(f"  Errors: {stats['errors']}")
    
    def generate_report(self, report_type: str = 'daily'):
        """
        Generate performance report
        
        Args:
            report_type: Type of report (daily, weekly, monthly, strategy)
        """
        if report_type == 'daily':
            print(self.report_generator.daily_summary(self.paper_trader))
        elif report_type == 'weekly':
            print(self.report_generator.weekly_summary(self.paper_trader))
        elif report_type == 'monthly':
            print(self.report_generator.monthly_summary(self.paper_trader))
        elif report_type == 'strategy':
            print(self.report_generator.strategy_performance_report(
                self.paper_trader, 
                self.strategy_manager
            ))
        else:
            logger.error(f"Unknown report type: {report_type}")
    
    def export_csv(self, filename: str = None):
        """Export bet history to CSV"""
        filepath = self.paper_trader.export_to_csv(filename)
        if filepath:
            logger.info(f"Exported to: {filepath}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Sports Betting Paper Trading Bot',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze NBA games once
  python paper_trading_cli.py analyze --sport NBA
  
  # Run live monitoring
  python paper_trading_cli.py live --sports NBA NFL
  
  # Show performance dashboard
  python paper_trading_cli.py dashboard
  
  # Settle completed games
  python paper_trading_cli.py settle
  
  # Generate daily report
  python paper_trading_cli.py report --type daily
  
  # Export bet history to CSV
  python paper_trading_cli.py export
        """
    )
    
    parser.add_argument('mode', 
                       choices=['live', 'analyze', 'dashboard', 'settle', 'report', 'export'],
                       help='Operation mode')
    
    parser.add_argument('--sport', 
                       help='Sport to analyze (for analyze mode)')
    
    parser.add_argument('--sports', 
                       nargs='+',
                       help='Sports to monitor (for live mode)')
    
    parser.add_argument('--api-key',
                       help='The Odds API key')
    
    parser.add_argument('--config',
                       default='config.yaml',
                       help='Configuration file path')
    
    parser.add_argument('--type',
                       default='daily',
                       choices=['daily', 'weekly', 'monthly', 'strategy'],
                       help='Report type (for report mode)')
    
    parser.add_argument('--duration',
                       type=int,
                       help='Duration in seconds (for dashboard mode)')
    
    parser.add_argument('--output',
                       help='Output filename (for export mode)')
    
    args = parser.parse_args()
    
    # Initialize CLI
    try:
        cli = PaperTradingCLI(config_path=args.config, api_key=args.api_key)
    except Exception as e:
        logger.error(f"Failed to initialize: {e}")
        sys.exit(1)
    
    # Execute command
    try:
        if args.mode == 'live':
            cli.run_live(sports=args.sports)
        
        elif args.mode == 'analyze':
            if not args.sport:
                logger.error("--sport is required for analyze mode")
                sys.exit(1)
            cli.analyze_now(args.sport)
        
        elif args.mode == 'dashboard':
            cli.show_dashboard(duration=args.duration)
        
        elif args.mode == 'settle':
            cli.settle_games()
        
        elif args.mode == 'report':
            cli.generate_report(report_type=args.type)
        
        elif args.mode == 'export':
            cli.export_csv(filename=args.output)
        
    except Exception as e:
        logger.error(f"Error executing {args.mode}: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
