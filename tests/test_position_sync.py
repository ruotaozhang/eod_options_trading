#!/usr/bin/env python3
"""
测试持仓同步功能
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.config import config
from src.data.market_data import MarketDataProvider
from src.trading.executor import TradingExecutor
from src.utils.logger_setup import setup_logger

def test_position_sync():
    """测试持仓同步功能"""
    print("🧪 测试持仓同步功能")
    print("=" * 50)
    
    try:
        # 初始化日志
        setup_logger()
        
        # 创建市场数据提供者和交易执行器
        print("正在初始化交易执行器...")
        market_data = MarketDataProvider()
        executor = TradingExecutor(market_data)  # 这会自动调用sync_existing_positions()
        
        # 获取持仓摘要
        position_summary = executor.get_position_summary()
        
        print("\n📊 持仓同步结果:")
        print(f"   系统中的持仓数: {position_summary['total_positions']}")
        print(f"   未实现盈亏: ${position_summary['total_unrealized_pnl']:.2f}")
        print(f"   当日总盈亏: ${position_summary['daily_pnl']:.2f}")
        print(f"   当日已实现盈亏: ${position_summary['daily_realized_pnl']:.2f}")
        print(f"   当日交易次数: {position_summary['daily_trades']}")
        
        if position_summary['total_positions'] > 0:
            print("\n📋 持仓详情:")
            for i, pos in enumerate(position_summary['positions'], 1):
                print(f"   {i}. {pos['symbol']}")
                print(f"      类型: {pos['type']}")
                print(f"      数量: {pos['quantity']}张")
                print(f"      入场价: ${pos['entry_price']:.2f}")
                print(f"      当前价: ${pos['current_price']:.2f}")
                print(f"      盈亏: ${pos['unrealized_pnl']:.2f}")
                
                # 计算盈亏百分比
                pnl_pct = (pos['unrealized_pnl'] / (pos['entry_price'] * pos['quantity'] * 100)) * 100
                print(f"      盈亏率: {pnl_pct:.2f}%")
                print()
        else:
            print("⚠️ 系统中没有持仓")
        
        # 获取风险摘要
        risk_summary = executor.get_risk_summary()
        print("💰 风险管理信息:")
        print(f"   账户价值: ${risk_summary['account_value']:.2f}")
        print(f"   买入力: ${risk_summary['buying_power']:.2f}")
        print(f"   最大日风险: ${risk_summary['max_daily_risk']:.2f}")
        print(f"   当前风险使用: ${risk_summary['current_risk_used']:.2f}")
        print(f"   风险使用率: {risk_summary['risk_utilization_pct']:.1f}%")
        
        return position_summary['total_positions']
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 0

def main():
    """主函数"""
    print("🚀 持仓同步功能测试")
    print("=" * 50)
    
    synced_positions = test_position_sync()
    
    print("=" * 50)
    print("📋 测试结果:")
    if synced_positions > 0:
        print(f"✅ 成功同步了 {synced_positions} 个持仓")
        print("现在您的交易系统应该能正确显示持仓数量和盈亏")
        print("\n💡 说明:")
        print("   当日总盈亏 = 当日已实现盈亏 + 未实现盈亏")
        print("   对于现有持仓，已实现盈亏通常为0（因为是之前的持仓）")
        print("   当日总盈亏主要反映当前持仓的浮动盈亏")
    else:
        print("❌ 没有同步到任何持仓")
        print("可能是账户没有持仓，或者同步过程中出错")

if __name__ == "__main__":
    main() 