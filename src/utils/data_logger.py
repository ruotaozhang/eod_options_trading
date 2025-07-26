"""
策略数据记录模块
记录策略运行过程中的各种指标和数据，用于后续分析和优化
"""

import os
import csv
import json
import pandas as pd
from datetime import datetime, time
from typing import Dict, List, Optional, Any
from pathlib import Path
import pytz
from loguru import logger


class StrategyDataLogger:
    """策略数据记录器"""
    
    def __init__(self):
        self.data_dir = Path("logs/strategy_data")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 获取美东时间的日期
        et_tz = pytz.timezone('America/New_York')
        self.today = datetime.now(et_tz).strftime('%Y%m%d')
        
        # 各种数据文件路径
        self.signal_log_path = self.data_dir / f"signals_{self.today}.csv"
        self.market_data_log_path = self.data_dir / f"market_data_{self.today}.csv"
        self.performance_log_path = self.data_dir / f"performance_{self.today}.csv"
        self.trade_analysis_path = self.data_dir / f"trade_analysis_{self.today}.csv"
        self.daily_summary_path = self.data_dir / f"daily_summary_{self.today}.json"
        
        # 初始化CSV文件
        self._init_csv_files()
        
    def _init_csv_files(self):
        """初始化CSV文件头"""
        
        # 信号记录CSV
        if not self.signal_log_path.exists():
            with open(self.signal_log_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    '时间', '信号类型', '信号强度', '置信度', '标的价格', '原因',
                    'RSI', 'VWAP', 'VWAP偏离%', 'MACD', 'ORB高点', 'ORB低点', 
                    '成交量', '成交量比率', '是否执行', '执行原因'
                ])
        
        # 市场数据记录CSV
        if not self.market_data_log_path.exists():
            with open(self.market_data_log_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    '时间', '标的价格', 'Bid', 'Ask', '成交量', 'RSI', 'VWAP', 'MACD',
                    '期权数量', '最佳Call价格', '最佳Put价格', 'VIX', '市场开放状态'
                ])
        
        # 交易表现记录CSV
        if not self.performance_log_path.exists():
            with open(self.performance_log_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    '时间', '账户总值', '买入力', '当日盈亏', '未实现盈亏', '已实现盈亏',
                    '持仓数量', '当日交易数', '风险利用率%', '最大日风险'
                ])
        
        # 交易分析记录CSV
        if not self.trade_analysis_path.exists():
            with open(self.trade_analysis_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    '时间', '动作', '期权代码', '期权类型', '行权价', '数量', '价格',
                    '信号类型', '信号置信度', '持有时间', '盈亏金额', '盈亏%',
                    '止损价', '止盈价', '退出原因', '标的入场价', '标的出场价'
                ])

    def log_signal(self, signal_data: Dict[str, Any], market_data: Dict[str, Any], 
                   executed: bool = False, execution_reason: str = ""):
        """记录信号数据"""
        try:
            et_tz = pytz.timezone('America/New_York')
            current_time = datetime.now(et_tz).strftime('%Y-%m-%d %H:%M:%S')
            
            with open(self.signal_log_path, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    current_time,
                    signal_data.get('type', ''),
                    signal_data.get('strength', ''),
                    signal_data.get('confidence', 0),
                    signal_data.get('price', 0),
                    signal_data.get('reason', ''),
                    market_data.get('rsi', ''),
                    market_data.get('vwap', ''),
                    market_data.get('vwap_deviation', ''),
                    market_data.get('macd', ''),
                    market_data.get('orb_high', ''),
                    market_data.get('orb_low', ''),
                    market_data.get('volume', ''),
                    market_data.get('volume_ratio', ''),
                    executed,
                    execution_reason
                ])
                
        except Exception as e:
            logger.error(f"记录信号数据失败: {e}")

    def log_market_data(self, market_data: Dict[str, Any]):
        """记录市场数据"""
        try:
            et_tz = pytz.timezone('America/New_York')
            current_time = datetime.now(et_tz).strftime('%Y-%m-%d %H:%M:%S')
            
            with open(self.market_data_log_path, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    current_time,
                    market_data.get('underlying_price', ''),
                    market_data.get('bid', ''),
                    market_data.get('ask', ''),
                    market_data.get('volume', ''),
                    market_data.get('rsi', ''),
                    market_data.get('vwap', ''),
                    market_data.get('macd', ''),
                    market_data.get('option_count', ''),
                    market_data.get('best_call_price', ''),
                    market_data.get('best_put_price', ''),
                    market_data.get('vix', ''),
                    market_data.get('market_open', True)
                ])
                
        except Exception as e:
            logger.error(f"记录市场数据失败: {e}")

    def log_performance(self, performance_data: Dict[str, Any]):
        """记录表现数据"""
        try:
            et_tz = pytz.timezone('America/New_York')
            current_time = datetime.now(et_tz).strftime('%Y-%m-%d %H:%M:%S')
            
            with open(self.performance_log_path, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    current_time,
                    performance_data.get('account_value', ''),
                    performance_data.get('buying_power', ''),
                    performance_data.get('daily_pnl', ''),
                    performance_data.get('unrealized_pnl', ''),
                    performance_data.get('realized_pnl', ''),
                    performance_data.get('position_count', ''),
                    performance_data.get('daily_trades', ''),
                    performance_data.get('risk_utilization_pct', ''),
                    performance_data.get('max_daily_risk', '')
                ])
                
        except Exception as e:
            logger.error(f"记录表现数据失败: {e}")

    def log_trade_analysis(self, trade_data: Dict[str, Any]):
        """记录交易分析数据"""
        try:
            et_tz = pytz.timezone('America/New_York')
            current_time = datetime.now(et_tz).strftime('%Y-%m-%d %H:%M:%S')
            
            with open(self.trade_analysis_path, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    current_time,
                    trade_data.get('action', ''),  # 开仓/平仓
                    trade_data.get('option_symbol', ''),
                    trade_data.get('option_type', ''),  # CALL/PUT
                    trade_data.get('strike_price', ''),
                    trade_data.get('quantity', ''),
                    trade_data.get('price', ''),
                    trade_data.get('signal_type', ''),
                    trade_data.get('signal_confidence', ''),
                    trade_data.get('holding_time', ''),  # 持有时间（分钟）
                    trade_data.get('pnl_amount', ''),
                    trade_data.get('pnl_percent', ''),
                    trade_data.get('stop_loss', ''),
                    trade_data.get('take_profit', ''),
                    trade_data.get('exit_reason', ''),
                    trade_data.get('underlying_entry_price', ''),
                    trade_data.get('underlying_exit_price', '')
                ])
                
        except Exception as e:
            logger.error(f"记录交易分析数据失败: {e}")

    def save_daily_summary(self, summary_data: Dict[str, Any]):
        """保存每日汇总数据"""
        try:
            summary_data['date'] = self.today
            summary_data['timestamp'] = datetime.now().isoformat()
            
            with open(self.daily_summary_path, 'w', encoding='utf-8') as f:
                json.dump(summary_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"保存每日汇总失败: {e}")

    def get_analysis_data(self, days: int = 30) -> Dict[str, pd.DataFrame]:
        """获取分析数据"""
        try:
            analysis_data = {}
            
            # 读取最近N天的数据文件
            for i in range(days):
                date = (datetime.now() - pd.Timedelta(days=i)).strftime('%Y%m%d')
                
                # 信号数据
                signal_file = self.data_dir / f"signals_{date}.csv"
                if signal_file.exists():
                    if 'signals' not in analysis_data:
                        analysis_data['signals'] = pd.read_csv(signal_file)
                    else:
                        analysis_data['signals'] = pd.concat([
                            analysis_data['signals'], 
                            pd.read_csv(signal_file)
                        ])
                
                # 交易数据
                trade_file = self.data_dir / f"trade_analysis_{date}.csv"
                if trade_file.exists():
                    if 'trades' not in analysis_data:
                        analysis_data['trades'] = pd.read_csv(trade_file)
                    else:
                        analysis_data['trades'] = pd.concat([
                            analysis_data['trades'], 
                            pd.read_csv(trade_file)
                        ])
                
                # 表现数据
                perf_file = self.data_dir / f"performance_{date}.csv"
                if perf_file.exists():
                    if 'performance' not in analysis_data:
                        analysis_data['performance'] = pd.read_csv(perf_file)
                    else:
                        analysis_data['performance'] = pd.concat([
                            analysis_data['performance'], 
                            pd.read_csv(perf_file)
                        ])
            
            return analysis_data
            
        except Exception as e:
            logger.error(f"获取分析数据失败: {e}")
            return {}


# 全局数据记录器实例
strategy_data_logger = StrategyDataLogger() 