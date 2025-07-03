# 测试目录结构说明

本文档说明了测试脚本的组织结构和使用方式。

## 📂 目录结构

```
tests/
├── README.md                      # 测试目录总体说明
├── DIRECTORY_STRUCTURE.md         # 本文档 - 目录结构详细说明
├── graceful_shutdown/             # 优雅退出功能专项测试
│   ├── README.md                  # 优雅退出测试说明
│   ├── test_graceful_shutdown.py  # 完整功能测试
│   ├── test_optimized_graceful_shutdown.py  # 优化版本测试
│   ├── test_clean_exit.py         # 清洁退出界面测试
│   ├── quick_manual_test.py       # 快速手动测试
│   └── final_manual_test.py       # 最终手动验证
├── demos/                         # 功能演示脚本
│   ├── README.md                  # 演示脚本说明
│   ├── demo_graceful_shutdown.py  # 优雅退出演示
│   └── demo_quick_exit.py         # 快速退出演示
├── debug/                         # 调试工具脚本
│   ├── README.md                  # 调试工具说明
│   ├── debug_option_pricing.py    # 期权定价调试
│   └── check_available_options.py # 可用期权检查
├── test_snapshots_api.py          # API快照测试
└── [其他现有测试脚本]             # 保持原有位置的测试脚本
```

## 🎯 分类原则

### 1. **graceful_shutdown/** - 优雅退出功能测试
**目的**: 专门测试和验证优雅退出功能的各个方面

**包含内容**:
- 完整的退出流程测试
- 性能优化测试  
- 界面清洁性测试
- 手动验证脚本

**使用场景**:
- 修改退出相关代码后的回归测试
- 性能优化验证
- 用户体验测试

### 2. **demos/** - 功能演示
**目的**: 向用户展示系统功能的演示脚本

**包含内容**:
- 交互式功能演示
- 教学用途的脚本
- 新用户学习材料

**使用场景**:
- 新用户了解系统功能
- 团队培训和演示
- 功能验证和展示

### 3. **debug/** - 调试工具
**目的**: 开发和运维过程中的调试辅助工具

**包含内容**:
- 市场数据调试脚本
- API连接测试工具
- 问题诊断脚本

**使用场景**:
- 开发阶段的问题调试
- 生产环境的故障排查
- API和数据验证

## 🚀 快速使用指南

### 测试优雅退出功能
```bash
# 完整测试
python tests/graceful_shutdown/test_graceful_shutdown.py

# 快速手动测试（推荐）
python tests/graceful_shutdown/quick_manual_test.py

# 界面清洁测试
python tests/graceful_shutdown/test_clean_exit.py
```

### 功能演示
```bash
# 优雅退出演示
python tests/demos/demo_graceful_shutdown.py

# 快速退出演示  
python tests/demos/demo_quick_exit.py
```

### 调试工具
```bash
# 期权定价调试
python tests/debug/debug_option_pricing.py

# 可用期权检查
python tests/debug/check_available_options.py
```

## 📝 开发指南

### 添加新的测试脚本

1. **确定分类**: 根据脚本目的选择合适的子目录
2. **命名规范**: 使用描述性的文件名
3. **路径设置**: 使用正确的项目根路径导入

```python
# 正确的路径设置示例
from pathlib import Path
import sys

# 根据脚本所在层级设置路径
project_root = Path(__file__).parent.parent.parent  # 对于子目录中的脚本
sys.path.insert(0, str(project_root))

from src.bot.trading_bot import EODOptionsTradingBot
```

### 路径层级说明

- **根目录脚本**: `.parent` (1层)
- **tests/脚本**: `.parent.parent` (2层)  
- **tests/子目录/脚本**: `.parent.parent.parent` (3层)

### 文档更新

添加新脚本时，请更新相应的README.md文件：
- 更新子目录的README.md
- 更新主README.md中的项目结构
- 必要时更新相关的.md文档中的路径引用

## ✅ 测试验证

所有移动的脚本都已验证可以正常运行：

```bash
# 验证脚本可以正常导入和运行
python tests/graceful_shutdown/test_clean_exit.py  ✅
python tests/demos/demo_graceful_shutdown.py       ✅  
python tests/debug/debug_option_pricing.py         ✅
```

## 🔄 维护说明

- **定期清理**: 删除过时的测试脚本
- **文档同步**: 保持README文档与实际结构同步
- **路径检查**: 新增脚本时验证导入路径正确
- **分类审查**: 定期审查脚本分类是否合理

---

此目录结构旨在提高代码组织性和可维护性，便于开发团队协作和新用户快速上手。 