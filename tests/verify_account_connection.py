#!/usr/bin/env python3
"""
验证Alpaca账户连接和配置
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.config import config
from alpaca.trading.client import TradingClient

def verify_account_connection():
    """验证账户连接"""
    print("🔍 验证Alpaca账户连接")
    print("=" * 50)
    
    try:
        # 显示配置信息
        print("📋 当前配置:")
        print(f"   API Base URL: {config.alpaca_base_url}")
        print(f"   API Key (前8位): {config.alpaca_api_key[:8]}...")
        print(f"   Secret Key (前8位): {config.alpaca_secret_key[:8]}...")
        print()
        
        # 创建交易客户端
        trading_client = TradingClient(
            api_key=config.alpaca_api_key,
            secret_key=config.alpaca_secret_key,
            paper=True if "paper" in config.alpaca_base_url else False
        )
        
        # 获取账户信息
        print("🏦 账户信息:")
        account = trading_client.get_account()
        
        print(f"   账户ID: {account.id}")
        print(f"   账户状态: {account.status}")
        print(f"   账户类型: {'纸面交易' if 'paper' in config.alpaca_base_url else '实盘交易'}")
        print(f"   总资产: ${float(account.portfolio_value):,.2f}")
        print(f"   现金: ${float(account.cash):,.2f}")
        print(f"   买入力: ${float(account.buying_power):,.2f}")
        print()
        
        # 检查最近订单（扩展时间范围）
        from datetime import datetime, timedelta
        from alpaca.trading.requests import GetOrdersRequest
        
        print("📊 扩展订单搜索（最近7天）:")
        
        # 尝试不同的时间范围
        for days in [1, 3, 7, 30]:
            try:
                after_date = datetime.now() - timedelta(days=days)
                orders = trading_client.get_orders(
                    GetOrdersRequest(
                        limit=50,
                        after=after_date
                    )
                )
                print(f"   最近{days}天: {len(orders)}个订单")
                
                if len(orders) > 0:
                    print("   最近5个订单:")
                    for i, order in enumerate(orders[:5]):
                        status = order.status.value if hasattr(order.status, 'value') else str(order.status)
                        side = order.side.value if hasattr(order.side, 'value') else str(order.side)
                        created_time = order.created_at.strftime('%m-%d %H:%M') if order.created_at else "Unknown"
                        print(f"     {i+1}. {order.symbol} {side} {order.qty} - {status} ({created_time})")
                    break
            except Exception as e:
                print(f"   最近{days}天查询失败: {e}")
        
        # 检查持仓
        print("\n📦 当前持仓:")
        positions = trading_client.get_all_positions()
        if positions:
            for pos in positions:
                print(f"   {pos.symbol}: {pos.qty}股, 价值${float(pos.market_value):,.2f}")
        else:
            print("   无持仓")
        
        return True
        
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("🚀 Alpaca账户连接验证工具")
    print("=" * 50)
    
    success = verify_account_connection()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ 账户连接验证成功")
        print("\n💡 如果您在其他地方看到开放订单，可能是:")
        print("   1. 不同的账户（实盘 vs 纸面交易）")
        print("   2. 不同的API密钥")
        print("   3. 其他券商平台")
        print("   4. 订单已经被处理（执行或取消）")
    else:
        print("❌ 账户连接验证失败")

if __name__ == "__main__":
    main() 