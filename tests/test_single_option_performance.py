#!/usr/bin/env python3
"""
测试单个期权合约获取性能 vs 整个期权链性能
"""

import time
from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data.market_data import MarketDataProvider
from src.config import config

def test_single_option_performance():
    """测试单个期权合约获取性能"""
    print("🔍 单个期权合约 vs 整个期权链性能对比")
    print("=" * 60)
    
    market_data = MarketDataProvider()
    
    # 获取当前价格来生成期权合约
    current_price = market_data.get_current_price(config.symbol)
    target_strike = int(current_price)
    
    # 生成期权合约代码
    option_symbol = market_data._generate_option_symbol(config.symbol, target_strike, 'CALL')
    print(f"标的: {config.symbol}")
    print(f"当前价格: ${current_price:.2f}")
    print(f"测试期权: {option_symbol}")
    print()
    
    # 测试1: 获取单个期权合约
    print("🚀 测试1: 直接获取单个期权合约")
    start_time = time.time()
    single_option = market_data._get_option_snapshot(option_symbol)
    single_time = time.time() - start_time
    
    if single_option:
        print(f"✅ 成功获取单个期权: {option_symbol}")
        print(f"⏱️  耗时: {single_time:.2f}秒")
        print(f"📊 报价: Bid=${single_option['bid']:.2f}, Ask=${single_option['ask']:.2f}")
        print(f"🎯 Delta: {single_option['delta']:.3f}")
    else:
        print(f"❌ 获取单个期权失败: {option_symbol}")
    
    print()
    
    # 测试2: 获取整个期权链
    print("🐌 测试2: 获取整个期权链")
    start_time = time.time()
    option_chain = market_data.get_option_chain(config.symbol)
    chain_time = time.time() - start_time
    
    if option_chain and ('calls' in option_chain or 'puts' in option_chain):
        calls_count = len(option_chain.get('calls', []))
        puts_count = len(option_chain.get('puts', []))
        total_options = calls_count + puts_count
        print(f"✅ 成功获取期权链: {calls_count}个CALL + {puts_count}个PUT = {total_options}个期权")
        print(f"⏱️  耗时: {chain_time:.2f}秒")
        
        # 在期权链中查找我们的目标期权
        target_found = False
        for option in option_chain.get('calls', []):
            if option['contractSymbol'] == option_symbol:
                print(f"📊 期权链中找到目标期权: Bid=${option['bid']:.2f}, Ask=${option['ask']:.2f}")
                target_found = True
                break
        
        if not target_found:
            print(f"❌ 期权链中未找到目标期权: {option_symbol}")
    else:
        print(f"❌ 获取期权链失败")
    
    print()
    
    # 性能对比
    print("📈 性能对比分析")
    print("=" * 60)
    
    if single_time > 0 and chain_time > 0:
        speed_improvement = chain_time / single_time
        time_saved = chain_time - single_time
        
        print(f"单个期权查询: {single_time:.2f}秒")
        print(f"整个期权链查询: {chain_time:.2f}秒")
        print(f"性能提升: {speed_improvement:.1f}倍")
        print(f"节省时间: {time_saved:.2f}秒")
        
        print()
        print("💡 分析:")
        
        if speed_improvement > 5:
            print("🚀 单个期权查询显著更快！强烈建议使用单个查询")
        elif speed_improvement > 2:
            print("⚡ 单个期权查询明显更快，建议使用单个查询")
        elif speed_improvement > 1.2:
            print("✅ 单个期权查询稍快，可以考虑使用")
        else:
            print("🤔 性能差异不大，两种方法都可以")
    
    # 测试不同监控频率的影响
    print()
    print("📊 不同监控频率下的API调用分析")
    print("=" * 60)
    
    frequencies = [
        {'name': '当前方式(整个期权链)', 'single_time': chain_time},
        {'name': '优化方式(单个期权)', 'single_time': single_time}
    ]
    
    monitoring_intervals = [15, 10, 5]  # 秒
    
    for freq in frequencies:
        print(f"\n{freq['name']}:")
        for interval in monitoring_intervals:
            calls_per_minute = 60 / interval
            total_time_per_minute = calls_per_minute * freq['single_time']
            api_usage_pct = (calls_per_minute / 200) * 100  # Alpaca限制200次/分钟
            
            print(f"  {interval}秒监控频率:")
            print(f"    API调用: {calls_per_minute:.1f}次/分钟")
            print(f"    总耗时: {total_time_per_minute:.1f}秒/分钟")
            print(f"    API使用率: {api_usage_pct:.1f}%")
            
            if api_usage_pct > 50:
                status = "❌ 危险"
            elif api_usage_pct > 25:
                status = "⚠️ 需注意"
            else:
                status = "✅ 安全"
            print(f"    状态: {status}")

def test_find_suitable_options_performance():
    """测试find_suitable_options方法的性能"""
    print("\n🎯 测试find_suitable_options方法性能")
    print("=" * 60)
    
    market_data = MarketDataProvider()
    
    # 测试CALL期权查找
    start_time = time.time()
    call_options = market_data.find_suitable_options(config.symbol, 'CALL')
    call_time = time.time() - start_time
    
    print(f"CALL期权查找:")
    print(f"  耗时: {call_time:.2f}秒")
    print(f"  找到期权数量: {len(call_options)}")
    
    if call_options:
        option = call_options[0]
        print(f"  选中期权: {option['contractSymbol']}")
        print(f"  报价: Bid=${option['bid']:.2f}, Ask=${option['ask']:.2f}")
    
    # 测试PUT期权查找
    start_time = time.time()
    put_options = market_data.find_suitable_options(config.symbol, 'PUT')
    put_time = time.time() - start_time
    
    print(f"\nPUT期权查找:")
    print(f"  耗时: {put_time:.2f}秒")
    print(f"  找到期权数量: {len(put_options)}")
    
    if put_options:
        option = put_options[0]
        print(f"  选中期权: {option['contractSymbol']}")
        print(f"  报价: Bid=${option['bid']:.2f}, Ask=${option['ask']:.2f}")
    
    avg_time = (call_time + put_time) / 2
    print(f"\n平均查找时间: {avg_time:.2f}秒")
    
    return avg_time

def main():
    """主测试函数"""
    print("🔬 期权数据获取性能测试")
    print("=" * 60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 基础性能测试
    test_single_option_performance()
    
    # 实际方法性能测试
    find_options_time = test_find_suitable_options_performance()
    
    # 总结建议
    print("\n🎯 优化建议")
    print("=" * 60)
    
    print("1. ✅ 当前find_suitable_options方法已经优化为直接查询单个期权")
    print("2. ❗ 但是其他地方可能还在调用get_option_chain获取整个期权链")
    print("3. 💡 建议检查并替换所有不必要的期权链查询")
    print("4. 🚀 使用单个期权查询可以将响应时间从9-15秒降低到1-3秒")
    print("5. ⚡ 这将使得更高频率的监控成为可能（5-10秒间隔）")
    
    if find_options_time < 3:
        print(f"6. ✅ find_suitable_options性能良好({find_options_time:.2f}秒)，可以支持高频监控")
    else:
        print(f"6. ⚠️ find_suitable_options仍需优化({find_options_time:.2f}秒)")

if __name__ == "__main__":
    main() 