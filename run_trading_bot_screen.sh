#!/bin/bash
# 使用screen会话运行交易机器人

echo "🚀 使用Screen会话启动交易机器人"
echo "=================================================="
echo "使用方法:"
echo "1. 运行此脚本启动"
echo "2. 关闭MacBook盖子"
echo "3. 重新打开后，运行: screen -r trading_bot"
echo "4. 按 Ctrl+A, D 分离会话"
echo "5. 按 Ctrl+C 停止程序"
echo "=================================================="

# 激活conda环境并启动screen会话
source /opt/miniconda3/etc/profile.d/conda.sh
conda activate eod_options_trading

# 启动screen会话
screen -S trading_bot -dm bash -c "
    echo '交易机器人已在screen会话中启动';
    echo '会话名称: trading_bot';
    echo '查看会话: screen -r trading_bot';
    echo '分离会话: Ctrl+A, D';
    echo '停止程序: Ctrl+C';
    echo '====================================';
    caffeinate -dimsu python main.py;
    echo '程序已停止，按任意键退出';
    read
"

echo "✅ Screen会话已启动"
echo "📱 查看会话: screen -r trading_bot"
echo "🔌 分离会话: Ctrl+A, D"
