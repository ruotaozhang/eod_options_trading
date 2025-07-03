#!/bin/bash
# 停止交易机器人

echo "🛑 停止交易机器人"
echo "=================================================="

# 检查是否有PID文件
if [ -f "trading_bot.pid" ]; then
    PID=$(cat trading_bot.pid)
    echo "📋 找到进程ID: $PID"
    
    # 检查进程是否还在运行
    if ps -p $PID > /dev/null; then
        echo "⏹️  正在停止进程 $PID..."
        kill $PID
        sleep 2
        
        # 检查是否成功停止
        if ps -p $PID > /dev/null; then
            echo "🔨 强制停止进程..."
            kill -9 $PID
        fi
        
        echo "✅ 程序已停止"
    else
        echo "ℹ️  进程已经停止"
    fi
    
    # 清理PID文件
    rm trading_bot.pid
else
    echo "⚠️  未找到PID文件，尝试查找所有相关进程..."
    
    # 查找所有可能的进程
    PIDS=$(pgrep -f "python main.py")
    if [ -n "$PIDS" ]; then
        echo "🔍 找到以下进程:"
        ps -p $PIDS
        echo "⏹️  停止所有相关进程..."
        kill $PIDS
        echo "✅ 所有进程已停止"
    else
        echo "ℹ️  未找到运行中的交易机器人进程"
    fi
fi

# 停止所有caffeinate进程
CAFE_PIDS=$(pgrep -f caffeinate)
if [ -n "$CAFE_PIDS" ]; then
    echo "☕ 停止caffeinate进程..."
    kill $CAFE_PIDS
fi

echo "🎯 停止操作完成"
