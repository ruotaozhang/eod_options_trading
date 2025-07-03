#!/bin/bash
# 使用nohup后台运行交易机器人

echo "🚀 使用nohup后台运行交易机器人"
echo "=================================================="
echo "程序将在后台运行，关闭终端也不会停止"
echo "日志将保存到 nohup.out 文件"
echo "=================================================="

# 激活conda环境
source /opt/miniconda3/etc/profile.d/conda.sh
conda activate eod_options_trading

# 使用nohup和caffeinate后台运行
nohup caffeinate -dimsu python main.py > trading_bot.log 2>&1 &

# 获取进程ID
PID=$!
echo "✅ 交易机器人已启动"
echo "�� 进程ID: $PID"
echo "📝 日志文件: trading_bot.log"
echo "🔍 查看日志: tail -f trading_bot.log"
echo "⏹️  停止程序: kill $PID"

# 保存PID到文件
echo $PID > trading_bot.pid
echo "💾 进程ID已保存到: trading_bot.pid"
