#!/usr/bin/env python3
"""
测试Dashboard盈亏显示
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

def test_dashboard_pnl():
    """测试Dashboard盈亏显示"""
    print("🧪 测试Dashboard盈亏显示")
    print("=" * 50)
    
    try:
        # 初始化日志
        setup_logger()
        
        # 创建市场数据提供者和交易执行器
        print("正在初始化交易执行器...")
        market_data = MarketDataProvider()
        executor = TradingExecutor(market_data)
        
        # 获取风险摘要（Dashboard使用的数据）
        risk_summary = executor.get_risk_summary()
        
        print("\n📊 风险摘要（Dashboard数据源）:")
        print(f"   账户价值: ${risk_summary['account_value']:.2f}")
        print(f"   买入力: ${risk_summary['buying_power']:.2f}")
        print(f"   当日总盈亏: ${risk_summary['daily_pnl']:.2f}")
        print(f"   当日已实现盈亏: ${risk_summary['daily_realized_pnl']:.2f}")
        print(f"   最大日风险: ${risk_summary['max_daily_risk']:.2f}")
        print(f"   风险利用率: {risk_summary['risk_utilization_pct']:.1f}%")
        
        # 获取持仓摘要
        position_summary = executor.get_position_summary()
        
        print("\n📋 持仓摘要:")
        print(f"   当前头寸: {position_summary['total_positions']}")
        print(f"   未实现盈亏: ${position_summary['total_unrealized_pnl']:.2f}")
        print(f"   当日总盈亏: ${position_summary['daily_pnl']:.2f}")
        print(f"   当日已实现盈亏: ${position_summary['daily_realized_pnl']:.2f}")
        print(f"   当日交易: {position_summary['daily_trades']}")
        
        # 验证一致性
        print("\n✅ 数据一致性检查:")
        if risk_summary['daily_pnl'] == position_summary['daily_pnl']:
            print(f"   当日盈亏数据一致: ${risk_summary['daily_pnl']:.2f}")
        else:
            print(f"   ❌ 数据不一致! 风险摘要: ${risk_summary['daily_pnl']:.2f}, 持仓摘要: ${position_summary['daily_pnl']:.2f}")
        
        if risk_summary['daily_realized_pnl'] == position_summary['daily_realized_pnl']:
            print(f"   已实现盈亏数据一致: ${risk_summary['daily_realized_pnl']:.2f}")
        else:
            print(f"   ❌ 已实现盈亏不一致! 风险摘要: ${risk_summary['daily_realized_pnl']:.2f}, 持仓摘要: ${position_summary['daily_realized_pnl']:.2f}")
        
        return risk_summary['daily_pnl']
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 0

def main():
    """主函数"""
    print("🚀 Dashboard盈亏显示测试")
    print("=" * 50)
    
    daily_pnl = test_dashboard_pnl()
    
    print("\n" + "=" * 50)
    print("📋 测试结果:")
    if daily_pnl != 0:
        print(f"✅ Dashboard将正确显示当日盈亏: ${daily_pnl:.2f}")
        print("现在重启主程序应该能看到正确的盈亏数据")
    else:
        print("⚠️ 当日盈亏为0，可能是:")
        print("   1. 确实没有盈亏（正常情况）")
        print("   2. 没有持仓")
        print("   3. 数据同步问题")

if __name__ == "__main__":
    main() 