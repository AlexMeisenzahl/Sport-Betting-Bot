"""
Main Sports Betting Bot
Orchestrates all strategies, sports, and sportsbooks
Provides real-time dashboard
"""

import time
from datetime import datetime
from typing import Dict, List
import random

from utils.config_loader import ConfigLoader
from utils.logger import setup_logger
from utils.paper_trading import PaperTradingEngine
from utils.risk_management import RiskManager
from sportsbooks.book_manager import SportsbookManager
from analytics.performance_tracker import PerformanceTracker
from analytics.clv_tracker import CLVTracker
from notifier import Notifier

# Import strategies
from strategies.sports_arbitrage import SportsArbitrageStrategy
from strategies.clv_strategy import CLVStrategy
from strategies.sharp_tracker import SharpMoneyTracker
from strategies.prop_analyzer import PropBetAnalyzer
from strategies.live_betting import LiveBettingEngine

# Import sport handlers
from sports.nba_handler import NBAHandler
from sports.nfl_handler import NFLHandler
from sports.mlb_handler import MLBHandler
from sports.nhl_handler import NHLHandler
from sports.soccer_handler import SoccerHandler
from sports.ncaaf_handler import NCAAFHandler
from sports.ncaab_handler import NCAABHandler


logger = setup_logger("betting_bot")


