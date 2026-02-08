"""
Tests for Paper Trading System Components
"""

import pytest
from datetime import datetime
from betting.paper_trader import PaperTrader
from strategies.value_betting import ValueBettingStrategy
from strategies.line_shopping import LineShoppingStrategy
from strategies.arbitrage import ArbitrageStrategy
from strategies.manager import StrategyManager


class TestPaperTrader:
    """Tests for PaperTrader"""
    
    def test_initialization(self, tmp_path):
        """Test paper trader initializes correctly"""
        trader = PaperTrader(starting_bankroll=10000, data_dir=str(tmp_path))
        assert trader.bankroll == 10000
        assert trader.starting_bankroll == 10000
        assert len(trader.bets) == 0
    
    def test_place_bet_success(self, tmp_path):
        """Test placing a valid bet"""
        trader = PaperTrader(starting_bankroll=10000, data_dir=str(tmp_path))
        
        bet = {
            'game_id': 'test_game_1',
            'sport': 'NBA',
            'bet_type': 'moneyline',
            'selection': 'Lakers',
            'odds': -110,
            'stake': 100,
            'strategy': 'test_strategy',
            'sportsbook': 'test_book'
        }
        
        bet_id = trader.place_bet(bet)
        
        assert bet_id is not None
        assert trader.bankroll == 9900  # 10000 - 100
        assert len(trader.bets) == 1
    
    def test_place_bet_insufficient_bankroll(self, tmp_path):
        """Test bet fails with insufficient bankroll"""
        trader = PaperTrader(starting_bankroll=100, data_dir=str(tmp_path))
        
        bet = {
            'game_id': 'test_game_1',
            'sport': 'NBA',
            'bet_type': 'moneyline',
            'selection': 'Lakers',
            'odds': -110,
            'stake': 200,  # More than bankroll
            'strategy': 'test_strategy',
            'sportsbook': 'test_book'
        }
        
        bet_id = trader.place_bet(bet)
        
        assert bet_id is None
        assert trader.bankroll == 100  # Unchanged
        assert len(trader.bets) == 0
    
    def test_settle_bet_win(self, tmp_path):
        """Test settling a winning bet"""
        trader = PaperTrader(starting_bankroll=10000, data_dir=str(tmp_path))
        
        bet = {
            'game_id': 'test_game_1',
            'sport': 'NBA',
            'bet_type': 'moneyline',
            'selection': 'Lakers',
            'odds': -110,
            'stake': 110,
            'strategy': 'test_strategy',
            'sportsbook': 'test_book'
        }
        
        bet_id = trader.place_bet(bet)
        assert trader.bankroll == 9890  # 10000 - 110
        
        # Settle as win
        result = trader.settle_bet(bet_id, 'win')
        
        assert result['result'] == 'win'
        # Win at -110: bet $110 to win $100
        # New bankroll = 9890 (after bet) + 110 (stake) + 100 (winnings) = 10100
        assert trader.bankroll == 10100
    
    def test_settle_bet_loss(self, tmp_path):
        """Test settling a losing bet"""
        trader = PaperTrader(starting_bankroll=10000, data_dir=str(tmp_path))
        
        bet = {
            'game_id': 'test_game_1',
            'sport': 'NBA',
            'bet_type': 'moneyline',
            'selection': 'Lakers',
            'odds': -110,
            'stake': 100,
            'strategy': 'test_strategy',
            'sportsbook': 'test_book'
        }
        
        bet_id = trader.place_bet(bet)
        assert trader.bankroll == 9900
        
        # Settle as loss
        result = trader.settle_bet(bet_id, 'loss')
        
        assert result['result'] == 'loss'
        assert trader.bankroll == 9900  # Stake already deducted
    
    def test_settle_bet_push(self, tmp_path):
        """Test settling a pushed bet"""
        trader = PaperTrader(starting_bankroll=10000, data_dir=str(tmp_path))
        
        bet = {
            'game_id': 'test_game_1',
            'sport': 'NBA',
            'bet_type': 'moneyline',
            'selection': 'Lakers',
            'odds': -110,
            'stake': 100,
            'strategy': 'test_strategy',
            'sportsbook': 'test_book'
        }
        
        bet_id = trader.place_bet(bet)
        assert trader.bankroll == 9900
        
        # Settle as push
        result = trader.settle_bet(bet_id, 'push')
        
        assert result['result'] == 'push'
        assert trader.bankroll == 10000  # Stake returned
    
    def test_get_performance(self, tmp_path):
        """Test performance metrics calculation"""
        trader = PaperTrader(starting_bankroll=10000, data_dir=str(tmp_path))
        
        # Place and settle some bets
        for i in range(3):
            bet = {
                'game_id': f'test_game_{i}',
                'sport': 'NBA',
                'bet_type': 'moneyline',
                'selection': 'Team',
                'odds': -110,
                'stake': 100,
                'strategy': 'test_strategy',
                'sportsbook': 'test_book'
            }
            bet_id = trader.place_bet(bet)
            # Win 2, lose 1
            trader.settle_bet(bet_id, 'win' if i < 2 else 'loss')
        
        perf = trader.get_performance()
        
        assert perf['total_bets'] == 3
        assert perf['wins'] == 2
        assert perf['losses'] == 1
        assert perf['win_rate'] == pytest.approx(2/3, rel=0.01)


