# 调试和工具脚本

本目录包含用于调试和分析的各种工具脚本。

## 脚本说明

### 期权相关调试

- **`debug_option_pricing.py`** - 期权定价调试
  - 调试期权价格计算
  - 验证定价模型
  - 分析价格异常

- **`check_available_options.py`** - 可用期权检查
  - 检查可交易的期权合约
  - 验证期权链数据
  - 分析流动性和价差

### 信号和策略调试

- **`detailed_signal_debug.py`** - 详细信号调试
  - 深度分析交易信号生成
  - 验证信号逻辑准确性
  - 输出详细的信号计算过程

- **`debug_signals.py`** - 信号系统调试
  - 调试ORB、VWAP等信号
  - 验证信号时机和条件
  - 分析信号失效原因

- **`check_signal_conditions.py`** - 信号条件检查
  - 检查各种信号触发条件
  - 验证时间窗口设置
  - 分析信号覆盖率

### 修复和优化脚本

- **`fix_orb_calculation_bug.py`** - ORB计算bug修复
  - 修复开盘区间突破计算问题
  - 验证修复效果
  - 提供详细的修复过程

- **`suggested_fixes.py`** - 建议修复脚本
  - 包含各种修复建议
  - 系统优化方案
  - 代码改进建议

## 运行方式

```bash
# 从项目根目录运行
python tests/debug/debug_option_pricing.py
python tests/debug/check_available_options.py
python tests/debug/detailed_signal_debug.py
python tests/debug/debug_signals.py
python tests/debug/check_signal_conditions.py
python tests/debug/fix_orb_calculation_bug.py
python tests/debug/suggested_fixes.py
```

## 使用场景

- **问题诊断** - 调试交易相关问题
- **数据验证** - 验证市场数据准确性
- **性能分析** - 分析系统性能瓶颈
- **开发辅助** - 协助新功能开发
- **信号调试** - 验证交易信号逻辑
- **策略优化** - 优化交易策略参数

## 注意事项

- 调试脚本可能产生大量日志输出
- 某些脚本需要市场开放时间运行
- 注意API调用频率限制
- 建议在测试环境中运行调试脚本 