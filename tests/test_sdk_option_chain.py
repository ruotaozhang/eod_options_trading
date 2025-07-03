#!/usr/bin/env python3
"""
测试Alpaca SDK的get_option_chain方法
验证能正常获取期权链和bid/ask、Greeks数据
"""

import os
import sys
from datetime import datetime, date
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加src路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from data.market_data import MarketDataProvider
from config import config


def test_sdk_option_chain():
    """测试SDK期权链获取方法"""
    
    print("🔍 测试Alpaca SDK期权链获取方法")
    print("="*60)
    
    try:
        # 创建市场数据提供器
        market_data = MarketDataProvider(config)
        
        # 获取当前SPY价格
        current_price = market_data.get_current_price('SPY')
        print(f"📈 SPY当前价格: ${current_price}")
        
        # 获取期权链数据
        print(f"📊 获取SPY期权链数据 (使用Alpaca SDK)...")
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
        
        total_options = len(calls) + len(puts)
        speed = total_options / total_time if total_time > 0 else 0
        print(f"🚀 处理速度: {speed:.0f}个期权/秒")
        
        # 分析数据质量
        print(f"\n📊 数据质量分析:")
        
        # 分析看涨期权
        call_greeks_count = 0
        call_bid_ask_count = 0
        call_samples = []
        
        for call in calls:
            has_greeks = (call.get('delta', 0) != 0 or call.get('gamma', 0) != 0 or 
                         call.get('theta', 0) != 0 or call.get('vega', 0) != 0)
            has_bid_ask = call.get('bid', 0) > 0 and call.get('ask', 0) > 0
            
            if has_greeks:
                call_greeks_count += 1
            if has_bid_ask:
                call_bid_ask_count += 1
            
            # 保存样本 - 优先选择有完整数据的
            if len(call_samples) < 3 and (has_greeks or has_bid_ask or call.get('midPrice', 0) > 0):
                call_samples.append(call)
        
        # 分析看跌期权
        put_greeks_count = 0
        put_bid_ask_count = 0
        put_samples = []
        
        for put in puts:
            has_greeks = (put.get('delta', 0) != 0 or put.get('gamma', 0) != 0 or 
                         put.get('theta', 0) != 0 or put.get('vega', 0) != 0)
            has_bid_ask = put.get('bid', 0) > 0 and put.get('ask', 0) > 0
            
            if has_greeks:
                put_greeks_count += 1
            if has_bid_ask:
                put_bid_ask_count += 1
            
            # 保存样本
            if len(put_samples) < 3 and (has_greeks or has_bid_ask or put.get('midPrice', 0) > 0):
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
            print(f"      到期日: {call['expiry']}")
            print(f"      Bid: ${call['bid']:.3f}, Ask: ${call['ask']:.3f}")
            print(f"      Delta: {call['delta']:.4f}, Gamma: {call['gamma']:.4f}")
            print(f"      Theta: {call['theta']:.4f}, Vega: {call['vega']:.4f}")
            print(f"      IV: {call['impliedVolatility']:.3f} ({call['impliedVolatility']*100:.1f}%)")
            print(f"      中间价: ${call['midPrice']:.3f}")
        
        print(f"\n📋 看跌期权样本:")
        for i, put in enumerate(put_samples[:3], 1):
            print(f"   📄 样本{i}: {put['contractSymbol']}")
            print(f"      行权价: ${put['strike']}")
            print(f"      到期日: {put['expiry']}")
            print(f"      Bid: ${put['bid']:.3f}, Ask: ${put['ask']:.3f}")
            print(f"      Delta: {put['delta']:.4f}, Gamma: {put['gamma']:.4f}")
            print(f"      Theta: {put['theta']:.4f}, Vega: {put['vega']:.4f}")
            print(f"      IV: {put['impliedVolatility']:.3f} ({put['impliedVolatility']*100:.1f}%)")
            print(f"      中间价: ${put['midPrice']:.3f}")
        
        # 筛选当日到期期权
        today = date.today()
        today_calls = [c for c in calls if c['expiry'] == today.strftime('%Y-%m-%d')]
        today_puts = [p for p in puts if p['expiry'] == today.strftime('%Y-%m-%d')]
        
        print(f"\n📅 当日到期期权分析:")
        print(f"   当日到期期权: {len(today_calls) + len(today_puts)} ({len(today_calls)}个看涨 + {len(today_puts)}个看跌)")
        
        if today_calls or today_puts:
            # 分析当日期权的数据质量
            today_greeks = sum(1 for opt in today_calls + today_puts 
                             if opt.get('delta', 0) != 0 or opt.get('gamma', 0) != 0)
            today_quotes = sum(1 for opt in today_calls + today_puts 
                             if opt.get('bid', 0) > 0 and opt.get('ask', 0) > 0)
            today_total = len(today_calls) + len(today_puts)
            
            print(f"   当日期权Greeks覆盖率: {today_greeks}/{today_total} ({today_greeks/today_total*100:.1f}%)")
            print(f"   当日期权Bid/Ask覆盖率: {today_quotes}/{today_total} ({today_quotes/today_total*100:.1f}%)")
            
            # 显示最佳当日期权候选
            suitable_today = []
            for opt in today_calls + today_puts:
                delta = abs(opt.get('delta', 0))
                if 0.25 <= delta <= 0.45 and opt.get('gamma', 0) > 0:
                    suitable_today.append(opt)
            
            if suitable_today:
                suitable_today.sort(key=lambda x: abs(x.get('delta', 0) - 0.35))
                best = suitable_today[0]
                print(f"\n🎯 最佳当日交易候选:")
                print(f"   合约: {best['contractSymbol']}")
                print(f"   行权价: ${best['strike']}")
                print(f"   Delta: {best['delta']:.4f}")
                print(f"   Gamma: {best['gamma']:.4f}")
                print(f"   Bid/Ask: ${best['bid']:.3f}/${best['ask']:.3f}")
        
        # 性能总结
        print(f"\n🏆 SDK方法总结:")
        print(f"   ✅ 总期权数量: {total_options}")
        print(f"   ⏱️ 总耗时: {total_time:.2f}秒")
        print(f"   🚀 处理速度: {speed:.0f}个期权/秒")
        print(f"   📊 Greeks数据覆盖率: {(call_greeks_count + put_greeks_count)/total_options*100:.1f}%")
        print(f"   💰 Bid/Ask数据覆盖率: {(call_bid_ask_count + put_bid_ask_count)/total_options*100:.1f}%")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n✅ SDK期权链测试完成")


if __name__ == "__main__":
    test_sdk_option_chain() 