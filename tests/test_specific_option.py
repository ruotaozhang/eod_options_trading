#!/usr/bin/env python3
"""
测试特定期权信息获取
获取6月4日到期、行权价596的SPY call期权的详细信息
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

# 添加src目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.data.market_data import MarketDataProvider


def test_specific_option():
    """测试获取特定期权信息"""
    
    print("🔍 测试期权信息获取")
    print("="*60)
    
    # 初始化市场数据提供者
    try:
        market_data = MarketDataProvider()
        print("✅ 市场数据客户端初始化成功")
    except Exception as e:
        print(f"❌ 客户端初始化失败: {e}")
        return
    
    # 目标期权信息
    underlying = "SPY"
    strike_price = 596.0
    option_type = "CALL"
    expiry_date = "2025-06-04"  # 6月4日
    
    print(f"\n📊 目标期权信息:")
    print(f"   标的: {underlying}")
    print(f"   到期日: {expiry_date}")
    print(f"   行权价: ${strike_price}")
    print(f"   类型: {option_type}")
    
    # 构建期权代码 (OSI格式: SPY250604C00596000)
    exp_date = datetime.strptime(expiry_date, "%Y-%m-%d")
    option_symbol = f"{underlying}{exp_date.strftime('%y%m%d')}C{int(strike_price * 1000):08d}"
    print(f"   期权代码: {option_symbol}")
    
    print("\n" + "="*60)
    
    # 1. 获取标的当前价格
    print("1️⃣ 获取标的当前价格...")
    try:
        current_price = market_data.get_current_price(underlying)
        print(f"   ✅ SPY当前价格: ${current_price:.2f}")
    except Exception as e:
        print(f"   ❌ 获取标的价格失败: {e}")
        current_price = 0
    
    # 2. 获取完整期权链
    print("\n2️⃣ 获取期权链数据...")
    try:
        option_chain = market_data.get_option_chain(underlying)
        if option_chain:
            calls_count = len(option_chain.get('calls', []))
            puts_count = len(option_chain.get('puts', []))
            print(f"   ✅ 期权链获取成功: {calls_count}个看涨期权, {puts_count}个看跌期权")
        else:
            print("   ❌ 期权链数据为空")
            return
    except Exception as e:
        print(f"   ❌ 获取期权链失败: {e}")
        return
    
    # 3. 查找特定期权
    print("\n3️⃣ 查找目标期权...")
    target_option = None
    
    # 在call期权中查找
    for option in option_chain.get('calls', []):
        if (option['strike'] == strike_price and 
            option['expiry'] == expiry_date):
            target_option = option
            break
    
    if not target_option:
        # 如果没找到，尝试查找最接近的期权
        print(f"   ⚠️ 未找到确切匹配的期权，查找最接近的...")
        closest_options = []
        for option in option_chain.get('calls', []):
            if option['expiry'] == expiry_date:
                strike_diff = abs(option['strike'] - strike_price)
                closest_options.append((strike_diff, option))
        
        if closest_options:
            closest_options.sort(key=lambda x: x[0])
            target_option = closest_options[0][1]
            print(f"   ⚠️ 找到最接近的期权: 行权价${target_option['strike']}")
    
    if not target_option:
        print("   ❌ 未找到目标期权或类似期权")
        return
    
    print(f"   ✅ 找到目标期权: {target_option['contractSymbol']}")
    
    # 4. 显示详细信息
    print("\n4️⃣ 期权详细信息:")
    print("="*60)
    
    print(f"📄 基本信息:")
    print(f"   合约代码: {target_option['contractSymbol']}")
    print(f"   行权价: ${target_option['strike']:.2f}")
    print(f"   到期日: {target_option['expiry']}")
    print(f"   到期天数: {target_option['days_to_exp']}天")
    
    print(f"\n💰 价格信息:")
    print(f"   买入价 (Bid): ${target_option['bid']:.4f}")
    print(f"   卖出价 (Ask): ${target_option['ask']:.4f}")
    print(f"   中间价 (Mid): ${target_option['midPrice']:.4f}")
    print(f"   最后成交价: ${target_option['lastPrice']:.4f}")
    print(f"   买入量: {target_option['bidSize']}")
    print(f"   卖出量: {target_option['askSize']}")
    
    print(f"\n📊 交易量信息:")
    print(f"   成交量: {target_option['volume']}")
    print(f"   未平仓合约: {target_option['openInterest']}")
    
    print(f"\n🔢 Greeks:")
    print(f"   Delta: {target_option['delta']:.4f}")
    print(f"   Gamma: {target_option['gamma']:.4f}")
    print(f"   Theta: {target_option['theta']:.4f}")
    print(f"   Vega: {target_option['vega']:.4f}")
    print(f"   Rho: {target_option['rho']:.4f}")
    
    print(f"\n📈 波动率:")
    print(f"   隐含波动率: {target_option['impliedVolatility']:.4f} ({target_option['impliedVolatility']*100:.2f}%)")
    
    # 5. 价内价外分析
    if current_price > 0:
        print(f"\n🎯 价内价外分析:")
        moneyness = current_price / target_option['strike']
        if moneyness > 1:
            itm_amount = current_price - target_option['strike']
            print(f"   状态: 价内 (ITM)")
            print(f"   价内程度: ${itm_amount:.2f}")
        elif moneyness < 1:
            otm_amount = target_option['strike'] - current_price
            print(f"   状态: 价外 (OTM)")
            print(f"   价外程度: ${otm_amount:.2f}")
        else:
            print(f"   状态: 平价 (ATM)")
        
        print(f"   价格比率: {moneyness:.4f}")
    
    # 6. 测试单独获取期权报价
    print("\n5️⃣ 测试单独期权报价获取...")
    try:
        quote = market_data.get_option_quote(target_option['contractSymbol'])
        if quote:
            print("   ✅ 单独报价获取成功:")
            print(f"      Bid: ${quote['bid']:.4f}")
            print(f"      Ask: ${quote['ask']:.4f}")
            print(f"      Mid: ${quote['midPrice']:.4f}")
            print(f"      Delta: {quote['delta']:.4f}")
            print(f"      IV: {quote['impliedVolatility']:.4f}")
        else:
            print("   ❌ 单独报价获取失败")
    except Exception as e:
        print(f"   ❌ 单独报价获取异常: {e}")
    
    print("\n" + "="*60)
    print("✅ 测试完成")


if __name__ == "__main__":
    test_specific_option() 