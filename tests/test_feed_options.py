#!/usr/bin/env python3
"""
测试不同的feed参数选项
找到最佳的数据源设置
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


def test_feed_options():
    """测试不同的feed参数选项"""
    
    print("🔍 测试不同的feed参数选项")
    print("="*60)
    
    # 获取API凭证
    api_key = os.getenv('ALPACA_API_KEY')
    api_secret = os.getenv('ALPACA_SECRET_KEY')
    
    if not api_key or not api_secret:
        print("❌ 缺少Alpaca API凭证")
        return
    
    url = "https://data.alpaca.markets/v1beta1/options/snapshots/SPY"
    headers = {
        "APCA-API-KEY-ID": api_key,
        "APCA-API-SECRET-KEY": api_secret
    }
    
    # 测试不同的feed参数
    feed_options = [
        None,  # 不设置feed参数
        "indicative", 
        "opra"
    ]
    
    for feed in feed_options:
        print(f"\n📡 测试feed={feed}:")
        
        try:
            params = {"limit": 100}  # 获取100个期权进行测试
            
            if feed is not None:
                params["feed"] = feed
            
            start_time = time.time()
            response = requests.get(url, headers=headers, params=params)
            end_time = time.time()
            
            if response.status_code == 200:
                data = response.json()
                snapshots = data.get('snapshots', {})
                
                # 统计数据质量
                greeks_count = 0
                quote_count = 0
                trade_count = 0
                iv_count = 0
                sample_greeks = {}
                
                for symbol, snapshot in snapshots.items():
                    if 'greeks' in snapshot and snapshot['greeks']:
                        greeks_count += 1
                        # 保存第一个有Greeks的样本
                        if not sample_greeks and snapshot['greeks']:
                            sample_greeks = {
                                'symbol': symbol,
                                'delta': snapshot['greeks'].get('delta'),
                                'gamma': snapshot['greeks'].get('gamma'),
                                'theta': snapshot['greeks'].get('theta')
                            }
                    if 'latest_quote' in snapshot and snapshot['latest_quote']:
                        quote_count += 1
                    if 'latest_trade' in snapshot and snapshot['latest_trade']:
                        trade_count += 1
                    if 'implied_volatility' in snapshot and snapshot['implied_volatility']:
                        iv_count += 1
                
                print(f"   ✅ 成功 - 返回{len(snapshots)}个期权")
                print(f"   ⏱️  请求时间: {end_time - start_time:.2f}秒")
                print(f"   📊 Greeks: {greeks_count}/{len(snapshots)} ({greeks_count/len(snapshots)*100:.1f}%)")
                print(f"   📊 报价: {quote_count}/{len(snapshots)} ({quote_count/len(snapshots)*100:.1f}%)")
                print(f"   📊 交易: {trade_count}/{len(snapshots)} ({trade_count/len(snapshots)*100:.1f}%)")
                print(f"   📊 IV: {iv_count}/{len(snapshots)} ({iv_count/len(snapshots)*100:.1f}%)")
                
                # 显示Greeks样本
                if sample_greeks:
                    print(f"   📄 Greeks样本 ({sample_greeks['symbol']}):")
                    print(f"      Delta: {sample_greeks['delta']}")
                    print(f"      Gamma: {sample_greeks['gamma']}")
                    print(f"      Theta: {sample_greeks['theta']}")
                else:
                    print(f"   📄 无Greeks数据样本")
                
                # 检查是否有分页
                if 'next_page_token' in data:
                    print(f"   📄 有更多数据可分页获取")
                
            else:
                print(f"   ❌ 失败: HTTP {response.status_code}")
                print(f"   错误: {response.text}")
                
        except Exception as e:
            print(f"   ❌ 请求失败: {e}")
        
        time.sleep(1)  # 防止限速
    
    print(f"\n🏆 结论:")
    print(f"   根据测试结果选择最佳的feed参数")
    print(f"   优先选择Greeks数据覆盖率最高的选项")
    print("\n✅ feed参数测试完成")


if __name__ == "__main__":
    test_feed_options() 