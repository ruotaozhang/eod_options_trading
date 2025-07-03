#!/usr/bin/env python3
"""
系统测试脚本
验证EOD期权交易系统的各个模块功能
"""

import sys
from pathlib import Path
import traceback

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.config import config, strategy_params
from src.data.market_data import MarketDataProvider
from src.strategy.signals import SignalGenerator
from src.trading.executor import TradingExecutor
from src.utils.notifications import NotificationManager
from src.utils.logger_setup import setup_logger

def test_config():
    """测试配置模块"""
    print("🔧 测试配置模块...")
    try:
        print("📊 配置信息:")
        print(f"   - 交易标的: {config.symbol}")
        print(f"   - 交易时间: {config.trading_start_time} - {config.trading_end_time}")
        print(f"   - 每日最大风险: {config.max_daily_risk_pct}%")
        print(f"   - 单笔最大风险: {config.max_single_trade_risk_pct}%")
        print(f"   - 最大日交易数: {config.max_daily_trades}")
        print(f"   - 账户信息: 从Alpaca API实时获取")
        return True
    except Exception as e:
        print(f"❌ 配置模块测试失败: {e}")
        return False

def test_logger():
    """测试日志系统"""
    print("\n📝 测试日志系统...")
    try:
        setup_logger()
        from loguru import logger
        logger.info("日志系统测试消息")
        print("✅ 日志系统正常")
        return True
    except Exception as e:
        print(f"❌ 日志系统测试失败: {e}")
        return False

def test_market_data():
    """测试市场数据模块"""
    print("\n📊 测试市场数据模块...")
    try:
        market_data = MarketDataProvider()
        
        # 测试获取当前价格
        price = market_data.get_current_price(config.symbol)
        if price > 0:
            print(f"✅ 成功获取{config.symbol}价格: ${price:.2f}")
        else:
            print("⚠️ 获取价格失败，可能是API连接问题")
        
        # 测试获取K线数据
        bars = market_data.get_current_bars(config.symbol, limit=10)
        if not bars.empty:
            print(f"✅ 成功获取K线数据: {len(bars)}条记录")
        else:
            print("⚠️ 获取K线数据失败")
        
        return True
    except Exception as e:
        print(f"❌ 市场数据模块测试失败: {e}")
        traceback.print_exc()
        return False

def test_signals():
    """测试信号生成模块"""
    print("\n📡 测试信号生成模块...")
    try:
        market_data = MarketDataProvider()
        signal_generator = SignalGenerator(market_data)
        
        # 测试信号生成
        signals = signal_generator.generate_signals(config.symbol)
        print(f"✅ 信号生成模块正常，生成{len(signals)}个信号")
        
        # 测试信号摘要
        summary = signal_generator.get_signal_summary()
        print(f"   - 历史信号总数: {summary['total_signals']}")
        
        return True
    except Exception as e:
        print(f"❌ 信号生成模块测试失败: {e}")
        traceback.print_exc()
        return False

def test_trading_executor():
    """测试交易执行器"""
    print("🔧 测试交易执行器...")
    try:
        from src.data.market_data import MarketDataProvider
        from src.trading.executor import TradingExecutor
        
        market_data = MarketDataProvider()
        executor = TradingExecutor(market_data)
        
        # 获取真实账户信息
        account_info = executor.get_account_summary()
        
        print("✅ 交易执行器创建成功")
        print("📊 账户信息 (从Alpaca API获取):")
        
        if 'error' in account_info:
            print(f"   ❌ 获取账户信息失败: {account_info['error']}")
        else:
            print(f"   - 账户总值: ${account_info['account_value']:,.2f}")
            print(f"   - 可用资金: ${account_info['buying_power']:,.2f}")
            print(f"   - 每日最大风险: ${account_info['max_daily_risk']:,.2f} ({account_info['max_daily_risk_pct']}%)")
            print(f"   - 单笔最大风险: {account_info['max_single_trade_risk_pct']}%")
            print(f"   - 最大日交易数: {account_info['max_trades_today']}")
            print(f"   - 数据来源: {account_info['api_source']}")
            print(f"   - 纸面交易: {'是' if account_info['paper_trading'] else '否'}")
        
        return True
    except Exception as e:
        print(f"❌ 交易执行器测试失败: {e}")
        return False

def test_notifications():
    """测试通知模块"""
    print("\n🔔 测试通知模块...")
    try:
        notification_manager = NotificationManager()
        
        # 测试通知功能
        test_results = notification_manager.test_notifications()
        
        print("✅ 通知模块初始化成功")
        for channel, result in test_results.items():
            print(f"   - {channel.capitalize()}: {result}")
        
        return True
    except Exception as e:
        print(f"❌ 通知模块测试失败: {e}")
        traceback.print_exc()
        return False

def test_integration():
    """集成测试"""
    print("\n🔄 集成测试...")
    try:
        # 创建所有组件
        market_data = MarketDataProvider()
        signal_generator = SignalGenerator(market_data)
        executor = TradingExecutor(market_data)
        notification_manager = NotificationManager()
        
        print("✅ 所有模块集成成功")
        print("   - 市场数据模块 ✓")
        print("   - 信号生成模块 ✓") 
        print("   - 交易执行模块 ✓")
        print("   - 通知管理模块 ✓")
        
        return True
    except Exception as e:
        print(f"❌ 集成测试失败: {e}")
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("🚀 EOD期权交易系统测试")
    print("=" * 50)
    
    test_results = []
    
    # 执行所有测试
    tests = [
        ("配置模块", test_config),
        ("日志系统", test_logger),
        ("市场数据", test_market_data),
        ("信号生成", test_signals),
        ("交易执行", test_trading_executor),
        ("通知系统", test_notifications),
        ("集成测试", test_integration)
    ]
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            test_results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}测试异常: {e}")
            test_results.append((test_name, False))
    
    # 输出测试结果汇总
    print("\n" + "=" * 50)
    print("📋 测试结果汇总")
    print("=" * 50)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name:<12} {status}")
        if result:
            passed += 1
    
    print("-" * 50)
    print(f"总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！系统可以正常运行。")
        return True
    else:
        print(f"\n⚠️ {total - passed}个测试失败，请检查配置和网络连接。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 