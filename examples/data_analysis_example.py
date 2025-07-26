#!/usr/bin/env python3
"""
数据分析使用示例
演示如何使用数据记录和分析功能
"""

import os
import sys
import pandas as pd
from datetime import datetime

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.utils.data_logger import StrategyDataLogger


def basic_analysis_example():
    """基础分析示例"""
    print("📊 基础数据分析示例")
    print("=" * 50)
    
    # 创建数据记录器
    logger = StrategyDataLogger()
    
    # 获取最近7天的数据
    data = logger.get_analysis_data(days=7)
    
    # 检查数据可用性
    for data_type, df in data.items():
        if not df.empty:
            print(f"✅ {data_type}: {len(df)}条记录")
            print(f"   时间范围: {df.iloc[0]['时间']} - {df.iloc[-1]['时间']}")
        else:
            print(f"❌ {data_type}: 无数据")
    
    print()


def signal_analysis_example():
    """信号分析示例"""
    print("📡 信号分析示例")
    print("=" * 50)
    
    logger = StrategyDataLogger()
    data = logger.get_analysis_data(days=7)
    
    if 'signals' not in data or data['signals'].empty:
        print("❌ 没有信号数据可供分析")
        return
    
    signals_df = data['signals']
    
    # 基本统计
    print(f"总信号数: {len(signals_df)}")
    print(f"执行率: {signals_df['是否执行'].mean()*100:.1f}%")
    print(f"平均置信度: {signals_df['置信度'].mean():.2f}")
    
    # 按信号类型分组
    signal_stats = signals_df.groupby('信号类型').agg({
        '置信度': ['mean', 'count'],
        '是否执行': 'sum'
    })
    
    print("\n按信号类型统计:")
    print(signal_stats)
    
    # 置信度分布
    print(f"\n置信度分布:")
    print(f"高置信度(>0.8): {len(signals_df[signals_df['置信度'] > 0.8])}")
    print(f"中等置信度(0.6-0.8): {len(signals_df[(signals_df['置信度'] >= 0.6) & (signals_df['置信度'] <= 0.8)])}")
    print(f"低置信度(<0.6): {len(signals_df[signals_df['置信度'] < 0.6])}")
    
    print()


def trade_analysis_example():
    """交易分析示例"""
    print("💰 交易分析示例")
    print("=" * 50)
    
    logger = StrategyDataLogger()
    data = logger.get_analysis_data(days=7)
    
    if 'trades' not in data or data['trades'].empty:
        print("❌ 没有交易数据可供分析")
        return
    
    trades_df = data['trades']
    
    # 只分析平仓记录
    close_trades = trades_df[trades_df['动作'] == '平仓']
    
    if close_trades.empty:
        print("❌ 没有平仓交易记录")
        return
    
    # 基本统计
    total_trades = len(close_trades)
    winning_trades = len(close_trades[close_trades['盈亏金额'] > 0])
    losing_trades = len(close_trades[close_trades['盈亏金额'] < 0])
    
    print(f"总交易数: {total_trades}")
    print(f"盈利交易: {winning_trades}")
    print(f"亏损交易: {losing_trades}")
    print(f"胜率: {winning_trades/total_trades*100:.1f}%")
    
    # 盈亏统计
    total_pnl = close_trades['盈亏金额'].sum()
    avg_win = close_trades[close_trades['盈亏金额'] > 0]['盈亏金额'].mean()
    avg_loss = close_trades[close_trades['盈亏金额'] < 0]['盈亏金额'].mean()
    
    print(f"\n盈亏统计:")
    print(f"总盈亏: ${total_pnl:.2f}")
    print(f"平均盈利: ${avg_win:.2f}")
    print(f"平均亏损: ${avg_loss:.2f}")
    print(f"最佳交易: ${close_trades['盈亏金额'].max():.2f}")
    print(f"最差交易: ${close_trades['盈亏金额'].min():.2f}")
    
    # 持有时间分析
    avg_holding = close_trades['持有时间'].mean()
    print(f"\n平均持有时间: {avg_holding:.1f}分钟")
    
    # 按期权类型分析
    if '期权类型' in close_trades.columns:
        option_stats = close_trades.groupby('期权类型')['盈亏金额'].agg(['sum', 'mean', 'count'])
        print(f"\n按期权类型统计:")
        print(option_stats)
    
    print()


