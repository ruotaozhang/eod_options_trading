#!/usr/bin/env python3
"""测试优化后的期权选择逻辑"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data.market_data import MarketDataProvider
from src.config import config

def test_optimized_option_selection():
    try:
        market_data = MarketDataProvider()
        current_price = market_data.get_current_price(config.symbol)
        print(f'🎯 当前{config.symbol}价格: ${current_price:.2f}')
        
        # 测试Call期权
        print('\n📈 Call期权候选:')
        calls = market_data.find_suitable_options(config.symbol, 'CALL', 0.35)
        for i, call in enumerate(calls, 1):
            print(f'  {i}. {call["contractSymbol"]} ({call["moneyness_type"]})')
            print(f'     行权价:${call["strike"]:.0f}, Delta:{call["delta"]:.3f}')
            print(f'     Bid/Ask:${call["bid"]:.2f}/${call["ask"]:.2f}, 价差:${call["ask"]-call["bid"]:.3f}')
        
        # 测试Put期权  
        print('\n📉 Put期权候选:')
        puts = market_data.find_suitable_options(config.symbol, 'PUT', 0.35)
        for i, put in enumerate(puts, 1):
            print(f'  {i}. {put["contractSymbol"]} ({put["moneyness_type"]})')
            print(f'     行权价:${put["strike"]:.0f}, Delta:{put["delta"]:.3f}')
            print(f'     Bid/Ask:${put["bid"]:.2f}/${put["ask"]:.2f}, 价差:${put["ask"]-put["bid"]:.3f}')
        
        print('\n✅ 优化后的期权选择逻辑测试完成！')
        print('🎯 新特性:')
        print('   • 多候选期权筛选 (ATM/轻度ITM/轻度OTM)')
        print('   • 流动性检查 (买卖价差、最小价格)')
        print('   • 智能排序 (流动性优先、Delta接近度)')
        
    except Exception as e:
        print(f'❌ 测试失败: {e}')
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = test_optimized_option_selection()
    sys.exit(0 if success else 1) 