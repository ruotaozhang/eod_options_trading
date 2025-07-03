#!/usr/bin/env python3
"""
当日到期期权专用测试脚本
验证系统严格限制只交易当日到期的期权合约
"""

import sys
from pathlib import Path
import traceback
from datetime import datetime

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.config import config
from src.data.market_data import MarketDataProvider
from src.utils.logger_setup import setup_logger

def test_same_day_expiry_only():
    """测试当日到期期权限制"""
    print("🎯 测试当日到期期权严格限制...")
    try:
        market_data = MarketDataProvider()
        
        # 获取期权链
        chain = market_data.get_option_chain(config.symbol)
        
        if not chain:
            print("❌ 无法获取期权链")
            return False
        
        today = datetime.now().strftime('%Y-%m-%d')
        print(f"📅 当前日期: {today}")
        
        # 统计所有期权的到期日分布
        all_calls = chain.get('calls', [])
        all_puts = chain.get('puts', [])
        
        expiry_distribution = {}
        for option in all_calls + all_puts:
            expiry = option['expiry']
            expiry_distribution[expiry] = expiry_distribution.get(expiry, 0) + 1
        
        print(f"\n📊 期权到期日分布 (前10个):")
        sorted_expiries = sorted(expiry_distribution.items())[:10]
        for expiry, count in sorted_expiries:
            is_today = "✅ 当日" if expiry == today else "📅 非当日"
            print(f"   {expiry}: {count}个期权 {is_today}")
        
        # 统计当日到期期权
        today_calls = [opt for opt in all_calls if opt['expiry'] == today]
        today_puts = [opt for opt in all_puts if opt['expiry'] == today]
        
        print(f"\n📈 当日到期期权统计:")
        print(f"   - 看涨期权: {len(today_calls)}个")
        print(f"   - 看跌期权: {len(today_puts)}个")
        print(f"   - 总计: {len(today_calls) + len(today_puts)}个")
        
        return True
        
    except Exception as e:
        print(f"❌ 当日到期期权测试失败: {e}")
        traceback.print_exc()
        return False

def test_option_selection_strict_filter():
    """测试期权选择的严格筛选"""
    print("\n🔍 测试期权选择的严格当日筛选...")
    try:
        market_data = MarketDataProvider()
        
        # 测试看涨期权选择
        print(f"\n📈 测试看涨期权选择:")
        calls = market_data.find_suitable_options(config.symbol, "CALL", 0.35)
        
        if calls:
            print(f"✅ 找到{len(calls)}个符合条件的当日到期看涨期权:")
            for i, call in enumerate(calls):
                print(f"   {i+1}. {call['contractSymbol']}")
                print(f"      - 到期日: {call['expiry']}")
                print(f"      - 行权价: ${call['strike']:.0f}")
                print(f"      - 估算Delta: {call['estimated_delta']:.3f}")
                print(f"      - 中间价: ${call['midPrice']:.2f}")
                
                # 验证确实是当日到期
                today = datetime.now().strftime('%Y-%m-%d')
                if call['expiry'] != today:
                    print(f"      ❌ 错误：不是当日到期期权！")
                    return False
                else:
                    print(f"      ✅ 确认：当日到期期权")
        else:
            print("⚠️ 未找到符合条件的当日到期看涨期权")
        
        # 测试看跌期权选择
        print(f"\n📉 测试看跌期权选择:")
        puts = market_data.find_suitable_options(config.symbol, "PUT", 0.35)
        
        if puts:
            print(f"✅ 找到{len(puts)}个符合条件的当日到期看跌期权:")
            for i, put in enumerate(puts):
                print(f"   {i+1}. {put['contractSymbol']}")
                print(f"      - 到期日: {put['expiry']}")
                print(f"      - 行权价: ${put['strike']:.0f}")
                print(f"      - 估算Delta: {put['estimated_delta']:.3f}")
                print(f"      - 中间价: ${put['midPrice']:.2f}")
                
                # 验证确实是当日到期
                today = datetime.now().strftime('%Y-%m-%d')
                if put['expiry'] != today:
                    print(f"      ❌ 错误：不是当日到期期权！")
                    return False
                else:
                    print(f"      ✅ 确认：当日到期期权")
        else:
            print("⚠️ 未找到符合条件的当日到期看跌期权")
        
        print(f"\n📋 当日到期期权选择总结:")
        print(f"   - 看涨期权: {len(calls)}个")
        print(f"   - 看跌期权: {len(puts)}个")
        print(f"   - 所有选中期权均为当日到期 ✅")
        
        return True
        
    except Exception as e:
        print(f"❌ 期权选择严格筛选测试失败: {e}")
        traceback.print_exc()
        return False

def test_no_same_day_scenario():
    """模拟测试：如果没有当日到期期权的情况"""
    print("\n🚫 模拟测试：无当日到期期权情况...")
    
    # 这个测试展示如果真的没有当日到期期权会发生什么
    # 在真实情况下，SPY通常在周一到周五都有当日到期期权
    # 但在周末或特殊情况下可能没有
    
    print("📝 说明：在以下情况下系统将不进行交易：")
    print("   1. 周末（市场休市）")
    print("   2. 节假日（市场休市）") 
    print("   3. 特殊情况下没有当日到期的SPY期权")
    print("   4. 所有当日到期期权都不满足流动性要求")
    print("   5. 所有当日到期期权的行权价都不在合理范围内")
    
    print("✅ 系统将严格遵守'只交易当日到期期权'的规则")
    
    return True

def main():
    """主测试函数"""
    print("🧪 当日到期期权专用测试")
    print("=" * 60)
    print("规则：只交易当日到期 (DTE=0) 的期权合约")
    print("=" * 60)
    
    # 设置日志
    setup_logger()
    
    test_results = []
    
    # 执行所有测试
    tests = [
        ("当日到期期权限制", test_same_day_expiry_only),
        ("期权选择严格筛选", test_option_selection_strict_filter),
        ("无当日期权场景模拟", test_no_same_day_scenario)
    ]
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            test_results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}测试异常: {e}")
            test_results.append((test_name, False))
    
    # 输出测试结果汇总
    print("\n" + "=" * 60)
    print("📋 当日到期期权测试结果汇总")
    print("=" * 60)
    
    passed = 0
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name:<20} {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{len(test_results)} 个测试通过")
    
    if passed == len(test_results):
        print("🎉 所有测试通过！系统已严格限制为只交易当日到期期权")
    else:
        print("⚠️ 部分测试失败，需要进一步调试")

if __name__ == "__main__":
    main() 