class TestValueBettingStrategy:
    """Tests for Value Betting Strategy"""
    
    def test_initialization(self):
        """Test strategy initializes with correct parameters"""
        strategy = ValueBettingStrategy(min_edge=0.05)
        assert strategy.min_edge == 0.05
    
    def test_odds_to_probability(self):
        """Test American odds to probability conversion"""
        strategy = ValueBettingStrategy()
        
        # Positive odds
        prob = strategy._odds_to_probability(+100)
        assert prob == pytest.approx(0.5, rel=0.01)
        
        prob = strategy._odds_to_probability(+200)
        assert prob == pytest.approx(0.333, rel=0.01)
        
        # Negative odds
        prob = strategy._odds_to_probability(-110)
        assert prob == pytest.approx(0.524, rel=0.01)
        
        prob = strategy._odds_to_probability(-200)
        assert prob == pytest.approx(0.667, rel=0.01)


class TestLineShoppingStrategy:
    """Tests for Line Shopping Strategy"""
    
    def test_initialization(self):
        """Test strategy initializes correctly"""
        strategy = LineShoppingStrategy(min_difference=5)
        assert strategy.min_difference == 5
    
    def test_is_better_odds(self):
        """Test odds comparison"""
        strategy = LineShoppingStrategy()
        
        # Positive odds - higher is better
        assert strategy._is_better_odds(+150, +100)
        assert not strategy._is_better_odds(+100, +150)
        
        # Negative odds - closer to 0 is better
        assert strategy._is_better_odds(-105, -110)
        assert not strategy._is_better_odds(-110, -105)
        
        # Mixed
        assert strategy._is_better_odds(+100, -110)


class TestArbitrageStrategy:
    """Tests for Arbitrage Strategy"""
    
    def test_initialization(self):
        """Test strategy initializes correctly"""
        strategy = ArbitrageStrategy(min_profit_margin=0.01)
        assert strategy.min_profit_margin == 0.01
    
    def test_american_to_decimal(self):
        """Test American to decimal odds conversion"""
        strategy = ArbitrageStrategy()
        
        # Positive odds
        decimal = strategy._american_to_decimal(+100)
        assert decimal == pytest.approx(2.0, rel=0.01)
        
        decimal = strategy._american_to_decimal(+200)
        assert decimal == pytest.approx(3.0, rel=0.01)
        
        # Negative odds
        decimal = strategy._american_to_decimal(-110)
        assert decimal == pytest.approx(1.909, rel=0.01)
        
        decimal = strategy._american_to_decimal(-200)
        assert decimal == pytest.approx(1.5, rel=0.01)
    
    def test_calculate_arbitrage_exists(self):
        """Test arbitrage detection when opportunity exists"""
        strategy = ArbitrageStrategy()
        
        # Example: +105 and +105 should have arbitrage
        # (Very rare but possible with pricing errors)
        result = strategy._calculate_arbitrage(+150, +150)
        
        # With both at +150 (decimal 2.5), implied prob = 0.4 each
        # Total = 0.8, so arbitrage exists
        assert result['is_arbitrage']
        assert result['profit_margin'] > 0
    
    def test_calculate_arbitrage_none(self):
        """Test when no arbitrage exists"""
        strategy = ArbitrageStrategy()
        
        # Typical market with vig: -110 and -110
        result = strategy._calculate_arbitrage(-110, -110)
        
        # With both at -110, implied prob = 0.524 each
        # Total = 1.048, no arbitrage
        assert not result['is_arbitrage']
        assert result['profit_margin'] == 0


class TestStrategyManager:
    """Tests for Strategy Manager"""
    
    def test_initialization(self):
        """Test strategy manager initializes"""
        config = {
            'strategies': {
                'value_betting': {'enabled': True, 'min_edge': 0.05},
                'line_shopping': {'enabled': True, 'min_difference': 5},
                'arbitrage': {'enabled': True, 'min_profit_margin': 0.01}
            }
        }
        
        manager = StrategyManager(config=config)
        
        assert 'value_betting' in manager.strategies
        assert 'line_shopping' in manager.strategies
        assert 'arbitrage' in manager.strategies
    
    def test_enable_disable_strategy(self):
        """Test enabling and disabling strategies"""
        config = {
            'strategies': {
                'value_betting': {'enabled': True, 'min_edge': 0.05}
            }
        }
        
        manager = StrategyManager(config=config)
        
        assert 'value_betting' in manager.enabled_strategies
        
        # Disable
        manager.disable_strategy('value_betting')
        assert 'value_betting' not in manager.enabled_strategies
        
        # Re-enable
        manager.enable_strategy('value_betting')
        assert 'value_betting' in manager.enabled_strategies


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
