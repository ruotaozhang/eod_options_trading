#!/usr/bin/env python3
"""
测试期权快照API的批量限制
测试不同批量大小的请求，找出每批最多可以请求多少个期权合约
"""

import os
import sys
from datetime import datetime, date
from dotenv import load_dotenv
import time

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


def test_batch_limits():
    """测试期权快照API的批量限制"""
    
    print("🔍 测试期权快照API批量限制")
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
    
    # 首先获取期权链来获得大量期权符号
    print("\n📊 获取SPY期权链...")
    try:
        request = OptionChainRequest(underlying_symbol="SPY")
        option_chain = option_client.get_option_chain(request)
        
        # 提取期权符号
        option_symbols = []
        if hasattr(option_chain, '__iter__'):
            for item in option_chain:
                if isinstance(item, str):
                    option_symbols.append(item)
                elif hasattr(item, 'symbol'):
                    option_symbols.append(item.symbol)
                elif isinstance(item, dict) and 'symbol' in item:
                    option_symbols.append(item['symbol'])
        
        print(f"✅ 获取到{len(option_symbols)}个期权符号")
        
        # 只测试6月4日到期的期权
        june4_options = [symbol for symbol in option_symbols if "250604" in symbol]
        print(f"📅 6月4日到期的期权: {len(june4_options)}个")
        
        if len(june4_options) < 10:
            print("❌ 6月4日期权数量太少，无法进行批量测试")
            return
            
    except Exception as e:
        print(f"❌ 获取期权链失败: {e}")
        return
    
    # 测试不同的批量大小
    batch_sizes = [10, 25, 50, 100, 150, 200, 250, 300, 500]
    
    print(f"\n🧪 测试不同批量大小:")
    print("-" * 60)
    
    successful_batches = []
    
    for batch_size in batch_sizes:
        if batch_size > len(june4_options):
            print(f"📏 批量大小{batch_size}: 超过可用期权数量({len(june4_options)})，跳过")
            continue
            
        test_symbols = june4_options[:batch_size]
        
        print(f"\n🔬 测试批量大小: {batch_size}")
        print(f"   期权合约: {test_symbols[:3]}...{test_symbols[-3:] if len(test_symbols) > 6 else test_symbols[3:]}")
        
        try:
            start_time = time.time()
            
            # 创建快照请求
            request = OptionSnapshotRequest(symbol_or_symbols=test_symbols)
            
            # 获取快照数据
            snapshot_data = option_client.get_option_snapshot(request)
            
            end_time = time.time()
            request_time = end_time - start_time
            
            if isinstance(snapshot_data, dict):
                received_count = len(snapshot_data)
                success_rate = received_count / batch_size * 100
                
                print(f"   ✅ 成功!")
                print(f"   📊 请求数量: {batch_size}")
                print(f"   📥 返回数量: {received_count}")
                print(f"   📈 成功率: {success_rate:.1f}%")
                print(f"   ⏱️  请求时间: {request_time:.2f}秒")
                print(f"   🚀 平均速度: {received_count/request_time:.1f}个/秒")
                
                successful_batches.append({
                    'batch_size': batch_size,
                    'received_count': received_count,
                    'success_rate': success_rate,
                    'request_time': request_time,
                    'speed': received_count/request_time
                })
                
                # 显示一些示例数据
                sample_keys = list(snapshot_data.keys())[:3]
                for key in sample_keys:
                    snapshot = snapshot_data[key]
                    if hasattr(snapshot, 'greeks') and snapshot.greeks:
                        print(f"      📄 {key}: Delta={snapshot.greeks.delta:.4f}")
                    else:
                        print(f"      📄 {key}: 无Greeks数据")
            else:
                print(f"   ❌ 返回数据格式异常: {type(snapshot_data)}")
                
        except Exception as e:
            print(f"   ❌ 失败: {e}")
            if "too many" in str(e).lower() or "limit" in str(e).lower():
                print(f"   🚫 批量大小{batch_size}超出API限制")
                break
            elif "rate" in str(e).lower():
                print(f"   ⏳ 可能遇到限速，等待5秒后继续...")
                time.sleep(5)
        
        # 防止限速
        time.sleep(0.5)
    
    # 总结结果
    print(f"\n" + "="*60)
    print("📊 批量测试结果总结:")
    print("-" * 60)
    
    if successful_batches:
        print(f"{'批量大小':>8} {'返回数量':>8} {'成功率':>8} {'时间(秒)':>10} {'速度(个/秒)':>12}")
        print("-" * 60)
        
        for result in successful_batches:
            print(f"{result['batch_size']:>8} {result['received_count']:>8} "
                  f"{result['success_rate']:>7.1f}% {result['request_time']:>9.2f} "
                  f"{result['speed']:>11.1f}")
        
        max_successful = max(successful_batches, key=lambda x: x['batch_size'])
        fastest = max(successful_batches, key=lambda x: x['speed'])
        
        print(f"\n🏆 最大成功批量: {max_successful['batch_size']}个")
        print(f"🚀 最快速度: {fastest['speed']:.1f}个/秒 (批量大小: {fastest['batch_size']})")
        
        # 推荐的批量大小
        if len(successful_batches) > 1:
            # 选择成功率高且速度快的批量大小
            good_batches = [b for b in successful_batches if b['success_rate'] >= 95]
            if good_batches:
                recommended = max(good_batches, key=lambda x: x['speed'])
                print(f"💡 推荐批量大小: {recommended['batch_size']}个 (成功率{recommended['success_rate']:.1f}%, 速度{recommended['speed']:.1f}个/秒)")
    else:
        print("❌ 没有成功的批量请求")
    
    print("\n✅ 批量限制测试完成")


if __name__ == "__main__":
    test_batch_limits() 