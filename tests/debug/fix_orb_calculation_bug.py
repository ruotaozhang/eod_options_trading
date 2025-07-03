#!/usr/bin/env python3
"""
修复ORB计算的bug
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from datetime import datetime, time, timedelta
from src.data.market_data import MarketDataProvider, TechnicalIndicators
from src.config import config, strategy_params
import pandas as pd

def debug_orb_calculation():
    """调试ORB计算逻辑"""
    print("🔍 调试ORB计算逻辑")
    print("=" * 50)
    
    try:
        # 初始化市场数据
        market_data = MarketDataProvider(config)
        
        # 获取SPY数据
        bars = market_data.get_current_bars("SPY", limit=200)
        print(f"✅ 获取到 {len(bars)} 条K线数据")
        
        if not bars.empty:
            print(f"数据时间范围: {bars['timestamp'].min()} 到 {bars['timestamp'].max()}")
            
            # 显示原始的ORB计算逻辑问题
            print("\n🚨 原始ORB计算逻辑问题:")
            market_open = bars['timestamp'].dt.time >= pd.Timestamp('09:30').time()
            orb_period_old = bars[market_open].head(15)  # 原始逻辑
            print(f"原始逻辑：开盘后数据 {len(bars[market_open])} 条，取前15条")
            
            if not orb_period_old.empty:
                print(f"原始ORB时间范围: {orb_period_old['timestamp'].min()} 到 {orb_period_old['timestamp'].max()}")
                old_result = {
                    'high': orb_period_old['high'].max(),
                    'low': orb_period_old['low'].min(),
                    'volume': orb_period_old['volume'].mean()
                }
                print(f"原始ORB结果: 高点=${old_result['high']:.2f}, 低点=${old_result['low']:.2f}")
            
            # 正确的ORB计算逻辑
            print("\n✅ 修复后的ORB计算逻辑:")
            today = datetime.now().date()
            market_open_time = datetime.combine(today, time(9, 30))
            orb_end_time = market_open_time + timedelta(minutes=15)
            
            # 筛选9:30-9:45的数据
            orb_period_new = bars[
                (bars['timestamp'] >= market_open_time) & 
                (bars['timestamp'] < orb_end_time)
            ]
            
            print(f"修复逻辑：9:30-9:45时间段内的数据 {len(orb_period_new)} 条")
            
            if not orb_period_new.empty:
                print(f"修复ORB时间范围: {orb_period_new['timestamp'].min()} 到 {orb_period_new['timestamp'].max()}")
                new_result = {
                    'high': orb_period_new['high'].max(),
                    'low': orb_period_new['low'].min(),
                    'volume': orb_period_new['volume'].mean()
                }
                print(f"修复ORB结果: 高点=${new_result['high']:.2f}, 低点=${new_result['low']:.2f}")
                
                # 比较差异
                if not orb_period_old.empty:
                    high_diff = abs(new_result['high'] - old_result['high'])
                    low_diff = abs(new_result['low'] - old_result['low'])
                    print(f"\n📊 差异分析:")
                    print(f"高点差异: ${high_diff:.2f}")
                    print(f"低点差异: ${low_diff:.2f}")
                    
                    if high_diff > 0.01 or low_diff > 0.01:
                        print("⚠️ 发现显著差异！这可能解释了信号问题。")
                    else:
                        print("✅ 差异很小，ORB计算不是主要问题。")
            else:
                print("❌ 无法找到9:30-9:45时段的数据")
                
        # 测试修复后的计算
        print("\n🔧 测试修复后的ORB计算函数:")
        fixed_orb = calculate_orb_levels_fixed(bars, 15)
        print(f"修复函数结果: {fixed_orb}")
        
    except Exception as e:
        print(f"❌ 调试失败: {e}")
        import traceback
        traceback.print_exc()

def calculate_orb_levels_fixed(df: pd.DataFrame, period_minutes: int = 15) -> dict:
    """修复后的ORB水平计算"""
    if df.empty:
        return {'high': 0, 'low': 0, 'volume': 0}
    
    # 使用正确的时间范围筛选
    today = datetime.now().date()
    market_open_time = datetime.combine(today, time(9, 30))
    orb_end_time = market_open_time + timedelta(minutes=period_minutes)
    
    # 筛选开盘后指定分钟内的数据
    orb_period = df[
        (df['timestamp'] >= market_open_time) & 
        (df['timestamp'] < orb_end_time)
    ]
    
    if orb_period.empty:
        # 如果当天数据不可用，使用最近的数据
        market_open_filter = df['timestamp'].dt.time >= pd.Timestamp('09:30').time()
        orb_period = df[market_open_filter].head(period_minutes)
        
        if orb_period.empty:
            return {'high': 0, 'low': 0, 'volume': 0}
    
    return {
        'high': orb_period['high'].max(),
        'low': orb_period['low'].min(),
        'volume': orb_period['volume'].mean()
    }

def create_fixed_market_data_file():
    """创建修复后的market_data.py文件内容"""
    print("\n📝 生成修复后的ORB计算代码:")
    
    fixed_code = '''
    @staticmethod
    def calculate_orb_levels(df: pd.DataFrame, period_minutes: int = 15) -> Dict[str, float]:
        """计算开盘区间突破水平 - 修复版"""
        if df.empty:
            return {'high': 0, 'low': 0, 'volume': 0}
        
        # 使用正确的时间范围筛选，而不是简单的head()
        try:
            today = datetime.now().date()
            market_open_time = datetime.combine(today, time(9, 30))
            orb_end_time = market_open_time + timedelta(minutes=period_minutes)
            
            # 筛选开盘后指定分钟内的数据
            orb_period = df[
                (df['timestamp'] >= market_open_time) & 
                (df['timestamp'] < orb_end_time)
            ]
            
            if orb_period.empty:
                # 后备方案：如果当天数据不可用，使用最近的数据
                market_open_filter = df['timestamp'].dt.time >= pd.Timestamp('09:30').time()
                orb_period = df[market_open_filter].head(period_minutes)
                
                if orb_period.empty:
                    return {'high': 0, 'low': 0, 'volume': 0}
            
            return {
                'high': orb_period['high'].max(),
                'low': orb_period['low'].min(),
                'volume': orb_period['volume'].mean()
            }
            
        except Exception as e:
            logger.error(f"ORB计算失败: {e}")
            return {'high': 0, 'low': 0, 'volume': 0}
    '''
    
    print(fixed_code)
    print("\n💡 这个修复应该解决ORB信号的问题！")

if __name__ == "__main__":
    debug_orb_calculation()
    create_fixed_market_data_file() 