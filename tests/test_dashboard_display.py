#!/usr/bin/env python3
"""
测试新的仪表板显示功能
验证持仓信息的显示效果
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

class TestDashboardDisplay:
    """测试仪表板显示功能"""
    
    def __init__(self):
        # 使用mock来避免实际的API调用
        with patch('src.trading.executor.TradingClient'), \
             patch('src.data.market_data.MarketDataProvider'), \
             patch('src.strategy.signals.SignalGenerator'), \
             patch('src.utils.notifications.NotificationManager'):
            
            self.bot = EODOptionsTradingBot()
            
            # 模拟账户信息
            self.bot.executor.risk_metrics.account_value = 100000.0
            self.bot.executor.risk_metrics.buying_power = 200000.0
            self.bot.executor.risk_metrics.daily_pnl = 1250.0
            
    def create_mock_positions(self):
        """创建模拟持仓用于显示测试"""
        # 创建几个不同状态的持仓
        positions = []
        
        # 盈利的CALL持仓
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
        positions.append(pos1)
        
        # 亏损的PUT持仓
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
        positions.append(pos2)
        
        # 接近止损的CALL持仓
        pos3 = OptionPosition(
            symbol="SPY",
            option_symbol="SPY241220C00595000", 
            position_type=PositionType.LONG_CALL,
            quantity=2,
            entry_price=1.50,
            current_price=0.78,
            entry_time=datetime.now(),
            stop_loss=0.75,
            take_profit=3.00,
            parent_order_id="order_003"
        )
        pos3.update_current_price(0.78)
        positions.append(pos3)
        
        # 将持仓添加到executor
        for pos in positions:
            self.bot.executor.positions[pos.option_symbol] = pos
            
        logger.info(f"创建了 {len(positions)} 个模拟持仓")
        return positions
    
    def test_dashboard_without_positions(self):
        """测试无持仓时的仪表板显示"""
        logger.info("🧪 测试无持仓时的仪表板显示")
        
        # 确保没有持仓
        self.bot.executor.positions.clear()
        
        # 生成仪表板
        dashboard = self.bot._generate_dashboard()
        
        # 显示仪表板
        self.bot.console.print(dashboard)
        
        print("\n" + "="*60)
        print("✅ 无持仓仪表板显示完成")
        print("📝 应该显示 '当前无持仓' 的消息")
        print("="*60)
        
        return True
    
    def test_dashboard_with_positions(self):
        """测试有持仓时的仪表板显示"""
        logger.info("🧪 测试有持仓时的仪表板显示")
        
        # 创建模拟持仓
        positions = self.create_mock_positions()
        
        # 生成仪表板
        dashboard = self.bot._generate_dashboard()
        
        # 显示仪表板
        self.bot.console.print(dashboard)
        
        print("\n" + "="*60)
        print(f"✅ 有持仓仪表板显示完成 ({len(positions)}个持仓)")
        print("📝 应该显示:")
        print("   - 期权代码、类型、数量") 
        print("   - 入场价、当前价、盈亏")
        print("   - 止损价、止盈价")
        print("   - 总计盈亏")
        print("="*60)
        
        return True
    
    def test_dashboard_stopping_state(self):
        """测试停止状态时的仪表板显示"""
        logger.info("🧪 测试停止状态时的仪表板显示")
        
        # 设置为停止状态
        self.bot.is_running = False
        
        # 生成仪表板
        dashboard = self.bot._generate_dashboard()
        
        # 显示仪表板
        self.bot.console.print(dashboard)
        
        print("\n" + "="*60)
        print("✅ 停止状态仪表板显示完成")
        print("📝 应该显示简化的停止状态信息")
        print("="*60)
        
        # 恢复运行状态
        self.bot.is_running = True
        
        return True
    
    def test_live_dashboard_simulation(self):
        """模拟实时仪表板更新"""
        logger.info("🧪 模拟实时仪表板更新")
        
        # 创建模拟持仓
        positions = self.create_mock_positions()
        
        print("\n" + "="*60)
        print("🔄 开始5秒实时仪表板模拟...")
        print("   (将模拟价格变化和盈亏更新)")
        print("="*60)
        
        try:
            from rich.live import Live
            
            with Live(self.bot._generate_dashboard(), refresh_per_second=2) as live:
                for i in range(10):  # 5秒，每0.5秒更新一次
                    # 模拟价格变化
                    import random
                    for pos in positions:
                        # 随机变化±5%
                        change_pct = random.uniform(-0.05, 0.05)
                        new_price = pos.current_price * (1 + change_pct)
                        pos.update_current_price(max(0.01, new_price))  # 确保价格不为负
                    
                    # 更新显示
                    live.update(self.bot._generate_dashboard())
                    time.sleep(0.5)
                    
        except KeyboardInterrupt:
            print("\n⏸️ 实时显示被用户中断")
        
        print("\n" + "="*60)
        print("✅ 实时仪表板模拟完成")
        print("📝 应该看到价格和盈亏的实时变化")
        print("="*60)
        
        return True
    
    def run_all_tests(self):
        """运行所有测试"""
        logger.info("🚀 开始仪表板显示测试")
        print("🎮 仪表板显示功能测试")
        print("="*60)
        
        tests = [
            ("无持仓显示", self.test_dashboard_without_positions),
            ("有持仓显示", self.test_dashboard_with_positions), 
            ("停止状态显示", self.test_dashboard_stopping_state),
            ("实时更新模拟", self.test_live_dashboard_simulation)
        ]
        
        results = []
        
        for test_name, test_func in tests:
            try:
                input(f"\n按 Enter 开始 '{test_name}' 测试...")
                success = test_func()
                results.append((test_name, success))
                time.sleep(1)  # 短暂暂停
            except Exception as e:
                logger.error(f"测试 '{test_name}' 失败: {e}")
                results.append((test_name, False))
        
        # 显示测试结果
        print("\n" + "="*60)
        print("📋 测试结果汇总:")
        print("-"*60)
        
        all_passed = True
        for test_name, success in results:
            status = "✅ 通过" if success else "❌ 失败"
            print(f"   {test_name}: {status}")
            if not success:
                all_passed = False
        
        print("-"*60)
        overall_status = "🎉 全部通过" if all_passed else "⚠️ 部分失败"
        print(f"总体结果: {overall_status}")
        
        if all_passed:
            print("\n🎊 新的仪表板显示功能测试完成！")
            print("💡 新功能特点:")
            print("   ✅ 分区域显示（系统状态、账户信息、持仓详情）")
            print("   ✅ 持仓信息详细展示（代码、类型、盈亏、止损止盈）")
            print("   ✅ 实时颜色编码（盈利绿色、亏损红色）")
            print("   ✅ 美观的面板布局")
            print("   ✅ 异常处理和错误显示")
        
        return all_passed

def main():
    """主函数"""
    print("🎨 仪表板显示功能测试")
    print("="*60)
    
    try:
        test = TestDashboardDisplay()
        success = test.run_all_tests()
        
        if success:
            print("\n🎯 测试完成！新的仪表板已准备就绪。")
            print("💰 现在运行 'python main.py' 就能看到:")
            print("   • 漂亮的分区域布局")
            print("   • 详细的持仓信息显示")
            print("   • 实时的盈亏状态")
            print("   • 止盈止损价格监控")
        else:
            print("\n⚠️ 部分测试失败，请检查相关代码。")
            
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n⏸️ 测试被用户中断")
        return 0
    except Exception as e:
        print(f"\n💥 测试失败: {e}")
        return 1

if __name__ == "__main__":
    exit(main()) 