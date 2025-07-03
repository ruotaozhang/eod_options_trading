#!/usr/bin/env python3
"""
测试新的API格式
确保能获取到bid/ask价格和Greeks数据
"""

import os
import sys
from datetime import datetime, date
from dotenv import load_dotenv
import requests
import json

# 加载环境变量
load_dotenv()

# 清除可能导致问题的环境变量
if 'USE_BRACKET_ORDERS' in os.environ:
    del os.environ['USE_BRACKET_ORDERS']
if 'BRACKET_ORDER_TIMEOUT' in os.environ:
    del os.environ['BRACKET_ORDER_TIMEOUT']


def test_new_api_format():
    """测试新的API格式"""
    
    print("🔍 测试新的API格式")
    print("="*60)
    
    # 获取API凭证
    api_key = os.getenv('ALPACA_API_KEY')
    api_secret = os.getenv('ALPACA_SECRET_KEY')
    
    if not api_key or not api_secret:
        print("❌ 缺少Alpaca API凭证")
        return
    
    # 使用您提供的API格式，但添加认证
    url = "https://data.alpaca.markets/v1beta1/options/snapshots/SPY?feed=indicative&limit=1000"
    
    headers = {
        "accept": "application/json",
        "APCA-API-KEY-ID": api_key,
        "APCA-API-SECRET-KEY": api_secret
    }
    
    print(f"📡 API调用: {url}")
    print(f"🔑 使用认证头")
    
    try:
        response = requests.get(url, headers=headers)
        
        print(f"\n📊 响应状态: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            snapshots = data.get('snapshots', {})
            
            print(f"✅ 成功获取数据")
            print(f"📥 期权数量: {len(snapshots)}")
            
            # 检查是否有分页
            if 'next_page_token' in data:
                print(f"📄 有更多数据: next_page_token存在")
            else:
                print(f"📄 没有更多数据")
            
            # 分析数据质量
            greeks_count = 0
            bid_ask_count = 0
            trade_count = 0
            iv_count = 0
            
            # 保存样本数据
            samples = []
            
            for symbol, snapshot in snapshots.items():
                has_greeks = 'greeks' in snapshot and snapshot['greeks']
                has_quote = 'latest_quote' in snapshot and snapshot['latest_quote']
                has_trade = 'latest_trade' in snapshot and snapshot['latest_trade']
                has_iv = 'implied_volatility' in snapshot and snapshot['implied_volatility']
                
                if has_greeks:
                    greeks_count += 1
                if has_quote:
                    bid_ask_count += 1
                if has_trade:
                    trade_count += 1
                if has_iv:
                    iv_count += 1
                
                # 保存前3个有完整数据的样本
                if len(samples) < 3 and (has_greeks or has_quote):
                    sample = {
                        'symbol': symbol,
                        'has_greeks': has_greeks,
                        'has_quote': has_quote,
                        'has_trade': has_trade,
                        'has_iv': has_iv,
                        'data': snapshot
                    }
                    samples.append(sample)
            
            print(f"\n📊 数据质量统计:")
            print(f"   Greeks: {greeks_count}/{len(snapshots)} ({greeks_count/len(snapshots)*100:.1f}%)")
            print(f"   Bid/Ask: {bid_ask_count}/{len(snapshots)} ({bid_ask_count/len(snapshots)*100:.1f}%)")
            print(f"   交易: {trade_count}/{len(snapshots)} ({trade_count/len(snapshots)*100:.1f}%)")
            print(f"   IV: {iv_count}/{len(snapshots)} ({iv_count/len(snapshots)*100:.1f}%)")
            
            # 显示样本数据
            print(f"\n📋 样本数据分析:")
            for i, sample in enumerate(samples, 1):
                print(f"\n   📄 样本{i}: {sample['symbol']}")
                print(f"      Greeks: {'✅' if sample['has_greeks'] else '❌'}")
                print(f"      Bid/Ask: {'✅' if sample['has_quote'] else '❌'}")
                print(f"      交易: {'✅' if sample['has_trade'] else '❌'}")
                print(f"      IV: {'✅' if sample['has_iv'] else '❌'}")
                
                # 显示具体数据
                if sample['has_greeks']:
                    greeks = sample['data']['greeks']
                    print(f"      Delta: {greeks.get('delta', 'N/A')}")
                    print(f"      Gamma: {greeks.get('gamma', 'N/A')}")
                    print(f"      Theta: {greeks.get('theta', 'N/A')}")
                
                if sample['has_quote']:
                    quote = sample['data']['latest_quote']
                    bid = quote.get('bid_price', 0)
                    ask = quote.get('ask_price', 0)
                    print(f"      Bid: ${bid}")
                    print(f"      Ask: ${ask}")
                
                if sample['has_iv']:
                    iv = sample['data']['implied_volatility']
                    print(f"      IV: {iv:.4f} ({iv*100:.2f}%)")
            
            # 寻找特定期权
            target_option = "SPY250604C00596000"
            if target_option in snapshots:
                print(f"\n🎯 目标期权分析: {target_option}")
                target_data = snapshots[target_option]
                
                if 'greeks' in target_data and target_data['greeks']:
                    greeks = target_data['greeks']
                    print(f"   ✅ Greeks数据:")
                    print(f"      Delta: {greeks.get('delta')}")
                    print(f"      Gamma: {greeks.get('gamma')}")
                    print(f"      Theta: {greeks.get('theta')}")
                    print(f"      Vega: {greeks.get('vega')}")
                    print(f"      Rho: {greeks.get('rho')}")
                
                if 'latest_quote' in target_data and target_data['latest_quote']:
                    quote = target_data['latest_quote']
                    print(f"   ✅ 报价数据:")
                    print(f"      Bid: ${quote.get('bid_price', 0)}")
                    print(f"      Ask: ${quote.get('ask_price', 0)}")
                else:
                    print(f"   ❌ 无报价数据")
            else:
                print(f"\n⚠️ 未找到目标期权: {target_option}")
                print(f"   可用期权示例: {list(snapshots.keys())[:5]}")
            
        else:
            print(f"❌ API调用失败: {response.status_code}")
            print(f"错误信息: {response.text}")
    
    except Exception as e:
        print(f"❌ 请求失败: {e}")
    
    print("\n✅ API格式测试完成")


if __name__ == "__main__":
    test_new_api_format() 