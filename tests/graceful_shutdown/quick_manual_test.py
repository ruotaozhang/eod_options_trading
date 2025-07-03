#!/usr/bin/env python3
"""
手动测试脚本 - 运行后按Ctrl+C测试真实的信号处理
"""

import sys
import signal
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.bot.trading_bot import EODOptionsTradingBot
from src.utils.logger_setup import setup_logger
from loguru import logger


def main():
    """主函数"""
    # 初始化日志
    setup_logger()
    
    logger.info("=" * 60)
    logger.info("🧪 手动测试优雅退出功能")
    logger.info("=" * 60)
    logger.info("⚠️  请在看到机器人启动后，按 Ctrl+C 测试退出功能")
    logger.info("预期: 立即停止状态更新，快速执行退出流程")
    
    # 全局机器人实例，用于信号处理
    bot = None
    
    def signal_handler(signum, frame):
        """信号处理函数"""
        signal_name = signal.Signals(signum).name
        logger.info(f"收到退出信号: {signal_name}")
        logger.info("=" * 60)
        logger.info("🛑 立即停止所有非必要操作，开始优雅退出...")
        
        if bot is not None:
            # 立即设置停止标志，停止主循环
            bot.is_running = False
            logger.info("✅ 主循环已停止")
            
            try:
                bot.stop(quick_mode=True)  # 使用快速模式
            except Exception as e:
                logger.error(f"优雅退出失败: {e}")
                logger.info("执行紧急停止...")
                bot.emergency_stop()
        
        sys.exit(0)
    
    # 注册信号处理
    signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # kill命令
    
    try:
        # 创建并启动交易机器人
        bot = EODOptionsTradingBot()
        
        # 启动机器人
        logger.info("正在启动交易机器人...")
        logger.info("🎯 现在按 Ctrl+C 测试优雅退出功能...")
        bot.start()
        
    except KeyboardInterrupt:
        logger.info("收到键盘中断信号")
        if bot is not None:
            logger.info("执行优雅退出流程...")
            try:
                bot.stop(quick_mode=True)
            except Exception as e:
                logger.error(f"优雅退出失败: {e}")
                logger.info("执行紧急停止...")
                bot.emergency_stop()
    except Exception as e:
        logger.error(f"程序运行异常: {e}")
        if bot is not None:
            logger.info("因异常执行紧急停止...")
            try:
                bot.emergency_stop()
            except:
                pass
        sys.exit(1)
    finally:
        logger.info("🧪 手动测试完成")


if __name__ == "__main__":
    main() 