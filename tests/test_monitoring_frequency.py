#!/usr/bin/env python3
"""
测试监控频率配置功能
"""

import time
from datetime import datetime
from loguru import logger

# 设置测试环境
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import config

def test_frequency_settings():
    """测试频率设置"""
    print("🔧 监控频率配置测试")
    print("=" * 50)
    
    # 显示当前配置
    print("📊 当前配置:")
    print(f"   持仓检查频率: {getattr(config, 'position_check_seconds', 15)} 秒")
    print(f"   市场数据更新: {getattr(config, 'market_data_update_seconds', 30)} 秒")
    print(f"   信号检查频率: {getattr(config, 'signal_check_minutes', 1)} 分钟")
    
    # 计算API调用频率
    position_freq = 60 / getattr(config, 'position_check_seconds', 15)
    market_data_freq = 60 / getattr(config, 'market_data_update_seconds', 30)
    signal_freq = getattr(config, 'signal_check_minutes', 1)
    
    total_calls_per_minute = position_freq + market_data_freq + signal_freq
    
    print(f"\n📈 API调用频率分析:")
    print(f"   持仓检查: {position_freq:.1f} 次/分钟")
    print(f"   市场数据: {market_data_freq:.1f} 次/分钟")
    print(f"   信号检查: {signal_freq:.1f} 次/分钟")
    print(f"   总计: {total_calls_per_minute:.1f} 次/分钟")
    
    # API限制检查
    api_limit = 200  # Alpaca API限制
    usage_percentage = (total_calls_per_minute / api_limit) * 100
    
    print(f"\n🚨 API限制检查:")
    print(f"   Alpaca限制: {api_limit} 次/分钟")
    print(f"   当前使用: {usage_percentage:.1f}%")
    
    if usage_percentage < 10:
        print("   状态: ✅ 非常安全")
    elif usage_percentage < 25:
        print("   状态: ✅ 安全")
    elif usage_percentage < 50:
        print("   状态: ⚠️ 需要注意")
    else:
        print("   状态: ❌ 可能超限")
    
    return total_calls_per_minute < api_limit

def test_different_configurations():
    """测试不同配置方案"""
    print("\n🎯 不同配置方案对比")
    print("=" * 50)
    
    configs = [
        {
            'name': '高频模式',
            'position_check': 10,
            'market_data': 20,
            'signal_check': 1
        },
        {
            'name': '平衡模式',
            'position_check': 15,
            'market_data': 30,
            'signal_check': 1
        },
        {
            'name': '保守模式',
            'position_check': 30,
            'market_data': 60,
            'signal_check': 2
        }
    ]
    
    for cfg in configs:
        position_freq = 60 / cfg['position_check']
        market_freq = 60 / cfg['market_data']
        signal_freq = cfg['signal_check']
        total = position_freq + market_freq + signal_freq
        usage_pct = (total / 200) * 100
        
        print(f"\n📋 {cfg['name']}:")
        print(f"   配置: 持仓{cfg['position_check']}s, 数据{cfg['market_data']}s, 信号{cfg['signal_check']}m")
        print(f"   频率: {total:.1f} 次/分钟")
        print(f"   API使用率: {usage_pct:.1f}%")
        
        if usage_pct < 10:
            status = "✅ 非常安全"
        elif usage_pct < 25:
            status = "✅ 安全"
        elif usage_pct < 50:
            status = "⚠️ 需要注意"
        else:
            status = "❌ 可能超限"
        print(f"   状态: {status}")

def simulate_monitoring_schedule():
    """模拟监控调度"""
    print("\n⏰ 监控调度模拟 (30秒)")
    print("=" * 50)
    
    position_check_interval = getattr(config, 'position_check_seconds', 15)
    market_data_interval = getattr(config, 'market_data_update_seconds', 30)
    
    start_time = time.time()
    last_position_check = 0
    last_market_data = 0
    
    print(f"开始时间: {datetime.now().strftime('%H:%M:%S')}")
    print(f"持仓检查间隔: {position_check_interval}秒")
    print(f"市场数据间隔: {market_data_interval}秒")
    print("\n执行记录:")
    
    while time.time() - start_time < 30:  # 运行30秒
        current_time = time.time() - start_time
        
        # 检查是否需要执行持仓检查
        if current_time - last_position_check >= position_check_interval:
            print(f"  {current_time:5.1f}s: 🔍 持仓检查")
            last_position_check = current_time
        
        # 检查是否需要执行市场数据更新
        if current_time - last_market_data >= market_data_interval:
            print(f"  {current_time:5.1f}s: 📊 市场数据更新")
            last_market_data = current_time
        
        time.sleep(1)  # 每秒检查一次
    
    print(f"\n结束时间: {datetime.now().strftime('%H:%M:%S')}")

def main():
    """主测试函数"""
    print("📊 实时监控频率配置测试")
    print("=" * 60)
    
    # 测试当前配置
    is_safe = test_frequency_settings()
    
    # 测试不同配置方案
    test_different_configurations()
    
    # 模拟监控调度
    simulate_monitoring_schedule()
    
    print("\n" + "=" * 60)
    print("🎯 测试总结:")
    
    if is_safe:
        print("✅ 当前配置在API限制内，可以安全使用")
    else:
        print("❌ 当前配置可能超出API限制，请调整")
    
    print("\n💡 建议:")
    print("1. 在Paper环境中先测试新配置")
    print("2. 监控系统日志中的API调用状态") 
    print("3. 根据策略类型选择合适的监控频率")
    print("4. 网络不稳定时使用保守配置")

if __name__ == "__main__":
    main() 