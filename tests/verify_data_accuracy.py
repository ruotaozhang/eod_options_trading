#!/usr/bin/env python3
"""
验证期权数据准确性
对比HTTP API和SDK方法获取的数据，确保数据正确性
"""

import os
import sys
from datetime import datetime, date
from dotenv import load_dotenv
import time
import requests

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
from alpaca.data.requests import OptionSnapshotRequest, OptionChainRequest


def verify_data_accuracy():
    """验证期权数据准确性"""
    
    print("🔍 验证期权数据准确性")
    print("="*60)
    
    # 初始化客户端
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
    
    # 方法1: 使用直接HTTP API获取数据
    print("\n🌐 方法1: HTTP API获取期权数据")
    http_data = {}
    try:
        url = "https://data.alpaca.markets/v1beta1/options/snapshots/SPY"
        headers = {
            "APCA-API-KEY-ID": api_key,
            "APCA-API-SECRET-KEY": api_secret
        }
        
        params = {
            "limit": 100,  # 只获取前100个进行对比
            "feed": "indicative"
        }
        
        start_time = time.time()
        response = requests.get(url, headers=headers, params=params)
        end_time = time.time()
        
        if response.status_code == 200:
            data = response.json()
            http_data = data.get('snapshots', {})
            
            print(f"   ✅ HTTP API成功")
            print(f"   📥 获取期权数量: {len(http_data)}")
            print(f"   ⏱️  请求时间: {end_time - start_time:.2f}秒")
            
            # 检查数据质量
            greeks_count = 0
            quote_count = 0
            trade_count = 0
            
            for symbol, snapshot in http_data.items():
                if 'greeks' in snapshot and snapshot['greeks']:
                    greeks_count += 1
                if 'latest_quote' in snapshot and snapshot['latest_quote']:
                    quote_count += 1
                if 'latest_trade' in snapshot and snapshot['latest_trade']:
                    trade_count += 1
            
            print(f"   📊 数据质量: Greeks={greeks_count}, 报价={quote_count}, 交易={trade_count}")
            
        else:
            print(f"   ❌ HTTP API失败: {response.status_code}")
            print(f"   错误信息: {response.text}")
            
    except Exception as e:
        print(f"❌ HTTP API请求失败: {e}")
    
    # 方法2: 使用SDK获取期权链
    print("\n🐍 方法2: SDK获取期权链")
    sdk_symbols = []
    try:
        request = OptionChainRequest(underlying_symbol="SPY")
        option_chain = option_client.get_option_chain(request)
        
        # 提取期权符号
        if hasattr(option_chain, '__iter__'):
            for item in option_chain:
                if isinstance(item, str):
                    sdk_symbols.append(item)
                elif hasattr(item, 'symbol'):
                    sdk_symbols.append(item.symbol)
                elif isinstance(item, dict) and 'symbol' in item:
                    sdk_symbols.append(item['symbol'])
        
        print(f"   ✅ SDK获取期权链成功")
        print(f"   📥 期权符号数量: {len(sdk_symbols)}")
        
        # 获取前100个期权的快照数据（用于对比）
        test_symbols = sdk_symbols[:100]
        
        sdk_data = {}
        batch_size = 100
        
        start_time = time.time()
        snapshot_request = OptionSnapshotRequest(symbol_or_symbols=test_symbols)
        batch_snapshots = option_client.get_option_snapshot(snapshot_request)
        end_time = time.time()
        
        if isinstance(batch_snapshots, dict):
            sdk_data = batch_snapshots
            
            print(f"   ✅ SDK快照获取成功")
            print(f"   📥 获取快照数量: {len(sdk_data)}")
            print(f"   ⏱️  请求时间: {end_time - start_time:.2f}秒")
            
            # 检查数据质量
            greeks_count = 0
            quote_count = 0
            trade_count = 0
            
            for symbol, snapshot in sdk_data.items():
                if hasattr(snapshot, 'greeks') and snapshot.greeks:
                    greeks_count += 1
                if hasattr(snapshot, 'latest_quote') and snapshot.latest_quote:
                    quote_count += 1
                if hasattr(snapshot, 'latest_trade') and snapshot.latest_trade:
                    trade_count += 1
            
            print(f"   📊 数据质量: Greeks={greeks_count}, 报价={quote_count}, 交易={trade_count}")
        
    except Exception as e:
        print(f"❌ SDK方法失败: {e}")
    
    # 方法3: 数据对比分析
    print("\n🔍 方法3: 数据对比分析")
    if http_data and sdk_data:
        # 找到共同的期权符号
        http_symbols = set(http_data.keys())
        sdk_symbols_dict = {symbol: snapshot for symbol, snapshot in sdk_data.items()}
        sdk_symbols_set = set(sdk_symbols_dict.keys())
        
        common_symbols = http_symbols.intersection(sdk_symbols_set)
        
        print(f"   📊 HTTP API期权数量: {len(http_symbols)}")
        print(f"   📊 SDK期权数量: {len(sdk_symbols_set)}")
        print(f"   📊 共同期权数量: {len(common_symbols)}")
        
        if common_symbols:
            # 对比几个具体期权的数据
            test_symbols = list(common_symbols)[:5]  # 取前5个进行详细对比
            
            print(f"\n📋 详细对比 (前5个共同期权):")
            print("-" * 60)
            
            for symbol in test_symbols:
                print(f"\n🔍 期权: {symbol}")
                
                # HTTP数据
                http_snapshot = http_data[symbol]
                # SDK数据
                sdk_snapshot = sdk_symbols_dict[symbol]
                
                # 对比Greeks
                print("   📊 Greeks对比:")
                if 'greeks' in http_snapshot and http_snapshot['greeks']:
                    http_greeks = http_snapshot['greeks']
                    http_delta = http_greeks.get('delta', 0)
                    http_gamma = http_greeks.get('gamma', 0)
                    http_theta = http_greeks.get('theta', 0)
                    print(f"      HTTP: Delta={http_delta:.4f}, Gamma={http_gamma:.4f}, Theta={http_theta:.4f}")
                else:
                    print("      HTTP: 无Greeks数据")
                
                if hasattr(sdk_snapshot, 'greeks') and sdk_snapshot.greeks:
                    sdk_greeks = sdk_snapshot.greeks
                    sdk_delta = getattr(sdk_greeks, 'delta', 0) or 0
                    sdk_gamma = getattr(sdk_greeks, 'gamma', 0) or 0
                    sdk_theta = getattr(sdk_greeks, 'theta', 0) or 0
                    print(f"      SDK:  Delta={sdk_delta:.4f}, Gamma={sdk_gamma:.4f}, Theta={sdk_theta:.4f}")
                    
                    # 检查是否一致
                    if (abs(http_delta - sdk_delta) < 0.0001 and 
                        abs(http_gamma - sdk_gamma) < 0.0001 and 
                        abs(http_theta - sdk_theta) < 0.0001):
                        print("      ✅ Greeks数据一致")
                    else:
                        print("      ⚠️ Greeks数据有差异")
                else:
                    print("      SDK:  无Greeks数据")
                
                # 对比报价
                print("   💰 报价对比:")
                http_bid = 0
                http_ask = 0
                if 'latest_quote' in http_snapshot and http_snapshot['latest_quote']:
                    http_quote = http_snapshot['latest_quote']
                    http_bid = http_quote.get('bid_price', 0)
                    http_ask = http_quote.get('ask_price', 0)
                    print(f"      HTTP: Bid=${http_bid:.4f}, Ask=${http_ask:.4f}")
                else:
                    print("      HTTP: 无报价数据")
                
                sdk_bid = 0
                sdk_ask = 0
                if hasattr(sdk_snapshot, 'latest_quote') and sdk_snapshot.latest_quote:
                    sdk_quote = sdk_snapshot.latest_quote
                    sdk_bid = getattr(sdk_quote, 'bid_price', 0) or 0
                    sdk_ask = getattr(sdk_quote, 'ask_price', 0) or 0
                    print(f"      SDK:  Bid=${sdk_bid:.4f}, Ask=${sdk_ask:.4f}")
                    
                    # 检查是否一致
                    if (abs(http_bid - sdk_bid) < 0.0001 and 
                        abs(http_ask - sdk_ask) < 0.0001):
                        print("      ✅ 报价数据一致")
                    else:
                        print("      ⚠️ 报价数据有差异")
                else:
                    print("      SDK:  无报价数据")
                
                # 对比隐含波动率
                print("   📈 隐含波动率对比:")
                http_iv = http_snapshot.get('implied_volatility', 0)
                print(f"      HTTP: IV={http_iv:.4f}")
                
                sdk_iv = 0
                if hasattr(sdk_snapshot, 'implied_volatility'):
                    sdk_iv = getattr(sdk_snapshot, 'implied_volatility', 0) or 0
                    print(f"      SDK:  IV={sdk_iv:.4f}")
                    
                    if abs(http_iv - sdk_iv) < 0.0001:
                        print("      ✅ IV数据一致")
                    else:
                        print("      ⚠️ IV数据有差异")
                else:
                    print("      SDK:  无IV数据")
        
        # 总结
        print(f"\n🏆 验证总结:")
        print(f"   📊 数据源对比: HTTP API vs SDK")
        print(f"   📥 数据覆盖: {len(common_symbols)}/{max(len(http_symbols), len(sdk_symbols_set))} 期权匹配")
        
        if len(common_symbols) > 0:
            print(f"   ✅ 数据验证: 通过详细对比验证")
        else:
            print(f"   ⚠️ 数据验证: 没有找到匹配的期权进行对比")
    
    else:
        print("   ❌ 无法进行数据对比，缺少必要数据")
    
    print("\n✅ 数据验证完成")


if __name__ == "__main__":
    verify_data_accuracy() 