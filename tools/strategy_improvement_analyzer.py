#!/usr/bin/env python3
"""
策略改进分析工具
深度分析记录的数据，提供具体的策略改进建议和参数优化方向
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from pathlib import Path
import json
from typing import Dict, List, Tuple, Optional
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.utils.data_logger import StrategyDataLogger


class StrategyImprovementAnalyzer:
    """策略改进分析器 - 专注于具体的策略优化指导"""
    
    def __init__(self, days: int = 30):
        self.data_logger = StrategyDataLogger()
        self.days = days
        self.analysis_data = {}
        self.improvement_insights = {}
        
    def load_data(self):
        """加载分析数据"""
        self.analysis_data = self.data_logger.get_analysis_data(self.days)
        
    def analyze_signal_effectiveness(self) -> Dict:
        """分析信号有效性 - 为信号优化提供指导"""
        if 'signals' not in self.analysis_data or self.analysis_data['signals'].empty:
            return {"error": "无信号数据"}
            
        signals_df = self.analysis_data['signals'].copy()
        
        insights = {}
        
        # 1. 按置信度区间分析执行率和成功率
        signals_df['置信度区间'] = pd.cut(
            signals_df['置信度'], 
            bins=[0, 0.6, 0.7, 0.8, 0.9, 1.0], 
            labels=['<0.6', '0.6-0.7', '0.7-0.8', '0.8-0.9', '≥0.9']
        )
        
        confidence_analysis = signals_df.groupby('置信度区间').agg({
            '是否执行': ['count', 'sum', 'mean']
        }).round(3)
        
        insights['confidence_execution'] = {
            'data': confidence_analysis,
            'recommendation': self._analyze_confidence_threshold(confidence_analysis)
        }
        
        # 2. 按信号类型分析表现
        signal_type_analysis = signals_df.groupby('信号类型').agg({
            '置信度': ['mean', 'std', 'min', 'max'],
            '是否执行': ['count', 'sum', 'mean']
        }).round(3)
        
        insights['signal_type_performance'] = {
            'data': signal_type_analysis,
            'recommendation': self._analyze_signal_types(signal_type_analysis)
        }
        
        # 3. 技术指标有效性分析
        if not signals_df.empty:
            tech_indicators = ['RSI', 'VWAP偏离%', 'MACD', '成交量比率']
            indicator_analysis = {}
            
            for indicator in tech_indicators:
                if indicator in signals_df.columns:
                    # 分析执行的信号vs未执行的信号在技术指标上的差异
                    executed = signals_df[signals_df['是否执行'] == True][indicator].dropna()
                    not_executed = signals_df[signals_df['是否执行'] == False][indicator].dropna()
                    
                    if len(executed) > 0 and len(not_executed) > 0:
                        indicator_analysis[indicator] = {
                            'executed_mean': executed.mean(),
                            'not_executed_mean': not_executed.mean(),
                            'difference': executed.mean() - not_executed.mean(),
                            'executed_std': executed.std(),
                            'not_executed_std': not_executed.std()
                        }
            
            insights['technical_indicators'] = {
                'data': indicator_analysis,
                'recommendation': self._analyze_technical_indicators(indicator_analysis)
            }
        
        # 4. 时间段分析
        signals_df['时间'] = pd.to_datetime(signals_df['时间'])
        signals_df['小时'] = signals_df['时间'].dt.hour
        
        hourly_analysis = signals_df.groupby('小时').agg({
            '是否执行': ['count', 'sum', 'mean'],
            '置信度': 'mean'
        }).round(3)
        
        insights['timing_analysis'] = {
            'data': hourly_analysis,
            'recommendation': self._analyze_timing_patterns(hourly_analysis)
        }
        
        return insights
    
    def analyze_trade_optimization(self) -> Dict:
        """分析交易优化 - 为交易参数调整提供指导"""
        if 'trades' not in self.analysis_data or self.analysis_data['trades'].empty:
            return {"error": "无交易数据"}
            
        trades_df = self.analysis_data['trades'].copy()
        close_trades = trades_df[trades_df['动作'] == '平仓'].copy()
        
        if close_trades.empty:
            return {"error": "无平仓交易记录"}
            
        insights = {}
        
        # 1. 止损止盈参数优化分析
        insights['stop_loss_take_profit'] = self._analyze_stop_loss_take_profit(close_trades)
        
        # 2. 持有时间优化分析
        insights['holding_time'] = self._analyze_holding_time_optimization(close_trades)
        
        # 3. 期权类型表现分析
        insights['option_type_performance'] = self._analyze_option_type_performance(close_trades)
        
        # 4. 退出原因分析
        insights['exit_reasons'] = self._analyze_exit_reasons(close_trades)
        
        # 5. 信号置信度与交易结果关联分析
        if '信号置信度' in close_trades.columns:
            insights['signal_confidence_correlation'] = self._analyze_signal_confidence_correlation(close_trades)
        
        return insights
    
    def analyze_risk_management(self) -> Dict:
        """分析风险管理 - 为风险参数优化提供指导"""
        insights = {}
        
        # 分析账户表现数据
        if 'performance' in self.analysis_data and not self.analysis_data['performance'].empty:
            perf_df = self.analysis_data['performance'].copy()
            perf_df['时间'] = pd.to_datetime(perf_df['时间'])
            
            insights['risk_utilization'] = self._analyze_risk_utilization(perf_df)
            insights['drawdown_analysis'] = self._analyze_drawdown_patterns(perf_df)
            insights['position_sizing'] = self._analyze_position_sizing_effectiveness(perf_df)
        
        # 分析交易风险
        if 'trades' in self.analysis_data and not self.analysis_data['trades'].empty:
            trades_df = self.analysis_data['trades']
            close_trades = trades_df[trades_df['动作'] == '平仓'].copy()
            
            if not close_trades.empty:
                insights['trade_risk'] = self._analyze_trade_risk_patterns(close_trades)
        
        return insights
    
    def analyze_market_environment_impact(self) -> Dict:
        """分析市场环境对策略的影响"""
        insights = {}
        
        if 'signals' in self.analysis_data and not self.analysis_data['signals'].empty:
            signals_df = self.analysis_data['signals'].copy()
            
            # 分析不同市场条件下的策略表现
            insights['market_conditions'] = self._analyze_market_conditions_impact(signals_df)
            
        if 'trades' in self.analysis_data and not self.analysis_data['trades'].empty:
            trades_df = self.analysis_data['trades']
            insights['volatility_impact'] = self._analyze_volatility_impact(trades_df)
        
        return insights
    
    def generate_improvement_recommendations(self) -> Dict:
        """生成具体的改进建议"""
        recommendations = {
            'immediate_actions': [],  # 立即可执行的改进
            'parameter_adjustments': [],  # 参数调整建议
            'strategy_modifications': [],  # 策略逻辑修改建议
            'risk_management_improvements': [],  # 风险管理改进
            'data_collection_enhancements': []  # 数据收集增强建议
        }
        
        # 基于各项分析生成建议
        signal_analysis = self.analyze_signal_effectiveness()
        trade_analysis = self.analyze_trade_optimization()
        risk_analysis = self.analyze_risk_management()
        market_analysis = self.analyze_market_environment_impact()
        
        # 处理信号相关建议
        if 'error' not in signal_analysis:
            recommendations.update(self._generate_signal_recommendations(signal_analysis))
        
        # 处理交易相关建议
        if 'error' not in trade_analysis:
            recommendations.update(self._generate_trade_recommendations(trade_analysis))
        
        # 处理风险管理建议
        if risk_analysis:
            recommendations.update(self._generate_risk_recommendations(risk_analysis))
        
        return recommendations
    
    def _analyze_confidence_threshold(self, confidence_analysis) -> str:
        """分析最优置信度阈值"""
        try:
            execution_rates = confidence_analysis[('是否执行', 'mean')]
            best_threshold = execution_rates.idxmax()
            
            return f"建议置信度阈值：{best_threshold}区间执行率最高({execution_rates.max():.1%})"
        except:
            return "需要更多数据分析最优置信度阈值"
    
    def _analyze_signal_types(self, signal_type_analysis) -> str:
        """分析信号类型表现"""
        try:
            execution_rates = signal_type_analysis[('是否执行', 'mean')]
            best_signal = execution_rates.idxmax()
            worst_signal = execution_rates.idxmin()
            
            return f"最佳信号类型：{best_signal}({execution_rates.max():.1%})，最差：{worst_signal}({execution_rates.min():.1%})"
        except:
            return "需要更多数据分析信号类型表现"
    
    def _analyze_technical_indicators(self, indicator_analysis) -> List[str]:
        """分析技术指标的判别力"""
        recommendations = []
        
        for indicator, data in indicator_analysis.items():
            difference = abs(data['difference'])
            if difference > data['executed_std']:  # 如果差异大于标准差，说明有判别力
                recommendations.append(f"{indicator}对信号质量有显著影响，应加强权重")
            else:
                recommendations.append(f"{indicator}判别力较弱，可考虑降低权重或移除")
        
        return recommendations
    
    def _analyze_timing_patterns(self, hourly_analysis) -> str:
        """分析时间模式"""
        try:
            execution_rates = hourly_analysis[('是否执行', 'mean')]
            best_hours = execution_rates.nlargest(3).index.tolist()
            worst_hours = execution_rates.nsmallest(3).index.tolist()
            
            return f"最佳交易时段：{best_hours}，最差时段：{worst_hours}"
        except:
            return "需要更多数据分析时间模式"
    
    def _analyze_stop_loss_take_profit(self, close_trades) -> Dict:
        """分析止损止盈设置的有效性"""
        analysis = {}
        
        # 分析退出原因
        exit_reasons = close_trades['退出原因'].value_counts()
        
        # 分析不同退出原因的盈亏表现
        exit_pnl = close_trades.groupby('退出原因')['盈亏%'].agg(['count', 'mean', 'std']).round(2)
        
        analysis['exit_distribution'] = exit_reasons.to_dict()
        analysis['exit_performance'] = exit_pnl.to_dict()
        
        # 生成建议
        if '止损' in exit_reasons.index and '止盈' in exit_reasons.index:
            stop_loss_ratio = exit_reasons['止损'] / (exit_reasons['止损'] + exit_reasons['止盈'])
            if stop_loss_ratio > 0.6:
                analysis['recommendation'] = "止损触发过于频繁，建议放宽止损幅度"
            elif stop_loss_ratio < 0.3:
                analysis['recommendation'] = "止损触发较少，可考虑收紧止损以控制风险"
            else:
                analysis['recommendation'] = "止损止盈比例合理"
        
        return analysis
    
    def _analyze_holding_time_optimization(self, close_trades) -> Dict:
        """分析最优持有时间"""
        analysis = {}
        
        # 按持有时间分段分析盈亏
        close_trades['持有时间段'] = pd.cut(
            close_trades['持有时间'], 
            bins=[0, 30, 60, 120, 240, float('inf')], 
            labels=['<30min', '30-60min', '1-2h', '2-4h', '>4h']
        )
        
        holding_time_analysis = close_trades.groupby('持有时间段').agg({
            '盈亏%': ['count', 'mean', 'std'],
            '盈亏金额': ['sum', 'mean']
        }).round(2)
        
        analysis['data'] = holding_time_analysis.to_dict()
        
        # 找出最优持有时间段
        avg_returns = holding_time_analysis[('盈亏%', 'mean')]
        best_period = avg_returns.idxmax()
        
        analysis['recommendation'] = f"最优持有时间段：{best_period}，平均收益率：{avg_returns.max():.2f}%"
        
        return analysis
    
    def _analyze_option_type_performance(self, close_trades) -> Dict:
        """分析期权类型表现"""
        type_performance = close_trades.groupby('期权类型').agg({
            '盈亏%': ['count', 'mean', 'std'],
            '盈亏金额': ['sum', 'mean'],
            '持有时间': 'mean'
        }).round(2)
        
        return {
            'data': type_performance.to_dict(),
            'recommendation': self._get_option_type_recommendation(type_performance)
        }
    
    def _get_option_type_recommendation(self, type_performance) -> str:
        """获取期权类型建议"""
        try:
            avg_returns = type_performance[('盈亏%', 'mean')]
            best_type = avg_returns.idxmax()
            worst_type = avg_returns.idxmin()
            
            return f"最佳期权类型：{best_type}({avg_returns.max():.2f}%)，考虑增加{best_type}交易频率"
        except:
            return "需要更多数据分析期权类型表现"
    
    def _analyze_exit_reasons(self, close_trades) -> Dict:
        """详细分析退出原因"""
        exit_analysis = close_trades.groupby('退出原因').agg({
            '盈亏金额': ['count', 'sum', 'mean'],
            '盈亏%': 'mean',
            '持有时间': 'mean'
        }).round(2)
        
        return {
            'data': exit_analysis.to_dict(),
            'insights': self._generate_exit_insights(exit_analysis)
        }
    
    def _generate_exit_insights(self, exit_analysis) -> List[str]:
        """生成退出原因洞察"""
        insights = []
        
        try:
            counts = exit_analysis[('盈亏金额', 'count')]
            avg_pnl = exit_analysis[('盈亏%', 'mean')]
            
            for reason in counts.index:
                pnl = avg_pnl.get(reason, 0)
                count = counts.get(reason, 0)
                
                if '止损' in reason and pnl < -5:
                    insights.append(f"{reason}平均损失{abs(pnl):.1f}%，出现{count}次，建议优化止损策略")
                elif '止盈' in reason and pnl > 10:
                    insights.append(f"{reason}平均收益{pnl:.1f}%，表现良好")
        except:
            insights.append("需要更多数据生成详细洞察")
        
        return insights
    
    def _analyze_signal_confidence_correlation(self, close_trades) -> Dict:
        """分析信号置信度与交易结果的关联"""
        correlation_analysis = {}
        
        # 计算置信度与盈亏的相关性
        if '信号置信度' in close_trades.columns and '盈亏%' in close_trades.columns:
            correlation = close_trades['信号置信度'].corr(close_trades['盈亏%'])
            correlation_analysis['correlation'] = correlation
            
            # 按置信度分段分析
            close_trades['置信度段'] = pd.cut(
                close_trades['信号置信度'], 
                bins=[0, 0.7, 0.8, 0.9, 1.0], 
                labels=['<0.7', '0.7-0.8', '0.8-0.9', '≥0.9']
            )
            
            confidence_performance = close_trades.groupby('置信度段')['盈亏%'].agg(['count', 'mean', 'std']).round(2)
            correlation_analysis['performance_by_confidence'] = confidence_performance.to_dict()
            
            if correlation > 0.3:
                correlation_analysis['recommendation'] = f"置信度与盈亏正相关({correlation:.2f})，应提高置信度阈值"
            elif correlation < -0.3:
                correlation_analysis['recommendation'] = f"置信度与盈亏负相关({correlation:.2f})，需检查信号逻辑"
            else:
                correlation_analysis['recommendation'] = "置信度与盈亏相关性较弱，需优化信号评分"
        
        return correlation_analysis
    
    def _analyze_risk_utilization(self, perf_df) -> Dict:
        """分析风险利用率模式"""
        risk_analysis = {}
        
        avg_risk = perf_df['风险利用率%'].mean()
        max_risk = perf_df['风险利用率%'].max()
        
        risk_analysis['statistics'] = {
            'average_risk_utilization': avg_risk,
            'maximum_risk_utilization': max_risk,
            'risk_efficiency': perf_df['当日盈亏'].sum() / avg_risk if avg_risk > 0 else 0
        }
        
        if avg_risk < 30:
            risk_analysis['recommendation'] = "风险利用率偏低，可适当增加仓位或交易频率"
        elif avg_risk > 70:
            risk_analysis['recommendation'] = "风险利用率偏高，建议降低单笔交易风险"
        else:
            risk_analysis['recommendation'] = "风险利用率适中"
        
        return risk_analysis
    
    def _analyze_drawdown_patterns(self, perf_df) -> Dict:
        """分析回撤模式"""
        # 计算滚动最大回撤
        perf_df['cumulative_pnl'] = perf_df['当日盈亏'].cumsum()
        perf_df['running_max'] = perf_df['cumulative_pnl'].expanding().max()
        perf_df['drawdown'] = perf_df['cumulative_pnl'] - perf_df['running_max']
        
        max_drawdown = perf_df['drawdown'].min()
        avg_drawdown = perf_df['drawdown'].mean()
        
        return {
            'max_drawdown': max_drawdown,
            'average_drawdown': avg_drawdown,
            'recommendation': f"最大回撤{max_drawdown:.2f}，{'需要加强风险控制' if max_drawdown < -100 else '回撤控制良好'}"
        }
    
    def _analyze_position_sizing_effectiveness(self, perf_df) -> Dict:
        """分析仓位大小有效性"""
        # 分析仓位数量与盈亏的关系
        if '持仓数量' in perf_df.columns:
            position_pnl_corr = perf_df['持仓数量'].corr(perf_df['当日盈亏'])
            
            return {
                'position_pnl_correlation': position_pnl_corr,
                'recommendation': (
                    "持仓数量与盈亏正相关，可考虑增加仓位" if position_pnl_corr > 0.3 
                    else "持仓数量与盈亏负相关，需优化仓位管理" if position_pnl_corr < -0.3
                    else "仓位大小影响有限"
                )
            }
        
        return {'recommendation': '需要更多持仓数据分析'}
    
    def _analyze_trade_risk_patterns(self, close_trades) -> Dict:
        """分析交易风险模式"""
        risk_analysis = {}
        
        # 计算风险调整收益
        if '盈亏%' in close_trades.columns:
            returns = close_trades['盈亏%']
            sharpe_ratio = returns.mean() / returns.std() if returns.std() > 0 else 0
            
            # 分析连续亏损
            losing_trades = (returns < 0).astype(int)
            max_consecutive_losses = 0
            current_losses = 0
            
            for loss in losing_trades:
                if loss:
                    current_losses += 1
                    max_consecutive_losses = max(max_consecutive_losses, current_losses)
                else:
                    current_losses = 0
            
            risk_analysis = {
                'sharpe_ratio': sharpe_ratio,
                'max_consecutive_losses': max_consecutive_losses,
                'win_rate': (returns > 0).mean(),
                'recommendation': (
                    f"夏普比率{sharpe_ratio:.2f}，最大连续亏损{max_consecutive_losses}次，"
                    f"{'表现良好' if sharpe_ratio > 1 else '需要优化风险收益比'}"
                )
            }
        
        return risk_analysis
    
    def _analyze_market_conditions_impact(self, signals_df) -> Dict:
        """分析市场条件对策略的影响"""
        market_analysis = {}
        
        # 分析不同RSI区间的信号表现
        if 'RSI' in signals_df.columns:
            signals_df['RSI区间'] = pd.cut(
                pd.to_numeric(signals_df['RSI'], errors='coerce'), 
                bins=[0, 30, 50, 70, 100], 
                labels=['超卖', '偏弱', '偏强', '超买']
            )
            
            rsi_performance = signals_df.groupby('RSI区间')['是否执行'].agg(['count', 'sum', 'mean']).round(3)
            market_analysis['rsi_impact'] = rsi_performance.to_dict()
        
        # 分析不同成交量环境的影响
        if '成交量比率' in signals_df.columns:
            volume_data = pd.to_numeric(signals_df['成交量比率'], errors='coerce')
            signals_df['成交量环境'] = pd.cut(
                volume_data, 
                bins=[0, 0.8, 1.2, 2.0, float('inf')], 
                labels=['低量', '正常', '放量', '巨量']
            )
            
            volume_performance = signals_df.groupby('成交量环境')['是否执行'].agg(['count', 'sum', 'mean']).round(3)
            market_analysis['volume_impact'] = volume_performance.to_dict()
        
        return market_analysis
    
    def _analyze_volatility_impact(self, trades_df) -> Dict:
        """分析波动率对交易的影响"""
        # 这里可以添加基于期权价格变化的波动率分析
        return {'recommendation': '需要添加VIX数据以分析波动率影响'}
    
    def _generate_signal_recommendations(self, signal_analysis) -> Dict:
        """基于信号分析生成建议"""
        recs = {
            'immediate_actions': [],
            'parameter_adjustments': [],
            'strategy_modifications': []
        }
        
        if 'confidence_execution' in signal_analysis:
            rec = signal_analysis['confidence_execution']['recommendation']
            recs['parameter_adjustments'].append(f"置信度阈值优化: {rec}")
        
        if 'technical_indicators' in signal_analysis:
            for rec in signal_analysis['technical_indicators']['recommendation']:
                recs['strategy_modifications'].append(f"技术指标权重调整: {rec}")
        
        return recs
    
    def _generate_trade_recommendations(self, trade_analysis) -> Dict:
        """基于交易分析生成建议"""
        recs = {
            'immediate_actions': [],
            'parameter_adjustments': [],
            'strategy_modifications': []
        }
        
        if 'stop_loss_take_profit' in trade_analysis:
            rec = trade_analysis['stop_loss_take_profit'].get('recommendation', '')
            if rec:
                recs['parameter_adjustments'].append(f"止损止盈优化: {rec}")
        
        if 'holding_time' in trade_analysis:
            rec = trade_analysis['holding_time'].get('recommendation', '')
            if rec:
                recs['strategy_modifications'].append(f"持有时间优化: {rec}")
        
        return recs
    
    def _generate_risk_recommendations(self, risk_analysis) -> Dict:
        """基于风险分析生成建议"""
        recs = {
            'risk_management_improvements': []
        }
        
        if 'risk_utilization' in risk_analysis:
            rec = risk_analysis['risk_utilization'].get('recommendation', '')
            if rec:
                recs['risk_management_improvements'].append(f"风险利用率: {rec}")
        
        if 'drawdown_analysis' in risk_analysis:
            rec = risk_analysis['drawdown_analysis'].get('recommendation', '')
            if rec:
                recs['risk_management_improvements'].append(f"回撤控制: {rec}")
        
        return recs
    
    def run_comprehensive_analysis(self) -> Dict:
        """运行全面的策略改进分析"""
        print("🔍 开始策略改进分析...")
        
        self.load_data()
        
        if not any(not df.empty for df in self.analysis_data.values()):
            return {"error": "没有足够的数据进行分析"}
        
        # 执行各项分析
        results = {
            'signal_effectiveness': self.analyze_signal_effectiveness(),
            'trade_optimization': self.analyze_trade_optimization(),
            'risk_management': self.analyze_risk_management(),
            'market_environment': self.analyze_market_environment_impact(),
            'improvement_recommendations': self.generate_improvement_recommendations()
        }
        
        print("✅ 策略改进分析完成!")
        return results


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="策略改进分析工具")
    parser.add_argument("--days", type=int, default=30, help="分析天数")
    
    args = parser.parse_args()
    
    analyzer = StrategyImprovementAnalyzer(days=args.days)
    results = analyzer.run_comprehensive_analysis()
    
    # 打印关键建议
    if 'improvement_recommendations' in results:
        recs = results['improvement_recommendations']
        
        print("\n" + "="*60)
        print("🎯 策略改进建议")
        print("="*60)
        
        for category, suggestions in recs.items():
            if suggestions:
                print(f"\n📋 {category}:")
                for i, suggestion in enumerate(suggestions, 1):
                    print(f"  {i}. {suggestion}")


if __name__ == "__main__":
    main() 