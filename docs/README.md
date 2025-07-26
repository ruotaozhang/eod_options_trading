# EOD期权交易机器人

## 项目简介

这是一个专门针对SPY当日到期期权的自动交易系统，采用多种技术分析策略，在美股交易时间内自动识别交易机会并执行交易。

## 核心特性

### 🚀 交易策略
- **开盘区间突破** (9:45-10:00): 基于开盘15分钟的价格区间突破
- **VWAP偏离策略**: 价格相对VWAP的偏离度交易
- **午后反转** (14:30-15:00): 捕捉日内反转机会  
- **整理突破** (11:30-12:30): 盘中整理后的突破交易

### ⚡ 技术指标
- **RSI**: 相对强弱指数，识别超买超卖
- **MACD**: 移动平均收敛散度，确认趋势
- **VWAP**: 成交量加权平均价，判断价格偏离
- **成交量分析**: 结合成交量确认信号强度

### 🛡️ 风险管理
- **固定风险**: 每日最大损失1-2%账户资金
- **实时止盈止损**: 新一代监控机制，市价单快速执行
  - 持仓时每15秒检查价格变化
  - 触发条件时立即提交市价单
  - 期权价值下跌50%自动止损
  - 期权价值上涨100%自动止盈
- **强制平仓**: 15:45前强制平仓所有头寸

### 📊 监控系统
- **终端监控**: 实时显示交易状态、持仓、盈亏
- **日志记录**: 详细的交易和系统日志
- **状态报告**: 每小时和日终交易报告

## 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd eod_options_trading

# 创建conda环境
conda create -n eod_options_trading python=3.9
conda activate eod_options_trading

# 安装TA-Lib
conda install -c conda-forge ta-lib

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置设置

复制配置模板：
```bash
cp config.env.example .env
```

编辑 `.env` 文件，填入您的配置：
```bash
# Alpaca API配置
ALPACA_API_KEY=your_api_key_here
ALPACA_SECRET_KEY=your_secret_key_here
ALPACA_BASE_URL=https://paper-api.alpaca.markets  # 纸面交易

# 风险管理配置（账户资金自动从API获取）
MAX_DAILY_RISK_PCT=2.0
MAX_SINGLE_TRADE_RISK_PCT=1.0
MAX_DAILY_TRADES=5
```

### 3. 运行方式

#### 🤖 自动交易模式
启动交易机器人：
```bash
# 测试模式（推荐，默认模式）
python main.py --mode test

# 实盘模式
python main.py --mode live

# 干运行模式（不执行实际交易）
python main.py --dry-run

# 快速退出模式
python main.py --quick-exit

# 查看日志
tail -f logs/trading/eod_trading_$(date +%Y%m%d).log
```

#### 🧪 系统测试
验证系统配置和连接：
```bash
python test_system.py
```

## 终端监控界面

启动终端监控后，您将看到：

```
🤖 EOD期权交易机器人监控台 | 运行时间: 0:01:23 | 更新时间: 14:35:42

┌─── 🔧 系统状态 ──────────────────────────┐  ┌─── 📊 当前持仓 ──────────────────────────┐
│ 交易时间    🟢 交易时间内  09:30-15:50    │  │ 合约         数量  均价    现价    盈亏    │
│ API连接     🟢 连接正常   Alpaca API可用  │  │ SPY241201C590  5   $1.25  $2.10  +$425  │
│ 市场数据    🟢 数据正常   SPY: $588.78   │  └─────────────────────────────────────────┘
└─────────────────────────────────────────┘
                                            ┌─── 📡 交易信号 ──────────────────────────┐
┌─── 💰 账户信息 ──────────────────────────┐  │ 时间     类型  置信度  原因               │
│ 账户总值    $10,555.67         💰        │  │ 14:35:12 LONG  0.85   VWAP偏离向上突破    │
│ 当日盈亏    +$425.00          📈        │  │ 14:32:45 LONG  0.72   RSI超卖反弹        │
│ 风险利用率  15.2%             ✅        │  └─────────────────────────────────────────┘
│ 买入力      $20,000.00        💵        │
└─────────────────────────────────────────┘  ┌─── 📈 市场数据 ──────────────────────────┐
                                            │ SPY价格      $588.78        📊          │
                                            │ 成交量       15.2M          📊          │
                                            │ 日内区间     $585.20-$590.15 📊          │
                                            │ VWAP        $587.45         📊          │
                                            └─────────────────────────────────────────┘

💡 提示: 按 Ctrl+C 退出监控 | 数据每5秒自动更新
```

## 项目结构

```
eod_options_trading/
├── main.py                 # 主程序入口
├── terminal_monitor.py     # 终端监控界面
├── test_system.py         # 系统测试
├── requirements.txt       # 依赖包
├── .env                   # 配置文件
├── src/                   # 源代码
│   ├── config.py          # 配置管理
│   ├── data/              # 数据模块
│   │   └── market_data.py # 市场数据获取
│   ├── strategy/          # 策略模块
│   │   └── signals.py     # 信号生成
│   ├── trading/           # 交易模块
│   │   └── executor.py    # 交易执行
│   ├── bot/               # 机器人主逻辑
│   │   └── trading_bot.py # 交易机器人
│   └── utils/             # 工具模块
│       ├── logger_setup.py    # 日志配置
│       └── notifications.py   # 通知管理
└── tests/                 # 测试脚本
    ├── graceful_shutdown/ # 优雅退出功能测试
    │   ├── test_graceful_shutdown.py
    │   ├── test_optimized_graceful_shutdown.py
    │   ├── test_clean_exit.py
    │   ├── quick_manual_test.py
    │   └── final_manual_test.py
    ├── demos/             # 功能演示脚本
    │   ├── demo_graceful_shutdown.py
    │   └── demo_quick_exit.py
    ├── debug/             # 调试工具脚本
    │   ├── debug_option_pricing.py
    │   └── check_available_options.py
    └── test_snapshots_api.py  # API测试脚本
```

## 使用说明

### 日常使用流程

1. **启动监控**: `python terminal_monitor.py`
2. **观察状态**: 查看系统状态、账户信息、市场数据
3. **关注信号**: 监控交易信号的生成和执行
4. **风险控制**: 注意风险利用率和当日盈亏

### 实盘交易前注意事项

1. ⚠️ **充分测试**: 在纸面交易环境充分测试策略
2. 🛡️ **风险控制**: 设置合理的风险参数
3. 📊 **监控重要**: 交易期间持续监控系统状态
4. 🕐 **时间管理**: 确保在交易时间内监控系统

## 常见问题

### Q: 如何切换到实盘交易？
A: 修改 `.env` 文件中的 `ALPACA_BASE_URL` 为 `https://api.alpaca.markets`

### Q: 系统会自动停止交易吗？
A: 是的，系统会在15:45自动平仓所有头寸，避免期权到期风险

### Q: 如何调整风险参数？
A: 修改 `.env` 文件中的 `MAX_DAILY_RISK_PCT` 和 `MAX_SINGLE_TRADE_RISK_PCT`

### Q: 如何查看详细日志？
A: 查看 `logs/` 目录下的日志文件

## 风险提示

⚠️ **重要警告**: 期权交易具有高风险，可能导致全部本金损失。本系统仅供学习和研究使用，不构成投资建议。使用前请充分了解期权交易风险并在模拟环境中充分测试。

📝 **免责声明**: 使用本系统进行实盘交易的所有风险由用户自行承担。开发者不对任何交易损失负责。

## 技术支持

- 📧 问题反馈: 提交GitHub Issue
- 📚 文档更新: 查看项目Wiki
- 🔄 版本更新: 关注Release页面 