#!/bin/bash
# 防止Mac进入睡眠状态并运行交易机器人

echo "🚀 启动交易机器人 (防睡眠模式)"
echo "关闭MacBook盖子后系统将继续运行"
echo "按 Ctrl+C 停止程序"
echo "=================================================="

# 使用caffeinate防止系统睡眠，并运行交易机器人
caffeinate -dimsu python main.py

echo "程序已停止"
