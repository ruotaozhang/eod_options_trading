#!/usr/bin/env python3
"""
测试优雅退出功能
验证机器人能否正确关闭所有持仓和订单
"""

import sys
from pathlib import Path

# 添加项目路径到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.trading.executor import TradingExecutor
from src.data.market_data import MarketDataProvider
from src.utils.logger_setup import setup_logger
from loguru import logger
import time


def test_graceful_shutdown():
    """测试优雅退出功能"""
    print("=" * 80)
    print("测试优雅退出功能")
    print("=" * 80)
    
    # 初始化日志
    setup_logger()
    
    try:
        # 创建组件
        market_data = MarketDataProvider()
        executor = TradingExecutor(market_data)
        
        # 更新账户信息
        logger.info("正在获取账户信息...")
        executor.update_account_info()
        
        # 获取账户摘要
        account_summary = executor.get_account_summary()
        logger.info(f"账户总值: ${account_summary['account_value']:,.2f}")
        logger.info(f"购买力: ${account_summary['buying_power']:,.2f}")
        
        print("\n" + "=" * 60)
        print("第1步: 检查当前持仓")
        print("=" * 60)
        
        # 同步现有持仓
        executor.sync_existing_positions()
        
        # 显示当前持仓
        position_summary = executor.get_position_summary()
        logger.info(f"当前持仓数量: {position_summary['total_positions']}")
        logger.info(f"未实现盈亏: ${position_summary['total_unrealized_pnl']:,.2f}")
        
        if position_summary['total_positions'] > 0:
            logger.info("当前持仓详情:")
            for pos in position_summary['positions']:
                logger.info(f"  {pos['symbol']}: {pos['quantity']}张, "
                           f"${pos['entry_price']:.2f} -> ${pos['current_price']:.2f}, "
                           f"盈亏${pos['unrealized_pnl']:,.2f}")
        
        print("\n" + "=" * 60)
        print("第2步: 检查开放订单")
        print("=" * 60)
        
        # 检查开放订单
        try:
            from alpaca.trading.enums import QueryOrderStatus
            from alpaca.trading.requests import GetOrdersRequest
            
            request = GetOrdersRequest(
                status=QueryOrderStatus.OPEN,
                limit=500
            )
            open_orders = executor.trading_client.get_orders(filter=request)
            logger.info(f"当前开放订单数量: {len(open_orders)}")
            
            if open_orders:
                logger.info("开放订单详情:")
                for order in open_orders:
                    logger.info(f"  {order.symbol} {order.side} {order.qty}张 "
                               f"@${order.limit_price if hasattr(order, 'limit_price') else 'Market'} "
                               f"状态:{order.status}")
        except Exception as e:
            logger.error(f"获取开放订单失败: {e}")
        
        print("\n" + "=" * 60)
        print("第3步: 测试优雅退出流程")
        print("=" * 60)
        
        # 模拟优雅退出流程
        print("\n开始执行优雅退出流程...")
        
        # 第一步：关闭所有持仓
        print("\n第1步: 关闭所有持仓")
        if position_summary['total_positions'] > 0:
            logger.info(f"检测到 {position_summary['total_positions']} 个持仓，正在平仓...")
            success = executor.close_all_positions("测试优雅退出")
            if success:
                logger.info("✅ 平仓请求已提交")
            else:
                logger.error("❌ 平仓请求失败")
        else:
            logger.info("✅ 没有检测到持仓")
        
        # 等待几秒让平仓订单生效
        logger.info("等待3秒让平仓订单生效...")
        time.sleep(3)
        
        # 第二步：验证所有持仓是否已关闭
        print("\n第2步: 验证所有持仓是否已关闭")
        max_attempts = 3
        for attempt in range(max_attempts):
            if executor.verify_positions_closed():
                logger.info("✅ 所有持仓已确认关闭")
                break
            else:
                if attempt < max_attempts - 1:
                    logger.warning(f"持仓验证失败，3秒后重试... (尝试 {attempt + 1}/{max_attempts})")
                    time.sleep(3)
                else:
                    logger.error("❌ 持仓关闭验证失败")
        
        # 第三步：取消所有开放订单
        print("\n第3步: 取消所有开放订单")
        success = executor.cancel_all_open_orders()
        if success:
            logger.info("✅ 订单取消请求已提交")
        else:
            logger.error("❌ 订单取消请求失败")
        
        # 等待几秒让取消订单生效
        logger.info("等待2秒让取消订单生效...")
        time.sleep(2)
        
        # 第四步：验证所有订单是否已取消
        print("\n第4步: 验证所有订单是否已取消")
        max_attempts = 3
        for attempt in range(max_attempts):
            if executor.verify_orders_cancelled():
                logger.info("✅ 所有订单已确认取消")
                break
            else:
                if attempt < max_attempts - 1:
                    logger.warning(f"订单验证失败，3秒后重试... (尝试 {attempt + 1}/{max_attempts})")
                    time.sleep(3)
                else:
                    logger.error("❌ 订单取消验证失败")
        
        print("\n" + "=" * 60)
        print("第4步: 最终状态确认")
        print("=" * 60)
        
        # 最终状态检查
        final_position_summary = executor.get_position_summary()
        logger.info(f"最终持仓数量: {final_position_summary['total_positions']}")
        logger.info(f"最终未实现盈亏: ${final_position_summary['total_unrealized_pnl']:,.2f}")
        
        try:
            request = GetOrdersRequest(
                status=QueryOrderStatus.OPEN,
                limit=500
            )
            final_open_orders = executor.trading_client.get_orders(filter=request)
            logger.info(f"最终开放订单数量: {len(final_open_orders)}")
        except Exception as e:
            logger.error(f"获取最终订单状态失败: {e}")
            final_open_orders = []
        
        print("\n" + "=" * 80)
        print("🎯 优雅退出功能测试完成")
        print("=" * 80)
        
        # 测试结果总结
        if (final_position_summary['total_positions'] == 0 and 
            len(final_open_orders) == 0):
            logger.info("✅ 优雅退出功能测试通过！")
        else:
            logger.warning("⚠️ 优雅退出功能可能存在问题，请检查剩余持仓和订单")
        
    except Exception as e:
        logger.error(f"测试过程中发生异常: {e}")
        return False
    
    return True


if __name__ == "__main__":
    test_graceful_shutdown() 