#!/usr/bin/env python3
"""
策略分析工具
分析系统运行期间收集的数据，生成策略表现报告和改进建议
"""

import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from pathlib import Path
import json
from typing import Dict, List, Optional

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.utils.data_logger import StrategyDataLogger

plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


class StrategyAnalyzer:
    """策略分析器"""
    
    def __init__(self, days: int = 30):
        self.data_logger = StrategyDataLogger()
        self.days = days
        self.analysis_data = {}
        self.report_dir = Path("reports")
        self.report_dir.mkdir(exist_ok=True)
        
    def load_data(self):
        """加载分析数据"""
        print(f"📊 正在加载最近{self.days}天的数据...")
        self.analysis_data = self.data_logger.get_analysis_data(self.days)
        
        for data_type, df in self.analysis_data.items():
            if not df.empty:
                print(f"✅ {data_type}: {len(df)}条记录")
            else:
                print(f"❌ {data_type}: 无数据")
    
    def analyze_signals(self) -> Dict:
        """分析信号表现"""
        if 'signals' not in self.analysis_data or self.analysis_data['signals'].empty:
            return {"error": "无信号数据"}
        
        signals_df = self.analysis_data['signals']
        
        # 基本统计
        total_signals = len(signals_df)
        executed_signals = len(signals_df[signals_df['是否执行'] == True])
        execution_rate = executed_signals / total_signals * 100 if total_signals > 0 else 0
        
        # 按信号类型分析
        signal_type_stats = signals_df.groupby('信号类型').agg({
            '置信度': ['mean', 'count'],
            '是否执行': 'sum'
        }).round(2)
        
        # 按时间段分析
        signals_df['时间'] = pd.to_datetime(signals_df['时间'])
        signals_df['小时'] = signals_df['时间'].dt.hour
        hourly_signals = signals_df.groupby('小时').size()
        
        # 置信度分析
        confidence_stats = signals_df['置信度'].describe()
        
        return {
            'total_signals': total_signals,
            'executed_signals': executed_signals,
            'execution_rate': execution_rate,
            'signal_type_stats': signal_type_stats.to_dict(),
            'hourly_distribution': hourly_signals.to_dict(),
            'confidence_stats': confidence_stats.to_dict(),
            'avg_confidence': signals_df['置信度'].mean(),
            'high_confidence_signals': len(signals_df[signals_df['置信度'] > 0.8])
        }
    
    def analyze_trades(self) -> Dict:
        """分析交易表现"""
        if 'trades' not in self.analysis_data or self.analysis_data['trades'].empty:
            return {"error": "无交易数据"}
        
        trades_df = self.analysis_data['trades']
        
        # 只分析平仓记录
        close_trades = trades_df[trades_df['动作'] == '平仓'].copy()
        
        if close_trades.empty:
            return {"error": "无平仓交易记录"}
        
        # 基本统计
        total_trades = len(close_trades)
        winning_trades = len(close_trades[close_trades['盈亏金额'] > 0])
        losing_trades = len(close_trades[close_trades['盈亏金额'] < 0])
        win_rate = winning_trades / total_trades * 100 if total_trades > 0 else 0
        
        # 盈亏统计
        total_pnl = close_trades['盈亏金额'].sum()
        avg_win = close_trades[close_trades['盈亏金额'] > 0]['盈亏金额'].mean()
        avg_loss = close_trades[close_trades['盈亏金额'] < 0]['盈亏金额'].mean()
        profit_factor = abs(avg_win * winning_trades / (avg_loss * losing_trades)) if losing_trades > 0 and avg_loss != 0 else float('inf')
        
        # 持有时间分析
        avg_holding_time = close_trades['持有时间'].mean()
        
        # 按期权类型分析
        option_type_stats = close_trades.groupby('期权类型').agg({
            '盈亏金额': ['sum', 'mean', 'count'],
            '盈亏%': 'mean'
        }).round(2)
        
        # 按退出原因分析
        exit_reason_stats = close_trades.groupby('退出原因').agg({
            '盈亏金额': ['sum', 'count'],
            '持有时间': 'mean'
        }).round(2)
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'avg_holding_time': avg_holding_time,
            'option_type_stats': option_type_stats.to_dict(),
            'exit_reason_stats': exit_reason_stats.to_dict(),
            'best_trade': close_trades['盈亏金额'].max(),
            'worst_trade': close_trades['盈亏金额'].min()
        }
    
    def analyze_performance(self) -> Dict:
        """分析整体表现"""
        if 'performance' not in self.analysis_data or self.analysis_data['performance'].empty:
            return {"error": "无表现数据"}
        
        perf_df = self.analysis_data['performance'].copy()
        perf_df['时间'] = pd.to_datetime(perf_df['时间'])
        perf_df = perf_df.sort_values('时间')
        
        # 账户增长分析
        initial_value = perf_df['账户总值'].iloc[0]
        final_value = perf_df['账户总值'].iloc[-1]
        total_return = (final_value - initial_value) / initial_value * 100 if initial_value > 0 else 0
        
        # 风险分析
        max_risk_used = perf_df['风险利用率%'].max()
        avg_risk_used = perf_df['风险利用率%'].mean()
        
        # 日盈亏分析
        daily_pnl_stats = perf_df['当日盈亏'].describe()
        max_drawdown = perf_df['当日盈亏'].min()
        max_profit = perf_df['当日盈亏'].max()
        
        return {
            'initial_value': initial_value,
            'final_value': final_value,
            'total_return_pct': total_return,
            'max_risk_used': max_risk_used,
            'avg_risk_used': avg_risk_used,
            'max_drawdown': max_drawdown,
            'max_profit': max_profit,
            'daily_pnl_stats': daily_pnl_stats.to_dict(),
            'data_points': len(perf_df)
        }
    
    def generate_charts(self):
        """生成图表"""
        print("📈 正在生成分析图表...")
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('策略表现分析', fontsize=16, fontweight='bold')
        
        # 图表1: 信号分布
        if 'signals' in self.analysis_data and not self.analysis_data['signals'].empty:
            signals_df = self.analysis_data['signals']
            signal_counts = signals_df['信号类型'].value_counts()
            axes[0, 0].pie(signal_counts.values, labels=signal_counts.index, autopct='%1.1f%%')
            axes[0, 0].set_title('信号类型分布')
        else:
            axes[0, 0].text(0.5, 0.5, '无信号数据', ha='center', va='center')
            axes[0, 0].set_title('信号类型分布')
        
        # 图表2: 交易盈亏分布
        if 'trades' in self.analysis_data and not self.analysis_data['trades'].empty:
            trades_df = self.analysis_data['trades']
            close_trades = trades_df[trades_df['动作'] == '平仓']
            if not close_trades.empty:
                axes[0, 1].hist(close_trades['盈亏金额'], bins=20, alpha=0.7, edgecolor='black')
                axes[0, 1].axvline(x=0, color='red', linestyle='--', alpha=0.7)
                axes[0, 1].set_title('交易盈亏分布')
                axes[0, 1].set_xlabel('盈亏金额 ($)')
                axes[0, 1].set_ylabel('交易次数')
            else:
                axes[0, 1].text(0.5, 0.5, '无交易数据', ha='center', va='center')
        else:
            axes[0, 1].text(0.5, 0.5, '无交易数据', ha='center', va='center')
        
        # 图表3: 账户价值变化
        if 'performance' in self.analysis_data and not self.analysis_data['performance'].empty:
            perf_df = self.analysis_data['performance'].copy()
            perf_df['时间'] = pd.to_datetime(perf_df['时间'])
            perf_df = perf_df.sort_values('时间')
            axes[1, 0].plot(perf_df['时间'], perf_df['账户总值'], linewidth=2)
            axes[1, 0].set_title('账户价值变化')
            axes[1, 0].set_xlabel('时间')
            axes[1, 0].set_ylabel('账户总值 ($)')
            axes[1, 0].tick_params(axis='x', rotation=45)
        else:
            axes[1, 0].text(0.5, 0.5, '无表现数据', ha='center', va='center')
        
        # 图表4: 风险利用率
        if 'performance' in self.analysis_data and not self.analysis_data['performance'].empty:
            perf_df = self.analysis_data['performance'].copy()
            perf_df['时间'] = pd.to_datetime(perf_df['时间'])
            perf_df = perf_df.sort_values('时间')
            axes[1, 1].plot(perf_df['时间'], perf_df['风险利用率%'], linewidth=2, color='orange')
            axes[1, 1].axhline(y=70, color='red', linestyle='--', alpha=0.7, label='风险警戒线')
            axes[1, 1].set_title('风险利用率变化')
            axes[1, 1].set_xlabel('时间')
            axes[1, 1].set_ylabel('风险利用率 (%)')
            axes[1, 1].tick_params(axis='x', rotation=45)
            axes[1, 1].legend()
        else:
            axes[1, 1].text(0.5, 0.5, '无表现数据', ha='center', va='center')
        
        plt.tight_layout()
        chart_path = self.report_dir / f"strategy_analysis_{datetime.now().strftime('%Y%m%d')}.png"
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        print(f"📊 图表已保存: {chart_path}")
        
        return chart_path
    
    def generate_report(self) -> str:
        """生成分析报告"""
        print("📋 正在生成分析报告...")
        
        # 分析各个方面
        signal_analysis = self.analyze_signals()
        trade_analysis = self.analyze_trades()
        performance_analysis = self.analyze_performance()
        
        # 生成报告文本
        report_lines = []
        report_lines.append("=" * 60)
        report_lines.append(f"策略分析报告 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("=" * 60)
        report_lines.append(f"分析周期: 最近{self.days}天")
        report_lines.append("")
        
        # 信号分析
        report_lines.append("📡 信号分析")
        report_lines.append("-" * 30)
        if "error" not in signal_analysis:
            report_lines.append(f"总信号数: {signal_analysis['total_signals']}")
            report_lines.append(f"执行信号数: {signal_analysis['executed_signals']}")
            report_lines.append(f"执行率: {signal_analysis['execution_rate']:.1f}%")
            report_lines.append(f"平均置信度: {signal_analysis['avg_confidence']:.2f}")
            report_lines.append(f"高置信度信号(>0.8): {signal_analysis['high_confidence_signals']}")
        else:
            report_lines.append(f"❌ {signal_analysis['error']}")
        report_lines.append("")
        
        # 交易分析
        report_lines.append("💰 交易分析")
        report_lines.append("-" * 30)
        if "error" not in trade_analysis:
            report_lines.append(f"总交易数: {trade_analysis['total_trades']}")
            report_lines.append(f"盈利交易: {trade_analysis['winning_trades']}")
            report_lines.append(f"亏损交易: {trade_analysis['losing_trades']}")
            report_lines.append(f"胜率: {trade_analysis['win_rate']:.1f}%")
            report_lines.append(f"总盈亏: ${trade_analysis['total_pnl']:.2f}")
            report_lines.append(f"平均盈利: ${trade_analysis['avg_win']:.2f}")
            report_lines.append(f"平均亏损: ${trade_analysis['avg_loss']:.2f}")
            report_lines.append(f"盈亏比: {trade_analysis['profit_factor']:.2f}")
            report_lines.append(f"平均持有时间: {trade_analysis['avg_holding_time']:.1f}分钟")
            report_lines.append(f"最佳交易: ${trade_analysis['best_trade']:.2f}")
            report_lines.append(f"最差交易: ${trade_analysis['worst_trade']:.2f}")
        else:
            report_lines.append(f"❌ {trade_analysis['error']}")
        report_lines.append("")
        
        # 表现分析
        report_lines.append("📈 表现分析")
        report_lines.append("-" * 30)
        if "error" not in performance_analysis:
            report_lines.append(f"期初账户价值: ${performance_analysis['initial_value']:,.2f}")
            report_lines.append(f"期末账户价值: ${performance_analysis['final_value']:,.2f}")
            report_lines.append(f"总收益率: {performance_analysis['total_return_pct']:.2f}%")
            report_lines.append(f"最大风险利用率: {performance_analysis['max_risk_used']:.1f}%")
            report_lines.append(f"平均风险利用率: {performance_analysis['avg_risk_used']:.1f}%")
            report_lines.append(f"最大回撤: ${performance_analysis['max_drawdown']:.2f}")
            report_lines.append(f"最大盈利: ${performance_analysis['max_profit']:.2f}")
        else:
            report_lines.append(f"❌ {performance_analysis['error']}")
        report_lines.append("")
        
        # 改进建议
        report_lines.append("💡 改进建议")
        report_lines.append("-" * 30)
        suggestions = self._generate_suggestions(signal_analysis, trade_analysis, performance_analysis)
        for suggestion in suggestions:
            report_lines.append(f"• {suggestion}")
        
        report_text = "\n".join(report_lines)
        
        # 保存报告
        report_path = self.report_dir / f"strategy_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_text)
        
        print(f"📋 报告已保存: {report_path}")
        print("\n" + report_text)
        
        return report_text
    
    def _generate_suggestions(self, signal_analysis, trade_analysis, performance_analysis) -> List[str]:
        """生成改进建议"""
        suggestions = []
        
        # 信号相关建议
        if "error" not in signal_analysis:
            if signal_analysis['execution_rate'] < 30:
                suggestions.append("信号执行率偏低，考虑放宽交易条件或降低置信度阈值")
            if signal_analysis['avg_confidence'] < 0.6:
                suggestions.append("信号平均置信度偏低，考虑优化信号生成逻辑")
        
        # 交易相关建议
        if "error" not in trade_analysis:
            if trade_analysis['win_rate'] < 50:
                suggestions.append("胜率偏低，考虑调整止损止盈比例或优化入场时机")
            if trade_analysis['profit_factor'] < 1.5:
                suggestions.append("盈亏比偏低，考虑减少止损幅度或增加止盈目标")
            if trade_analysis['avg_holding_time'] > 120:
                suggestions.append("平均持有时间较长，考虑优化退出机制")
        
        # 表现相关建议
        if "error" not in performance_analysis:
            if performance_analysis['max_risk_used'] > 80:
                suggestions.append("风险利用率过高，考虑降低单笔交易风险或减少交易频率")
            if performance_analysis['total_return_pct'] < 0:
                suggestions.append("总收益为负，需要全面审查策略逻辑和参数设置")
        
        if not suggestions:
            suggestions.append("当前策略表现良好，建议继续优化细节参数")
        
        return suggestions
    
    def run_analysis(self):
        """运行完整分析"""
        print("🔍 开始策略分析...")
        
        # 加载数据
        self.load_data()
        
        if not any(not df.empty for df in self.analysis_data.values()):
            print("❌ 没有找到可分析的数据，请确保系统已运行一段时间并记录了数据")
            return
        
        # 生成图表
        self.generate_charts()
        
        # 生成报告
        self.generate_report()
        
        print("✅ 分析完成!")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="策略分析工具")
    parser.add_argument(
        "--days", 
        type=int, 
        default=30,
        help="分析最近多少天的数据 (默认: 30天)"
    )
    
    args = parser.parse_args()
    
    analyzer = StrategyAnalyzer(days=args.days)
    analyzer.run_analysis()


if __name__ == "__main__":
    main() 