"""
检查可用的期权合约和行权价
"""

import requests
import os
import sys
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
import pathlib
project_root = pathlib.Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.config import config
from src.data.market_data import MarketDataProvider

def check_available_options():
    """检查可用的期权合约"""
    
    headers = {
        'APCA-API-KEY-ID': config.alpaca_api_key,
        'APCA-API-SECRET-KEY': config.alpaca_secret_key,
        'accept': 'application/json'
    }
    
    # 获取当前SPY价格
    market_data = MarketDataProvider(config)
    current_price = market_data.get_current_price("SPY")
    print(f"📊 当前SPY价格: ${current_price:.2f}")
    
    # 检查当日期权
    today = datetime.now()
    print(f"📅 当前时间: {today.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 检查当日和明日的期权
    dates_to_check = [
        today,  # 今日
        today + timedelta(days=1),  # 明日
        today + timedelta(days=7),  # 下周
    ]
    
    for date in dates_to_check:
        date_str = date.strftime("%y%m%d")
        print(f"\n🔍 检查 {date.strftime('%Y-%m-%d')} ({date_str}) 的期权:")
        print("=" * 60)
        
        # 获取期权链
        url = 'https://data.alpaca.markets/v1beta1/options/snapshots/SPY'
        params = {
            'feed': 'indicative',
            'limit': 1000  # 获取更多数据
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                snapshots = data.get('snapshots', {})
                
                # 过滤出指定日期的期权
                date_options = {}
                for symbol, snapshot in snapshots.items():
                    if date_str in symbol:
                        date_options[symbol] = snapshot
                
                if date_options:
                    print(f"✅ 找到 {len(date_options)} 个期权合约")
                    
                    # 解析并排序期权
                    calls_with_prices = []
                    puts_with_prices = []
                    
                    for symbol, snapshot in date_options.items():
                        try:
                            # 解析行权价
                            strike_str = symbol[-8:]  # 最后8位是行权价
                            strike = int(strike_str) / 1000.0
                            
                            quote = snapshot.get('latest_quote', {})
                            trade = snapshot.get('latest_trade', {})
                            greeks = snapshot.get('greeks', {})
                            
                            bid = quote.get('bid_price', 0)
                            ask = quote.get('ask_price', 0)
                            last = trade.get('price', 0)
                            delta = greeks.get('delta', 0)
                            
                            option_data = {
                                'symbol': symbol,
                                'strike': strike,
                                'bid': bid,
                                'ask': ask,
                                'last': last,
                                'delta': delta,
                                'has_price': bid > 0 or ask > 0 or last > 0
                            }
                            
                            if 'C' in symbol:
                                calls_with_prices.append(option_data)
                            else:
                                puts_with_prices.append(option_data)
                                
                        except:
                            continue
                    
                    # 排序并显示
                    calls_with_prices.sort(key=lambda x: x['strike'])
                    puts_with_prices.sort(key=lambda x: x['strike'])
                    
                    # 找到当前价格附近的期权
                    print(f"\n📈 Call期权 (当前价格附近):")
                    relevant_calls = [c for c in calls_with_prices 
                                    if abs(c['strike'] - current_price) <= 10]
                    
                    if relevant_calls:
                        for call in relevant_calls[:10]:
                            status = "✅有价格" if call['has_price'] else "❌无价格"
                            moneyness = "ITM" if call['strike'] < current_price else "OTM"
                            print(f"   ${call['strike']:3.0f} {moneyness} - Bid:${call['bid']:.2f} Ask:${call['ask']:.2f} Last:${call['last']:.2f} {status}")
                    else:
                        print("   ❌ 没有找到当前价格附近的Call期权")
                    
                    print(f"\n📉 Put期权 (当前价格附近):")
                    relevant_puts = [p for p in puts_with_prices 
                                   if abs(p['strike'] - current_price) <= 10]
                    
                    if relevant_puts:
                        for put in relevant_puts[:10]:
                            status = "✅有价格" if put['has_price'] else "❌无价格"
                            moneyness = "ITM" if put['strike'] > current_price else "OTM"
                            print(f"   ${put['strike']:3.0f} {moneyness} - Bid:${put['bid']:.2f} Ask:${put['ask']:.2f} Last:${put['last']:.2f} {status}")
                    else:
                        print("   ❌ 没有找到当前价格附近的Put期权")
                    
                    # 统计有价格的期权
                    calls_with_real_prices = [c for c in calls_with_prices if c['has_price']]
                    puts_with_real_prices = [p for p in puts_with_prices if p['has_price']]
                    
                    print(f"\n📊 总结:")
                    print(f"   Call期权总数: {len(calls_with_prices)}, 有价格: {len(calls_with_real_prices)}")
                    print(f"   Put期权总数: {len(puts_with_prices)}, 有价格: {len(puts_with_real_prices)}")
                    
                else:
                    print(f"❌ 没有找到 {date.strftime('%Y-%m-%d')} 的期权")
            else:
                print(f"❌ API错误: {response.text}")
                
        except Exception as e:
            print(f"❌ 异常: {e}")

if __name__ == "__main__":
    print("🔍 检查可用期权合约")
    print("=" * 50)
    
    check_available_options() 