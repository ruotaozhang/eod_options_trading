#!/usr/bin/env python3
"""
调试脚本：检查为什么没有交易信号
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from datetime import datetime, time
from src.data.market_data import MarketDataProvider, TechnicalIndicators
from src.strategy.signals import SignalGenerator
from src.config import config, strategy_params
import pandas as pd

def debug_signal_generation():
    """调试信号生成过程"""
    print("🔍 调试交易信号生成逻辑")
    print("=" * 60)
    
    # 初始化组件
    try:
        market_data = MarketDataProvider(config)
        signal_generator = SignalGenerator(market_data)
        
        print("✅ 组件初始化成功")
    except Exception as e:
        print(f"❌ 组件初始化失败: {e}")
        return
    
    # 检查市场数据获取
    print("\n📊 检查市场数据获取...")
    try:
        current_price = market_data.get_current_price("SPY")
        print(f"✅ 当前SPY价格: ${current_price:.2f}")
        
        # 获取K线数据
        bars = market_data.get_current_bars("SPY", limit=100)
        print(f"✅ 获取K线数据: {len(bars)}条")
        if not bars.empty:
            latest_bar = bars.iloc[-1]
            print(f"   最新K线: {latest_bar['timestamp']} 价格=${latest_bar['close']:.2f} 成交量={latest_bar['volume']:,}")
        
    except Exception as e:
        print(f"❌ 市场数据获取失败: {e}")
        return
    
    # 检查当前时间和交易时间
    print("\n⏰ 检查时间条件...")
    current_time = datetime.now().time()
    print(f"当前时间: {current_time}")
    
    # ORB时间窗口
    orb_start = time(9, 45)
    orb_end = time(10, 0)
    in_orb_window = orb_start <= current_time <= orb_end
    print(f"ORB窗口 (09:45-10:00): {'✅ 在窗口内' if in_orb_window else '❌ 不在窗口内'}")
    
    # VWAP信号（全时段）
    print(f"VWAP信号: ✅ 全时段监控")
    
    # 反转信号时间窗口
    reversal_start = time(14, 30)
    reversal_end = time(15, 0)
    in_reversal_window = reversal_start <= current_time <= reversal_end
    print(f"反转窗口 (14:30-15:00): {'✅ 在窗口内' if in_reversal_window else '❌ 不在窗口内'}")
    
    # 检查信号生成逻辑
    print("\n🎯 检查信号生成...")
    try:
        # 更新市场数据
        success = signal_generator.update_market_data("SPY")
        if not success:
            print("❌ 更新市场数据失败")
            return
        print("✅ 市场数据更新成功")
        
        # 检查ORB水平
        if signal_generator.orb_levels:
            print(f"ORB水平: 高点=${signal_generator.orb_levels['high']:.2f}, 低点=${signal_generator.orb_levels['low']:.2f}, 成交量={signal_generator.orb_levels['volume']:,}")
        else:
            print("❌ ORB水平未计算")
        
        # 检查VWAP数据
        if not signal_generator.vwap_data.empty:
            current_vwap = signal_generator.vwap_data.iloc[-1]
            vwap_deviation = (current_price - current_vwap) / current_vwap * 100
            print(f"VWAP: 当前=${current_vwap:.2f}, 偏离={vwap_deviation:.2f}%")
            print(f"VWAP偏离阈值: {strategy_params.vwap_breakout_threshold}%")
        else:
            print("❌ VWAP数据为空")
            
        # 生成信号
        signals = signal_generator.generate_signals("SPY")
        if signals:
            print(f"🎉 生成了 {len(signals)} 个信号:")
            for signal in signals:
                print(f"   - {signal.signal_type.value}: {signal.reason} (置信度: {signal.confidence:.2f})")
        else:
            print("⚠️ 没有生成任何信号")
            
        # 详细检查各个信号条件
        print("\n🔍 详细检查信号条件...")
        
        # 检查ORB信号条件
        if in_orb_window and signal_generator.orb_levels:
            print("ORB信号检查:")
            latest_bar = signal_generator.current_bars.iloc[-1]
            current_price_check = latest_bar['close']
            current_volume = latest_bar['volume']
            
            # 计算RSI
            indicators = TechnicalIndicators()
            rsi_series = indicators.calculate_rsi(signal_generator.current_bars)
            if not rsi_series.empty:
                current_rsi = rsi_series.iloc[-1]
                print(f"   当前RSI: {current_rsi:.1f}")
                print(f"   多头RSI阈值: {strategy_params.orb_rsi_threshold_long}")
                print(f"   空头RSI阈值: {strategy_params.orb_rsi_threshold_short}")
            
            volume_threshold = signal_generator.orb_levels['volume'] * strategy_params.orb_volume_multiplier
            print(f"   当前成交量: {current_volume:,}")
            print(f"   成交量阈值: {volume_threshold:,.0f}")
            
            # 检查突破条件
            above_high = current_price_check > signal_generator.orb_levels['high']
            below_low = current_price_check < signal_generator.orb_levels['low']
            volume_ok = current_volume > volume_threshold
            
            print(f"   价格突破高点: {'✅' if above_high else '❌'} ({current_price_check:.2f} vs {signal_generator.orb_levels['high']:.2f})")
            print(f"   价格跌破低点: {'✅' if below_low else '❌'} ({current_price_check:.2f} vs {signal_generator.orb_levels['low']:.2f})")
            print(f"   成交量充足: {'✅' if volume_ok else '❌'}")
            
        # 检查VWAP信号条件
        if not signal_generator.vwap_data.empty:
            print("\nVWAP信号检查:")
            recent_bars = signal_generator.current_bars.tail(strategy_params.vwap_confirmation_minutes)
            recent_vwap = signal_generator.vwap_data.tail(strategy_params.vwap_confirmation_minutes)
            
            if len(recent_bars) >= strategy_params.vwap_confirmation_minutes:
                threshold_pct = strategy_params.vwap_breakout_threshold
                print(f"   偏离阈值: {threshold_pct}%")
                print(f"   当前偏离: {vwap_deviation:.2f}%")
                
                # 检查持续性
                above_threshold = all(recent_bars['close'] > recent_vwap * (1 + threshold_pct/100))
                below_threshold = all(recent_bars['close'] < recent_vwap * (1 - threshold_pct/100))
                print(f"   持续在VWAP上方: {'✅' if above_threshold else '❌'}")
                print(f"   持续在VWAP下方: {'✅' if below_threshold else '❌'}")
                
                # 检查MACD
                indicators = TechnicalIndicators()
                macd_data = indicators.calculate_macd(signal_generator.current_bars)
                if not macd_data['histogram'].empty:
                    current_macd = macd_data['histogram'].iloc[-1]
                    prev_macd = macd_data['histogram'].iloc[-2] if len(macd_data['histogram']) > 1 else 0
                    print(f"   当前MACD柱状图: {current_macd:.4f}")
                    print(f"   前一MACD柱状图: {prev_macd:.4f}")
                    print(f"   MACD转正: {'✅' if current_macd > prev_macd and current_macd > 0 else '❌'}")
                    print(f"   MACD转负: {'✅' if current_macd < prev_macd and current_macd < 0 else '❌'}")
            else:
                print(f"   数据不足，需要{strategy_params.vwap_confirmation_minutes}分钟数据")
        
    except Exception as e:
        print(f"❌ 信号生成检查失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_signal_generation() 