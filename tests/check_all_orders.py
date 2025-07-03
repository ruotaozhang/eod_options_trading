#!/usr/bin/env python3
"""
检查Alpaca账户中的所有订单（包括历史订单）
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.config import config
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetOrdersRequest

def check_all_orders():
    """检查所有订单"""
    print("🔍 检查Alpaca账户所有订单")
    print("=" * 50)
    
    try:
        # 创建交易客户端
        trading_client = TradingClient(
            api_key=config.alpaca_api_key,
            secret_key=config.alpaca_secret_key,
            paper=True if "paper" in config.alpaca_base_url else False
        )
        
        print(f"📊 账户类型: {'纸面交易' if 'paper' in config.alpaca_base_url else '实盘'}")
        
        # 获取最近3天的所有订单
        after_date = datetime.now() - timedelta(days=3)
        
        print(f"📋 获取最近3天的所有订单（自{after_date.strftime('%Y-%m-%d')}）...")
        
        try:
            all_orders = trading_client.get_orders(
                GetOrdersRequest(
                    limit=100,
                    after=after_date
                )
            )
        except Exception as e:
            print(f"使用日期过滤失败: {e}")
            # 降级：获取最近100个订单
            all_orders = trading_client.get_orders(
                GetOrdersRequest(
                    limit=100
                )
            )
        
        print(f"📦 总订单数量: {len(all_orders)}")
        
        if not all_orders:
            print("✅ 没有找到任何订单")
            return 0, 0, 0
        
        # 按状态分类订单
        status_groups = {}
        for order in all_orders:
            status = str(order.status).upper()
            if status not in status_groups:
                status_groups[status] = []
            status_groups[status].append(order)
        
        print("\n📊 订单状态分布:")
        for status, orders in status_groups.items():
            print(f"   {status}: {len(orders)}个")
        
        print("\n📋 所有订单详情:")
        print("-" * 120)
        print(f"{'时间':<12} {'ID':<20} {'符号':<20} {'类型':<10} {'方向':<6} {'数量':<8} {'价格':<12} {'状态':<12}")
        print("-" * 120)
        
        # 按时间倒序排列
        all_orders.sort(key=lambda x: x.created_at if x.created_at else datetime.min, reverse=True)
        
        open_orders = []
        filled_orders = []
        canceled_orders = []
        
        for order in all_orders:
            try:
                # 时间处理
                created_at = order.created_at
                if isinstance(created_at, str):
                    try:
                        created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    except:
                        created_at = datetime.now()
                
                time_str = created_at.strftime('%m-%d %H:%M') if created_at else "Unknown"
                
                # 订单信息
                order_id = str(order.id)[:15] + "..." if len(str(order.id)) > 18 else str(order.id)
                symbol = order.symbol
                order_type = order.order_type.value if hasattr(order.order_type, 'value') else str(order.order_type)
                side = order.side.value if hasattr(order.side, 'value') else str(order.side)
                qty = float(order.qty)
                status = order.status.value if hasattr(order.status, 'value') else str(order.status)
                
                # 价格信息
                price_info = "MARKET"
                if hasattr(order, 'limit_price') and order.limit_price:
                    price_info = f"${float(order.limit_price):.2f}"
                elif hasattr(order, 'stop_price') and order.stop_price:
                    price_info = f"Stop@${float(order.stop_price):.2f}"
                
                print(f"{time_str:<12} {order_id:<20} {symbol:<20} {order_type:<10} {side:<6} {qty:<8.0f} {price_info:<12} {status:<12}")
                
                # 分类
                if status.upper() in ['NEW', 'ACCEPTED', 'PENDING_NEW', 'PARTIALLY_FILLED']:
                    open_orders.append(order)
                elif status.upper() == 'FILLED':
                    filled_orders.append(order)
                elif status.upper() in ['CANCELED', 'CANCELLED']:
                    canceled_orders.append(order)
                    
            except Exception as e:
                print(f"处理订单时出错: {e}")
        
        print("-" * 120)
        print(f"\n📊 详细统计:")
        print(f"   开放订单: {len(open_orders)}")
        print(f"   已成交订单: {len(filled_orders)}")
        print(f"   已取消订单: {len(canceled_orders)}")
        
        # 分析开放订单
        if open_orders:
            print(f"\n⚠️ 发现 {len(open_orders)} 个开放订单:")
            for order in open_orders:
                print(f"   - {order.symbol} {order.side.value} {order.qty} @{order.limit_price if hasattr(order, 'limit_price') and order.limit_price else 'MARKET'}")
                
                # 计算订单年龄
                if order.created_at:
                    if isinstance(order.created_at, str):
                        created_at = datetime.fromisoformat(order.created_at.replace('Z', '+00:00'))
                    else:
                        created_at = order.created_at
                    age_hours = (datetime.now() - created_at.replace(tzinfo=None)).total_seconds() / 3600
                    print(f"     创建于{age_hours:.1f}小时前")
        
        # 分析最近的交易活动
        if filled_orders:
            recent_filled = [o for o in filled_orders if (datetime.now() - (o.created_at.replace(tzinfo=None) if hasattr(o.created_at, 'replace') else datetime.now())).days < 1]
            print(f"\n📈 最近24小时成交: {len(recent_filled)}个订单")
        
        return len(open_orders), len(filled_orders), len(canceled_orders)
        
    except Exception as e:
        print(f"❌ 获取订单失败: {e}")
        import traceback
        traceback.print_exc()
        return 0, 0, 0

def main():
    """主函数"""
    print("🚀 Alpaca账户完整订单检查工具")
    print("=" * 50)
    
    open_count, filled_count, canceled_count = check_all_orders()
    
    print("\n" + "=" * 50)
    print("📋 总结:")
    print(f"   当前开放订单: {open_count}")
    print(f"   已成交订单: {filled_count}")
    print(f"   已取消订单: {canceled_count}")
    
    if open_count > 0:
        print(f"\n⚠️ 您确实有 {open_count} 个开放订单需要注意！")
    else:
        print("\n✅ 当前没有开放订单")
        if filled_count > 0 or canceled_count > 0:
            print("您可能看到的是历史订单记录")

if __name__ == "__main__":
    main() 