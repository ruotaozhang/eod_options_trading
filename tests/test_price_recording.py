"""
测试价格记录功能
验证开仓和平仓时的价格记录是否正确
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import os
import shutil
from alpaca.trading.enums import OrderStatus

from src.trading.executor import TradingExecutor, OptionPosition, PositionType
from src.data.market_data import MarketDataProvider
from src.strategy.signals import TradingSignal, SignalType, SignalStrength
from src.bot.trading_bot import EODOptionsTradingBot
from src.config import config


class TestPriceRecording(unittest.TestCase):
    """测试价格记录功能"""
    
    def setUp(self):
        """测试前的准备工作"""
        # 创建测试用的日志目录
        self.test_log_dir = 'logs/test'
        if not os.path.exists(self.test_log_dir):
            os.makedirs(self.test_log_dir)
        
        # 创建测试用的track日志目录
        self.test_track_dir = 'logs/test/track'
        if not os.path.exists(self.test_track_dir):
            os.makedirs(self.test_track_dir)
        
        # 创建mock对象
        self.mock_trading_client = Mock()
        self.mock_market_data = Mock(spec=MarketDataProvider)
        
        # 创建TradingExecutor实例，只传 market_data
        self.executor = TradingExecutor(self.mock_market_data)
        # 用mock替换trading_client
        self.executor.trading_client = self.mock_trading_client
        
        # 创建TradingBot实例
        self.trading_bot = EODOptionsTradingBot()
        self.trading_bot.tracked_log_path = os.path.join(self.test_track_dir, 'test_track.csv')
        self.trading_bot.market_data = self.mock_market_data
        
        # 设置executor的trading_bot引用
        self.executor.trading_bot_ref = self.trading_bot
        
        # 设置测试用的期权代码
        self.test_option = "SPY250613C00500000"
    
    def tearDown(self):
        """测试后的清理工作"""
        # 删除测试用的日志目录
        if os.path.exists(self.test_log_dir):
            shutil.rmtree(self.test_log_dir)
    
    @patch.object(TradingExecutor, '_check_trading_limits', return_value=True)
    def test_entry_price_recording(self, mock_check_limits):
        """测试开仓价格记录"""
        # 模拟订单成交
        mock_order = Mock()
        mock_order.id = "test_order_id"
        mock_order.qty = 1
        
        # 模拟订单成交信息
        mock_fill = Mock()
        mock_fill.qty = "1"
        mock_fill.price = "2.50"
        
        # 设置mock对象的行为
        self.mock_trading_client.submit_order.return_value = mock_order
        self.mock_trading_client.get_order_by_id.return_value = Mock(status=OrderStatus.FILLED)
        self.mock_trading_client.get_order_fills.return_value = [mock_fill]
        
        # 模拟市场数据
        self.mock_market_data._get_option_snapshot.return_value = {
            'lastPrice': 2.50,
            'bid': 2.45,
            'ask': 2.55,
            'midPrice': 2.50
        }
        self.mock_market_data.find_suitable_options.return_value = [
            {'contractSymbol': 'SPY250613C00500000', 'strike': 500, 'bid': 2.45, 'ask': 2.55, 'delta': 0.5}
        ]
        
        # 执行开仓
        signal = TradingSignal(
            signal_type=SignalType.LONG,
            strength=SignalStrength.STRONG,
            timestamp=datetime.now(),
            price=2.50,
            reason="Test signal",
            confidence=0.8
        )
        
        success = self.executor.execute_trade(signal)
        self.assertTrue(success)
        
        # 验证开仓价格记录
        position = next(iter(self.executor.positions.values()))
        self.assertEqual(position.entry_price, 2.50)
        
        # 验证track日志
        with open(self.trading_bot.tracked_log_path, 'r') as f:
            lines = f.readlines()
            # 跳过header
            data_lines = [line.strip().split(',') for line in lines[1:] if line.strip()]
            entry_prices = [cols[3] for cols in data_lines if len(cols) > 3 and cols[3]]
            self.assertTrue(any(abs(float(p) - 2.5) < 1e-6 for p in entry_prices))

    def test_get_option_latest_trade_for_tracking(self):
        """测试专门用于tracking的期权最新成交价获取"""
        # 创建真实的MarketDataProvider实例
        provider = MarketDataProvider()
        
        # Mock requests.get
        with patch('requests.get') as mock_get:
            # 设置mock响应
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {
                'trades': {
                    'SPY250613C00500000': [
                        {'price': 2.50, 'size': 100, 'timestamp': '2025-06-13T10:30:00Z'}
                    ]
                }
            }
            mock_get.return_value = mock_response
            
            # 测试获取最新成交价
            result = provider.get_option_latest_trade_for_tracking("SPY250613C00500000")
            
            # 验证结果
            self.assertEqual(result, 2.50)
            
            # 验证API调用
            mock_get.assert_called_once()
            args, kwargs = mock_get.call_args
            self.assertEqual(args[0], "https://data.alpaca.markets/v1beta1/options/trades/latest")
            self.assertEqual(kwargs['params']['symbols'], 'SPY250613C00500000')

    def test_track_option_with_latest_trade_api(self):
        """测试track_option使用最新成交价API"""
        # Mock get_option_latest_trade_for_tracking
        self.mock_market_data.get_option_latest_trade_for_tracking.return_value = 2.50
        
        # 执行track_option
        self.trading_bot.track_option("SPY250613C00500000", 2.45)
        
        # 验证API调用
        self.mock_market_data.get_option_latest_trade_for_tracking.assert_called_once_with("SPY250613C00500000")
        
        # 验证track日志
        with open(self.trading_bot.tracked_log_path, 'r') as f:
            lines = f.readlines()
            self.assertTrue(any('2.5' in line and '2.45' in line for line in lines))

    def test_update_option_close_price_with_latest_trade_api(self):
        """测试update_option_close_price使用最新成交价API"""
        # 先添加一个tracked option
        self.trading_bot.tracked_options["SPY250613C00500000"] = {'entry_price': 2.45, 'close_price': None}
        
        # Mock get_option_latest_trade_for_tracking
        self.mock_market_data.get_option_latest_trade_for_tracking.return_value = 2.75
        
        # 执行update_option_close_price
        self.trading_bot.update_option_close_price("SPY250613C00500000", 2.70)
        
        # 验证API调用
        self.mock_market_data.get_option_latest_trade_for_tracking.assert_called_once_with("SPY250613C00500000")
        
        # 验证track日志
        with open(self.trading_bot.tracked_log_path, 'r') as f:
            lines = f.readlines()
            self.assertTrue(any('2.75' in line and '2.7' in line for line in lines))

    def test_exit_price_recording(self):
        """测试平仓价格记录"""
        # 创建测试头寸
        position = OptionPosition(
            symbol="SPY",
            option_symbol="SPY250613C00500000",
            position_type=PositionType.LONG_CALL,
            quantity=1,
            entry_price=2.50,
            current_price=2.50,
            entry_time=datetime.now(),
            stop_loss=2.25,
            take_profit=3.00
        )
        self.executor.positions[position.option_symbol] = position
        
        # 模拟平仓订单
        mock_order = Mock()
        mock_order.id = "test_exit_order_id"
        mock_order.qty = 1
        
        # 模拟平仓成交信息
        mock_fill = Mock()
        mock_fill.qty = "1"
        mock_fill.price = "2.75"
        
        # 设置mock对象的行为
        self.mock_trading_client.submit_order.return_value = mock_order
        self.mock_trading_client.get_order_fills.return_value = [mock_fill]
        
        # Mock get_option_latest_trade_for_tracking for tracking bot
        self.mock_market_data.get_option_latest_trade_for_tracking.return_value = 2.75
        
        # 执行平仓
        success = self.executor._execute_market_exit(position, "Test exit")
        self.assertTrue(success)
        
        # 验证平仓价格记录
        self.assertEqual(position.current_price, 2.75)
        
        # 验证track日志
        with open(self.trading_bot.tracked_log_path, 'r') as f:
            lines = f.readlines()
            self.assertTrue(any('2.75' in line for line in lines))


if __name__ == '__main__':
    unittest.main() 