#!/usr/bin/env python3
"""
账户信息查看器
直接从Alpaca API获取并显示真实的账户信息
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent))

def main():
    """主函数"""
    print("💰 Alpaca账户信息查看器")
    print("=" * 50)
    
    try:
        # 导入配置
        from src.config import config
        from src.data.market_data import MarketDataProvider
        from src.trading.executor import TradingExecutor
        
        print("🔗 正在连接Alpaca API...")
        
        # 创建交易执行器
        market_data = MarketDataProvider()
        executor = TradingExecutor(market_data)
        
        # 获取账户信息
        account_info = executor.get_account_summary()
        
        if 'error' in account_info:
            print(f"❌ 获取账户信息失败: {account_info['error']}")
            print("\n🔧 请检查以下配置：")
            print("   1. ALPACA_API_KEY 是否正确")
            print("   2. ALPACA_SECRET_KEY 是否正确")  
            print("   3. ALPACA_BASE_URL 是否正确")
            print("   4. 网络连接是否正常")
            return
        
        print("✅ 成功获取账户信息\n")
        
        # 显示账户信息
        print("📊 账户详情:")
        print(f"   💵 账户总值: ${account_info['account_value']:,.2f}")
        print(f"   💳 可用资金: ${account_info['buying_power']:,.2f}")
        print(f"   📊 数据来源: {account_info['api_source']}")
        print(f"   🧪 纸面交易: {'是' if account_info['paper_trading'] else '否'}")
        
        print("\n🛡️ 风险管理设置:")
        print(f"   📈 每日最大风险: ${account_info['max_daily_risk']:,.2f} ({account_info['max_daily_risk_pct']}%)")
        print(f"   🎯 单笔最大风险: {account_info['max_single_trade_risk_pct']}% 约${account_info['account_value'] * account_info['max_single_trade_risk_pct'] / 100:,.2f}")
        print(f"   🔢 每日最大交易: {account_info['max_trades_today']}笔")
        
        print("\n💡 重要说明:")
        print("   • 账户资金直接从Alpaca API获取，无需手动配置")
        print("   • 所有风险计算基于实时账户价值进行")
        print("   • 纸面交易账户可随时重置资金金额")
        
    except ImportError as e:
        print(f"❌ 导入模块失败: {e}")
        print("💡 请确保在项目根目录运行此脚本")
    except Exception as e:
        print(f"❌ 程序运行失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 