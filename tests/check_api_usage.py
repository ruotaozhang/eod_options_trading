#!/usr/bin/env python3
"""
检查5秒监控频率的API使用率
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import config

def check_api_usage():
    """检查API使用率"""
    print("🚀 极高频监控配置 (5秒)")
    print("=" * 40)
    print(f"持仓检查频率: {config.position_check_seconds}秒")
    print(f"市场数据更新: {config.market_data_update_seconds}秒") 
    print(f"信号检查频率: {config.signal_check_seconds}秒")
    print()
    
    # 计算每分钟API调用次数
    position_calls = 60 / config.position_check_seconds
    market_calls = 60 / config.market_data_update_seconds  
    signal_calls = 60 / config.signal_check_seconds
    total_calls = position_calls + market_calls + signal_calls
    
    print("📊 API调用频率分析:")
    print(f"持仓检查: {position_calls:.1f} 次/分钟")
    print(f"市场数据: {market_calls:.1f} 次/分钟")
    print(f"信号检查: {signal_calls:.1f} 次/分钟")
    print(f"总计: {total_calls:.1f} 次/分钟")
    print()
    
    # 计算API使用率
    api_usage = (total_calls / 200) * 100
    print(f"🚨 API使用率: {api_usage:.1f}%")
    print(f"Alpaca限制: 200次/分钟")
    print(f"剩余裕度: {200 - total_calls:.1f}次/分钟")
    
    if api_usage < 15:
        status = "✅ 非常安全"
        advice = "可以安全使用此配置"
    elif api_usage < 30:
        status = "⚠️ 需要监控"
        advice = "建议密切监控API调用状态"
    elif api_usage < 50:
        status = "⚠️ 中等风险"
        advice = "需要谨慎使用，考虑降低频率"
    else:
        status = "❌ 高风险"
        advice = "不建议使用此配置，风险过高"
    
    print(f"状态: {status}")
    print(f"建议: {advice}")
    print()
    
    # 响应时间分析
    print("⚡ 系统响应能力:")
    print(f"最快止损响应: {config.position_check_seconds}秒")
    print(f"最快市场变化感知: {config.market_data_update_seconds}秒")
    print(f"最快信号响应: {config.signal_check_seconds}秒")
    print()
    
    print("💡 优势:")
    print("- 极快的风险控制响应")
    print("- 实时价格跟踪")
    print("- 快速信号识别")
    print("- 最小化延迟损失")
    
    return api_usage

if __name__ == "__main__":
    check_api_usage() 