#!/usr/bin/env python3
"""
末日期权交易机器人 - 主程序入口
基于Alpaca API的SPY当日到期期权自动交易系统
"""

import argparse
import sys
import signal
from pathlib import Path

# 添加项目路径到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.bot.trading_bot import EODOptionsTradingBot
from src.utils.logger_setup import setup_logger
from src.config import config
from loguru import logger


def main():
    """主函数"""
    # 设置命令行参数
    parser = argparse.ArgumentParser(description="EOD期权交易机器人")
    parser.add_argument(
        "--mode", 
        choices=["live", "test"], 
        default="test",
        help="运行模式: live(实盘) 或 test(测试)"
    )
    parser.add_argument(
        "--config", 
        type=str,
        help="配置文件路径"
    )
    parser.add_argument(
        "--dry-run", 
        action="store_true",
        help="干运行模式（不执行实际交易）"
    )
    parser.add_argument(
        "--log-level", 
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="日志级别"
    )
    parser.add_argument(
        "--quick-exit", 
        action="store_true",
        help="启用快速退出模式（跳过验证步骤）"
    )
    
    args = parser.parse_args()
    
    # 初始化日志
    setup_logger()
    
    logger.info("=" * 60)
    logger.info("EOD期权交易机器人启动")
    logger.info("=" * 60)
    logger.info(f"运行模式: {args.mode}")
    logger.info(f"日志级别: {args.log_level}")
    logger.info(f"干运行模式: {args.dry_run}")
    logger.info(f"快速退出模式: {args.quick_exit}")
    logger.info(f"交易标的: {config.symbol}")
    logger.info(f"API地址: {config.alpaca_base_url}")
    
    # 全局机器人实例，用于信号处理
    bot = None
    
    def signal_handler(signum, frame):
        """信号处理函数"""
        signal_name = signal.Signals(signum).name
        
        if bot is not None:
            # 立即停止Live显示，避免输出混乱
            bot.force_stop_display()
        
        # 立即在控制台显示清晰的退出信息
        print(f"\n{'=' * 60}")
        print(f"🛑 收到退出信号: {signal_name}")
        print("✅ 立即停止主循环，开始优雅退出...")
        print(f"{'=' * 60}")
        
        logger.info(f"收到退出信号: {signal_name}")
        logger.info("🛑 立即停止所有非必要操作，开始优雅退出...")
        
        if bot is not None:
            # 立即设置停止标志，停止主循环
            bot.is_running = False
            logger.info("✅ 主循环已停止")
            
            try:
                bot.stop(quick_mode=args.quick_exit)
            except Exception as e:
                logger.error(f"优雅退出失败: {e}")
                logger.info("执行紧急停止...")
                bot.emergency_stop()
        
        print("🎯 优雅退出完成")
        sys.exit(0)
    
    # 注册信号处理
    signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # kill命令
    
    try:
        # 创建并启动交易机器人
        bot = EODOptionsTradingBot()
        
        # 如果是干运行模式，修改机器人配置
        if args.dry_run:
            logger.info("启用干运行模式 - 所有交易将被模拟")
            # 这里可以添加干运行模式的特殊配置
        
        # 启动机器人
        logger.info("正在启动交易机器人...")
        logger.info("按 Ctrl+C 可触发优雅退出")
        bot.executor.trading_bot_ref = bot
        bot.start()
        
    except KeyboardInterrupt:
        logger.info("收到键盘中断信号")
        if bot is not None:
            logger.info("执行优雅退出流程...")
            try:
                bot.stop(quick_mode=args.quick_exit)
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
        logger.info("程序结束")


if __name__ == "__main__":
    main() 