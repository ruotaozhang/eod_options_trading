#!/usr/bin/env python3
"""
测试1000个期权的批量请求
验证是否可以突破之前发现的100个限制
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


def test_large_batch():
    """测试1000个期权的批量请求"""
    
    print("🔍 测试1000个期权的批量请求")
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
    
    # 获取期权链
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
        
        if len(option_symbols) < 1000:
            print(f"⚠️ 只有{len(option_symbols)}个期权，小于1000个")
            test_symbols = option_symbols
        else:
            test_symbols = option_symbols[:1000]
            
    except Exception as e:
        print(f"❌ 获取期权链失败: {e}")
        return
    
    # 测试大批量请求
    test_sizes = [500, 1000, 1500, 2000]
    
    for test_size in test_sizes:
        if test_size > len(option_symbols):
            print(f"\n📏 测试大小{test_size}: 超过可用期权数量({len(option_symbols)})，跳过")
            continue
            
        current_test_symbols = option_symbols[:test_size]
        
        print(f"\n🔬 测试批量大小: {test_size}")
        print(f"   期权数量: {len(current_test_symbols)}")
        print(f"   示例: {current_test_symbols[:3]}...{current_test_symbols[-3:]}")
        
        try:
            start_time = time.time()
            
            # 创建快照请求
            request = OptionSnapshotRequest(symbol_or_symbols=current_test_symbols)
            
            # 获取快照数据
            snapshot_data = option_client.get_option_snapshot(request)
            
            end_time = time.time()
            request_time = end_time - start_time
            
            if isinstance(snapshot_data, dict):
                received_count = len(snapshot_data)
                success_rate = received_count / test_size * 100
                
                print(f"   ✅ 成功!")
                print(f"   📊 请求数量: {test_size}")
                print(f"   📥 返回数量: {received_count}")
                print(f"   📈 成功率: {success_rate:.1f}%")
                print(f"   ⏱️  请求时间: {request_time:.2f}秒")
                print(f"   🚀 平均速度: {received_count/request_time:.1f}个/秒")
                
                # 检查一些示例数据
                sample_count = 0
                greeks_count = 0
                for key, snapshot in snapshot_data.items():
                    sample_count += 1
                    if hasattr(snapshot, 'greeks') and snapshot.greeks:
                        greeks_count += 1
                    if sample_count >= 10:  # 只检查前10个
                        break
                
                print(f"   📊 样本检查 (前10个): {greeks_count}/{sample_count} 有Greeks数据")
                
            else:
                print(f"   ❌ 返回数据格式异常: {type(snapshot_data)}")
                
        except Exception as e:
            print(f"   ❌ 失败: {e}")
            error_msg = str(e).lower()
            if "limit" in error_msg:
                print(f"   🚫 批量大小{test_size}超出API限制")
                if "100" in str(e):
                    print(f"   📏 API仍然限制为100个")
                elif "symbol limit" in error_msg:
                    print(f"   📏 遇到符号数量限制")
                break
            elif "rate" in error_msg:
                print(f"   ⏳ 可能遇到限速，等待5秒后继续...")
                time.sleep(5)
            elif "timeout" in error_msg:
                print(f"   ⏰ 请求超时，可能是批量太大")
                break
        
        # 防止限速
        time.sleep(1)
    
    print("\n✅ 大批量测试完成")


if __name__ == "__main__":
    test_large_batch() 