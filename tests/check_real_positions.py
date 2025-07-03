#!/usr/bin/env python3
"""
检查Alpaca账户实际持仓
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.config import config
from alpaca.trading.client import TradingClient

def check_real_positions():
    """检查实际持仓"""
    print("🔍 检查Alpaca账户实际持仓")
    print("=" * 50)
    
    try:
        # 创建交易客户端
        trading_client = TradingClient(
            api_key=config.alpaca_api_key,
            secret_key=config.alpaca_secret_key,
            paper=True if "paper" in config.alpaca_base_url else False
        )
        
        # 获取所有持仓
        positions = trading_client.get_all_positions()
        
        print(f"📊 账户类型: {'纸面交易' if 'paper' in config.alpaca_base_url else '实盘'}")
        print(f"📦 总持仓数量: {len(positions)}")
        print()
        
        if not positions:
            print("❌ 账户当前没有任何持仓")
            return 0, 0
        
        print("📋 持仓详情:")
        print("-" * 80)
        print(f"{'符号':<20} {'数量':<10} {'成本':<12} {'市值':<12} {'盈亏':<12} {'类型'}")
        print("-" * 80)
        
        total_market_value = 0
        total_unrealized_pnl = 0
        
        for position in positions:
            try:
                symbol = position.symbol
                qty = float(position.qty)
                avg_entry_price = float(position.avg_entry_price)
                market_value = float(position.market_value)
                
                # 尝试获取未实现盈亏，使用不同的可能属性名
                unrealized_pnl = 0.0
                for attr_name in ['unrealized_pnl', 'unrealized_pl', 'pnl', 'pl']:
                    if hasattr(position, attr_name):
                        unrealized_pnl = float(getattr(position, attr_name))
                        break
                
                # 如果没有找到盈亏属性，手动计算
                if unrealized_pnl == 0.0:
                    unrealized_pnl = market_value - (avg_entry_price * qty)
                
                side = getattr(position, 'side', 'LONG')
                
                total_market_value += market_value
                total_unrealized_pnl += unrealized_pnl
                
                # 判断是否为期权
                asset_type = "期权" if len(symbol) > 10 else "股票"
                
                print(f"{symbol:<20} {qty:<10.0f} ${avg_entry_price:<11.2f} ${market_value:<11.2f} ${unrealized_pnl:<11.2f} {asset_type}")
                
            except Exception as e:
                print(f"处理持仓 {getattr(position, 'symbol', 'UNKNOWN')} 时出错: {e}")
                # 输出position对象的所有属性以便调试
                print(f"   Position attributes: {[attr for attr in dir(position) if not attr.startswith('_')]}")
        
        print("-" * 80)
        print(f"{'总计':<20} {'':<10} {'':<12} ${total_market_value:<11.2f} ${total_unrealized_pnl:<11.2f}")
        print()
        
        # 检查期权持仓
        option_positions = [pos for pos in positions if len(pos.symbol) > 10]
        if option_positions:
            print("🎯 期权持仓:")
            for pos in option_positions:
                # 尝试获取盈亏信息
                pnl = 0.0
                for attr_name in ['unrealized_pnl', 'unrealized_pl', 'pnl', 'pl']:
                    if hasattr(pos, attr_name):
                        pnl = float(getattr(pos, attr_name))
                        break
                
                print(f"   {pos.symbol}: {pos.qty}张, 盈亏${pnl:.2f}")
        else:
            print("⚠️ 没有期权持仓")
        
        return len(positions), len(option_positions)
        
    except Exception as e:
        print(f"❌ 获取持仓失败: {e}")
        return 0, 0

def main():
    """主函数"""
    print("🚀 Alpaca账户持仓检查工具")
    print("=" * 50)
    
    total_positions, option_positions = check_real_positions()
    
    print("\n" + "=" * 50)
    print("📋 总结:")
    print(f"   总持仓数: {total_positions}")
    print(f"   期权持仓: {option_positions}")
    
    if total_positions > 0:
        print("\n💡 说明:")
        print("   如果您的交易系统显示0持仓，但这里显示有持仓，")
        print("   说明系统没有同步Alpaca账户的实际持仓。")
        print("   需要添加持仓同步功能。")

if __name__ == "__main__":
    main() 