class SportsBettingBot:
    """
    Main bot with comprehensive dashboard
    
    Tests ALL strategies across ALL sports to identify what works
    """
    
    # Alert display constants
    MAX_ALERTS_STORED = 10  # Maximum number of alerts to keep in memory
    MAX_ALERTS_DISPLAYED = 5  # Maximum number of alerts to show in dashboard
    MAX_ALERT_NAME_LENGTH = 30  # Maximum length for game/market names in alerts
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the betting bot"""
        logger.info("=" * 60)
        logger.info("SPORTS BETTING BOT STARTING")
        logger.info("=" * 60)
        
        # Load configuration
        self.config = ConfigLoader(config_path)
        
        # Initialize paper trading
        self.paper_trading = PaperTradingEngine(
            starting_bankroll=self.config.get_starting_bankroll(),
            realistic_mode=self.config.get('paper_trading', 'realistic_mode', default=True)
        )
        
        # Initialize risk management
        self.risk_manager = RiskManager(
            starting_bankroll=self.config.get_starting_bankroll(),
            max_daily_loss_percent=self.config.get('risk_management', 'max_daily_loss_percent', default=0.10),
            max_total_drawdown_percent=self.config.get('risk_management', 'max_total_drawdown_percent', default=0.20),
            max_concurrent_bets=self.config.get_max_concurrent_bets(),
            kelly_fraction=self.config.get_kelly_fraction()
        )
        
        # Initialize sportsbook manager
        enabled_books = {
            book: self.config.get('sportsbooks', book, 'enabled', default=False)
            for book in ['fanduel', 'draftkings', 'betmgm', 'caesars', 'pointsbet']
        }
        self.sportsbook_manager = SportsbookManager(enabled_books)
        
        # Initialize analytics
        self.performance_tracker = PerformanceTracker()
        self.clv_tracker = CLVTracker()
        
        # Initialize alerts list
        self.alerts = []
        
        # Initialize notifier
        try:
            self.notifier = Notifier(self.config)
        except Exception as e:
            logger.warning(f"Failed to initialize notifier: {e}. Continuing without notifications.")
            self.notifier = None
        
        # Initialize strategies
        self.strategies = {}
        if self.config.is_strategy_enabled('arbitrage'):
            self.strategies['arbitrage'] = SportsArbitrageStrategy(
                min_profit_percent=self.config.get('strategies', 'arbitrage', 'min_profit_percent', default=0.5)
            )
        if self.config.is_strategy_enabled('clv_model'):
            # Will initialize per sport
            pass
        if self.config.is_strategy_enabled('sharp_tracker'):
            self.strategies['sharp_tracker'] = SharpMoneyTracker(
                min_sharp_score=self.config.get('strategies', 'sharp_tracker', 'min_sharp_score', default=70)
            )
        if self.config.is_strategy_enabled('prop_analyzer'):
            self.strategies['prop_analyzer'] = PropBetAnalyzer(
                min_edge_percent=self.config.get('strategies', 'prop_analyzer', 'min_edge_percent', default=10)
            )
        if self.config.is_strategy_enabled('live_betting'):
            self.strategies['live_betting'] = LiveBettingEngine(
                min_edge_percent=self.config.get('strategies', 'live_betting', 'min_edge_percent', default=5)
            )
        
        # Initialize sport handlers
        self.sport_handlers = {}
        if self.config.is_sport_enabled('nba'):
            self.sport_handlers['nba'] = NBAHandler()
        if self.config.is_sport_enabled('nfl'):
            self.sport_handlers['nfl'] = NFLHandler()
        if self.config.is_sport_enabled('mlb'):
            self.sport_handlers['mlb'] = MLBHandler()
        if self.config.is_sport_enabled('nhl'):
            self.sport_handlers['nhl'] = NHLHandler()
        if self.config.is_sport_enabled('soccer'):
            self.sport_handlers['soccer'] = SoccerHandler()
        if self.config.is_sport_enabled('ncaaf'):
            self.sport_handlers['ncaaf'] = NCAAFHandler()
        if self.config.is_sport_enabled('ncaab'):
            self.sport_handlers['ncaab'] = NCAABHandler()
        
        self.running = False
        self.day_count = 0
        
        logger.info(f"Initialized with {len(self.strategies)} strategies and {len(self.sport_handlers)} sports")
    
    def add_alert(self, message: str):
        """
        Add an alert to the alerts list with timestamp
        
        Args:
            message: Alert message with emoji prefix
        
        Note:
            Keeps the last MAX_ALERTS_STORED alerts in memory.
            Dashboard displays the last MAX_ALERTS_DISPLAYED alerts.
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        alert_entry = f"[{timestamp}] {message}"
        
        # Add to alerts list (keep last MAX_ALERTS_STORED)
        self.alerts.append(alert_entry)
        if len(self.alerts) > self.MAX_ALERTS_STORED:
            self.alerts = self.alerts[-self.MAX_ALERTS_STORED:]
    
    def run(self, duration_days: int = 30):
        """
        Run the bot for specified duration
        
        Args:
            duration_days: Number of days to run (default: 30 for testing)
        """
        logger.info(f"Starting {duration_days}-day paper trading test")
        self.running = True
        
        try:
            while self.running and self.day_count < duration_days:
                self.day_count += 1
                
                logger.info(f"\n{'=' * 60}")
                logger.info(f"DAY {self.day_count} / {duration_days}")
                logger.info(f"{'=' * 60}\n")
                
                # Run daily cycle
                self._run_daily_cycle()
                
                # Display dashboard
                self.display_dashboard()
                
                # Check if should halt due to losses
                if self.risk_manager.should_halt_trading(self.paper_trading.get_bankroll()):
                    logger.warning("HALTING: Maximum drawdown reached")
                    break
                
                # Simulate day passing (in production, would run continuously)
                time.sleep(2)  # Short delay for demonstration
                
            # Testing period complete
            logger.info(f"\n{'=' * 60}")
            logger.info(f"30-DAY TEST COMPLETE!")
            logger.info(f"{'=' * 60}\n")
            
            # Generate final recommendations
            self._generate_final_recommendations()
            
        except KeyboardInterrupt:
            logger.info("\nBot stopped by user")
        finally:
            self.running = False
    
    def _run_daily_cycle(self):
        """Run one day's worth of betting activity"""
        
        # Scan all sports for opportunities
        for sport_name, handler in self.sport_handlers.items():
            logger.info(f"\nScanning {sport_name.upper()}...")
            
            # Get today's games
            games = handler.fetch_games_today()
            
            if not games:
                logger.info(f"  No games today for {sport_name}")
                continue
            
            logger.info(f"  Found {len(games)} games")
            
            # Check which strategies are enabled for this sport
            sport_strategies = self.config.get_sport_strategies(sport_name)
            
            for game in games:
                # Try each enabled strategy
                if 'arbitrage' in sport_strategies and 'arbitrage' in self.strategies:
                    self._try_arbitrage(sport_name, game)
                
                if 'clv_model' in sport_strategies:
                    self._try_clv_model(sport_name, game)
                
                if 'sharp_tracker' in sport_strategies and 'sharp_tracker' in self.strategies:
                    self._try_sharp_tracker(sport_name, game)
                
                if 'props' in sport_strategies and 'prop_analyzer' in self.strategies:
                    self._try_props(sport_name, game)
                
                if 'live' in sport_strategies and 'live_betting' in self.strategies:
                    self._try_live_betting(sport_name, game)
        
        # Settle some bets (simulate games finishing)
        self._settle_pending_bets()
    
    def _try_arbitrage(self, sport: str, game: Dict):
        """Try to find arbitrage opportunities"""
        arb_strategy = self.strategies.get('arbitrage')
        if not arb_strategy:
            return
        
        opportunities = arb_strategy.find_arbitrage_opportunities(
            self.sportsbook_manager,
            sport,
            [game['game_id']]
        )
        
        for opp in opportunities:
            # Validate opportunity
            valid, reason = arb_strategy.validate_opportunity(opp)
            if not valid:
                continue
            
            # Calculate stakes
            bankroll = self.paper_trading.get_bankroll()
            stakes = arb_strategy.calculate_optimal_stakes(opp, bankroll)
            
            # Place both sides (in reality, would place sequentially with checks)
            logger.info(f"  ARBITRAGE OPPORTUNITY: {opp['game']} - {opp['type']}")
            logger.info(f"    Expected profit: ${stakes['expected_profit']:.2f} ({opp['profit_percent']:.2f}%)")
            
            # Add alert to dashboard
            game_short = opp.get('game', 'Unknown')[:self.MAX_ALERT_NAME_LENGTH]  # Truncate long names
            alert_msg = f"💰 {game_short}... ({opp['profit_percent']:.1f}% profit)"
            self.add_alert(alert_msg)
            
            # Send notification
            if self.notifier:
                try:
                    self.notifier.alert_opportunity_found(opp['game'], opp['profit_percent'])
                except Exception as e:
                    logger.debug(f"Notification failed: {e}")
    
    def _try_clv_model(self, sport: str, game: Dict):
        """Try CLV strategy with predictive model"""
        # Initialize CLV strategy for this sport
        clv_strategy = CLVStrategy(
            sport=sport,
            min_edge_points=self.config.get('strategies', 'clv_model', 'min_edge_points', default=1.5)
        )
        
        # Get current line (mock)
        current_line = random.uniform(-10, 10)
        
        # Find value bets
        value_bet = clv_strategy.find_value_bets(game, current_line)
        
        if value_bet:
            logger.info(f"  CLV VALUE BET: {game.get('home')} vs {game.get('away')}")
            logger.info(f"    Predicted: {value_bet['predicted_spread']:.1f}, Line: {value_bet['bet_line']:.1f}")
            logger.info(f"    Edge: {value_bet['edge_points']:.1f} points")
            
            # Place bet if passes risk checks
            self._place_bet(sport, game, 'clv_model', value_bet)
    
    def _try_sharp_tracker(self, sport: str, game: Dict):
        """Try sharp money tracking"""
        sharp_tracker = self.strategies.get('sharp_tracker')
        if not sharp_tracker:
            return
        
        # Monitor line movements
        sharp_tracker.monitor_line_movements(sport, game['game_id'], self.sportsbook_manager)
        
        # Detect signals
        signal = sharp_tracker.detect_sharp_signals(sport, game['game_id'])
        
        if signal:
            logger.info(f"  SHARP SIGNAL: {game.get('home')} vs {game.get('away')}")
            logger.info(f"    Score: {signal['sharp_score']}, Side: {signal['sharp_side']}")
    
    def _try_props(self, sport: str, game: Dict):
        """Try prop analyzer"""
        prop_analyzer = self.strategies.get('prop_analyzer')
        if not prop_analyzer:
            return
        
        opportunities = prop_analyzer.analyze_player_props(sport, game)
        
        for opp in opportunities:
            logger.info(f"  PROP OPPORTUNITY: {opp['player']} {opp['prop_type']} {opp['side']}")
            logger.info(f"    Line: {opp['line']}, Expected: {opp['expected']}, Edge: {opp['edge_percent']:.1f}%")
    
    def _try_live_betting(self, sport: str, game: Dict):
        """Try live betting"""
        live_engine = self.strategies.get('live_betting')
        if not live_engine:
            return
        
        # Monitor live games
        live_games = live_engine.monitor_live_games(sport)
        
        for live_game in live_games:
            opp = live_engine.detect_live_opportunities(live_game)
            if opp:
                logger.info(f"  LIVE OPPORTUNITY: {live_game.get('home')} vs {live_game.get('away')}")
    
    def _place_bet(self, sport: str, game: Dict, strategy: str, bet_info: Dict):
        """Place a bet through paper trading"""
        bankroll = self.paper_trading.get_bankroll()
        pending_count = len(self.paper_trading.get_pending_bets())
        
        # Calculate stake
        stake = bankroll * 0.02  # 2% of bankroll per bet
        
        # Check risk management
        allowed, reason = self.risk_manager.check_bet_allowed(
            bankroll, stake, pending_count, 0  # Simplified
        )
        
        if not allowed:
            logger.warning(f"  Bet blocked: {reason}")
            return
        
        # Place bet
        bet = self.paper_trading.place_bet(
            sport=sport,
            game=game.get('game_id', 'unknown'),
            bet_type='spread',
            side=bet_info.get('side', 'home'),
            odds=-110,
            stake=stake,
            strategy=strategy
        )
        
        if bet:
            logger.info(f"  ✓ Bet placed: {bet['id']} - ${stake:.2f}")
    
    def _settle_pending_bets(self):
        """Settle pending bets (simulate games finishing)"""
        pending = self.paper_trading.get_pending_bets()
        
        # Randomly settle some bets
        for bet in pending[:min(3, len(pending))]:  # Settle up to 3 per day
            # Random outcome (in production, fetch actual results)
            won = random.random() < 0.52  # Slight edge
            
            # Mock closing line for CLV
            closing_line = bet['odds'] + random.uniform(-5, 5)
            
            # Settle bet
            self.paper_trading.settle_bet(bet['id'], won, closing_line)
            
            # Track performance
            self.performance_tracker.track_bet_result(bet, 'win' if won else 'loss')
            
            # Track CLV
            self.clv_tracker.track_bet_clv(bet, closing_line)
    
    def display_dashboard(self):
        """
        Real-time terminal dashboard showing:
        - Current bankroll and P&L
        - Active bets
        - Strategy performance matrix
        - Sport performance breakdown
        - Current opportunities
        - CLV tracking
        """
        print("\n" + "=" * 80)
        print(f"SPORTS BETTING BOT DASHBOARD - Day {self.day_count}")
        print("=" * 80)
        
        # Bankroll section
        stats = self.paper_trading.get_stats()
        print(f"\n💰 BANKROLL")
        print(f"   Current: ${stats['current_bankroll']:.2f}")
        print(f"   Starting: ${stats['starting_bankroll']:.2f}")
        print(f"   Profit/Loss: ${stats['total_profit']:.2f} ({stats['roi']*100:+.2f}%)")
        
        # Bet statistics
        print(f"\n📊 BETTING STATISTICS")
        print(f"   Total Bets: {stats['total_bets']}")
        print(f"   Wins: {stats['wins']} | Losses: {stats['losses']}")
        print(f"   Win Rate: {stats['win_rate']*100:.1f}%")
        print(f"   Pending: {stats['pending_bets']}")
        
        # CLV Analysis
        if self.clv_tracker.clv_records:
            avg_clv = self.clv_tracker.calculate_average_clv()
            print(f"\n📈 CLOSING LINE VALUE (CLV)")
            print(f"   Average CLV: {avg_clv:+.2f} points")
            if avg_clv > 0.5:
                print(f"   Status: ✓ BEATING THE CLOSING LINE")
            elif avg_clv < -0.5:
                print(f"   Status: ✗ LOSING TO THE CLOSING LINE")
            else:
                print(f"   Status: ≈ NEUTRAL")
        
        # Strategy performance matrix
        if stats['total_bets'] >= 5:
            print(f"\n🎯 STRATEGY PERFORMANCE")
            for strategy_name in ['arbitrage', 'clv_model', 'sharp_tracker', 'prop_analyzer', 'live_betting']:
                perf = self.performance_tracker.calculate_strategy_performance(strategy_name)
                if perf['total_bets'] > 0:
                    print(f"   {strategy_name:20s}: {perf['total_bets']:3d} bets | ROI: {perf['roi']*100:+6.2f}%")
        
        # Alerts section
        if self.alerts:
            print(f"\n🚨 ALERTS (Last {min(len(self.alerts), self.MAX_ALERTS_DISPLAYED)})")
            print("   " + "─" * 56)
            for alert in self.alerts[-self.MAX_ALERTS_DISPLAYED:]:  # Show last MAX_ALERTS_DISPLAYED alerts
                print(f"   {alert}")
            print("   " + "─" * 56)
        
        print("\n" + "=" * 80)
    
    def _generate_final_recommendations(self):
        """Generate recommendations after testing period"""
        print("\n" + "=" * 80)
        print("30-DAY TEST RESULTS & RECOMMENDATIONS")
        print("=" * 80)
        
        recommendations = self.performance_tracker.generate_recommendations(min_sample_size=10)
        
        print(f"\n✅ STRATEGIES TO DEPLOY ({len(recommendations['deploy'])} found):")
        for rec in recommendations['deploy'][:5]:  # Top 5
            print(f"   • {rec['strategy']:15s} + {rec['sport']:10s} → +{rec['roi']*100:.1f}% ROI ({rec['bets']} bets)")
        
        print(f"\n❌ STRATEGIES TO AVOID ({len(recommendations['avoid'])} found):")
        for rec in recommendations['avoid'][:5]:  # Worst 5
            print(f"   • {rec['strategy']:15s} + {rec['sport']:10s} → {rec['roi']*100:.1f}% ROI ({rec['bets']} bets)")
        
        # Overall CLV
        avg_clv = self.clv_tracker.calculate_average_clv()
        print(f"\n📈 OVERALL CLOSING LINE VALUE: {avg_clv:+.2f} points")
        
        # Final stats
        stats = self.paper_trading.get_stats()
        print(f"\n💰 FINAL BANKROLL: ${stats['current_bankroll']:.2f}")
        print(f"   Total Return: {stats['roi']*100:+.2f}%")
        
        print("\n" + "=" * 80)


if __name__ == "__main__":
    # Run the bot
    bot = SportsBettingBot()
    bot.run(duration_days=30)