def performance_analysis_example():
    """表现分析示例"""
    print("📈 表现分析示例")
    print("=" * 50)
    
    logger = StrategyDataLogger()
    data = logger.get_analysis_data(days=7)
    
    if 'performance' not in data or data['performance'].empty:
        print("❌ 没有表现数据可供分析")
        return
    
    perf_df = data['performance']
    
    # 账户价值变化
    initial_value = perf_df['账户总值'].iloc[0]
    final_value = perf_df['账户总值'].iloc[-1]
    total_return = (final_value - initial_value) / initial_value * 100
    
    print(f"期初账户价值: ${initial_value:,.2f}")
    print(f"期末账户价值: ${final_value:,.2f}")
    print(f"总收益率: {total_return:.2f}%")
    
    # 风险分析
    max_risk = perf_df['风险利用率%'].max()
    avg_risk = perf_df['风险利用率%'].mean()
    
    print(f"\n风险分析:")
    print(f"最大风险利用率: {max_risk:.1f}%")
    print(f"平均风险利用率: {avg_risk:.1f}%")
    
    # 日盈亏分析
    max_daily_profit = perf_df['当日盈亏'].max()
    max_daily_loss = perf_df['当日盈亏'].min()
    
    print(f"\n日盈亏分析:")
    print(f"最大日盈利: ${max_daily_profit:.2f}")
    print(f"最大日亏损: ${max_daily_loss:.2f}")
    
    print()


def export_data_example():
    """数据导出示例"""
    print("💾 数据导出示例")
    print("=" * 50)
    
    logger = StrategyDataLogger()
    data = logger.get_analysis_data(days=7)
    
    # 导出为Excel文件（保存到reports目录）
    from pathlib import Path
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    filename = reports_dir / f"strategy_data_{datetime.now().strftime('%Y%m%d')}.xlsx"
    
    try:
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            for data_type, df in data.items():
                if not df.empty:
                    sheet_name = data_type.capitalize()
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
                    print(f"✅ {data_type}数据已导出到{sheet_name}工作表")
        
        print(f"\n📁 数据已导出到: {filename}")
        
    except Exception as e:
        print(f"❌ 导出失败: {e}")
    
    print()


def custom_analysis_example():
    """自定义分析示例"""
    print("🔧 自定义分析示例")
    print("=" * 50)
    
    logger = StrategyDataLogger()
    data = logger.get_analysis_data(days=7)
    
    # 示例：分析信号准确性
    if 'signals' in data and not data['signals'].empty:
        signals_df = data['signals']
        
        # 分析不同置信度区间的执行率
        signals_df['置信度区间'] = pd.cut(
            signals_df['置信度'], 
            bins=[0, 0.6, 0.8, 1.0], 
            labels=['低(0-0.6)', '中(0.6-0.8)', '高(0.8-1.0)']
        )
        
        confidence_analysis = signals_df.groupby('置信度区间')['是否执行'].agg(['count', 'sum', 'mean'])
        confidence_analysis.columns = ['总信号数', '执行数', '执行率']
        confidence_analysis['执行率'] = confidence_analysis['执行率'] * 100
        
        print("置信度区间分析:")
        print(confidence_analysis)
    
    # 示例：分析交易时间分布
    if 'trades' in data and not data['trades'].empty:
        trades_df = data['trades']
        
        # 转换时间并提取小时
        trades_df['时间'] = pd.to_datetime(trades_df['时间'])
        trades_df['小时'] = trades_df['时间'].dt.hour
        
        hourly_trades = trades_df.groupby('小时').size()
        
        print(f"\n交易时间分布:")
        for hour, count in hourly_trades.items():
            print(f"{hour}:00-{hour}:59: {count}笔交易")
    
    print()


def main():
    """主函数"""
    print("🔍 数据分析使用示例")
    print("=" * 60)
    print("本示例展示如何使用系统的数据记录和分析功能")
    print("=" * 60)
    print()
    
    # 运行各种分析示例
    basic_analysis_example()
    signal_analysis_example()
    trade_analysis_example()
    performance_analysis_example()
    export_data_example()
    custom_analysis_example()
    
    print("🎉 示例完成！")
    print("\n💡 提示:")
    print("- 运行 python tools/strategy_analyzer.py 可生成完整的分析报告")
    print("- 查看 docs/DATA_LOGGING_GUIDE.md 了解更多详细信息")


if __name__ == "__main__":
    main() 