#!/usr/bin/env python3
"""
测试更新后的市场数据实现
确保能正常获取bid/ask和Greeks数据
"""

import os
import sys
from datetime import datetime, date
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 清除可能导致问题的环境变量
if 'USE_BRACKET_ORDERS' in os.environ:
    del os.environ['USE_BRACKET_ORDERS']
if 'BRACKET_ORDER_TIMEOUT' in os.environ:
    del os.environ['BRACKET_ORDER_TIMEOUT']

# 添加src路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from data.market_data import MarketDataProvider
from config import config

def test_updated_market_data():
    """测试更新后的市场数据实现"""
    
    print("🔍 测试更新后的市场数据实现")
    print("="*60)
    
    try:
        # 创建市场数据提供器
        market_data = MarketDataProvider(config)
        
        # 获取期权链数据
        print(f"📊 获取SPY期权链数据...")
        start_time = datetime.now()
        
        option_chain = market_data.get_option_chain('SPY')
        
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()
        
        if not option_chain:
            print("❌ 未获取到期权链数据")
            return
        
        calls = option_chain.get('calls', [])
        puts = option_chain.get('puts', [])
        underlying_price = option_chain.get('underlying_price', 0)
        
        print(f"✅ 成功获取期权链数据")
        print(f"📥 看涨期权: {len(calls)}")
        print(f"📥 看跌期权: {len(puts)}")
        print(f"📈 标的价格: ${underlying_price}")
        print(f"⏱️ 总耗时: {total_time:.2f}秒")
        
        # 分析数据质量
        print(f"\n📊 数据质量分析:")
        
        # 分析看涨期权
        call_greeks_count = 0
        call_bid_ask_count = 0
        call_samples = []
        
        for call in calls:
            has_greeks = call.get('delta', 0) != 0 or call.get('gamma', 0) != 0
            has_bid_ask = call.get('bid', 0) > 0 and call.get('ask', 0) > 0
            
            if has_greeks:
                call_greeks_count += 1
            if has_bid_ask:
                call_bid_ask_count += 1
            
            # 保存样本
            if len(call_samples) < 3 and (has_greeks or has_bid_ask):
                call_samples.append(call)
        
        # 分析看跌期权
        put_greeks_count = 0
        put_bid_ask_count = 0
        put_samples = []
        
        for put in puts:
            has_greeks = put.get('delta', 0) != 0 or put.get('gamma', 0) != 0
            has_bid_ask = put.get('bid', 0) > 0 and put.get('ask', 0) > 0
            
            if has_greeks:
                put_greeks_count += 1
            if has_bid_ask:
                put_bid_ask_count += 1
            
            # 保存样本
            if len(put_samples) < 3 and (has_greeks or has_bid_ask):
                put_samples.append(put)
        
        print(f"   看涨期权:")
        print(f"      Greeks: {call_greeks_count}/{len(calls)} ({call_greeks_count/len(calls)*100:.1f}%)")
        print(f"      Bid/Ask: {call_bid_ask_count}/{len(calls)} ({call_bid_ask_count/len(calls)*100:.1f}%)")
        
        print(f"   看跌期权:")
        print(f"      Greeks: {put_greeks_count}/{len(puts)} ({put_greeks_count/len(puts)*100:.1f}%)")
        print(f"      Bid/Ask: {put_bid_ask_count}/{len(puts)} ({put_bid_ask_count/len(puts)*100:.1f}%)")
        
        # 显示样本数据
        print(f"\n📋 看涨期权样本:")
        for i, call in enumerate(call_samples[:3], 1):
            print(f"   📄 样本{i}: {call['contractSymbol']}")
            print(f"      行权价: ${call['strike']}")
            print(f"      Bid: ${call['bid']:.3f}, Ask: ${call['ask']:.3f}")
            print(f"      Delta: {call['delta']:.4f}, Gamma: {call['gamma']:.4f}")
            print(f"      Theta: {call['theta']:.4f}, Vega: {call['vega']:.4f}")
            print(f"      IV: {call['impliedVolatility']:.3f} ({call['impliedVolatility']*100:.1f}%)")
            print(f"      中间价: ${call['midPrice']:.3f}")
        
        print(f"\n📋 看跌期权样本:")
        for i, put in enumerate(put_samples[:3], 1):
            print(f"   📄 样本{i}: {put['contractSymbol']}")
            print(f"      行权价: ${put['strike']}")
            print(f"      Bid: ${put['bid']:.3f}, Ask: ${put['ask']:.3f}")
            print(f"      Delta: {put['delta']:.4f}, Gamma: {put['gamma']:.4f}")
            print(f"      Theta: {put['theta']:.4f}, Vega: {put['vega']:.4f}")
            print(f"      IV: {put['impliedVolatility']:.3f} ({put['impliedVolatility']*100:.1f}%)")
            print(f"      中间价: ${put['midPrice']:.3f}")
        
        # 寻找ATM期权
        print(f"\n🎯 ATM期权分析:")
        atm_strike = round(underlying_price)
        
        atm_call = None
        atm_put = None
        
        for call in calls:
            if call['strike'] == atm_strike:
                atm_call = call
                break
        
        for put in puts:
            if put['strike'] == atm_strike:
                atm_put = put
                break
        
        if atm_call:
            print(f"   📈 ATM看涨期权 (${atm_strike}):")
            print(f"      合约: {atm_call['contractSymbol']}")
            print(f"      Bid: ${atm_call['bid']:.3f}, Ask: ${atm_call['ask']:.3f}")
            print(f"      Delta: {atm_call['delta']:.4f}, Gamma: {atm_call['gamma']:.4f}")
            print(f"      Theta: {atm_call['theta']:.4f}, Vega: {atm_call['vega']:.4f}")
        
        if atm_put:
            print(f"   📉 ATM看跌期权 (${atm_strike}):")
            print(f"      合约: {atm_put['contractSymbol']}")
            print(f"      Bid: ${atm_put['bid']:.3f}, Ask: ${atm_put['ask']:.3f}")
            print(f"      Delta: {atm_put['delta']:.4f}, Gamma: {atm_put['gamma']:.4f}")
            print(f"      Theta: {atm_put['theta']:.4f}, Vega: {atm_put['vega']:.4f}")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n✅ 测试完成")


if __name__ == "__main__":
    test_updated_market_data() 