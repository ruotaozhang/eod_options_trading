#!/usr/bin/env python3
"""
VWAP修复验证测试
验证修复后的VWAP计算是否正确处理跨日数据污染问题
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, time
import pytz

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data.market_data import TechnicalIndicators, MarketDataProvider
from src.config import config
from loguru import logger


def create_test_data():
    """创建测试数据：包含前一天和当天的数据"""
    et_tz = pytz.timezone('US/Eastern')
    
    # 创建前一天的数据 (周一)
    yesterday = datetime.now(et_tz) - timedelta(days=1)
    yesterday_start = et_tz.localize(datetime.combine(yesterday.date(), time(9, 30)))
    
    prev_day_data = []
    for i in range(390):  # 前一天9:30-16:00，390分钟
        timestamp = yesterday_start + timedelta(minutes=i)
        prev_day_data.append({
            'timestamp': timestamp.astimezone(pytz.UTC),  # 转换为UTC存储
            'open': 600.0 + np.random.normal(0, 0.5),
            'high': 601.0 + np.random.normal(0, 0.5),
            'low': 599.0 + np.random.normal(0, 0.5),
            'close': 600.0 + np.random.normal(0, 0.5),
            'volume': 1000 + np.random.randint(0, 500)
        })
    
    # 创建当天的数据 (周二) - 跳空低开
    today = datetime.now(et_tz)
    today_start = et_tz.localize(datetime.combine(today.date(), time(9, 30)))
    
    today_data = []
    for i in range(60):  # 当天开盘后60分钟
        timestamp = today_start + timedelta(minutes=i)
        today_data.append({
            'timestamp': timestamp.astimezone(pytz.UTC),  # 转换为UTC存储
            'open': 595.0 + np.random.normal(0, 0.3),  # 跳空低开到595
            'high': 596.0 + np.random.normal(0, 0.3),
            'low': 594.0 + np.random.normal(0, 0.3),
            'close': 595.0 + np.random.normal(0, 0.3),
            'volume': 1200 + np.random.randint(0, 300)
        })
    
    # 合并数据
    all_data = prev_day_data + today_data
    df = pd.DataFrame(all_data)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    return df


def test_original_vwap_calculation(df):
    """测试原始的VWAP计算（有跨日污染问题）"""
    logger.info("=== 测试原始VWAP计算（跨日污染版本） ===")
    
    typical_price = (df['high'] + df['low'] + df['close']) / 3
    original_vwap = (typical_price * df['volume']).cumsum() / df['volume'].cumsum()
    
    logger.info(f"原始VWAP计算:")
    logger.info(f"  - 使用数据: {len(df)} 条记录")
    logger.info(f"  - 首个VWAP值: {original_vwap.iloc[0]:.2f}")
    logger.info(f"  - 最后VWAP值: {original_vwap.iloc[-1]:.2f}")
    logger.info(f"  - 前一天最后价格: {df['close'].iloc[389]:.2f}")
    logger.info(f"  - 当天首个价格: {df['close'].iloc[390]:.2f}")
    logger.info(f"  - 当天最后价格: {df['close'].iloc[-1]:.2f}")
    
    return original_vwap


def test_fixed_vwap_calculation(df):
    """测试修复后的VWAP计算（只使用当日数据）"""
    logger.info("=== 测试修复后VWAP计算（当日数据版本） ===")
    
    fixed_vwap = TechnicalIndicators.calculate_vwap(df)
    
    # 统计有效VWAP数据
    valid_vwap = fixed_vwap.dropna()
    
    logger.info(f"修复后VWAP计算:")
    logger.info(f"  - 输入数据: {len(df)} 条记录")
    logger.info(f"  - 有效VWAP: {len(valid_vwap)} 条记录")
    logger.info(f"  - NaN数据: {len(df) - len(valid_vwap)} 条记录")
    
    if len(valid_vwap) > 0:
        logger.info(f"  - 首个有效VWAP: {valid_vwap.iloc[0]:.2f}")
        logger.info(f"  - 最后有效VWAP: {valid_vwap.iloc[-1]:.2f}")
        
        # 分析当日数据
        et_tz = pytz.timezone('US/Eastern')
        today_et = datetime.now(et_tz).date()
        
        df_with_et = df.copy()
        df_with_et['timestamp'] = pd.to_datetime(df_with_et['timestamp'])
        if df_with_et['timestamp'].dt.tz is None:
            df_with_et['timestamp'] = df_with_et['timestamp'].dt.tz_localize('UTC')
        df_with_et['timestamp_et'] = df_with_et['timestamp'].dt.tz_convert(et_tz)
        
        today_data = df_with_et[df_with_et['timestamp_et'].dt.date == today_et]
        logger.info(f"  - 当日数据范围: {len(today_data)} 条")
        logger.info(f"  - 当日首个价格: {today_data['close'].iloc[0]:.2f}")
        logger.info(f"  - 当日最后价格: {today_data['close'].iloc[-1]:.2f}")
    
    return fixed_vwap


def compare_vwap_results(original_vwap, fixed_vwap, df):
    """比较原始和修复后的VWAP结果"""
    logger.info("=== VWAP对比分析 ===")
    
    # 获取当日数据的索引范围
    et_tz = pytz.timezone('US/Eastern')
    today_et = datetime.now(et_tz).date()
    
    df_with_et = df.copy()
    df_with_et['timestamp'] = pd.to_datetime(df_with_et['timestamp'])
    if df_with_et['timestamp'].dt.tz is None:
        df_with_et['timestamp'] = df_with_et['timestamp'].dt.tz_localize('UTC')
    df_with_et['timestamp_et'] = df_with_et['timestamp'].dt.tz_convert(et_tz)
    
    today_mask = df_with_et['timestamp_et'].dt.date == today_et
    today_indices = df_with_et[today_mask].index
    
    if len(today_indices) > 0:
        # 比较当日数据的VWAP值
        first_today_idx = today_indices[0]
        last_today_idx = today_indices[-1]
        
        original_first_today = original_vwap.iloc[first_today_idx]
        original_last_today = original_vwap.iloc[last_today_idx]
        
        fixed_first_today = fixed_vwap.iloc[first_today_idx] if not pd.isna(fixed_vwap.iloc[first_today_idx]) else "NaN"
        fixed_last_today = fixed_vwap.iloc[last_today_idx] if not pd.isna(fixed_vwap.iloc[last_today_idx]) else "NaN"
        
        logger.info(f"当日首个VWAP对比:")
        logger.info(f"  - 原始方法: {original_first_today:.2f}")
        logger.info(f"  - 修复方法: {fixed_first_today}")
        
        logger.info(f"当日最后VWAP对比:")
        logger.info(f"  - 原始方法: {original_last_today:.2f}")
        logger.info(f"  - 修复方法: {fixed_last_today}")
        
        # 分析差异
        if not pd.isna(fixed_vwap.iloc[first_today_idx]):
            first_diff = abs(original_first_today - float(fixed_first_today))
            logger.info(f"当日首个VWAP差异: {first_diff:.2f}")
        
        # 理论分析
        today_data = df_with_et[today_mask]
        today_first_price = today_data['close'].iloc[0]
        typical_price_first = (today_data['high'].iloc[0] + today_data['low'].iloc[0] + today_data['close'].iloc[0]) / 3
        
        logger.info(f"理论分析:")
        logger.info(f"  - 当日首个典型价格: {typical_price_first:.2f}")
        logger.info(f"  - 当日首个收盘价: {today_first_price:.2f}")
        logger.info(f"  - 修复版首个VWAP应该接近: {typical_price_first:.2f}")


def test_market_data_integration():
    """测试与市场数据提供者的集成"""
    logger.info("=== 测试市场数据集成 ===")
    
    try:
        market_data = MarketDataProvider()
        
        # 获取实际市场数据
        bars = market_data.get_current_bars("SPY", limit=100)
        
        if not bars.empty:
            logger.info(f"获取到SPY数据: {len(bars)} 条记录")
            
            # 计算VWAP
            vwap = TechnicalIndicators.calculate_vwap(bars)
            valid_vwap = vwap.dropna()
            
            logger.info(f"实际市场数据VWAP结果:")
            logger.info(f"  - 总数据: {len(bars)} 条")
            logger.info(f"  - 有效VWAP: {len(valid_vwap)} 条")
            
            if len(valid_vwap) > 0:
                logger.info(f"  - 最新VWAP: {valid_vwap.iloc[-1]:.2f}")
                logger.info(f"  - 最新价格: {bars['close'].iloc[-1]:.2f}")
                
                # 计算偏离度
                deviation = (bars['close'].iloc[-1] - valid_vwap.iloc[-1]) / valid_vwap.iloc[-1] * 100
                logger.info(f"  - 当前偏离度: {deviation:.2f}%")
            else:
                logger.warning("没有有效的VWAP数据 - 可能是非交易时间或当日数据不足")
        else:
            logger.warning("无法获取市场数据 - 可能是API配置问题或非交易时间")
            
    except Exception as e:
        logger.error(f"市场数据集成测试失败: {e}")


def main():
    """主测试函数"""
    logger.info("🔧 开始VWAP修复验证测试")
    
    # 1. 创建测试数据
    logger.info("创建测试数据...")
    test_df = create_test_data()
    
    # 2. 测试原始VWAP计算
    original_vwap = test_original_vwap_calculation(test_df)
    
    # 3. 测试修复后VWAP计算
    fixed_vwap = test_fixed_vwap_calculation(test_df)
    
    # 4. 对比结果
    compare_vwap_results(original_vwap, fixed_vwap, test_df)
    
    # 5. 测试市场数据集成
    test_market_data_integration()
    
    logger.info("✅ VWAP修复验证测试完成")


if __name__ == "__main__":
    main() 