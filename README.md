# EOD Options Trading System

基于价格就近选择的0DTE期权自动交易系统，采用极高频监控和快速执行机制。

## 🚀 快速开始

```bash
# 选择正确的conda环境
conda activate eod_options_trading

# 启动交易系统（生产模式）
python main.py

# 启动测试模式
python main.py --mode test
```

## 📁 项目结构（实际代码组织）

```
eod_options_trading/
├── src/                        # 核心源代码
│   ├── bot/                   # 交易机器人主控制
│   │   └── trading_bot.py     # 主要机器人逻辑和仪表板
│   ├── data/                  # 市场数据和期权处理
│   │   └── market_data.py     # 数据获取、期权选择逻辑
│   ├── strategy/              # 交易信号生成
│   │   └── signals.py         # ORB、VWAP、反转信号生成
│   ├── trading/               # 交易执行和风险管理
│   │   └── executor.py        # 订单执行、持仓管理
│   ├── utils/                 # 工具模块
│   │   ├── logger_setup.py    # 日志配置
│   │   └── notifications.py   # 通知管理
│   └── config.py             # 统一配置管理
├── tests/                     # 测试脚本
├── docs/                      # 文档目录
├── logs/                      # 系统日志
├── main.py                   # 主启动文件
├── config.env.example        # 配置文件模板
└── requirements.txt          # 依赖包列表
```

## ⚙️ 配置设置

1. 复制配置文件模板：
```bash
cp config.env.example .env
```

2. 编辑 `.env` 文件，填入您的Alpaca API密钥。

## 🎯 核心特性（基于实际代码实现）

### **期权选择策略**
- **Call期权**：选择floor(当前价格)行权价
- **Put期权**：选择ceil(当前价格)行权价
- **无delta依赖**：不依赖希腊字母计算
- **无价差筛选**：仅监控不筛选流动性

### **信号生成机制**
- **开盘区间突破（ORB）**：09:45-10:00时间窗口
- **VWAP偏离信号**：全时段监控，0.15%偏离阈值
- **午后反转信号**：14:30-15:00时间窗口
- **整理突破信号**：11:30-12:30时间窗口

### **风险控制体系**
- **账户级别**：每日最大风险2%，单笔最大风险1%
- **持仓级别**：止损10%，止盈20%
- **时间级别**：15:45强制平仓
- **监控频率**：5秒极高频实时监控

### **订单执行机制**
- **入场**：限价单买入（带0.1%滑点保护）
- **出场**：市价单卖出（确保立即成交）
- **监控**：5秒频率价格跟踪
- **备用**：主平仓失败时启用备用机制

## 📊 系统监控频率（实际配置）

```python
# 来自src/config.py的实际设置
position_check_seconds = 5      # 持仓检查：5秒
market_data_update_seconds = 5  # 市场数据：5秒  
signal_check_seconds = 5        # 信号检查：5秒
```

**监控内容**：
- 实时价格更新和盈亏计算
- 止盈止损条件检查
- 风险指标监控
- 强制平仓时间检查

## 🧪 测试和验证

运行各种测试脚本：
```bash
cd tests

# 基础功能测试
python test_new_contract_selection.py    # 期权选择逻辑测试
python test_single_option_performance.py # 性能测试
python check_api_usage.py               # API使用率检查

# 系统测试
python test_monitoring_frequency.py     # 监控频率验证
python test_graceful_shutdown.py        # 优雅退出测试
```

## 📚 技术文档

核心文档位于 `docs/` 目录：
- [0DTE交易策略](docs/0DTE_TRADING_STRATEGY.md) - 实际期权选择和信号逻辑
- [风险管理总结](docs/RISK_MANAGEMENT_SUMMARY.md) - 代码实现的风险控制
- [实时止损机制](docs/REAL_TIME_STOP_LOSS_MECHANISM.md) - 市价单执行机制

## 🎮 运行模式

### **生产模式**
```bash
python main.py
```
- 实时交易
- 完整风险检查
- 所有监控功能

### **测试模式**
```bash
python main.py --mode test
```
- Paper Trading
- 相同逻辑
- 安全测试环境

## 💻 本地运行

### **直接运行**
```bash
# 生产模式
python main.py

# 测试模式 (推荐)
python main.py --mode test

# 查看日志
tail -f logs/trading/eod_trading_$(date +%Y%m%d).log
```

### **后台运行**
```bash
# 后台运行（适合长期运行）
nohup python main.py > logs/nohup.out 2>&1 &

# 查看运行进程
ps aux | grep main.py

# 停止程序
pkill -f "python main.py"
```

## ⚠️ 重要提醒

### **风险控制**
- 本系统采用极高频监控（5秒）
- 使用市价单确保快速平仓
- 有完整的备用平仓机制
- 15:45强制平仓避免行权风险

### **使用建议**
- 建议先在Paper Trading环境充分测试
- 0DTE期权交易风险极高，需要丰富经验
- 严格遵循系统的风险管理参数
- 实时监控系统运行状态

## 📈 系统优势

- ✅ **简化快速**：基于价格就近选择，无复杂计算
- ✅ **极高频监控**：5秒刷新确保及时响应
- ✅ **可靠执行**：市价单 + 备用机制
- ✅ **全面风控**：多层次风险保护
- ✅ **实时仪表板**：Rich UI美观显示
- ✅ **优雅退出**：支持正常和紧急停止

## 📞 故障排除

1. **API连接问题**：检查.env文件中的API密钥
2. **期权数据获取失败**：验证交易时间和市场状态
3. **监控频率过高**：可在config.py中调整秒数
4. **风险检查失败**：检查账户余额和交易限制

如有其他问题，请查看 `docs/` 目录中的详细文档。 