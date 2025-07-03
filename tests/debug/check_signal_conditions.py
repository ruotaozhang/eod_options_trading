#!/usr/bin/env python3
"""
检查信号生成条件 - 简化版本
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from datetime import datetime, time
from src.config import strategy_params

def check_signal_conditions():
    """检查当前信号条件"""
    print("🔍 检查信号生成条件")
    print("=" * 40)
    
    # 当前时间
    now = datetime.now()
    current_time = now.time()
    print(f"当前时间: {current_time}")
    print(f"当前日期: {now.date()}")
    
    # 检查各个信号的时间窗口
    print("\n⏰ 信号时间窗口检查:")
    
    # ORB信号窗口
    orb_start = time(9, 45)
    orb_end = time(10, 0)
    in_orb = orb_start <= current_time <= orb_end
    print(f"ORB突破 (09:45-10:00): {'✅ 在窗口内' if in_orb else '❌ 不在窗口内'}")
    
    # VWAP信号（全天）
    print(f"VWAP偏离 (全天监控): ✅ 可检测")
    
    # 午后反转信号
    reversal_start = time(14, 30)
    reversal_end = time(15, 0)
    in_reversal = reversal_start <= current_time <= reversal_end
    print(f"午后反转 (14:30-15:00): {'✅ 在窗口内' if in_reversal else '❌ 不在窗口内'}")
    
    # 整理突破信号
    consolidation_start = time(11, 30)
    consolidation_end = time(12, 30)
    in_consolidation = consolidation_start <= current_time <= consolidation_end
    print(f"整理突破 (11:30-12:30): {'✅ 在窗口内' if in_consolidation else '❌ 不在窗口内'}")
    
    # 检查策略参数
    print("\n🎯 策略参数检查:")
    print(f"ORB成交量倍数: {strategy_params.orb_volume_multiplier}")
    print(f"ORB多头RSI阈值: {strategy_params.orb_rsi_threshold_long}")
    print(f"ORB空头RSI阈值: {strategy_params.orb_rsi_threshold_short}")
    print(f"VWAP偏离阈值: {strategy_params.vwap_breakout_threshold}%")
    print(f"VWAP确认分钟数: {strategy_params.vwap_confirmation_minutes}")
    print(f"RSI周期: {strategy_params.rsi_period}")
    
    # 分析可能的问题
    print("\n🤔 可能的问题分析:")
    
    # 时间窗口问题
    if not any([in_orb, in_reversal, in_consolidation]):
        print("⚠️ 当前不在任何特定信号时间窗口内")
        print("   - ORB信号只在09:45-10:00检测")
        print("   - 午后反转只在14:30-15:00检测") 
        print("   - 整理突破只在11:30-12:30检测")
        print("   - 只有VWAP信号是全天监控的")
    
    # 参数严格性问题
    print("\n📊 参数严格性分析:")
    if strategy_params.orb_rsi_threshold_long >= 60:
        print("⚠️ ORB多头RSI阈值可能过高 (≥60)")
        print("   建议: 考虑降低到50-55")
    
    if strategy_params.orb_rsi_threshold_short <= 40:
        print("⚠️ ORB空头RSI阈值可能过低 (≤40)")
        print("   建议: 考虑提高到45-50")
        
    if strategy_params.vwap_breakout_threshold <= 0.15:
        print("⚠️ VWAP偏离阈值可能过小 (≤0.15%)")
        print("   建议: 考虑降低到0.1%或0.08%")
        
    if strategy_params.orb_volume_multiplier >= 1.2:
        print("⚠️ ORB成交量倍数可能过高 (≥1.2)")
        print("   建议: 考虑降低到1.1")
    
    # 市场条件分析
    print("\n📈 市场条件考虑:")
    print("最近可能的原因:")
    print("1. 市场波动性较低，没有足够的突破")
    print("2. 信号参数过于严格")
    print("3. 时间窗口限制过多")
    print("4. 技术指标条件要求过高")
    
    # 建议的解决方案
    print("\n💡 建议的解决方案:")
    print("1. 临时放宽参数进行测试:")
    print("   - ORB RSI阈值: 多头55, 空头45")
    print("   - VWAP偏离阈值: 0.1%")
    print("   - ORB成交量倍数: 1.1")
    print("2. 增加更多时间窗口或使用全天监控")
    print("3. 添加额外的信号类型")
    print("4. 降低信号组合条件的要求")

if __name__ == "__main__":
    check_signal_conditions() 