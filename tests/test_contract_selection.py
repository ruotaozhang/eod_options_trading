#!/usr/bin/env python3
"""
合约选择详细测试脚本
模拟完整的开仓条件满足时的合约选择过程
"""

import sys
from pathlib import Path
import traceback
from datetime import datetime

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.config import config, strategy_params
from src.data.market_data import MarketDataProvider
from src.trading.executor import TradingExecutor
from src.strategy.signals import TradingSignal, SignalType, SignalStrength
from src.utils.logger_setup import setup_logger

def test_contract_selection_process():
    """测试完整的合约选择过程"""
    print("🎯 模拟开仓条件满足时的合约选择过程")
    print("=" * 60)
    
    try:
        # 初始化组件
        market_data = MarketDataProvider()
        executor = TradingExecutor(market_data)
        
        # 获取当前SPY价格
        current_price = market_data.get_current_price(config.symbol)
        print(f"📊 当前{config.symbol}价格: ${current_price:.2f}")
        
        # 模拟看涨信号
        print(f"\n📈 模拟看涨信号 (LONG) 的合约选择:")
        print("-" * 40)
        
        call_signal = TradingSignal(
            signal_type=SignalType.LONG,
            strength=SignalStrength.STRONG,
            timestamp=datetime.now(),
            price=current_price,
            confidence=0.8,
            reason="测试看涨信号"
        )
        
        # 获取目标Delta
        target_delta = (strategy_params.option_delta_min + strategy_params.option_delta_max) / 2
        print(f"🎯 目标Delta范围: {strategy_params.option_delta_min:.2f} - {strategy_params.option_delta_max:.2f}")
        print(f"🎯 目标Delta中值: {target_delta:.2f}")
        
        # 获取候选期权
        candidate_calls = market_data.find_suitable_options(config.symbol, "CALL", target_delta)
        
        if candidate_calls:
            print(f"\n📋 找到{len(candidate_calls)}个候选看涨期权:")
            for i, option in enumerate(candidate_calls):
                print(f"   {i+1}. {option['contractSymbol']}")
                print(f"      📍 行权价: ${option['strike']:.0f}")
                print(f"      📊 估算Delta: {option['estimated_delta']:.3f}")
                print(f"      💰 中间价: ${option['midPrice']:.2f}")
                print(f"      📅 到期日: {option['expiry']}")
                print(f"      🎯 Delta偏离度: {abs(option['estimated_delta'] - target_delta):.3f}")
                print()
            
            # 系统选择的最佳期权（第一个，Delta最接近目标）
            best_call = candidate_calls[0]
            print(f"✅ 系统选择的最佳看涨期权:")
            print(f"   合约代码: {best_call['contractSymbol']}")
            print(f"   选择原因: Delta最接近目标值 ({target_delta:.2f})")
            print(f"   实际Delta: {best_call['estimated_delta']:.3f}")
            print(f"   行权价: ${best_call['strike']:.0f}")
            print(f"   价内程度: {((current_price / best_call['strike'] - 1) * 100):+.1f}%")
        else:
            print("❌ 未找到符合条件的看涨期权")
        
        # 模拟看跌信号
        print(f"\n📉 模拟看跌信号 (SHORT) 的合约选择:")
        print("-" * 40)
        
        put_signal = TradingSignal(
            signal_type=SignalType.SHORT,
            strength=SignalStrength.MEDIUM,
            timestamp=datetime.now(),
            price=current_price,
            confidence=0.75,
            reason="测试看跌信号"
        )
        
        # 获取候选期权
        candidate_puts = market_data.find_suitable_options(config.symbol, "PUT", target_delta)
        
        if candidate_puts:
            print(f"\n📋 找到{len(candidate_puts)}个候选看跌期权:")
            for i, option in enumerate(candidate_puts):
                print(f"   {i+1}. {option['contractSymbol']}")
                print(f"      📍 行权价: ${option['strike']:.0f}")
                print(f"      📊 估算Delta: {option['estimated_delta']:.3f}")
                print(f"      💰 中间价: ${option['midPrice']:.2f}")
                print(f"      📅 到期日: {option['expiry']}")
                print(f"      🎯 Delta偏离度: {abs(option['estimated_delta'] - target_delta):.3f}")
                print()
            
            # 系统选择的最佳期权
            best_put = candidate_puts[0]
            print(f"✅ 系统选择的最佳看跌期权:")
            print(f"   合约代码: {best_put['contractSymbol']}")
            print(f"   选择原因: Delta最接近目标值 ({target_delta:.2f})")
            print(f"   实际Delta: {best_put['estimated_delta']:.3f}")
            print(f"   行权价: ${best_put['strike']:.0f}")
            print(f"   价内程度: {((best_put['strike'] / current_price - 1) * 100):+.1f}%")
        else:
            print("❌ 未找到符合条件的看跌期权")
        
        return True
        
    except Exception as e:
        print(f"❌ 合约选择测试失败: {e}")
        traceback.print_exc()
        return False

