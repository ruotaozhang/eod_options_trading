#!/usr/bin/env python3
"""
快速退出演示
展示如何使用快速模式进行退出，减少验证等待时间
"""

import sys
import signal
import time
from pathlib import Path

# 添加项目路径到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.bot.trading_bot import EODOptionsTradingBot
from src.utils.logger_setup import setup_logger
from loguru import logger


def main():
    """演示快速退出功能"""
    # 初始化日志
    setup_logger()
    
    print("=" * 80)
    print("快速退出功能演示")
    print("=" * 80)
    print("这个脚本演示了快速退出模式：")
    print("- 跳过大部分验证步骤")
    print("- 减少等待时间")
    print("- 快速完成退出流程")
    print()
    print("按 Ctrl+C 可以触发快速退出流程")
    print("=" * 80)
    
    # 全局机器人实例
    bot = None
    
    def signal_handler(signum, frame):
        """信号处理函数 - 快速退出模式"""
        signal_name = signal.Signals(signum).name
        logger.info(f"收到退出信号: {signal_name}")
        logger.info("🚀 启用快速退出模式")
        
        if bot is not None:
            # 立即停止主循环
            bot.is_running = False
            logger.info("✅ 主循环已停止")
            
            try:
                # 使用快速模式退出
                bot.stop(quick_mode=True)
            except Exception as e:
                logger.error(f"快速退出失败: {e}")
                logger.info("执行紧急停止...")
                bot.emergency_stop()
        
        print("\n🎯 快速退出演示完成！")
        sys.exit(0)
    
    # 注册信号处理
    signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # kill命令
    
    try:
        # 创建交易机器人（但不启动主循环）
        logger.info("正在初始化交易机器人...")
        bot = EODOptionsTradingBot()
        
        # 获取当前状态
        logger.info("正在检查当前账户状态...")
        bot.executor.update_account_info()
        bot.executor.sync_existing_positions()
        
        position_summary = bot.executor.get_position_summary()
        logger.info(f"当前持仓数量: {position_summary['total_positions']}")
        
        if position_summary['total_positions'] > 0:
            logger.info("当前持仓详情:")
            for pos in position_summary['positions']:
                logger.info(f"  {pos['symbol']}: {pos['quantity']}张, 盈亏${pos['unrealized_pnl']:,.2f}")
        
        # 检查开放订单
        try:
            from alpaca.trading.enums import QueryOrderStatus
            from alpaca.trading.requests import GetOrdersRequest
            
            request = GetOrdersRequest(
                status=QueryOrderStatus.OPEN,
                limit=500
            )
            open_orders = bot.executor.trading_client.get_orders(filter=request)
            logger.info(f"当前开放订单数量: {len(open_orders)}")
            
            if open_orders:
                logger.info("开放订单详情:")
                for order in open_orders[:5]:  # 只显示前5个
                    logger.info(f"  {order.symbol} {order.side} {order.qty}张")
                if len(open_orders) > 5:
                    logger.info(f"  ... 还有 {len(open_orders) - 5} 个订单")
        except Exception as e:
            logger.error(f"获取开放订单失败: {e}")
        
        print("\n" + "=" * 60)
        print("现在可以按 Ctrl+C 来测试快速退出功能")
        print("相比普通退出，快速模式将：")
        print("✅ 减少等待时间 (3秒 → 1秒)")
        print("✅ 跳过持仓验证步骤")
        print("✅ 跳过订单验证步骤")
        print("✅ 快速完成退出流程")
        print("=" * 60)
        
        # 保持运行，等待退出信号
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("收到键盘中断信号")
        if bot is not None:
            logger.info("执行快速退出流程...")
            try:
                bot.stop(quick_mode=True)
            except Exception as e:
                logger.error(f"快速退出失败: {e}")
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
    finally:
        print("\n演示结束")


if __name__ == "__main__":
    main() 