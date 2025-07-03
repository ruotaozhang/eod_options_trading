#!/bin/bash
# 检查交易机器人状态

echo "📊 交易机器人状态检查"
echo "=================================================="

# 检查进程状态
echo "🔍 检查运行中的进程..."
PIDS=$(pgrep -f "python main.py")
CAFE_PIDS=$(pgrep -f caffeinate)

if [ -n "$PIDS" ]; then
    echo "✅ 交易机器人正在运行:"
    ps -p $PIDS -o pid,ppid,time,command
    
    if [ -n "$CAFE_PIDS" ]; then
        echo "☕ Caffeinate也在运行 (防睡眠):"
        ps -p $CAFE_PIDS -o pid,time,command
    fi
else
    echo "❌ 交易机器人未运行"
fi

# 检查PID文件
echo ""
echo "📋 检查PID文件..."
if [ -f "trading_bot.pid" ]; then
    SAVED_PID=$(cat trading_bot.pid)
    echo "💾 保存的PID: $SAVED_PID"
    
    if ps -p $SAVED_PID > /dev/null; then
        echo "✅ PID对应的进程正在运行"
    else
        echo "⚠️  PID对应的进程已停止，清理PID文件..."
        rm trading_bot.pid
    fi
else
    echo "ℹ️  未找到PID文件"
fi

# 检查日志文件
echo ""
echo "📝 检查日志文件..."
if [ -f "trading_bot.log" ]; then
    LOG_SIZE=$(stat -f%z trading_bot.log 2>/dev/null || stat -c%s trading_bot.log 2>/dev/null)
    echo "📄 日志文件大小: $LOG_SIZE 字节"
    echo "📅 最后10行日志:"
    tail -10 trading_bot.log
else
    echo "ℹ️  未找到日志文件"
fi

# 检查Screen会话
echo ""
echo "🖥️  检查Screen会话..."
SCREEN_SESSIONS=$(screen -ls | grep trading_bot)
if [ -n "$SCREEN_SESSIONS" ]; then
    echo "✅ 找到Screen会话:"
    echo "$SCREEN_SESSIONS"
else
    echo "ℹ️  未找到trading_bot相关的Screen会话"
fi

# 检查系统睡眠状态
echo ""
echo "😴 检查系统睡眠设置..."
SLEEP_STATUS=$(pmset -g | grep "sleep" | head -1)
echo "$SLEEP_STATUS"

echo ""
echo "🎯 状态检查完成"
