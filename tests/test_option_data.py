#!/usr/bin/env python3
"""
期权数据API测试脚本
验证Alpaca原生期权数据API的功能
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

def test_option_chain():
    """测试期权链数据获取"""
    print("🔗 测试期权链数据获取...")
    try:
        market_data = MarketDataProvider()
        
        # 获取SPY期权链
        chain = market_data.get_option_chain(config.symbol)
        
        if chain:
            print("✅ 成功获取期权链数据")
            print(f"   - 标的价格: ${chain.get('underlying_price', 0):.2f}")
            print(f"   - 看涨期权数量: {len(chain.get('calls', []))}")
            print(f"   - 看跌期权数量: {len(chain.get('puts', []))}")
            
            # 显示一些看涨期权样例
            calls = chain.get('calls', [])[:3]
            if calls:
                print("\n📈 看涨期权样例:")
                for call in calls:
                    print(f"   - {call['contractSymbol']}: 行权价${call['strike']:.0f}, "
                          f"Delta={call['delta']:.3f}, 买价${call['bid']:.2f}, "
                          f"卖价${call['ask']:.2f}")
            
            # 显示一些看跌期权样例
            puts = chain.get('puts', [])[:3]
            if puts:
                print("\n📉 看跌期权样例:")
                for put in puts:
                    print(f"   - {put['contractSymbol']}: 行权价${put['strike']:.0f}, "
                          f"Delta={put['delta']:.3f}, 买价${put['bid']:.2f}, "
                          f"卖价${put['ask']:.2f}")
            
            return True
        else:
            print("❌ 未获取到期权链数据")
            return False
            
    except Exception as e:
        print(f"❌ 期权链测试失败: {e}")
        traceback.print_exc()
        return False

def test_option_selection():
    """测试期权选择功能"""
    print("\n🎯 测试期权选择功能...")
    try:
        market_data = MarketDataProvider()
        
        # 测试找合适的看涨期权
        calls = market_data.find_suitable_options(config.symbol, "CALL", 0.35)
        print(f"✅ 找到{len(calls)}个合适的看涨期权:")
        for i, call in enumerate(calls):
            print(f"   {i+1}. {call['contractSymbol']}: Delta={call['actual_delta']:.3f}, "
                  f"行权价${call['strike']:.0f}, 中间价${call['midPrice']:.2f}")
        
        # 测试找合适的看跌期权
        puts = market_data.find_suitable_options(config.symbol, "PUT", 0.35)
        print(f"\n✅ 找到{len(puts)}个合适的看跌期权:")
        for i, put in enumerate(puts):
            print(f"   {i+1}. {put['contractSymbol']}: Delta={put['actual_delta']:.3f}, "
                  f"行权价${put['strike']:.0f}, 中间价${put['midPrice']:.2f}")
        
        return len(calls) > 0 or len(puts) > 0
        
    except Exception as e:
        print(f"❌ 期权选择测试失败: {e}")
        traceback.print_exc()
        return False

def test_option_quote():
    """测试单个期权报价获取"""
    print("\n💰 测试期权报价获取...")
    try:
        market_data = MarketDataProvider()
        
        # 先获取一个期权合约代码
        calls = market_data.find_suitable_options(config.symbol, "CALL", 0.35)
        
        if calls:
            option_symbol = calls[0]['contractSymbol']
            quote = market_data.get_option_quote(option_symbol)
            
            if quote:
                print(f"✅ 成功获取期权报价: {option_symbol}")
                print(f"   - 买价: ${quote['bid']:.2f}")
                print(f"   - 卖价: ${quote['ask']:.2f}")
                print(f"   - 中间价: ${quote['midPrice']:.2f}")
                print(f"   - 最后价格: ${quote['lastPrice']:.2f}")
                print(f"   - Delta: {quote['delta']:.3f}")
                print(f"   - 隐含波动率: {quote['impliedVolatility']:.3f}")
                return True
            else:
                print("❌ 未获取到期权报价")
                return False
        else:
            print("❌ 未找到合适的期权合约")
            return False
            
    except Exception as e:
        print(f"❌ 期权报价测试失败: {e}")
        traceback.print_exc()
        return False

def test_option_symbol_parsing():
    """测试期权代码解析"""
    print("\n🔍 测试期权代码解析...")
    try:
        market_data = MarketDataProvider()
        
        # 测试样例
        test_symbols = [
            "SPY250602C00623000",
            "SPY250602P00600000",
            "AAPL250602C00250000"
        ]
        
        for symbol in test_symbols:
            parsed = market_data.parse_option_symbol(symbol)
            if parsed:
                print(f"✅ {symbol} -> 标的:{parsed['underlying_symbol']}, "
                      f"到期:{parsed['exp_date']}, 类型:{parsed['option_type']}, "
                      f"行权价:${parsed['strike_price']:.2f}")
            else:
                print(f"❌ 解析失败: {symbol}")
        
        return True
        
    except Exception as e:
        print(f"❌ 期权代码解析测试失败: {e}")
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("🧪 期权数据API测试")
    print("=" * 50)
    
    # 设置日志
    setup_logger()
    
    test_results = []
    
    # 执行所有测试
    tests = [
        ("期权代码解析", test_option_symbol_parsing),
        ("期权链数据获取", test_option_chain),
        ("期权选择功能", test_option_selection),
        ("期权报价获取", test_option_quote)
    ]
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            test_results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}测试异常: {e}")
            test_results.append((test_name, False))
    
    # 输出测试结果汇总
    print("\n" + "=" * 50)
    print("📋 期权数据API测试结果汇总")
    print("=" * 50)
    
    passed = 0
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name:<20} {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{len(test_results)} 个测试通过")
    
    if passed == len(test_results):
        print("🎉 所有测试通过！期权数据API工作正常")
    else:
        print("⚠️ 部分测试失败，请检查配置和网络连接")

if __name__ == "__main__":
    main() 