#!/usr/bin/env python3
"""
优化后优雅退出功能测试脚本
测试按Ctrl+C后是否立即停止状态检查并快速执行退出流程
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


def simulate_user_interrupt(bot, delay=5):
    """模拟用户按Ctrl+C"""
    time.sleep(delay)
    logger.info("🧪 模拟用户按Ctrl+C...")
    
    # 模拟信号处理
    bot.is_running = False
    logger.info("✅ 立即停止主循环")
    
    # 执行优雅退出
    try:
        bot.stop(quick_mode=True)  # 使用快速模式测试
    except Exception as e:
        logger.error(f"优雅退出失败: {e}")
        bot.emergency_stop()


def main():
    """主测试函数"""
    # 初始化日志
    setup_logger()
    
    logger.info("=" * 60)
    logger.info("🧪 优化后优雅退出功能测试")
    logger.info("=" * 60)
    logger.info("测试目标: 验证Ctrl+C后立即停止状态检查")
    logger.info("预期行为: 立即停止主循环，不再调用API获取状态")
    
    try:
        # 创建机器人实例
        bot = EODOptionsTradingBot()
        
        # 启动模拟中断线程（5秒后触发）
        interrupt_thread = threading.Thread(
            target=simulate_user_interrupt, 
            args=(bot, 5),
            daemon=True
        )
        interrupt_thread.start()
        
        logger.info("⏰ 机器人将在5秒后收到退出信号...")
        logger.info("📊 观察是否立即停止状态更新...")
        
        # 启动机器人 (这会进入主循环)
        bot.start()
        
    except KeyboardInterrupt:
        logger.info("收到真实的Ctrl+C信号")
        if 'bot' in locals():
            bot.is_running = False
            bot.stop(quick_mode=True)
    except Exception as e:
        logger.error(f"测试过程中发生异常: {e}")
    finally:
        logger.info("🧪 测试完成")


if __name__ == "__main__":
    main() 