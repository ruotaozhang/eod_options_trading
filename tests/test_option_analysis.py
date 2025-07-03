#!/usr/bin/env python3
"""
详细期权分析脚本
获取6月4日到期的SPY期权的全面信息，包括不同行权价的Greeks和价格数据
"""

import os
import sys
from datetime import datetime, date
from dotenv import load_dotenv
import pandas as pd

# 加载环境变量
load_dotenv()

# 清除可能导致问题的环境变量
if 'USE_BRACKET_ORDERS' in os.environ:
    del os.environ['USE_BRACKET_ORDERS']
if 'BRACKET_ORDER_TIMEOUT' in os.environ:
    del os.environ['BRACKET_ORDER_TIMEOUT']

# 添加src目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.data.market_data import MarketDataProvider


def analyze_options_detailed():
    """详细分析期权数据"""
    
    print("📊 SPY期权详细分析")
    print("="*80)
    
    # 初始化市场数据提供者
    try:
        market_data = MarketDataProvider()
        print("✅ 市场数据客户端初始化成功")
    except Exception as e:
        print(f"❌ 客户端初始化失败: {e}")
        return
    
    # 目标信息
    underlying = "SPY"
    target_strike = 596.0
    expiry_date = "2025-06-04"  # 6月4日
    
    print(f"\n📈 标的: {underlying}")
    print(f"🗓️ 目标到期日: {expiry_date}")
    print(f"🎯 目标行权价: ${target_strike}")
    
    # 获取标的当前价格
    print("\n1️⃣ 获取标的当前价格...")
    current_price = market_data.get_current_price(underlying)
    print(f"   ✅ {underlying}当前价格: ${current_price:.2f}")
    
    # 获取期权链
    print("\n2️⃣ 获取期权链数据...")
    option_chain = market_data.get_option_chain(underlying)
    if not option_chain:
        print("   ❌ 期权链数据获取失败")
        return
    
    calls_count = len(option_chain.get('calls', []))
    puts_count = len(option_chain.get('puts', []))
    print(f"   ✅ 期权链获取成功: {calls_count}个看涨期权, {puts_count}个看跌期权")
    
    # 筛选6月4日到期的期权
    print(f"\n3️⃣ 筛选{expiry_date}到期的期权...")
    june4_calls = [opt for opt in option_chain.get('calls', []) if opt['expiry'] == expiry_date]
    june4_puts = [opt for opt in option_chain.get('puts', []) if opt['expiry'] == expiry_date]
    
    print(f"   📞 6月4日看涨期权: {len(june4_calls)}个")
    print(f"   📞 6月4日看跌期权: {len(june4_puts)}个")
    
    if not june4_calls:
        print("   ❌ 未找到6月4日到期的期权")
        return
    
    # 找到围绕当前价格的期权
    print(f"\n4️⃣ 分析围绕当前价格的期权 (${current_price:.2f})...")
    
    # 选择当前价格附近的行权价 (-5 到 +5)
    target_strikes = [current_price + i for i in range(-5, 6)]
    
    print("\n📋 看涨期权 (CALL) 详细信息:")
    print("-" * 80)
    print(f"{'行权价':>8} {'合约代码':>18} {'Bid':>8} {'Ask':>8} {'Mid':>8} {'Last':>8} {'Delta':>8} {'Gamma':>8} {'Theta':>8} {'Vega':>8} {'IV':>8}")
    print("-" * 80)
    
    call_found = False
    for strike in sorted(target_strikes):
        for call in june4_calls:
            if abs(call['strike'] - strike) < 0.5:  # 找到最接近的行权价
                call_found = True
                symbol = call['contractSymbol'][:18] + ".." if len(call['contractSymbol']) > 18 else call['contractSymbol']
                print(f"{call['strike']:8.0f} {symbol:>18} "
                      f"{call['bid']:8.4f} {call['ask']:8.4f} {call['midPrice']:8.4f} {call['lastPrice']:8.4f} "
                      f"{call['delta']:8.4f} {call['gamma']:8.4f} {call['theta']:8.4f} {call['vega']:8.4f} "
                      f"{call['impliedVolatility']:8.4f}")
                break
    
    if not call_found:
        print("   ❌ 未找到指定行权价附近的看涨期权")
    
    # 查找特定的596行权价期权
    print(f"\n5️⃣ 查找行权价${target_strike}的期权详情...")
    target_call = None
    target_put = None
    
    for call in june4_calls:
        if call['strike'] == target_strike:
            target_call = call
            break
    
    for put in june4_puts:
        if put['strike'] == target_strike:
            target_put = put
            break
    
    if target_call:
        print(f"\n📞 看涨期权 ${target_strike} Call:")
        print(f"   合约代码: {target_call['contractSymbol']}")
        print(f"   💰 Bid: ${target_call['bid']:.4f}")
        print(f"   💰 Ask: ${target_call['ask']:.4f}")
        print(f"   💰 Mid: ${target_call['midPrice']:.4f}")
        print(f"   💰 Last: ${target_call['lastPrice']:.4f}")
        print(f"   📊 Volume: {target_call['volume']}")
        print(f"   📊 Open Interest: {target_call['openInterest']}")
        print(f"   🔢 Delta: {target_call['delta']:.4f}")
        print(f"   🔢 Gamma: {target_call['gamma']:.4f}")
        print(f"   🔢 Theta: {target_call['theta']:.4f}")
        print(f"   🔢 Vega: {target_call['vega']:.4f}")
        print(f"   🔢 Rho: {target_call['rho']:.4f}")
        print(f"   📈 IV: {target_call['impliedVolatility']:.4f} ({target_call['impliedVolatility']*100:.2f}%)")
        
        # 计算理论价值和价内价外程度
        moneyness = current_price / target_call['strike']
        if moneyness > 1:
            itm_amount = current_price - target_call['strike']
            print(f"   🎯 状态: 价内 (ITM), 价内程度: ${itm_amount:.2f}")
        else:
            otm_amount = target_call['strike'] - current_price
            print(f"   🎯 状态: 价外 (OTM), 价外程度: ${otm_amount:.2f}")
        print(f"   🎯 价格比率: {moneyness:.4f}")
        
        # 计算时间价值（如果有last price）
        if target_call['lastPrice'] > 0 and moneyness > 1:
            intrinsic_value = max(0, current_price - target_call['strike'])
            time_value = target_call['lastPrice'] - intrinsic_value
            print(f"   ⏰ 内在价值: ${intrinsic_value:.4f}")
            print(f"   ⏰ 时间价值: ${time_value:.4f}")
    else:
        print(f"   ❌ 未找到行权价${target_strike}的看涨期权")
    
    if target_put:
        print(f"\n📞 看跌期权 ${target_strike} Put:")
        print(f"   合约代码: {target_put['contractSymbol']}")
        print(f"   💰 Bid: ${target_put['bid']:.4f}")
        print(f"   💰 Ask: ${target_put['ask']:.4f}")
        print(f"   💰 Mid: ${target_put['midPrice']:.4f}")
        print(f"   💰 Last: ${target_put['lastPrice']:.4f}")
        print(f"   📊 Volume: {target_put['volume']}")
        print(f"   📊 Open Interest: {target_put['openInterest']}")
        print(f"   🔢 Delta: {target_put['delta']:.4f}")
        print(f"   🔢 Gamma: {target_put['gamma']:.4f}")
        print(f"   🔢 Theta: {target_put['theta']:.4f}")
        print(f"   🔢 Vega: {target_put['vega']:.4f}")
        print(f"   🔢 Rho: {target_put['rho']:.4f}")
        print(f"   📈 IV: {target_put['impliedVolatility']:.4f} ({target_put['impliedVolatility']*100:.2f}%)")
    else:
        print(f"   ❌ 未找到行权价${target_strike}的看跌期权")
    
    # 找到有实际报价的期权
    print(f"\n6️⃣ 寻找有活跃报价的期权...")
    active_calls = [c for c in june4_calls if c['bid'] > 0 and c['ask'] > 0]
    active_puts = [p for p in june4_puts if p['bid'] > 0 and p['ask'] > 0]
    
    print(f"   📞 有活跃报价的看涨期权: {len(active_calls)}个")
    print(f"   📞 有活跃报价的看跌期权: {len(active_puts)}个")
    
    if active_calls:
        print("\n🔥 活跃看涨期权示例 (前5个):")
        print("-" * 80)
        for i, call in enumerate(active_calls[:5]):
            spread = call['ask'] - call['bid']
            spread_pct = (spread / call['ask'] * 100) if call['ask'] > 0 else 0
            print(f"   {i+1}. 行权价${call['strike']:.0f}: Bid=${call['bid']:.4f} Ask=${call['ask']:.4f} "
                  f"Spread=${spread:.4f}({spread_pct:.1f}%) IV={call['impliedVolatility']*100:.1f}%")
    
    print("\n" + "="*80)
    print("✅ 详细分析完成")
    
    # API性能总结
    print(f"\n📊 API调用总结:")
    print(f"   ✅ 成功获取{underlying}当前价格")
    print(f"   ✅ 成功获取期权链数据({calls_count + puts_count}个期权)")
    print(f"   ✅ 成功解析期权数据结构")
    print(f"   ✅ 成功筛选特定到期日期权")
    print(f"   ✅ 成功提取Greeks和价格信息")


if __name__ == "__main__":
    analyze_options_detailed() 