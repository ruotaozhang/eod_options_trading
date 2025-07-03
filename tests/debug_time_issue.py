#!/usr/bin/env python3
"""
调试时间问题
"""

import sys
from pathlib import Path
import pytz
from datetime import datetime

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.config import config

def debug_time_issue():
    """调试时间问题"""
    print("🔍 调试时间检查问题")
    print("=" * 60)
    
    # 1. 显示当前时间信息
    now_local = datetime.now()
    et_tz = pytz.timezone('America/New_York')
    now_et = datetime.now(et_tz)
    
    print("📅 时间信息:")
    print(f"   本地时间 (PDT):  {now_local.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   美东时间 (EDT):  {now_et.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"   配置交易时间:    {config.trading_start_time} - {config.trading_end_time}")
    print()
    
    # 2. 模拟原始的时间检查逻辑
    print("🔧 原始时间检查逻辑:")
    current_time = datetime.now().time()  # 使用本地时间 (PDT)
    start_time = datetime.strptime(config.trading_start_time, "%H:%M").time()
    end_time = datetime.strptime(config.trading_end_time, "%H:%M").time()
    
    print(f"   当前本地时间:    {current_time.strftime('%H:%M:%S')}")
    print(f"   交易开始时间:    {start_time.strftime('%H:%M:%S')}")
    print(f"   交易结束时间:    {end_time.strftime('%H:%M:%S')}")
    
    in_trading_hours_original = start_time <= current_time <= end_time
    print(f"   原始逻辑结果:    {'✅ 可交易' if in_trading_hours_original else '❌ 不可交易'}")
    print()
    
    # 3. 正确的时间检查逻辑 (使用美东时间)
    print("✅ 修正后的时间检查逻辑:")
    current_et_time = now_et.time()
    weekday = now_et.weekday()
    is_weekday = weekday < 5
    
    print(f"   当前美东时间:    {current_et_time.strftime('%H:%M:%S')}")
    print(f"   是否工作日:      {'是' if is_weekday else '否'} (周{weekday + 1})")
    
    in_trading_hours_correct = is_weekday and start_time <= current_et_time <= end_time
    print(f"   修正逻辑结果:    {'✅ 可交易' if in_trading_hours_correct else '❌ 不可交易'}")
    print()
    
    # 4. 分析问题
    print("🔍 问题分析:")
    if in_trading_hours_original != in_trading_hours_correct:
        print("   ❗ 发现问题: 原始逻辑使用本地时间(PDT)与美东交易时间比较")
        print("   📝 解决方案: 修改代码使用美东时间进行判断")
    else:
        print("   🤔 时间逻辑一致，可能有其他问题")
    print()
    
    # 5. 时区转换示例
    print("🌍 时区转换示例:")
    print(f"   PDT 09:30 → EDT 12:30")
    print(f"   PDT 15:50 → EDT 18:50")
    print(f"   美股交易时间是 EDT 09:30-15:50，不是 PDT 09:30-15:50")
    
    return in_trading_hours_original, in_trading_hours_correct

def main():
    """主函数"""
    print("🚀 时间问题调试工具")
    print("=" * 60)
    
    original_result, correct_result = debug_time_issue()
    
    print("\n" + "=" * 60)
    print("📋 结论:")
    if original_result != correct_result:
        print("✅ 确认问题: 时间检查使用了错误的时区")
        print("🔧 需要修复: 使用美东时间而不是本地时间")
    else:
        print("🤔 时间逻辑看起来正确，需要进一步调查")

if __name__ == "__main__":
    main() 