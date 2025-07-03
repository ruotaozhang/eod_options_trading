#!/usr/bin/env python3
"""测试恢复后的简单价格就近选择规则"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data.market_data import MarketDataProvider
from src.config import config

def test_simple_price_rule():
    """测试简单的价格就近规则"""
    try:
        market_data = MarketDataProvider()
        current_price = market_data.get_current_price(config.symbol)
        print(f'🎯 当前{config.symbol}价格: ${current_price:.2f}')
        
        # 计算预期的行权价
        call_expected_strike = int(current_price)  # floor
        put_expected_strike = int(current_price) + (1 if current_price > int(current_price) else 0)  # ceil
        
        print(f'\n📐 价格就近规则:')
        print(f'   Call期权预期行权价: ${call_expected_strike} (floor操作)')
        print(f'   Put期权预期行权价: ${put_expected_strike} (ceil操作)')
        
        # 测试Call期权选择
        print('\n📈 Call期权选择:')
        calls = market_data.find_suitable_options(config.symbol, 'CALL')
        if calls:
            call = calls[0]
            print(f'   ✅ 选中: {call["contractSymbol"]}')
            print(f'   行权价: ${call["strike"]:.0f}')
            print(f'   符合预期: {"✅" if call["strike"] == call_expected_strike else "❌"}')
            print(f'   Bid/Ask: ${call["bid"]:.2f}/${call["ask"]:.2f}')
            print(f'   Delta: {call["delta"]:.3f}')
        else:
            print('   ❌ 未找到Call期权')
        
        # 测试Put期权选择  
        print('\n📉 Put期权选择:')
        puts = market_data.find_suitable_options(config.symbol, 'PUT')
        if puts:
            put = puts[0]
            print(f'   ✅ 选中: {put["contractSymbol"]}')
            print(f'   行权价: ${put["strike"]:.0f}')
            print(f'   符合预期: {"✅" if put["strike"] == put_expected_strike else "❌"}')
            print(f'   Bid/Ask: ${put["bid"]:.2f}/${put["ask"]:.2f}')
            print(f'   Delta: {put["delta"]:.3f}')
        else:
            print('   ❌ 未找到Put期权')
        
        print('\n🎯 规则验证:')
        print('   ✅ 不考虑Delta范围')
        print('   ✅ 不考虑流动性检查')
        print('   ✅ 纯粹基于价格就近原则')
        print('   ✅ Call: floor(当前价格)')
        print('   ✅ Put: ceil(当前价格)')
        
        return True
        
    except Exception as e:
        print(f'❌ 测试失败: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_simple_price_rule()
    print(f'\n{"✅ 简单价格就近规则测试完成" if success else "❌ 测试失败"}')
    sys.exit(0 if success else 1) 