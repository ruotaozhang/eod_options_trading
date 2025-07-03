#!/usr/bin/env python3
"""
最终手动测试脚本 - 验证清洁退出功能
运行后按Ctrl+C验证修复效果
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
    
    print("=" * 60)
    print("🎯 最终手动测试 - 清洁退出功能")
    print("=" * 60)
    print("✅ 修复内容:")
    print("   - 立即停止Live显示避免重复表格")
    print("   - 清晰的退出步骤输出")
    print("   - 干净的界面结束")
    print()
    print("🎮 操作说明:")
    print("   1. 等待机器人启动完成")
    print("   2. 按 Ctrl+C 触发退出")
    print("   3. 观察界面是否干净整洁")
    print("=" * 60)
    
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
        
        if bot is not None:
            # 立即设置停止标志，停止主循环
            bot.is_running = False
            
            try:
                bot.stop(quick_mode=True)  # 使用快速模式
            except Exception as e:
                print(f"优雅退出失败: {e}")
                bot.emergency_stop()
        
        print("🎯 优雅退出完成")
        print("✅ 界面应该干净整洁，无重复表格")
        sys.exit(0)
    
    # 注册信号处理
    signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # kill命令
    
    try:
        # 创建并启动交易机器人
        bot = EODOptionsTradingBot()
        
        # 启动机器人
        print("正在启动交易机器人...")
        print("🎯 现在按 Ctrl+C 测试清洁退出功能...")
        bot.start()
        
    except KeyboardInterrupt:
        print("收到键盘中断信号")
        if bot is not None:
            print("执行优雅退出流程...")
            try:
                bot.stop(quick_mode=True)
            except Exception as e:
                print(f"优雅退出失败: {e}")
                bot.emergency_stop()
    except Exception as e:
        print(f"程序运行异常: {e}")
        if bot is not None:
            try:
                bot.emergency_stop()
            except:
                pass
        sys.exit(1)
    finally:
        print("🎯 最终手动测试完成")


if __name__ == "__main__":
    main() 