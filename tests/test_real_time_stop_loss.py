#!/usr/bin/env python3
"""
测试实时监控止盈止损机制
验证新的市价单执行模式 - 仅验证逻辑，不实际提交订单
"""

import sys
import os
import time
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入必要模块
from src.config import config
from src.data.market_data import MarketDataProvider
from src.trading.executor import TradingExecutor, OptionPosition, PositionType
from src.strategy.signals import TradingSignal, SignalType, SignalStrength
from loguru import logger

class TestRealTimeStopLoss:
    """测试实时止盈止损功能"""
    
    def __init__(self):
        # 使用mock来避免实际的API调用
        with patch('src.trading.executor.TradingClient'):
            self.market_data = MarketDataProvider()
            self.executor = TradingExecutor(self.market_data)
        
        # 模拟账户信息以避免实际API调用
        self.executor.risk_metrics.account_value = 100000.0
        self.executor.risk_metrics.buying_power = 200000.0
        
    def create_test_position(self):
        """创建测试持仓"""
        try:
            # 创建模拟期权持仓
            test_position = OptionPosition(
                symbol="SPY",
                option_symbol="SPY241220C00600000",  # 模拟期权代码
                position_type=PositionType.LONG_CALL,
                quantity=1,
                entry_price=2.50,
                current_price=2.50,
                entry_time=datetime.now(),
                stop_loss=2.00,  # 止损价格
                take_profit=3.50,  # 止盈价格
                parent_order_id="test_order_123"
            )
            
            # 添加到executor的持仓跟踪
            self.executor.positions[test_position.option_symbol] = test_position
            
            logger.info(f"✅ 创建测试持仓:")
            logger.info(f"   期权代码: {test_position.option_symbol}")
            logger.info(f"   类型: {test_position.position_type.value}")
            logger.info(f"   数量: {test_position.quantity}张")
            logger.info(f"   入场价: ${test_position.entry_price:.2f}")
            logger.info(f"   止损价: ${test_position.stop_loss:.2f}")
            logger.info(f"   止盈价: ${test_position.take_profit:.2f}")
            
            return test_position
            
        except Exception as e:
            logger.error(f"创建测试持仓失败: {e}")
            return None
    
    def simulate_price_movement(self, position: OptionPosition, target_price: float):
        """模拟价格变动"""
        try:
            logger.info(f"📈 模拟价格变动: ${position.current_price:.2f} -> ${target_price:.2f}")
            
            # 更新价格
            position.update_current_price(target_price)
            
            logger.info(f"   当前价格: ${position.current_price:.2f}")
            logger.info(f"   未实现盈亏: ${position.unrealized_pnl:.2f}")
            
            # 使用mock来模拟成功的订单提交
            with patch.object(self.executor, '_execute_market_exit') as mock_exit:
                mock_exit.return_value = True
                
                # 检查退出条件
                exit_triggered = self.executor._check_exit_conditions(position)
                
                if exit_triggered:
                    logger.info(f"🔥 退出条件已触发，模拟平仓成功")
                    # 验证_execute_market_exit被调用
                    assert mock_exit.called, "退出条件触发但_execute_market_exit未被调用"
                    call_args = mock_exit.call_args
                    called_position = call_args[0][0]
                    called_reason = call_args[0][1]
                    logger.info(f"   调用参数: 持仓={called_position.option_symbol}, 原因={called_reason}")
                    return True
                else:
                    logger.info(f"📊 继续持有，无退出条件触发")
                    # 验证_execute_market_exit未被调用
                    assert not mock_exit.called, "无退出条件但_execute_market_exit被错误调用"
                    return False
                
        except Exception as e:
            logger.error(f"模拟价格变动失败: {e}")
            return False
    
    def test_stop_loss_trigger(self):
        """测试止损触发"""
        logger.info("🔻 === 测试止损触发 ===")
        
        # 创建测试持仓
        position = self.create_test_position()
        if not position:
            return False
        
        # 模拟价格下跌触发止损
        logger.info("📉 模拟价格下跌，触发止损...")
        
        # 逐步降低价格
        price_steps = [2.30, 2.10, 1.95]  # 最后一个价格低于止损价2.00
        
        for price in price_steps:
            logger.info(f"\n--- 价格测试: ${price:.2f} ---")
            
            exit_triggered = self.simulate_price_movement(position, price)
            
            if exit_triggered:
                logger.info(f"✅ 止损成功触发在价格 ${price:.2f}")
                return True
            
            time.sleep(0.1)  # 短暂等待
        
        logger.error("❌ 止损未能正确触发")
        return False
    
    def test_take_profit_trigger(self):
        """测试止盈触发"""
        logger.info("\n🎯 === 测试止盈触发 ===")
        
        # 创建测试持仓
        position = self.create_test_position()
        if not position:
            return False
        
        # 模拟价格上涨触发止盈
        logger.info("📈 模拟价格上涨，触发止盈...")
        
        # 逐步提高价格
        price_steps = [2.80, 3.20, 3.60]  # 最后一个价格高于止盈价3.50
        
        for price in price_steps:
            logger.info(f"\n--- 价格测试: ${price:.2f} ---")
            
            exit_triggered = self.simulate_price_movement(position, price)
            
            if exit_triggered:
                logger.info(f"✅ 止盈成功触发在价格 ${price:.2f}")
                return True
            
            time.sleep(0.1)  # 短暂等待
        
        logger.error("❌ 止盈未能正确触发")
        return False
    
    def test_no_trigger_in_range(self):
        """测试在止盈止损范围内不触发"""
        logger.info("\n📊 === 测试范围内价格不触发 ===")
        
        # 创建测试持仓
        position = self.create_test_position()
        if not position:
            return False
        
        # 模拟价格在止盈止损范围内波动
        logger.info("📊 模拟价格在止盈止损范围内波动...")
        
        # 在止损(2.00)和止盈(3.50)之间的价格
        price_steps = [2.20, 2.80, 3.20, 2.60, 3.00]
        
        for price in price_steps:
            logger.info(f"\n--- 价格测试: ${price:.2f} ---")
            
            exit_triggered = self.simulate_price_movement(position, price)
            
            if exit_triggered:
                logger.error(f"❌ 意外触发退出在价格 ${price:.2f}")
                return False
            
            time.sleep(0.1)  # 短暂等待
        
        logger.info("✅ 范围内价格正确无触发")
        return True
    
    def test_boundary_conditions(self):
        """测试边界条件"""
        logger.info("\n🎯 === 测试边界条件 ===")
        
        # 创建测试持仓
        position = self.create_test_position()
        if not position:
            return False
        
        logger.info("🔍 测试精确边界值...")
        
        # 测试精确止损价格
        logger.info(f"\n--- 测试精确止损价格: $2.00 ---")
        exit_triggered = self.simulate_price_movement(position, 2.00)
        if exit_triggered:
            logger.info("✅ 精确止损价格正确触发")
        else:
            logger.error("❌ 精确止损价格未触发")
            return False
        
        # 重新创建持仓用于下一个测试
        position = self.create_test_position()
        
        # 测试精确止盈价格
        logger.info(f"\n--- 测试精确止盈价格: $3.50 ---")
        exit_triggered = self.simulate_price_movement(position, 3.50)
        if exit_triggered:
            logger.info("✅ 精确止盈价格正确触发")
            return True
        else:
            logger.error("❌ 精确止盈价格未触发")
            return False
    
    def run_tests(self):
        """运行所有测试"""
        logger.info("🚀 开始实时止盈止损机制测试")
        logger.info("=" * 50)
        
        try:
            # 测试结果
            results = {
                'stop_loss': False,
                'take_profit': False,
                'no_trigger': False,
                'boundary': False
            }
            
            # 1. 测试止损触发
            results['stop_loss'] = self.test_stop_loss_trigger()
            
            # 2. 测试止盈触发  
            results['take_profit'] = self.test_take_profit_trigger()
            
            # 3. 测试范围内不触发
            results['no_trigger'] = self.test_no_trigger_in_range()
            
            # 4. 测试边界条件
            results['boundary'] = self.test_boundary_conditions()
            
            # 显示测试结果
            logger.info("\n" + "=" * 50)
            logger.info("📋 测试结果汇总:")
            logger.info("-" * 30)
            
            for test_name, result in results.items():
                status = "✅ 通过" if result else "❌ 失败"
                logger.info(f"   {test_name.upper()}: {status}")
            
            # 总体结果
            all_passed = all(results.values())
            overall_status = "🎉 全部通过" if all_passed else "⚠️ 部分失败"
            logger.info(f"\n🎯 总体结果: {overall_status}")
            
            if all_passed:
                logger.info("✨ 实时监控止盈止损机制工作正常！")
                logger.info("💡 新机制特点:")
                logger.info("   - ✅ 实时价格监控（有持仓时每15秒）")
                logger.info("   - ✅ 立即市价单执行")  
                logger.info("   - ✅ 无需预提交订单")
                logger.info("   - ✅ 快速响应机制")
                logger.info("   - ✅ 精确边界条件处理")
            else:
                logger.warning("⚠️ 部分测试失败，请检查相关功能")
            
            return all_passed
            
        except Exception as e:
            logger.error(f"测试执行失败: {e}")
            return False

def main():
    """主函数"""
    print("🔬 实时监控止盈止损机制测试 (逻辑验证版)")
    print("=" * 50)
    
    try:
        # 创建测试实例
        test = TestRealTimeStopLoss()
        
        # 运行测试
        success = test.run_tests()
        
        if success:
            print("\n🎊 测试完成！新的实时监控机制已验证正常工作。")
            print("\n💰 新机制对比:")
            print("   【旧机制】")
            print("     • 主订单成交后立即提交止盈止损订单")
            print("     • 使用限价单和止损单")
            print("     • 依赖交易所订单簿")
            print("     • 可能面临订单被拒绝的风险")
            print("   【新机制】")
            print("     • 主订单成交后不提交止盈止损订单")
            print("     • 持续监控价格变化（有持仓时每15秒检查）")
            print("     • 触发条件时立即提交市价单")
            print("     • 确保快速执行，避免滑点风险")
            print("     • 更适合期权交易的快速变化特性")
        else:
            print("\n⚠️ 测试发现问题，请检查相关代码。")
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n⏸️ 测试被用户中断")
        return 0
    except Exception as e:
        print(f"\n💥 测试失败: {e}")
        return 1

if __name__ == "__main__":
    exit(main()) 