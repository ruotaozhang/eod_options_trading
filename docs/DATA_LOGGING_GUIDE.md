# 数据记录与策略分析指南

## 📊 概述

系统现在具备了全面的数据记录和分析功能，可以记录运行过程中的各种指标和数据，用于后续的策略优化和改进。

## 🗂️ 数据记录结构

### 自动生成的数据文件

运行系统后，会在 `logs/strategy_data/` 目录下自动生成以下文件：

```
logs/strategy_data/
├── signals_YYYYMMDD.csv        # 信号记录
├── market_data_YYYYMMDD.csv    # 市场数据记录
├── performance_YYYYMMDD.csv    # 账户表现记录
├── trade_analysis_YYYYMMDD.csv # 交易分析记录
└── daily_summary_YYYYMMDD.json # 每日汇总数据
```

### 数据内容说明

#### 1. 信号记录 (signals_*.csv)
- **时间**: 信号生成时间
- **信号类型**: LONG/SHORT
- **信号强度**: WEAK/MEDIUM/STRONG
- **置信度**: 0-1之间的数值
- **标的价格**: 信号生成时的标的价格
- **原因**: 信号生成原因
- **技术指标**: RSI, VWAP, MACD等
- **是否执行**: 信号是否被执行
- **执行原因**: 执行或不执行的原因

#### 2. 市场数据记录 (market_data_*.csv)
- **时间**: 记录时间
- **标的价格**: SPY当前价格
- **买入价/卖出价**: Bid/Ask价格
- **成交量**: 当前成交量
- **技术指标**: RSI, VWAP, MACD数值
- **期权信息**: 期权数量和价格
- **市场状态**: 是否开盘

#### 3. 交易分析记录 (trade_analysis_*.csv)
- **时间**: 交易时间
- **动作**: 开仓/平仓
- **期权代码**: 具体期权合约
- **期权类型**: CALL/PUT
- **行权价**: 期权行权价
- **数量**: 交易数量
- **价格**: 成交价格
- **信号信息**: 信号类型和置信度
- **持有时间**: 持有时间(分钟)
- **盈亏信息**: 盈亏金额和百分比
- **止损止盈**: 设置的止损止盈价格
- **退出原因**: 平仓原因

#### 4. 账户表现记录 (performance_*.csv)
- **时间**: 记录时间
- **账户总值**: 账户总价值
- **买入力**: 可用买入力
- **当日盈亏**: 当日总盈亏
- **未实现盈亏**: 持仓未实现盈亏
- **已实现盈亏**: 已平仓盈亏
- **持仓数量**: 当前持仓数
- **当日交易数**: 当日执行的交易数
- **风险利用率**: 风险利用百分比

#### 5. 每日汇总 (daily_summary_*.json)
- **交易日期**: 交易日期
- **运行时间**: 系统运行时长
- **信号统计**: 生成和执行的信号数
- **交易统计**: 执行的交易数和胜率
- **盈亏统计**: 总盈亏、最佳/最差交易
- **风险统计**: 风险利用率、最大回撤
- **配置快照**: 当日使用的策略参数

## 📈 数据分析

### 使用分析工具

系统提供了专门的分析工具，可以自动分析收集的数据并生成报告：

```bash
# 分析最近30天的数据（默认）
python tools/strategy_analyzer.py

# 分析最近7天的数据
python tools/strategy_analyzer.py --days 7

# 分析最近60天的数据
python tools/strategy_analyzer.py --days 60
```

### 分析输出

分析工具会生成：

1. **控制台报告**: 直接在终端显示分析结果
2. **详细报告文件**: 保存在 `reports/strategy_report_*.txt`
3. **可视化图表**: 保存在 `reports/strategy_analysis_*.png`

### 分析内容

#### 📡 信号分析
- 总信号数和执行率
- 各类信号的表现
- 信号置信度分布
- 信号时间分布

#### 💰 交易分析
- 交易胜率和盈亏比
- 平均持有时间
- 按期权类型的表现
- 退出原因统计

#### 📈 表现分析
- 账户价值变化
- 总收益率
- 风险利用率变化
- 最大回撤和盈利

#### 💡 改进建议
- 基于数据分析的自动建议
- 参数优化方向
- 策略改进思路

## 🔧 使用方法

### 1. 启动数据记录

数据记录功能已自动集成到系统中，无需额外配置。启动交易系统即可开始记录：

```bash
python main.py
```

### 2. 查看实时数据

在系统运行期间，数据会实时写入CSV文件，您可以随时查看：

```bash
# 查看最新的信号记录
tail -f logs/strategy_data/signals_$(date +%Y%m%d).csv

# 查看最新的交易记录
tail -f logs/strategy_data/trade_analysis_$(date +%Y%m%d).csv
```

### 3. 定期分析

建议每周运行一次分析，了解策略表现：

```bash
# 每周分析
python tools/strategy_analyzer.py --days 7
```

### 4. 参数优化

根据分析结果调整策略参数：

- **胜率偏低**: 调整 `stop_loss_pct` 和 `take_profit_pct`
- **信号执行率低**: 降低信号置信度阈值
- **风险利用率高**: 减少 `max_single_trade_risk_pct`
- **持有时间长**: 优化退出机制

## 📋 数据分析示例

### 典型分析报告

```
策略分析报告 - 2024-01-15 10:30:00
============================================================
分析周期: 最近30天

📡 信号分析
------------------------------
总信号数: 45
执行信号数: 12
执行率: 26.7%
平均置信度: 0.72
高置信度信号(>0.8): 8

💰 交易分析
------------------------------
总交易数: 12
盈利交易: 8
亏损交易: 4
胜率: 66.7%
总盈亏: $234.50
平均盈利: $45.30
平均亏损: -$23.10
盈亏比: 1.96
平均持有时间: 45.2分钟

📈 表现分析
------------------------------
期初账户价值: $10,000.00
期末账户价值: $10,234.50
总收益率: 2.35%
最大风险利用率: 45.2%
平均风险利用率: 18.7%

💡 改进建议
------------------------------
• 当前策略表现良好，建议继续优化细节参数
• 考虑适当提高信号执行率，当前26.7%偏低
```

## ⚠️ 注意事项

1. **数据完整性**: 确保系统稳定运行，避免数据丢失
2. **存储空间**: 定期清理旧数据，避免占用过多磁盘空间
3. **隐私保护**: 注意保护交易数据的安全性
4. **参数调整**: 基于数据分析谨慎调整参数，避免过度优化

## 🚀 高级用法

### 自定义分析

您可以直接使用Python分析数据：

```python
import pandas as pd
from src.utils.data_logger import StrategyDataLogger

# 创建数据记录器
logger = StrategyDataLogger()

# 获取分析数据
data = logger.get_analysis_data(days=30)

# 自定义分析
signals_df = data['signals']
trades_df = data['trades']

# 分析信号成功率
signal_success = signals_df.groupby('信号类型')['是否执行'].mean()
print(signal_success)
```

### 导出数据

```python
# 导出为Excel文件（保存到reports目录）
from pathlib import Path
reports_dir = Path("reports")
reports_dir.mkdir(exist_ok=True)

with pd.ExcelWriter(reports_dir / 'strategy_analysis.xlsx') as writer:
    data['signals'].to_excel(writer, sheet_name='Signals')
    data['trades'].to_excel(writer, sheet_name='Trades')
    data['performance'].to_excel(writer, sheet_name='Performance')
```

通过这个全面的数据记录和分析系统，您可以深入了解策略的表现，发现改进机会，并基于真实数据优化交易策略！ 