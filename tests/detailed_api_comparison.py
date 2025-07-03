#!/usr/bin/env python3
"""
详细分析HTTP API和SDK的数据差异
找出为什么HTTP API返回的数据质量不同
"""

import os
import sys
from datetime import datetime, date
from dotenv import load_dotenv
import time
import requests
import json

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


def detailed_api_comparison():
    """详细对比HTTP API和SDK的数据差异"""
    
    print("🔍 详细分析HTTP API和SDK数据差异")
    print("="*60)
    
    # 初始化客户端
    api_key = os.getenv('ALPACA_API_KEY')
    api_secret = os.getenv('ALPACA_SECRET_KEY')
    
    if not api_key or not api_secret:
        print("❌ 缺少Alpaca API凭证")
        return
        
    option_client = OptionHistoricalDataClient(api_key, api_secret)
    
    # 测试特定期权
    test_option = "SPY250604C00596000"  # 我们之前测试过的期权
    
    print(f"\n🎯 测试特定期权: {test_option}")
    print("-" * 40)
    
    # 方法1: 使用HTTP API获取单个期权快照
    print("\n🌐 HTTP API - 单个期权快照:")
    try:
        url = f"https://data.alpaca.markets/v1beta1/options/snapshots/{test_option}"
        headers = {
            "APCA-API-KEY-ID": api_key,
            "APCA-API-SECRET-KEY": api_secret
        }
        
        params = {"feed": "indicative"}
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ 成功获取单个期权快照")
            print(f"   📄 原始响应: {json.dumps(data, indent=2)[:500]}...")
            
            if 'snapshot' in data:
                snapshot = data['snapshot']
                
                # 检查各种数据
                print(f"\n   📊 数据分析:")
                print(f"      Greeks: {'有' if 'greeks' in snapshot and snapshot['greeks'] else '无'}")
                print(f"      报价: {'有' if 'latest_quote' in snapshot and snapshot['latest_quote'] else '无'}")
                print(f"      交易: {'有' if 'latest_trade' in snapshot and snapshot['latest_trade'] else '无'}")
                print(f"      IV: {'有' if 'implied_volatility' in snapshot else '无'}")
                
                if 'greeks' in snapshot and snapshot['greeks']:
                    greeks = snapshot['greeks']
                    print(f"      Delta: {greeks.get('delta', 'N/A')}")
                    print(f"      Gamma: {greeks.get('gamma', 'N/A')}")
                    print(f"      Theta: {greeks.get('theta', 'N/A')}")
        else:
            print(f"   ❌ 请求失败: {response.status_code}")
            print(f"   错误: {response.text}")
            
    except Exception as e:
        print(f"❌ HTTP API请求失败: {e}")
    
    # 方法2: 使用HTTP API获取SPY全部期权快照（查找特定期权）
    print(f"\n🌐 HTTP API - SPY全部期权快照:")
    try:
        url = "https://data.alpaca.markets/v1beta1/options/snapshots/SPY"
        headers = {
            "APCA-API-KEY-ID": api_key,
            "APCA-API-SECRET-KEY": api_secret
        }
        
        params = {
            "limit": 1000,
            "feed": "indicative"
        }
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            snapshots = data.get('snapshots', {})
            
            print(f"   ✅ 成功获取SPY期权快照")
            print(f"   📥 总期权数量: {len(snapshots)}")
            
            if test_option in snapshots:
                snapshot = snapshots[test_option]
                print(f"   🎯 找到目标期权: {test_option}")
                
                print(f"\n   📊 数据分析:")
                print(f"      Greeks: {'有' if 'greeks' in snapshot and snapshot['greeks'] else '无'}")
                print(f"      报价: {'有' if 'latest_quote' in snapshot and snapshot['latest_quote'] else '无'}")
                print(f"      交易: {'有' if 'latest_trade' in snapshot and snapshot['latest_trade'] else '无'}")
                print(f"      IV: {'有' if 'implied_volatility' in snapshot else '无'}")
                
                if 'greeks' in snapshot and snapshot['greeks']:
                    greeks = snapshot['greeks']
                    print(f"      Delta: {greeks.get('delta', 'N/A')}")
                    print(f"      Gamma: {greeks.get('gamma', 'N/A')}")
                    print(f"      Theta: {greeks.get('theta', 'N/A')}")
                    print(f"      Vega: {greeks.get('vega', 'N/A')}")
                    print(f"      Rho: {greeks.get('rho', 'N/A')}")
                
                if 'latest_quote' in snapshot and snapshot['latest_quote']:
                    quote = snapshot['latest_quote']
                    print(f"      Bid: ${quote.get('bid_price', 0)}")
                    print(f"      Ask: ${quote.get('ask_price', 0)}")
                
                if 'implied_volatility' in snapshot:
                    iv = snapshot['implied_volatility']
                    print(f"      IV: {iv} ({iv*100:.2f}%)")
            else:
                print(f"   ⚠️ 未找到目标期权: {test_option}")
                print(f"   📝 可用期权示例: {list(snapshots.keys())[:5]}")
        else:
            print(f"   ❌ 请求失败: {response.status_code}")
            print(f"   错误: {response.text}")
            
    except Exception as e:
        print(f"❌ HTTP API请求失败: {e}")
    
    # 方法3: 使用SDK获取期权快照
    print(f"\n🐍 SDK - 期权快照:")
    try:
        snapshot_request = OptionSnapshotRequest(symbol_or_symbols=[test_option])
        snapshots = option_client.get_option_snapshot(snapshot_request)
        
        if isinstance(snapshots, dict) and test_option in snapshots:
            snapshot = snapshots[test_option]
            
            print(f"   ✅ 成功获取SDK期权快照")
            print(f"   🎯 目标期权: {test_option}")
            
            print(f"\n   📊 数据分析:")
            print(f"      Greeks: {'有' if hasattr(snapshot, 'greeks') and snapshot.greeks else '无'}")
            print(f"      报价: {'有' if hasattr(snapshot, 'latest_quote') and snapshot.latest_quote else '无'}")
            print(f"      交易: {'有' if hasattr(snapshot, 'latest_trade') and snapshot.latest_trade else '无'}")
            print(f"      IV: {'有' if hasattr(snapshot, 'implied_volatility') and snapshot.implied_volatility else '无'}")
            
            if hasattr(snapshot, 'greeks') and snapshot.greeks:
                greeks = snapshot.greeks
                print(f"      Delta: {getattr(greeks, 'delta', 'N/A')}")
                print(f"      Gamma: {getattr(greeks, 'gamma', 'N/A')}")
                print(f"      Theta: {getattr(greeks, 'theta', 'N/A')}")
                print(f"      Vega: {getattr(greeks, 'vega', 'N/A')}")
                print(f"      Rho: {getattr(greeks, 'rho', 'N/A')}")
            
            if hasattr(snapshot, 'latest_quote') and snapshot.latest_quote:
                quote = snapshot.latest_quote
                print(f"      Bid: ${getattr(quote, 'bid_price', 0)}")
                print(f"      Ask: ${getattr(quote, 'ask_price', 0)}")
            
            if hasattr(snapshot, 'implied_volatility') and snapshot.implied_volatility:
                iv = snapshot.implied_volatility
                print(f"      IV: {iv} ({iv*100:.2f}%)")
                
        else:
            print(f"   ❌ 未获取到期权快照")
            print(f"   📝 响应类型: {type(snapshots)}")
            if isinstance(snapshots, dict):
                print(f"   📝 可用期权: {list(snapshots.keys())}")
            
    except Exception as e:
        print(f"❌ SDK请求失败: {e}")
    
    # 方法4: 测试不同的feed参数
    print(f"\n🔬 测试不同的feed参数:")
    feeds = ["indicative", "opra"]
    
    for feed in feeds:
        print(f"\n   📡 测试feed={feed}:")
        try:
            url = "https://data.alpaca.markets/v1beta1/options/snapshots/SPY"
            headers = {
                "APCA-API-KEY-ID": api_key,
                "APCA-API-SECRET-KEY": api_secret
            }
            
            params = {
                "limit": 10,  # 只取10个测试
                "feed": feed
            }
            
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                snapshots = data.get('snapshots', {})
                
                # 统计数据质量
                greeks_count = 0
                quote_count = 0
                trade_count = 0
                iv_count = 0
                
                for symbol, snapshot in snapshots.items():
                    if 'greeks' in snapshot and snapshot['greeks']:
                        greeks_count += 1
                    if 'latest_quote' in snapshot and snapshot['latest_quote']:
                        quote_count += 1
                    if 'latest_trade' in snapshot and snapshot['latest_trade']:
                        trade_count += 1
                    if 'implied_volatility' in snapshot and snapshot['implied_volatility']:
                        iv_count += 1
                
                print(f"      ✅ 成功 - 返回{len(snapshots)}个期权")
                print(f"      📊 Greeks: {greeks_count}/{len(snapshots)}")
                print(f"      📊 报价: {quote_count}/{len(snapshots)}")
                print(f"      📊 交易: {trade_count}/{len(snapshots)}")
                print(f"      📊 IV: {iv_count}/{len(snapshots)}")
                
            else:
                print(f"      ❌ 失败: {response.status_code}")
                print(f"      错误: {response.text}")
                
        except Exception as e:
            print(f"      ❌ 请求失败: {e}")
    
    print("\n✅ 详细对比完成")


if __name__ == "__main__":
    detailed_api_comparison() 