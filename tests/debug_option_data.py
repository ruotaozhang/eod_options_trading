#!/usr/bin/env python3
"""
期权数据调试脚本
检查Alpaca期权API返回的原始数据结构
"""

import sys
from pathlib import Path
import json
import requests
from datetime import datetime

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.config import config
from src.utils.logger_setup import setup_logger

def debug_raw_option_data():
    """调试原始期权数据"""
    print("🔍 调试Alpaca期权API原始数据...")
    
    try:
        # 直接调用Alpaca期权API
        url = f"https://data.alpaca.markets/v1beta1/options/snapshots/{config.symbol}"
        headers = {
            'APCA-API-KEY-ID': config.alpaca_api_key,
            'APCA-API-SECRET-KEY': config.alpaca_secret_key
        }
        
        print(f"📡 请求URL: {url}")
        response = requests.get(url, headers=headers)
        
        print(f"📊 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"📋 原始数据结构:")
            print(f"   - 数据键: {list(data.keys())}")
            
            snapshots = data.get('snapshots', {})
            print(f"   - 期权快照数量: {len(snapshots)}")
            
            # 分析前几个期权
            print(f"\n🔍 分析前5个期权合约:")
            for i, (symbol, snapshot) in enumerate(list(snapshots.items())[:5]):
                print(f"\n期权 {i+1}: {symbol}")
                print(f"   快照结构: {list(snapshot.keys())}")
                
                # 检查报价数据
                latest_quote = snapshot.get('latestQuote', {})
                if latest_quote:
                    print(f"   最新报价: {latest_quote}")
                else:
                    print(f"   ❌ 无最新报价数据")
                
                # 检查Greeks数据
                greeks = snapshot.get('greeks', {})
                if greeks:
                    print(f"   Greeks: {greeks}")
                else:
                    print(f"   ❌ 无Greeks数据")
                
                # 检查成交数据
                latest_trade = snapshot.get('latestTrade', {})
                if latest_trade:
                    print(f"   最新成交: {latest_trade}")
                else:
                    print(f"   ❌ 无最新成交数据")
            
            # 统计期权类型
            calls = []
            puts = []
            
            for symbol, snapshot in snapshots.items():
                if 'C' in symbol:
                    calls.append(symbol)
                elif 'P' in symbol:
                    puts.append(symbol)
            
            print(f"\n📊 期权统计:")
            print(f"   - 看涨期权: {len(calls)}")
            print(f"   - 看跌期权: {len(puts)}")
            
            # 显示部分看跌期权（如果有的话）
            if puts:
                print(f"\n📈 部分看跌期权:")
                for put in puts[:3]:
                    print(f"   - {put}")
            
            return True
            
        else:
            print(f"❌ API请求失败: {response.status_code}")
            print(f"   错误信息: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 调试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_option_filter_criteria():
    """检查期权过滤条件"""
    print(f"\n🎯 检查期权过滤条件...")
    
    from src.data.market_data import MarketDataProvider
    
    try:
        market_data = MarketDataProvider()
        chain = market_data.get_option_chain(config.symbol)
        
        if not chain:
            print("❌ 无法获取期权链")
            return False
        
        today = datetime.now().strftime('%Y-%m-%d')
        print(f"📅 今日日期: {today}")
        
        # 分析看涨期权
        calls = chain.get('calls', [])
        print(f"\n📈 看涨期权分析 (共{len(calls)}个):")
        
        today_calls = [c for c in calls if c['expiry'] == today]
        print(f"   - 今日到期: {len(today_calls)}")
        
        valid_delta_calls = [c for c in today_calls if c.get('delta', 0) != 0]
        print(f"   - 有效Delta: {len(valid_delta_calls)}")
        
        if valid_delta_calls:
            print(f"   - Delta范围: {min(c['delta'] for c in valid_delta_calls):.3f} ~ {max(c['delta'] for c in valid_delta_calls):.3f}")
        
        # 显示所有今日到期的期权（无论Delta如何）
        print(f"\n📋 今日到期的期权 (前10个):")
        for i, option in enumerate(today_calls[:10]):
            print(f"   {i+1}. {option['contractSymbol']}: 行权价${option['strike']:.0f}, "
                  f"Delta={option['delta']:.3f}, 买价${option['bid']:.2f}")
        
        # 分析看跌期权
        puts = chain.get('puts', [])
        print(f"\n📉 看跌期权分析 (共{len(puts)}个):")
        
        today_puts = [p for p in puts if p['expiry'] == today]
        print(f"   - 今日到期: {len(today_puts)}")
        
        valid_delta_puts = [p for p in today_puts if p.get('delta', 0) != 0]
        print(f"   - 有效Delta: {len(valid_delta_puts)}")
        
        if valid_delta_puts:
            print(f"   - Delta范围: {min(p['delta'] for p in valid_delta_puts):.3f} ~ {max(p['delta'] for p in valid_delta_puts):.3f}")
        
        return True
        
    except Exception as e:
        print(f"❌ 检查过滤条件失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("🛠️ 期权数据调试工具")
    print("=" * 50)
    
    setup_logger()
    
    # 调试原始数据
    debug_raw_option_data()
    
    # 检查过滤条件
    check_option_filter_criteria()

if __name__ == "__main__":
    main() 