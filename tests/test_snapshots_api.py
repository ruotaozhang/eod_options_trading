"""
精确测试Alpaca option snapshots API
根据官方文档测试不同的参数组合
"""

import requests
import os
import sys
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config import config
from src.data.market_data import MarketDataProvider

def test_snapshots_api_direct():
    """直接测试snapshots API，尝试不同的参数组合"""
    
    headers = {
        'APCA-API-KEY-ID': config.alpaca_api_key,
        'APCA-API-SECRET-KEY': config.alpaca_secret_key,
        'accept': 'application/json'
    }
    
    # 获取当前SPY价格
    market_data = MarketDataProvider(config)
    current_price = market_data.get_current_price("SPY")
    print(f"📊 当前SPY价格: ${current_price:.2f}")
    
    # 生成期权代码
    today = datetime.now()
    date_str = today.strftime("%y%m%d")
    strike = int(current_price)  # 当前价格的整数部分
    
    option_symbol = f"SPY{date_str}C{strike*1000:08d}"
    print(f"🎯 测试期权代码: {option_symbol}")
    
    # 测试不同的feed类型
    feed_types = ['indicative', 'sip', 'otc']
    
    for feed in feed_types:
        print(f"\n🔍 测试feed={feed}:")
        print("-" * 40)
        
        url = 'https://data.alpaca.markets/v1beta1/options/snapshots'
        params = {
            'symbols': option_symbol,
            'feed': feed
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"原始响应: {data}")
                
                if 'snapshots' in data and option_symbol in data['snapshots']:
                    snapshot = data['snapshots'][option_symbol]
                    
                    print(f"✅ 找到数据:")
                    
                    # 最新报价
                    if 'latest_quote' in snapshot and snapshot['latest_quote']:
                        quote = snapshot['latest_quote']
                        print(f"   📈 最新报价:")
                        print(f"      买价: ${quote.get('bid_price', 0):.4f}")
                        print(f"      卖价: ${quote.get('ask_price', 0):.4f}")
                        print(f"      买量: {quote.get('bid_size', 0)}")
                        print(f"      卖量: {quote.get('ask_size', 0)}")
                        print(f"      时间: {quote.get('timestamp', 'N/A')}")
                    
                    # 最新交易
                    if 'latest_trade' in snapshot and snapshot['latest_trade']:
                        trade = snapshot['latest_trade']
                        print(f"   💰 最新交易:")
                        print(f"      价格: ${trade.get('price', 0):.4f}")
                        print(f"      数量: {trade.get('size', 0)}")
                        print(f"      时间: {trade.get('timestamp', 'N/A')}")
                        print(f"      交易所: {trade.get('exchange', 'N/A')}")
                    
                    # Greeks
                    if 'greeks' in snapshot and snapshot['greeks']:
                        greeks = snapshot['greeks']
                        print(f"   🔬 Greeks:")
                        print(f"      Delta: {greeks.get('delta', 0):.4f}")
                        print(f"      Gamma: {greeks.get('gamma', 0):.4f}")
                        print(f"      Theta: {greeks.get('theta', 0):.4f}")
                        print(f"      Vega: {greeks.get('vega', 0):.4f}")
                        print(f"      Rho: {greeks.get('rho', 0):.4f}")
                    
                    # 隐含波动率
                    if 'implied_volatility' in snapshot:
                        print(f"   📊 隐含波动率: {snapshot['implied_volatility']:.4f}")
                    
                else:
                    print(f"❌ 未找到期权数据")
                    print(f"可用的symbols: {list(data.get('snapshots', {}).keys())[:5]}")
                    
            else:
                print(f"❌ API错误 ({response.status_code}): {response.text}")
                
        except Exception as e:
            print(f"❌ 异常: {e}")

def test_alternative_symbols():
    """测试其他可能的期权代码格式"""
    
    headers = {
        'APCA-API-KEY-ID': config.alpaca_api_key,
        'APCA-API-SECRET-KEY': config.alpaca_secret_key,
        'accept': 'application/json'
    }
    
    print(f"\n🔄 测试替代期权代码格式:")
    print("=" * 50)
    
    # 从期权链API获取一些实际存在的期权代码
    url = 'https://data.alpaca.markets/v1beta1/options/snapshots/SPY'
    params = {
        'feed': 'indicative',
        'limit': 20
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            snapshots = data.get('snapshots', {})
            
            print(f"✅ 从期权链获取到 {len(snapshots)} 个期权")
            
            # 找到今日到期且接近当前价格的期权
            today = datetime.now().strftime("%y%m%d")
            current_price = 598.6  # 大概的SPY价格
            
            relevant_options = []
            for symbol, snapshot in snapshots.items():
                if today in symbol:
                    try:
                        # 解析行权价
                        strike_str = symbol[-8:]
                        strike = int(strike_str) / 1000.0
                        
                        # 选择接近当前价格的期权
                        if abs(strike - current_price) <= 5:
                            quote = snapshot.get('latest_quote', {})
                            bid = quote.get('bid_price', 0)
                            ask = quote.get('ask_price', 0)
                            
                            relevant_options.append({
                                'symbol': symbol,
                                'strike': strike,
                                'bid': bid,
                                'ask': ask,
                                'has_quotes': bid > 0 or ask > 0
                            })
                    except:
                        continue
            
            # 排序并显示
            relevant_options.sort(key=lambda x: abs(x['strike'] - current_price))
            
            print(f"\n📋 找到 {len(relevant_options)} 个相关期权:")
            for i, opt in enumerate(relevant_options[:10]):
                status = "✅有报价" if opt['has_quotes'] else "❌无报价"
                option_type = "C" if "C" in opt['symbol'] else "P"
                print(f"{i+1:2d}. {opt['symbol']} ({option_type}{opt['strike']:.0f}) - Bid:${opt['bid']:.4f} Ask:${opt['ask']:.4f} {status}")
                
        else:
            print(f"❌ 获取期权链失败: {response.text}")
            
    except Exception as e:
        print(f"❌ 异常: {e}")

if __name__ == "__main__":
    print("🧪 精确测试Alpaca Option Snapshots API")
    print("=" * 60)
    
    test_snapshots_api_direct()
    test_alternative_symbols() 