#!/usr/bin/env python3
"""
详细的信号调试脚本
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from datetime import datetime, time
from src.data.market_data import MarketDataProvider, TechnicalIndicators
from src.strategy.signals import SignalGenerator
from src.config import config, strategy_params

def detailed_signal_debug():
    """详细调试每个信号条件"""
    print("🔍 详细信号条件调试")
    print("=" * 60)
    
    try:
        # 初始化组件
        market_data = MarketDataProvider(config)
        signal_generator = SignalGenerator(market_data)
        indicators = TechnicalIndicators()
        
        # 更新数据
        success = signal_generator.update_market_data("SPY")
        if not success:
            print("❌ 数据更新失败")
            return
            
        current_time = datetime.now().time()
        print(f"当前时间: {current_time}")
        
        # 检查时间窗口
        orb_start = time(9, 45)
        orb_end = time(10, 15)
        in_orb_window = orb_start <= current_time <= orb_end
        print(f"ORB时间窗口 (09:45-10:15): {'✅' if in_orb_window else '❌'}")
        
        if not in_orb_window:
            print("🚫 不在ORB时间窗口内，跳过ORB检查")
            return
            
        # 检查数据可用性
        if signal_generator.current_bars.empty:
            print("❌ 没有市场数据")
            return
            
        if not signal_generator.orb_levels:
            print("❌ 没有ORB水平")
            return
            
        print("✅ 基础数据检查通过")
        
        # 获取当前价格和成交量
        latest_bar = signal_generator.current_bars.iloc[-1]
        current_price = latest_bar['close']
        current_volume = latest_bar['volume']
        
        print(f"\n📊 当前市场数据:")
        print(f"   当前价格: ${current_price:.2f}")
        print(f"   当前成交量: {current_volume:,.0f}")
        print(f"   ORB高点: ${signal_generator.orb_levels['high']:.2f}")
        print(f"   ORB低点: ${signal_generator.orb_levels['low']:.2f}")
        print(f"   ORB成交量: {signal_generator.orb_levels['volume']:,.0f}")
        
        # 检查价格突破条件
        above_high = current_price > signal_generator.orb_levels['high']
        below_low = current_price < signal_generator.orb_levels['low']
        print(f"\n💰 价格突破检查:")
        print(f"   突破高点: {'✅' if above_high else '❌'} ({current_price:.2f} vs {signal_generator.orb_levels['high']:.2f})")
        print(f"   跌破低点: {'✅' if below_low else '❌'} ({current_price:.2f} vs {signal_generator.orb_levels['low']:.2f})")
        
        # 检查成交量条件
        volume_threshold = signal_generator.orb_levels['volume'] * strategy_params.orb_volume_multiplier
        volume_ok = current_volume > volume_threshold
        print(f"\n📊 成交量检查:")
        print(f"   当前成交量: {current_volume:,.0f}")
        print(f"   成交量阈值: {volume_threshold:,.0f} (倍数: {strategy_params.orb_volume_multiplier})")
        print(f"   成交量充足: {'✅' if volume_ok else '❌'}")
        
        # 计算并检查RSI
        rsi_series = indicators.calculate_rsi(signal_generator.current_bars)
        if rsi_series.empty:
            print("\n❌ 无法计算RSI")
            return
            
        current_rsi = rsi_series.iloc[-1]
        rsi_long_ok = current_rsi > strategy_params.orb_rsi_threshold_long
        rsi_short_ok = current_rsi < strategy_params.orb_rsi_threshold_short
        
        print(f"\n📈 RSI检查:")
        print(f"   当前RSI: {current_rsi:.1f}")
        print(f"   多头RSI阈值: {strategy_params.orb_rsi_threshold_long}")
        print(f"   空头RSI阈值: {strategy_params.orb_rsi_threshold_short}")
        print(f"   RSI支持多头: {'✅' if rsi_long_ok else '❌'}")
        print(f"   RSI支持空头: {'✅' if rsi_short_ok else '❌'}")
        
        # 综合条件检查
        print(f"\n🎯 综合信号条件:")
        
        # 多头信号条件
        long_conditions = [above_high, volume_ok, rsi_long_ok]
        long_signal_possible = all(long_conditions)
        print(f"   多头信号: {'✅ 满足' if long_signal_possible else '❌ 不满足'}")
        print(f"     - 突破高点: {'✅' if above_high else '❌'}")
        print(f"     - 成交量足: {'✅' if volume_ok else '❌'}")
        print(f"     - RSI>阈值: {'✅' if rsi_long_ok else '❌'}")
        
        # 空头信号条件  
        short_conditions = [below_low, volume_ok, rsi_short_ok]
        short_signal_possible = all(short_conditions)
        print(f"   空头信号: {'✅ 满足' if short_signal_possible else '❌ 不满足'}")
        print(f"     - 跌破低点: {'✅' if below_low else '❌'}")
        print(f"     - 成交量足: {'✅' if volume_ok else '❌'}")
        print(f"     - RSI<阈值: {'✅' if rsi_short_ok else '❌'}")
        
        # 如果有信号可能，但实际没生成，检查具体原因
        if long_signal_possible or short_signal_possible:
            print(f"\n🚨 发现信号条件满足但未生成信号！")
            # 直接调用信号检查方法
            orb_signal = signal_generator.check_opening_range_breakout("SPY")
            if orb_signal:
                print(f"✅ 成功生成信号: {orb_signal.signal_type.value} - {orb_signal.reason}")
            else:
                print("❌ 信号方法返回None，可能有其他问题")
        
        # 测试放宽参数的效果
        print(f"\n🔧 测试放宽参数:")
        original_long = strategy_params.orb_rsi_threshold_long
        original_short = strategy_params.orb_rsi_threshold_short
        original_volume = strategy_params.orb_volume_multiplier
        
        strategy_params.orb_rsi_threshold_long = 50
        strategy_params.orb_rsi_threshold_short = 50
        strategy_params.orb_volume_multiplier = 1.0
        
        print(f"   放宽RSI阈值到50，成交量倍数到1.0")
        
        # 重新检查条件
        rsi_long_relaxed = current_rsi > 50
        rsi_short_relaxed = current_rsi < 50
        volume_relaxed = current_volume > signal_generator.orb_levels['volume']
        
        long_relaxed = above_high and volume_relaxed and rsi_long_relaxed
        short_relaxed = below_low and volume_relaxed and rsi_short_relaxed
        
        print(f"   放宽后多头信号: {'✅' if long_relaxed else '❌'}")
        print(f"   放宽后空头信号: {'✅' if short_relaxed else '❌'}")
        
        # 恢复参数
        strategy_params.orb_rsi_threshold_long = original_long
        strategy_params.orb_rsi_threshold_short = original_short
        strategy_params.orb_volume_multiplier = original_volume
        
    except Exception as e:
        print(f"❌ 调试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    detailed_signal_debug() 