"""
测试新的Alpaca HTTP API获取期权链数据
"""

import os
import sys
from datetime import datetime
from loguru import logger

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import config
from src.data.market_data import MarketDataProvider

def test_new_option_chain_api():
    """测试新的HTTP API获取期权链数据"""
    try:
        logger.info("=" * 60)
        logger.info("🚀 测试新的Alpaca HTTP API获取期权链数据")
        logger.info("=" * 60)
        
        # 初始化市场数据提供者
        market_data = MarketDataProvider(config)
        
        # 测试获取SPY期权链
        symbol = "SPY"
        logger.info(f"📊 开始获取 {symbol} 期权链数据...")
        
        start_time = datetime.now()
        option_chain = market_data.get_option_chain(symbol)
        end_time = datetime.now()
        
        total_time = (end_time - start_time).total_seconds()
        
        if option_chain:
            calls = option_chain.get('calls', [])
            puts = option_chain.get('puts', [])
            underlying_price = option_chain.get('underlying_price', 0)
            
            logger.info(f"✅ 期权链数据获取成功!")
            logger.info(f"📈 标的价格: ${underlying_price:.2f}")
            logger.info(f"📞 看涨期权: {len(calls)}个")
            logger.info(f"📞 看跌期权: {len(puts)}个")
            logger.info(f"⏱️  总用时: {total_time:.2f}秒")
            
            # 显示一些示例期权数据
            if calls:
                logger.info("\n🔍 看涨期权示例 (前5个):")
                for i, call in enumerate(calls[:5]):
                    logger.info(
                        f"  {i+1}. {call['contractSymbol']} | "
                        f"Strike: ${call['strike']:.2f} | "
                        f"Bid: ${call['bid']:.2f} | "
                        f"Ask: ${call['ask']:.2f} | "
                        f"Delta: {call['delta']:.3f} | "
                        f"到期: {call['expiry']}"
                    )
            
            if puts:
                logger.info("\n🔍 看跌期权示例 (前5个):")
                for i, put in enumerate(puts[:5]):
                    logger.info(
                        f"  {i+1}. {put['contractSymbol']} | "
                        f"Strike: ${put['strike']:.2f} | "
                        f"Bid: ${put['bid']:.2f} | "
                        f"Ask: ${put['ask']:.2f} | "
                        f"Delta: {put['delta']:.3f} | "
                        f"到期: {put['expiry']}"
                    )
            
            # 统计不同到期日的期权数量
            expiry_counts = {}
            for option in calls + puts:
                expiry = option['expiry']
                expiry_counts[expiry] = expiry_counts.get(expiry, 0) + 1
            
            logger.info(f"\n📅 不同到期日的期权分布:")
            for expiry, count in sorted(expiry_counts.items())[:10]:  # 显示前10个到期日
                logger.info(f"  {expiry}: {count}个期权")
            
            # 检查当日到期期权
            today = datetime.now().strftime('%Y-%m-%d')
            today_options = [opt for opt in calls + puts if opt['expiry'] == today]
            logger.info(f"\n📆 今日到期期权: {len(today_options)}个")
            
            return True
        else:
            logger.error("❌ 未获取到期权链数据")
            return False
            
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_multiple_symbols():
    """测试多个股票的期权链获取"""
    symbols = ["SPY", "QQQ", "AAPL"]
    logger.info(f"\n🔄 测试多个股票期权链获取: {symbols}")
    
    market_data = MarketDataProvider(config)
    
    for symbol in symbols:
        try:
            logger.info(f"\n📊 获取 {symbol} 期权链...")
            start_time = datetime.now()
            option_chain = market_data.get_option_chain(symbol)
            end_time = datetime.now()
            
            if option_chain:
                calls_count = len(option_chain.get('calls', []))
                puts_count = len(option_chain.get('puts', []))
                total_time = (end_time - start_time).total_seconds()
                
                logger.info(f"✅ {symbol}: {calls_count}个看涨 + {puts_count}个看跌期权，用时{total_time:.2f}秒")
            else:
                logger.warning(f"⚠️  {symbol}: 未获取到期权数据")
                
        except Exception as e:
            logger.error(f"❌ {symbol}: 获取失败 - {e}")

if __name__ == "__main__":
    # 测试基本功能
    success = test_new_option_chain_api()
    
    if success:
        # 测试多个股票
        test_multiple_symbols()
        
        logger.info("\n" + "=" * 60)
        logger.info("🎉 新API测试完成!")
        logger.info("=" * 60)
    else:
        logger.error("❌ 基础测试失败，跳过多股票测试") 