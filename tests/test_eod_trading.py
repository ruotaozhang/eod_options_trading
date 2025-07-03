#!/usr/bin/env python3
"""
简单的EOD期权交易测试
验证新API格式在实际交易场景中的表现
"""

import os
import sys
from datetime import datetime, date, time
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加src路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from data.market_data import MarketDataProvider
from config import config


def test_eod_options_trading():
    """测试当日到期期权交易功能"""
    
    print("🔍 测试当日到期期权交易功能")
    print("="*60)
    
    try:
        # 创建市场数据提供器
        market_data = MarketDataProvider(config)
        
        # 获取当前SPY价格
        current_price = market_data.get_current_price('SPY')
        print(f"📈 SPY当前价格: ${current_price}")
        
        # 获取期权链
        start_time = datetime.now()
        option_chain = market_data.get_option_chain('SPY')
        end_time = datetime.now()
        
        if not option_chain:
            print("❌ 未获取到期权链数据")
            return
        
        calls = option_chain.get('calls', [])
        puts = option_chain.get('puts', [])
        
        print(f"⏱️ 数据获取耗时: {(end_time - start_time).total_seconds():.2f}秒")
        print(f"📊 期权总数: {len(calls) + len(puts)} ({len(calls)}个看涨 + {len(puts)}个看跌)")
        
        # 筛选当日到期期权
        today = date.today()
        today_calls = [c for c in calls if c['expiry'] == today.strftime('%Y-%m-%d')]
        today_puts = [p for p in puts if p['expiry'] == today.strftime('%Y-%m-%d')]
        
        print(f"📅 当日到期期权: {len(today_calls) + len(today_puts)} ({len(today_calls)}个看涨 + {len(today_puts)}个看跌)")
        
        # 寻找合适的交易期权 (Delta 0.30-0.40)
        suitable_calls = []
        suitable_puts = []
        
        for call in today_calls:
            delta = abs(call.get('delta', 0))
            if 0.30 <= delta <= 0.40 and call.get('gamma', 0) > 0:
                suitable_calls.append(call)
        
        for put in today_puts:
            delta = abs(put.get('delta', 0))
            if 0.30 <= delta <= 0.40 and put.get('gamma', 0) > 0:
                suitable_puts.append(put)
        
        print(f"🎯 适合交易的期权: {len(suitable_calls) + len(suitable_puts)} ({len(suitable_calls)}个看涨 + {len(suitable_puts)}个看跌)")
        
        # 显示最佳候选期权
        if suitable_calls:
            # 按Gamma排序，选择流动性最好的
            suitable_calls.sort(key=lambda x: x.get('gamma', 0), reverse=True)
            best_call = suitable_calls[0]
            
            print(f"\n🏆 最佳看涨期权候选:")
            print(f"   合约: {best_call['contractSymbol']}")
            print(f"   行权价: ${best_call['strike']}")
            print(f"   到期日: {best_call['expiry']}")
            print(f"   Delta: {best_call['delta']:.4f}")
            print(f"   Gamma: {best_call['gamma']:.4f}")
            print(f"   Theta: {best_call['theta']:.4f}")
            print(f"   Vega: {best_call['vega']:.4f}")
            print(f"   隐含波动率: {best_call['impliedVolatility']:.3f}")
            print(f"   理论价格: ${best_call['midPrice']:.3f}")
        
        if suitable_puts:
            # 按Gamma排序，选择流动性最好的
            suitable_puts.sort(key=lambda x: x.get('gamma', 0), reverse=True)
            best_put = suitable_puts[0]
            
            print(f"\n🏆 最佳看跌期权候选:")
            print(f"   合约: {best_put['contractSymbol']}")
            print(f"   行权价: ${best_put['strike']}")
            print(f"   到期日: {best_put['expiry']}")
            print(f"   Delta: {best_put['delta']:.4f}")
            print(f"   Gamma: {best_put['gamma']:.4f}")
            print(f"   Theta: {best_put['theta']:.4f}")
            print(f"   Vega: {best_put['vega']:.4f}")
            print(f"   隐含波动率: {best_put['impliedVolatility']:.3f}")
            print(f"   理论价格: ${best_put['midPrice']:.3f}")
        
        # 分析数据质量
        print(f"\n📊 数据质量评估:")
        
        # Greeks数据覆盖率
        calls_with_greeks = sum(1 for c in today_calls if c.get('delta', 0) != 0)
        puts_with_greeks = sum(1 for p in today_puts if p.get('delta', 0) != 0)
        
        total_today = len(today_calls) + len(today_puts)
        total_with_greeks = calls_with_greeks + puts_with_greeks
        
        print(f"   Greeks覆盖率: {total_with_greeks}/{total_today} ({total_with_greeks/total_today*100:.1f}%)")
        
        # 报价数据覆盖率 (虽然bid/ask为0，但这是indicative feed的正常现象)
        calls_with_quotes = sum(1 for c in today_calls if c.get('midPrice', 0) > 0)
        puts_with_quotes = sum(1 for p in today_puts if p.get('midPrice', 0) > 0)
        total_with_quotes = calls_with_quotes + puts_with_quotes
        
        print(f"   理论价格覆盖率: {total_with_quotes}/{total_today} ({total_with_quotes/total_today*100:.1f}%)")
        
        # 交易能力评估
        if suitable_calls or suitable_puts:
            print(f"\n✅ 系统状态: 准备就绪，可以进行EOD期权交易")
            print(f"   可交易期权数量: {len(suitable_calls) + len(suitable_puts)}")
            print(f"   数据获取速度: {(len(calls) + len(puts)) / (end_time - start_time).total_seconds():.0f} 期权/秒")
        else:
            print(f"\n⚠️ 系统状态: 当前没有找到合适的交易期权")
            print(f"   建议检查市场时间和期权流动性")
    
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n✅ EOD期权交易测试完成")


if __name__ == "__main__":
    test_eod_options_trading() 