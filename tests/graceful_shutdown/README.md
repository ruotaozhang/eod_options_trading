# 优雅退出功能测试

本目录包含所有与优雅退出功能相关的测试脚本。

## 脚本说明

### 主要测试脚本

- **`test_graceful_shutdown.py`** - 完整的优雅退出功能测试
  - 测试完整的4步退出流程
  - 验证平仓和订单取消
  - 包含API调用验证

- **`test_optimized_graceful_shutdown.py`** - 优化后的退出测试
  - 测试优化后的快速响应
  - 验证5秒后自动触发退出
  - 专注于响应速度验证

- **`test_clean_exit.py`** - 清洁退出界面测试
  - 验证不显示重复表格
  - 测试Live组件正确停止
  - 检查界面整洁性

### 手动测试脚本

- **`quick_manual_test.py`** - 快速手动测试
  - 运行后手动按Ctrl+C
  - 测试真实信号处理
  - 简化的测试流程

- **`final_manual_test.py`** - 最终手动验证
  - 完整的用户体验测试
  - 包含详细的操作说明
  - 验证所有修复效果

## 运行方式

### 自动化测试
```bash
# 从项目根目录运行
python tests/graceful_shutdown/test_graceful_shutdown.py
python tests/graceful_shutdown/test_optimized_graceful_shutdown.py
python tests/graceful_shutdown/test_clean_exit.py
```

### 手动测试
```bash
# 手动按Ctrl+C测试
python tests/graceful_shutdown/quick_manual_test.py
python tests/graceful_shutdown/final_manual_test.py
```

## 测试重点

1. **响应速度** - Ctrl+C后立即响应（<0.5秒）
2. **界面清洁** - 无重复表格显示
3. **步骤完整** - 完整执行4步退出流程
4. **状态验证** - 确认持仓和订单正确关闭
5. **错误处理** - 异常情况下的降级处理

## 预期结果

✅ 立即响应用户操作  
✅ 明确的状态反馈  
✅ 清洁的界面显示  
✅ 完整的安全退出  
✅ 稳定的错误处理 