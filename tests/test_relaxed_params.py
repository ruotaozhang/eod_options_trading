#!/usr/bin/env python3
"""
测试放宽参数后的信号生成
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from datetime import datetime, time
from src.data.market_data import MarketDataProvider
from src.strategy.signals import SignalGenerator
from src.config import config, strategy_params

def test_relaxed_parameters():
    """测试放宽参数后的信号生成"""
    print("🧪 测试放宽参数后的信号生成")
    print("=" * 50)
    
    # 备份原始参数
    original_params = {
        'orb_rsi_threshold_long': strategy_params.orb_rsi_threshold_long,
        'orb_rsi_threshold_short': strategy_params.orb_rsi_threshold_short,
        'vwap_breakout_threshold': strategy_params.vwap_breakout_threshold,
        'orb_volume_multiplier': strategy_params.orb_volume_multiplier
    }
    
    print("📊 原始参数:")
    for key, value in original_params.items():
        print(f"   {key}: {value}")
    
    # 设置放宽的参数
    print("\n🔧 设置放宽的参数:")
    strategy_params.orb_rsi_threshold_long = 55  # 降低从60到55
    strategy_params.orb_rsi_threshold_short = 45  # 提高从40到45  
    strategy_params.vwap_breakout_threshold = 0.1  # 降低从0.15到0.1
    strategy_params.orb_volume_multiplier = 1.1  # 降低从1.2到1.1
    
    relaxed_params = {
        'orb_rsi_threshold_long': strategy_params.orb_rsi_threshold_long,
        'orb_rsi_threshold_short': strategy_params.orb_rsi_threshold_short,
        'vwap_breakout_threshold': strategy_params.vwap_breakout_threshold,
        'orb_volume_multiplier': strategy_params.orb_volume_multiplier
    }
    
    for key, value in relaxed_params.items():
        print(f"   {key}: {value}")
    
    try:
        # 初始化组件
        market_data = MarketDataProvider(config)
        signal_generator = SignalGenerator(market_data)
        
        # 获取当前市场数据
        current_price = market_data.get_current_price("SPY")
        print(f"\n📈 当前SPY价格: ${current_price:.2f}")
        
        # 更新市场数据
        success = signal_generator.update_market_data("SPY")
        if not success:
            print("❌ 更新市场数据失败")
            return
        
        # 生成信号
        signals = signal_generator.generate_signals("SPY")
        
        print(f"\n🎯 使用放宽参数的信号生成结果:")
        if signals:
            print(f"🎉 生成了 {len(signals)} 个信号:")
            for signal in signals:
                print(f"   - {signal.signal_type.value}: {signal.reason}")
                print(f"     置信度: {signal.confidence:.2f}")
                print(f"     价格: ${signal.price:.2f}")
        else:
            print("⚠️ 仍然没有生成任何信号")
        
        # 检查当前VWAP偏离情况
        if not signal_generator.vwap_data.empty:
            current_vwap = signal_generator.vwap_data.iloc[-1]
            vwap_deviation = (current_price - current_vwap) / current_vwap * 100
            print(f"\n📊 VWAP分析:")
            print(f"   当前VWAP: ${current_vwap:.2f}")
            print(f"   当前偏离: {vwap_deviation:.3f}%")
            print(f"   新阈值: {strategy_params.vwap_breakout_threshold}%")
            print(f"   是否超过阈值: {'✅' if abs(vwap_deviation) > strategy_params.vwap_breakout_threshold else '❌'}")
        
        # 检查当前时间和可能的信号
        current_time = datetime.now().time()
        print(f"\n⏰ 时间分析:")
        print(f"   当前时间: {current_time}")
        
        # 检查是否接近ORB窗口
        orb_start = time(9, 45)
        orb_end = time(10, 0)
        if time(9, 40) <= current_time <= time(10, 5):
            print("   🎯 接近或在ORB窗口内，检查ORB条件:")
            if signal_generator.orb_levels:
                print(f"   ORB高点: ${signal_generator.orb_levels['high']:.2f}")
                print(f"   ORB低点: ${signal_generator.orb_levels['low']:.2f}")
                print(f"   当前价格: ${current_price:.2f}")
                
                if current_price > signal_generator.orb_levels['high']:
                    print("   ✅ 价格已突破ORB高点")
                elif current_price < signal_generator.orb_levels['low']:
                    print("   ✅ 价格已跌破ORB低点")
                else:
                    print("   ❌ 价格在ORB区间内")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 恢复原始参数
        print(f"\n🔄 恢复原始参数...")
        strategy_params.orb_rsi_threshold_long = original_params['orb_rsi_threshold_long']
        strategy_params.orb_rsi_threshold_short = original_params['orb_rsi_threshold_short']
        strategy_params.vwap_breakout_threshold = original_params['vwap_breakout_threshold']
        strategy_params.orb_volume_multiplier = original_params['orb_volume_multiplier']
        print("✅ 参数已恢复")

if __name__ == "__main__":
    test_relaxed_parameters() 