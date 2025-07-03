#!/usr/bin/env python3
"""
快速测试新的仪表板显示功能
非交互式版本，直接运行所有测试
"""

import sys
import time
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入必要模块
from src.bot.trading_bot import EODOptionsTradingBot
from src.trading.executor import OptionPosition, PositionType
from loguru import logger

def quick_test():
    """快速测试仪表板功能"""
    print("🎨 快速仪表板显示测试")
    print("="*50)
    
    try:
        # 使用mock避免API调用
        with patch('src.trading.executor.TradingClient'), \
             patch('src.data.market_data.MarketDataProvider'), \
             patch('src.strategy.signals.SignalGenerator'), \
             patch('src.utils.notifications.NotificationManager'):
            
            bot = EODOptionsTradingBot()
            
            # 确保bot处于运行状态
            bot.is_running = True
            
            # 模拟账户信息
            bot.executor.risk_metrics.account_value = 100000.0
            bot.executor.risk_metrics.buying_power = 200000.0
            bot.executor.risk_metrics.daily_pnl = 1250.0
            
            # 模拟position_summary和risk_summary的返回值
            def mock_get_position_summary():
                return {
                    'total_positions': len(bot.executor.positions),
                    'daily_trades': 5,
                    'daily_pnl': 850.0,
                    'positions': []
                }
            
            def mock_get_risk_summary():
                return {
                    'account_value': 100000.0,
                    'daily_pnl': 1250.0,
                    'risk_utilization_pct': 35.5
                }
            
            bot.executor.get_position_summary = mock_get_position_summary
            bot.executor.get_risk_summary = mock_get_risk_summary
            
            print("\n1️⃣ 测试无持仓显示:")
            print("-" * 30)
            
            # 确保没有持仓
            bot.executor.positions.clear()
            dashboard = bot._generate_dashboard()
            bot.console.print(dashboard)
            
            print("\n2️⃣ 测试有持仓显示:")
            print("-" * 30)
            
            # 创建模拟持仓
            pos1 = OptionPosition(
                symbol="SPY",
                option_symbol="SPY241220C00590000",
                position_type=PositionType.LONG_CALL,
                quantity=5,
                entry_price=2.10,
                current_price=2.85,
                entry_time=datetime.now(),
                stop_loss=1.05,
                take_profit=4.20,
                parent_order_id="order_001"
            )
            pos1.update_current_price(2.85)
            
            pos2 = OptionPosition(
                symbol="SPY", 
                option_symbol="SPY241220P00585000",
                position_type=PositionType.LONG_PUT,
                quantity=3,
                entry_price=1.75,
                current_price=1.20,
                entry_time=datetime.now(),
                stop_loss=0.88,
                take_profit=3.50,
                parent_order_id="order_002"
            )
            pos2.update_current_price(1.20)
            
            # 添加盈利持仓
            pos3 = OptionPosition(
                symbol="SPY",
                option_symbol="SPY241220C00600000",
                position_type=PositionType.LONG_CALL,
                quantity=2,
                entry_price=1.50,
                current_price=2.25,
                entry_time=datetime.now(),
                stop_loss=0.75,
                take_profit=3.00,
                parent_order_id="order_003"
            )
            pos3.update_current_price(2.25)
            
            # 添加到executor
            bot.executor.positions[pos1.option_symbol] = pos1
            bot.executor.positions[pos2.option_symbol] = pos2
            bot.executor.positions[pos3.option_symbol] = pos3
            
            dashboard = bot._generate_dashboard()
            bot.console.print(dashboard)
            
            print("\n3️⃣ 测试停止状态显示:")
            print("-" * 30)
            
            bot.is_running = False
            dashboard = bot._generate_dashboard()
            bot.console.print(dashboard)
            
            print("\n✅ 仪表板测试完成!")
            print("🎯 新仪表板功能:")
            print("   • 分区域布局（系统状态、账户信息、持仓详情）")
            print("   • 持仓信息详细显示（代码、类型、盈亏、止损止盈）")
            print("   • 实时颜色编码（盈利绿色、亏损红色）")
            print("   • 美观的面板设计")
            print("   • 总计盈亏显示")
            
            return True
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = quick_test()
    exit(0 if success else 1) 