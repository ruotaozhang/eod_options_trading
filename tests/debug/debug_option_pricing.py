"""
调试期权代码和定价问题
"""

import requests
import os
import sys
from datetime import datetime

# 添加项目根目录到Python路径
import pathlib
project_root = pathlib.Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.config import config
from src.data.market_data import MarketDataProvider

def test_option_symbols():
    """测试不同的期权代码格式"""
    
    headers = {
        'APCA-API-KEY-ID': config.alpaca_api_key,
        'APCA-API-SECRET-KEY': config.alpaca_secret_key,
        'accept': 'application/json'
    }
    
    # 获取当前SPY价格
    market_data = MarketDataProvider(config)
    current_price = market_data.get_current_price("SPY")
    print(f"📊 当前SPY价格: ${current_price:.2f}")
    
    # 测试不同的期权代码格式
    today = datetime.now()
    date_str = today.strftime("%y%m%d")
    
    symbols_to_test = [
        f'SPY{date_str}C00598000',   # 我们当前的格式
        f'SPY{date_str}C598',        # 简化格式
        f'SPY {date_str}C598',       # 带空格
        f'SPY{date_str}C00599000',   # $599行权价
        f'SPY{date_str}C00600000',   # $600行权价
    ]
    
    print(f"\n🔍 测试期权代码格式 (日期: {date_str}):")
    print("=" * 60)
    
    for symbol in symbols_to_test:
        print(f"\n测试: {symbol}")
        url = 'https://data.alpaca.markets/v1beta1/options/snapshots'
        params = {'symbols': symbol, 'feed': 'indicative'}
        
        try:
            response = requests.get(url, headers=headers, params=params)
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if 'snapshots' in data and symbol in data['snapshots']:
                    snapshot = data['snapshots'][symbol]
                    quote = snapshot.get('latest_quote', {})
                    trade = snapshot.get('latest_trade', {})
                    greeks = snapshot.get('greeks', {})
                    
                    print(f"✅ 找到数据:")
                    print(f"   买价: ${quote.get('bid_price', 0):.2f}")
                    print(f"   卖价: ${quote.get('ask_price', 0):.2f}")
                    print(f"   最新价: ${trade.get('price', 0):.2f}")
                    print(f"   Delta: {greeks.get('delta', 0):.3f}")
                    print(f"   IV: {snapshot.get('implied_volatility', 0):.2%}")
                else:
                    print(f"❌ 未找到数据: {data}")
            else:
                print(f"❌ API错误: {response.text}")
                
        except Exception as e:
            print(f"❌ 异常: {e}")

def test_option_chain_api():
    """测试期权链API"""
    print(f"\n🔗 测试期权链API:")
    print("=" * 40)
    
    headers = {
        'APCA-API-KEY-ID': config.alpaca_api_key,
        'APCA-API-SECRET-KEY': config.alpaca_secret_key,
        'accept': 'application/json'
    }
    
    url = 'https://data.alpaca.markets/v1beta1/options/snapshots/SPY'
    params = {
        'feed': 'indicative',
        'limit': 10
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if 'snapshots' in data:
                print(f"✅ 找到 {len(data['snapshots'])} 个期权合约")
                
                # 显示前几个合约
                for symbol, snapshot in list(data['snapshots'].items())[:5]:
                    quote = snapshot.get('latest_quote', {})
                    trade = snapshot.get('latest_trade', {})
                    
                    print(f"\n合约: {symbol}")
                    print(f"   买价: ${quote.get('bid_price', 0):.2f}")
                    print(f"   卖价: ${quote.get('ask_price', 0):.2f}")
                    print(f"   最新价: ${trade.get('price', 0):.2f}")
            else:
                print(f"❌ 无期权数据: {data}")
        else:
            print(f"❌ API错误: {response.text}")
            
    except Exception as e:
        print(f"❌ 异常: {e}")

if __name__ == "__main__":
    print("🐛 期权代码和定价调试")
    print("=" * 50)
    
    test_option_symbols()
    test_option_chain_api() 