def test_selection_algorithm():
    """测试选择算法的详细逻辑"""
    print(f"\n🔍 期权选择算法详解")
    print("=" * 60)
    
    print("📋 选择步骤:")
    print("1️⃣ 确定期权类型 (CALL/PUT)")
    print("2️⃣ 筛选当日到期期权 (DTE=0)")
    print("3️⃣ 行权价范围筛选 (当前价格±10%)")
    print("4️⃣ 流动性检查 (必须有买卖价或成交价)")
    print("5️⃣ Delta范围筛选 (目标Delta±0.20)")
    print("6️⃣ 按Delta接近程度排序")
    print("7️⃣ 选择第一个 (Delta最接近目标)")
    
    print(f"\n🎯 选择标准优先级:")
    print("1. Delta接近程度 (最重要)")
    print("2. 流动性 (必须有报价)")
    print("3. 行权价合理性 (±10%范围内)")
    print("4. 当日到期 (DTE=0)")
    
    print(f"\n📊 具体参数:")
    print(f"   - 标的: {config.symbol}")
    print(f"   - 目标Delta: {strategy_params.option_delta_min:.2f} - {strategy_params.option_delta_max:.2f}")
    print(f"   - Delta筛选范围: ±0.20")
    print(f"   - 行权价范围: 当前价格的90% - 110%")
    print(f"   - 到期日: 只选择当日到期 (DTE=0)")
    print(f"   - 最大候选数量: 5个")
    
    return True

def test_position_sizing():
    """测试头寸规模计算"""
    print(f"\n💰 头寸规模计算逻辑")
    print("=" * 60)
    
    try:
        market_data = MarketDataProvider()
        executor = TradingExecutor(market_data)
        
        # 更新账户信息
        executor.update_account_info()
        
        print(f"📊 账户信息:")
        print(f"   - 账户总值: ${executor.risk_metrics.account_value:,.2f}")
        print(f"   - 买入力: ${executor.risk_metrics.buying_power:,.2f}")
        print(f"   - 单笔最大风险: {strategy_params.config.max_single_trade_risk_pct}% = ${executor.risk_metrics.account_value * strategy_params.config.max_single_trade_risk_pct / 100:,.2f}")
        print(f"   - 最大合约数量: {strategy_params.config.max_contracts_per_trade}张")
        
        # 模拟不同期权价格的头寸计算
        test_prices = [0.50, 1.00, 2.00, 5.00, 10.00]
        signal_confidence = 0.8
        
        print(f"\n📈 不同期权价格的头寸规模:")
        print(f"信号置信度: {signal_confidence}")
        
        for price in test_prices:
            position_size = executor.calculate_position_size(price, signal_confidence)
            total_cost = position_size * price * 100
            risk_pct = (total_cost / executor.risk_metrics.account_value) * 100
            
            print(f"   期权价格${price:.2f} -> {position_size}张合约 (总成本${total_cost:,.0f}, 风险{risk_pct:.2f}%)")
        
        return True
        
    except Exception as e:
        print(f"❌ 头寸规模测试失败: {e}")
        return False

def test_complete_selection_flow():
    """测试完整的选择流程"""
    print(f"\n🔄 完整选择流程演示")
    print("=" * 60)
    
    try:
        market_data = MarketDataProvider()
        executor = TradingExecutor(market_data)
        
        # 获取当前价格
        current_price = market_data.get_current_price(config.symbol)
        
        # 模拟交易信号
        signal = TradingSignal(
            signal_type=SignalType.LONG,
            strength=SignalStrength.STRONG,
            timestamp=datetime.now(),
            price=current_price,
            confidence=0.8,
            reason="ORB突破信号"
        )
        
        print(f"📊 交易信号:")
        print(f"   - 类型: {signal.signal_type.value}")
        print(f"   - 置信度: {signal.confidence}")
        print(f"   - 原因: {signal.reason}")
        
        # 查找最佳期权
        print(f"\n🔍 正在查找最佳期权...")
        best_option_symbol = executor.find_best_option(signal)
        
        if best_option_symbol:
            print(f"✅ 找到最佳期权: {best_option_symbol}")
            
            # 获取期权价格
            option_price = executor._get_option_price(best_option_symbol)
            print(f"💰 期权价格: ${option_price:.2f}")
            
            # 计算头寸大小
            position_size = executor.calculate_position_size(option_price, signal.confidence)
            print(f"📊 头寸大小: {position_size}张合约")
            
            # 计算总投资
            total_investment = position_size * option_price * 100
            print(f"💵 总投资金额: ${total_investment:,.2f}")
            
            print(f"\n✅ 如果条件满足，系统将交易:")
            print(f"   合约: {best_option_symbol}")
            print(f"   数量: {position_size}张")
            print(f"   单价: ${option_price:.2f}")
            print(f"   总额: ${total_investment:,.2f}")
            
        else:
            print("❌ 未找到符合条件的期权，系统将不进行交易")
        
        return best_option_symbol is not None
        
    except Exception as e:
        print(f"❌ 完整流程测试失败: {e}")
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("🧪 期权合约选择详细测试")
    print("=" * 80)
    
    # 设置日志
    setup_logger()
    
    test_results = []
    
    # 执行所有测试
    tests = [
        ("合约选择过程", test_contract_selection_process),
        ("选择算法详解", test_selection_algorithm),
        ("头寸规模计算", test_position_sizing),
        ("完整选择流程", test_complete_selection_flow)
    ]
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            test_results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}测试异常: {e}")
            test_results.append((test_name, False))
    
    # 输出测试结果汇总
    print(f"\n" + "=" * 80)
    print("📋 期权合约选择测试结果汇总")
    print("=" * 80)
    
    passed = 0
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name:<20} {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{len(test_results)} 个测试通过")

if __name__ == "__main__":
    main() 