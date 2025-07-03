# 测试脚本说明

这个文件夹包含了所有与交易系统相关的测试脚本，按功能分类如下：

## 🧪 核心功能测试

### 期权合约选择
- `test_new_contract_selection.py` - 测试新的期权合约选择逻辑（基于价格就近选择）
- `test_contract_selection.py` - 原始合约选择逻辑测试
- `test_same_day_only.py` - 当日到期期权测试

### 期权数据获取
- `test_new_option_chain_api.py` - 测试新的HTTP API期权链数据获取
- `test_sdk_option_chain.py` - 测试SDK方式期权链数据获取
- `test_option_snapshot.py` - 测试期权快照API
- `test_option_data.py` - 期权数据获取测试
- `test_fixed_option_data.py` - 修复后的期权数据测试

## 🔧 API测试与对比

### API升级相关
- `api_upgrade_summary.py` - API升级总结
- `test_updated_api.py` - 更新后API测试
- `test_new_api_format.py` - 新API格式测试
- `test_correct_api.py` - 正确API使用测试

### API对比分析
- `detailed_api_comparison.py` - 详细API对比分析
- `final_api_comparison.py` - 最终API对比
- `verify_data_accuracy.py` - 数据准确性验证

### Feed选项测试
- `test_feed_options.py` - 不同数据源测试

## 📊 系统功能测试

### 账户与连接
- `verify_account_connection.py` - 验证账户连接
- `check_account.py` - 检查账户状态

### 订单管理
- `check_all_orders.py` - 检查所有订单
- `check_open_orders.py` - 检查开放订单

### 持仓管理
- `check_real_positions.py` - 检查真实持仓
- `test_position_sync.py` - 持仓同步测试

### 盈亏分析
- `test_dashboard_pnl.py` - 仪表板盈亏测试

## 🚀 交易系统测试

### 完整交易流程
- `test_eod_trading.py` - 末日期权交易测试
- `test_system.py` - 系统完整性测试
- `quick_start.py` - 快速启动测试

### 期权分析
- `test_option_analysis.py` - 期权分析测试
- `test_specific_option.py` - 特定期权测试

## 🔍 调试与故障排除

### 数据问题调试
- `debug_option_data.py` - 期权数据调试
- `debug_option_chain_sdk.py` - SDK期权链调试
- `debug_time_issue.py` - 时间相关问题调试

## 📈 性能与批量测试

### 批量处理
- `test_large_batch.py` - 大批量数据测试
- `test_batch_limits.py` - 批量限制测试

## 🎯 使用方法

所有测试脚本都可以直接运行：

```bash
# 从项目根目录运行
python tests/test_new_contract_selection.py

# 或者进入tests目录运行
cd tests
python test_new_contract_selection.py
```

## 📝 注意事项

1. **环境要求**：确保已激活conda环境 `eod_options_trading`
2. **配置文件**：确保根目录有正确的 `.env` 配置文件
3. **API密钥**：确保Alpaca API密钥配置正确
4. **市场时间**：部分测试需要在市场开放时间运行

## 🔧 维护

- 新增测试脚本请放在此文件夹中
- 更新测试后请相应更新此说明文档
- 定期清理过时的测试脚本 