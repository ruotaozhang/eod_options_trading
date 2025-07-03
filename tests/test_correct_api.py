#!/usr/bin/env python3
"""
测试正确的期权链API用法
使用标的符号直接获取所有期权快照，测试limit=1000参数
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


def test_correct_api():
    """测试正确的期权链API用法"""
    
    print("🔍 测试正确的期权链API (limit=1000)")
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
    
    # 方法1: 使用直接的HTTP请求（按文档方式）
    print("\n🌐 方法1: 直接HTTP请求测试")
    try:
        url = "https://data.alpaca.markets/v1beta1/options/snapshots/SPY"
        headers = {
            "APCA-API-KEY-ID": api_key,
            "APCA-API-SECRET-KEY": api_secret
        }
        
        # 测试不同的limit值
        limits = [100, 500, 1000]
        
        for limit in limits:
            print(f"\n📊 测试limit={limit}")
            params = {
                "limit": limit,
                "feed": "indicative"  # 使用免费数据源
            }
            
            start_time = time.time()
            response = requests.get(url, headers=headers, params=params)
            end_time = time.time()
            
            if response.status_code == 200:
                data = response.json()
                snapshots = data.get('snapshots', {})
                
                print(f"   ✅ 成功!")
                print(f"   📥 返回期权数量: {len(snapshots)}")
                print(f"   ⏱️  请求时间: {end_time - start_time:.2f}秒")
                print(f"   🚀 速度: {len(snapshots)/(end_time - start_time):.1f}个/秒")
                
                # 检查是否有next_page_token
                if 'next_page_token' in data:
                    print(f"   📄 有更多数据: next_page_token = {data['next_page_token'][:20]}...")
                else:
                    print("   📄 没有更多数据")
                
                # 检查几个样本数据
                sample_count = 0
                greeks_count = 0
                for symbol, snapshot in snapshots.items():
                    sample_count += 1
                    if 'greeks' in snapshot and snapshot['greeks']:
                        greeks_count += 1
                    if sample_count >= 10:
                        break
                
                print(f"   📊 样本检查: {greeks_count}/{sample_count} 有Greeks数据")
                
                # 显示一个完整的示例
                if snapshots:
                    first_symbol = list(snapshots.keys())[0]
                    first_snapshot = snapshots[first_symbol]
                    print(f"   📄 示例期权: {first_symbol}")
                    
                    if 'latest_quote' in first_snapshot:
                        quote = first_snapshot['latest_quote']
                        print(f"      报价: Bid=${quote.get('bid_price', 0):.2f}, Ask=${quote.get('ask_price', 0):.2f}")
                    
                    if 'greeks' in first_snapshot and first_snapshot['greeks']:
                        greeks = first_snapshot['greeks']
                        print(f"      Greeks: Delta={greeks.get('delta', 0):.4f}, Gamma={greeks.get('gamma', 0):.4f}")
                    
                    if 'implied_volatility' in first_snapshot:
                        iv = first_snapshot['implied_volatility']
                        print(f"      IV: {iv:.4f} ({iv*100:.2f}%)")
                
            else:
                print(f"   ❌ 请求失败: HTTP {response.status_code}")
                print(f"   错误信息: {response.text}")
                
            time.sleep(0.5)  # 防止限速
            
    except Exception as e:
        print(f"❌ HTTP请求失败: {e}")
    
    # 方法2: 检查Python SDK是否有对应的方法
    print(f"\n🐍 方法2: 检查Python SDK方法")
    try:
        # 列出所有可用的方法
        client_methods = [method for method in dir(option_client) if not method.startswith('_')]
        print(f"可用方法: {client_methods}")
        
        # 检查是否有直接获取期权链快照的方法
        snapshot_methods = [method for method in client_methods if 'snapshot' in method.lower()]
        print(f"快照相关方法: {snapshot_methods}")
        
    except Exception as e:
        print(f"❌ SDK检查失败: {e}")
    
    print("\n✅ API测试完成")


if __name__ == "__main__":
    test_correct_api() 