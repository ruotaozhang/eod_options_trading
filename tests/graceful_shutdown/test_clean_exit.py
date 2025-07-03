#!/usr/bin/env python3
"""
清洁退出测试脚本
验证按Ctrl+C后不显示重复表格，界面清洁
"""

import sys
import signal
import time
import threading
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.bot.trading_bot import EODOptionsTradingBot
from src.utils.logger_setup import setup_logger
from loguru import logger


def simulate_ctrl_c(bot, delay=3):
    """模拟Ctrl+C信号"""
    time.sleep(delay)
    print(f"\n{'🧪 ' * 20}")
    print("🧪 模拟发送Ctrl+C信号...")
    print(f"{'🧪 ' * 20}")
    
    # 触发信号处理
    import os
    os.kill(os.getpid(), signal.SIGINT)


def main():
    """主测试函数"""
    # 初始化日志
    setup_logger()
    
    print("=" * 60)
    print("🧪 清洁退出测试")
    print("=" * 60)
    print("测试目标: 验证退出时不显示重复表格")
    print("预期行为: 干净的退出信息，无重复显示")
    print("⏰ 将在3秒后自动触发退出信号...")
    
    # 全局机器人实例
    bot = None
    
    def signal_handler(signum, frame):
        """信号处理函数"""
        signal_name = signal.Signals(signum).name
        
        # 立即显示退出信息
        print(f"\n{'=' * 60}")
        print(f"🛑 收到退出信号: {signal_name}")
        print("✅ 立即停止主循环，开始优雅退出...")
        print(f"{'=' * 60}")
        
        if bot is not None:
            bot.is_running = False
            try:
                bot.stop(quick_mode=True)
            except Exception as e:
                print(f"优雅退出失败: {e}")
                bot.emergency_stop()
        
        print("🎯 优雅退出完成")
        print("🧪 测试完成 - 检查界面是否清洁")
        sys.exit(0)
    
    # 注册信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # 创建机器人实例
        bot = EODOptionsTradingBot()
        
        # 启动模拟信号线程
        signal_thread = threading.Thread(
            target=simulate_ctrl_c, 
            args=(bot, 3),
            daemon=True
        )
        signal_thread.start()
        
        # 启动机器人
        bot.start()
        
    except KeyboardInterrupt:
        print("收到真实的Ctrl+C信号")
        if bot is not None:
            bot.is_running = False
            bot.stop(quick_mode=True)
    except Exception as e:
        print(f"测试过程中发生异常: {e}")
    finally:
        print("🧪 清洁退出测试完成")


if __name__ == "__main__":
    main() 