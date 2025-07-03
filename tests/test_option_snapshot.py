#!/usr/bin/env python3
"""
测试期权快照API获取Greeks数据
使用特定期权合约符号来获取包含Greeks的快照数据
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

from alpaca.data.historical import OptionHistoricalDataClient
from alpaca.data.requests import OptionSnapshotRequest


def test_option_snapshot():
    """测试期权快照API获取Greeks"""
    
    print("🔍 测试期权快照API获取Greeks")
    print("="*60)
    
    # 初始化期权数据客户端
    try:
        api_key = os.getenv('ALPACA_API_KEY')
        api_secret = os.getenv('ALPACA_SECRET_KEY')
        
        if not api_key or not api_secret:
            print("❌ 缺少Alpaca API凭证")
            return
            
        option_client = OptionHistoricalDataClient(api_key, api_secret)
        print("✅ 期权数据客户端初始化成功")
    except Exception as e:
        print(f"❌ 客户端初始化失败: {e}")
        return
    
    # 测试特定期权合约
    option_symbols = [
        "SPY250604C00596000",  # 6月4日596 Call
        "SPY250604C00595000",  # 6月4日595 Call  
        "SPY250604P00596000",  # 6月4日596 Put
        "SPY250606C00596000",  # 6月6日596 Call (周五到期)
    ]
    
    print(f"\n📊 测试期权合约快照:")
    
    for option_symbol in option_symbols:
        print(f"\n{'='*50}")
        print(f"🎯 期权合约: {option_symbol}")
        
        try:
            # 创建快照请求
            request = OptionSnapshotRequest(symbol_or_symbols=[option_symbol])
            
            # 获取快照数据
            snapshot_data = option_client.get_option_snapshot(request)
            
            print(f"   ✅ 快照数据获取成功")
            print(f"   📄 数据类型: {type(snapshot_data)}")
            
            # 解析快照数据
            if hasattr(snapshot_data, option_symbol):
                snapshot = snapshot_data[option_symbol]
                print(f"   📊 找到期权数据: {option_symbol}")
                
                # 显示报价信息
                if hasattr(snapshot, 'latest_quote') and snapshot.latest_quote:
                    quote = snapshot.latest_quote
                    print(f"   💰 最新报价:")
                    print(f"      Bid: ${quote.bid_price:.4f} (Size: {quote.bid_size})")
                    print(f"      Ask: ${quote.ask_price:.4f} (Size: {quote.ask_size})")
                    print(f"      Timestamp: {quote.timestamp}")
                else:
                    print(f"   ❌ 无报价数据")
                
                # 显示交易信息
                if hasattr(snapshot, 'latest_trade') and snapshot.latest_trade:
                    trade = snapshot.latest_trade
                    print(f"   📈 最新交易:")
                    print(f"      Price: ${trade.price:.4f}")
                    print(f"      Size: {trade.size}")
                    print(f"      Timestamp: {trade.timestamp}")
                else:
                    print(f"   ❌ 无交易数据")
                
                # 显示Greeks
                if hasattr(snapshot, 'greeks') and snapshot.greeks:
                    greeks = snapshot.greeks
                    print(f"   🔢 Greeks:")
                    print(f"      Delta: {greeks.delta:.4f}")
                    print(f"      Gamma: {greeks.gamma:.4f}")
                    print(f"      Theta: {greeks.theta:.4f}")
                    print(f"      Vega: {greeks.vega:.4f}")
                    print(f"      Rho: {greeks.rho:.4f}")
                else:
                    print(f"   ❌ 无Greeks数据")
                
                # 显示隐含波动率
                if hasattr(snapshot, 'implied_volatility'):
                    iv = snapshot.implied_volatility
                    print(f"   📈 隐含波动率: {iv:.4f} ({iv*100:.2f}%)")
                else:
                    print(f"   ❌ 无隐含波动率数据")
                
                # 显示所有可用属性
                print(f"   📝 所有属性: {[attr for attr in dir(snapshot) if not attr.startswith('_')]}")
                
            elif isinstance(snapshot_data, dict):
                print(f"   📊 快照数据字典键: {list(snapshot_data.keys())}")
                for key, value in snapshot_data.items():
                    print(f"      {key}: {type(value)} - {value}")
            else:
                print(f"   ❌ 未找到期权数据结构")
                print(f"   📄 数据内容: {snapshot_data}")
                
        except Exception as e:
            print(f"   ❌ 获取快照失败: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*60)
    print("✅ 期权快照测试完成")


if __name__ == "__main__":
    test_option_snapshot() 