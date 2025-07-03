#!/usr/bin/env python3
"""
检查Alpaca账户中的开放订单
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
from alpaca.trading.enums import OrderStatus, OrderSide, OrderType, TimeInForce

def check_open_orders():
    """检查开放订单"""
    print("🔍 检查Alpaca账户开放订单")
    print("=" * 50)
    
    try:
        # 创建交易客户端
        trading_client = TradingClient(
            api_key=config.alpaca_api_key,
            secret_key=config.alpaca_secret_key,
            paper=True if "paper" in config.alpaca_base_url else False
        )
        
        # 获取所有开放订单
        print("📋 获取开放订单...")
        
        # 方法1: 直接获取所有开放订单（不指定status）
        try:
            open_orders = trading_client.get_orders()
            # 过滤出开放状态的订单
            open_orders = [order for order in open_orders if str(order.status).upper() in ['NEW', 'ACCEPTED', 'PENDING_NEW', 'PARTIALLY_FILLED']]
        except Exception as e1:
            print(f"方法1失败: {e1}")
            # 方法2: 使用字符串状态
            try:
                open_orders = trading_client.get_orders(
                    GetOrdersRequest(
                        status="open"  # 使用字符串而不是枚举
                    )
                )
            except Exception as e2:
                print(f"方法2失败: {e2}")
                # 方法3: 不指定状态，然后手动过滤
                open_orders = trading_client.get_orders()
                print(f"获取到 {len(open_orders)} 个订单，正在过滤开放订单...")
                open_orders = [order for order in open_orders 
                             if hasattr(order, 'status') and 
                             str(order.status).upper() not in ['FILLED', 'CANCELED', 'EXPIRED', 'REJECTED']]
        
        print(f"📊 账户类型: {'纸面交易' if 'paper' in config.alpaca_base_url else '实盘'}")
        print(f"📦 开放订单数量: {len(open_orders)}")
        print()
        
        if not open_orders:
            print("✅ 没有开放订单")
            return 0, 0, 0
        
        print("📋 开放订单详情:")
        print("-" * 100)
        print(f"{'ID':<20} {'符号':<20} {'类型':<10} {'方向':<6} {'数量':<8} {'价格':<12} {'状态':<10} {'时间'}")
        print("-" * 100)
        
        option_orders = []
        stock_orders = []
        
        for order in open_orders:
            try:
                order_id = str(order.id)[:15] + "..." if len(str(order.id)) > 18 else str(order.id)
                symbol = order.symbol
                order_type = order.order_type.value if hasattr(order.order_type, 'value') else str(order.order_type)
                side = order.side.value if hasattr(order.side, 'value') else str(order.side)
                qty = float(order.qty)
                
                # 获取价格信息
                price_info = "MARKET"
                if hasattr(order, 'limit_price') and order.limit_price:
                    price_info = f"${float(order.limit_price):.2f}"
                elif hasattr(order, 'stop_price') and order.stop_price:
                    price_info = f"Stop@${float(order.stop_price):.2f}"
                
                status = order.status.value if hasattr(order.status, 'value') else str(order.status)
                
                # 获取创建时间
                created_at = order.created_at
                if isinstance(created_at, str):
                    # 如果是字符串，尝试解析
                    try:
                        created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    except:
                        created_at = datetime.now()
                
                time_str = created_at.strftime('%m-%d %H:%M') if created_at else "Unknown"
                
                print(f"{order_id:<20} {symbol:<20} {order_type:<10} {side:<6} {qty:<8.0f} {price_info:<12} {status:<10} {time_str}")
                
                # 分类订单
                if len(symbol) > 10:  # 期权
                    option_orders.append({
                        'id': order.id,
                        'symbol': symbol,
                        'type': order_type,
                        'side': side,
                        'qty': qty,
                        'price': price_info,
                        'created_at': created_at
                    })
                else:  # 股票
                    stock_orders.append({
                        'id': order.id,
                        'symbol': symbol,
                        'type': order_type,
                        'side': side,
                        'qty': qty,
                        'price': price_info,
                        'created_at': created_at
                    })
                    
            except Exception as e:
                print(f"处理订单时出错: {e}")
                print(f"订单对象属性: {[attr for attr in dir(order) if not attr.startswith('_')]}")
        
        print("-" * 100)
        print(f"📊 订单分类:")
        print(f"   期权订单: {len(option_orders)}")
        print(f"   股票订单: {len(stock_orders)}")
        
        # 分析期权订单
        if option_orders:
            print("\n🎯 期权订单分析:")
            
            # 按符号分组
            symbol_groups = {}
            for order in option_orders:
                symbol = order['symbol']
                if symbol not in symbol_groups:
                    symbol_groups[symbol] = []
                symbol_groups[symbol].append(order)
            
            for symbol, orders in symbol_groups.items():
                print(f"\n   {symbol}:")
                buy_orders = [o for o in orders if o['side'] == 'BUY']
                sell_orders = [o for o in orders if o['side'] == 'SELL']
                
                print(f"     买入订单: {len(buy_orders)}")
                print(f"     卖出订单: {len(sell_orders)}")
                
                if sell_orders:
                    print("     卖出订单详情:")
                    for order in sell_orders:
                        age_hours = (datetime.now() - order['created_at']).total_seconds() / 3600 if order['created_at'] else 0
                        print(f"       - {order['type']} {order['price']} (创建于{age_hours:.1f}小时前)")
        
        # 检查可能的问题
        print("\n⚠️ 潜在问题分析:")
        
        # 检查旧订单
        old_orders = []
        now = datetime.now()
        for order_list in [option_orders, stock_orders]:
            for order in order_list:
                if order['created_at'] and (now - order['created_at']).days > 0:
                    old_orders.append(order)
        
        if old_orders:
            print(f"   发现 {len(old_orders)} 个超过1天的旧订单")
        
        # 检查孤儿止盈止损单
        orphan_orders = []
        for order in option_orders:
            if order['side'] == 'SELL' and order['type'] in ['LIMIT', 'STOP_LIMIT']:
                # 这可能是止盈止损单，但没有对应的持仓
                orphan_orders.append(order)
        
        if orphan_orders:
            print(f"   发现 {len(orphan_orders)} 个可能的孤儿止盈止损单")
            print("   （这些是卖出订单，但可能没有对应的持仓）")
        
        return len(open_orders), len(option_orders), len(orphan_orders)
        
    except Exception as e:
        print(f"❌ 获取开放订单失败: {e}")
        import traceback
        traceback.print_exc()
        return 0, 0, 0

def suggest_cleanup():
    """建议清理方案"""
    print("\n💡 订单管理建议:")
    print("1. 检查孤儿止盈止损单：")
    print("   - 如果没有对应持仓，应该取消这些订单")
    print("   - 避免意外成交")
    
    print("\n2. 清理旧订单：")
    print("   - 超过1天的订单通常应该取消")
    print("   - 特别是当日期权的订单")
    
    print("\n3. 系统改进：")
    print("   - 添加订单清理功能")
    print("   - 在平仓时自动取消相关止盈止损单")
    print("   - 定期检查和清理孤儿订单")

def main():
    """主函数"""
    print("🚀 Alpaca账户开放订单检查工具")
    print("=" * 50)
    
    total_orders, option_orders, orphan_orders = check_open_orders()
    
    print("\n" + "=" * 50)
    print("📋 总结:")
    print(f"   总开放订单: {total_orders}")
    print(f"   期权订单: {option_orders}")
    print(f"   可疑孤儿订单: {orphan_orders}")
    
    if total_orders > 0:
        suggest_cleanup()
        
        if orphan_orders > 0:
            print(f"\n⚠️ 警告: 发现 {orphan_orders} 个可疑订单")
            print("建议手动检查这些订单是否需要取消")

if __name__ == "__main__":
    main() 