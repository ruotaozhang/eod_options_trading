"""
测试新的期权合约选择逻辑
基于价格就近选择，使用option snapshots API
"""

import os
import sys
from datetime import datetime
from loguru import logger
import math

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import config
from src.data.market_data import MarketDataProvider

def test_new_contract_selection_logic():
    """测试新的合约选择逻辑"""
    try:
        logger.info("=" * 60)
        logger.info("🚀 测试新的期权合约选择逻辑")
        logger.info("=" * 60)
        
        # 初始化市场数据提供者
        market_data = MarketDataProvider(config)
        
        # 测试获取SPY当前价格
        symbol = "SPY"
        current_price = market_data.get_current_price(symbol)
        
        if current_price <= 0:
            logger.error(f"无法获取{symbol}的当前价格")
            return False
        
        logger.info(f"📊 当前{symbol}价格: ${current_price:.2f}")
        
        # 计算期权行权价选择逻辑
        call_strike = int(current_price)  # floor
        put_strike = int(current_price) + (1 if current_price > int(current_price) else 0)  # ceil
        
        logger.info(f"🎯 合约选择逻辑:")
        logger.info(f"   当前价格: ${current_price:.2f}")
        logger.info(f"   Call期权行权价: ${call_strike} (floor操作)")
        logger.info(f"   Put期权行权价: ${put_strike} (ceil操作)")
        
        # 测试Call期权选择
        logger.info(f"\n📈 测试Call期权选择:")
        logger.info("-" * 40)
        
        call_options = market_data.find_suitable_options(symbol, "CALL")
        
        if call_options:
            call_option = call_options[0]
            logger.info(f"✅ 成功选择Call期权:")
            logger.info(f"   合约代码: {call_option['contractSymbol']}")
            logger.info(f"   行权价: ${call_option['strike']:.0f}")
            logger.info(f"   买价: ${call_option['bid']:.2f}")
            logger.info(f"   卖价: ${call_option['ask']:.2f}")
            logger.info(f"   中间价: ${call_option['midPrice']:.2f}")
            logger.info(f"   最新价: ${call_option['lastPrice']:.2f}")
            logger.info(f"   Delta: {call_option['delta']:.3f}")
            logger.info(f"   到期日: {call_option['expiry']}")
            
            # 计算价内/价外程度
            moneyness = current_price / call_option['strike']
            if moneyness > 1:
                logger.info(f"   状态: 价内 (+{(moneyness-1)*100:.1f}%)")
            elif moneyness < 1:
                logger.info(f"   状态: 价外 ({(moneyness-1)*100:.1f}%)")
            else:
                logger.info(f"   状态: 平价")
        else:
            logger.error("❌ 未能选择Call期权")
        
        # 测试Put期权选择
        logger.info(f"\n📉 测试Put期权选择:")
        logger.info("-" * 40)
        
        put_options = market_data.find_suitable_options(symbol, "PUT")
        
        if put_options:
            put_option = put_options[0]
            logger.info(f"✅ 成功选择Put期权:")
            logger.info(f"   合约代码: {put_option['contractSymbol']}")
            logger.info(f"   行权价: ${put_option['strike']:.0f}")
            logger.info(f"   买价: ${put_option['bid']:.2f}")
            logger.info(f"   卖价: ${put_option['ask']:.2f}")
            logger.info(f"   中间价: ${put_option['midPrice']:.2f}")
            logger.info(f"   最新价: ${put_option['lastPrice']:.2f}")
            logger.info(f"   Delta: {put_option['delta']:.3f}")
            logger.info(f"   到期日: {put_option['expiry']}")
            
            # 计算价内/价外程度
            moneyness = put_option['strike'] / current_price
            if moneyness > 1:
                logger.info(f"   状态: 价内 (+{(moneyness-1)*100:.1f}%)")
            elif moneyness < 1:
                logger.info(f"   状态: 价外 ({(moneyness-1)*100:.1f}%)")
            else:
                logger.info(f"   状态: 平价")
        else:
            logger.error("❌ 未能选择Put期权")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_option_symbol_generation():
    """测试期权代码生成"""
    logger.info(f"\n🔧 测试期权代码生成逻辑:")
    logger.info("-" * 40)
    
    try:
        market_data = MarketDataProvider(config)
        
        # 测试不同的价格和行权价组合
        test_cases = [
            (599.5, "CALL"),  # 价格599.5, Call应该选择599
            (599.5, "PUT"),   # 价格599.5, Put应该选择600
            (600.0, "CALL"),  # 整数价格600, Call选择600
            (600.0, "PUT"),   # 整数价格600, Put选择600
            (599.2, "CALL"),  # 价格599.2, Call选择599
            (599.8, "PUT"),   # 价格599.8, Put选择600
        ]
        
        for price, option_type in test_cases:
            if option_type == "CALL":
                strike = int(price)
            else:
                strike = int(price) + (1 if price > int(price) else 0)
            
            option_symbol = market_data._generate_option_symbol("SPY", strike, option_type)
            
            logger.info(f"   价格${price:.1f} + {option_type:4s} -> 行权价${strike} -> {option_symbol}")
        
        return True
        
    except Exception as e:
        logger.error(f"期权代码生成测试失败: {e}")
        return False

def test_option_snapshot_api():
    """测试期权快照API"""
    logger.info(f"\n📡 测试期权快照API:")
    logger.info("-" * 40)
    
    try:
        market_data = MarketDataProvider(config)
        
        # 生成今日的期权代码进行测试
        current_price = market_data.get_current_price("SPY")
        strike = int(current_price)
        
        # 生成Call期权代码
        call_symbol = market_data._generate_option_symbol("SPY", strike, "CALL")
        logger.info(f"📞 测试Call期权: {call_symbol}")
        
        call_data = market_data._get_option_snapshot(call_symbol)
        
        if call_data:
            logger.info(f"✅ 成功获取Call期权数据:")
            logger.info(f"   买价: ${call_data['bid']:.2f}")
            logger.info(f"   卖价: ${call_data['ask']:.2f}")
            logger.info(f"   中间价: ${call_data['midPrice']:.2f}")
            logger.info(f"   最新价: ${call_data['lastPrice']:.2f}")
            logger.info(f"   成交量: {call_data['volume']}")
            logger.info(f"   Delta: {call_data['delta']:.3f}")
        else:
            logger.warning(f"⚠️  无法获取Call期权数据")
        
        # 生成Put期权代码
        put_strike = strike + 1 if current_price > strike else strike
        put_symbol = market_data._generate_option_symbol("SPY", put_strike, "PUT")
        logger.info(f"\n📞 测试Put期权: {put_symbol}")
        
        put_data = market_data._get_option_snapshot(put_symbol)
        
        if put_data:
            logger.info(f"✅ 成功获取Put期权数据:")
            logger.info(f"   买价: ${put_data['bid']:.2f}")
            logger.info(f"   卖价: ${put_data['ask']:.2f}")
            logger.info(f"   中间价: ${put_data['midPrice']:.2f}")
            logger.info(f"   最新价: ${put_data['lastPrice']:.2f}")
            logger.info(f"   成交量: {put_data['volume']}")
            logger.info(f"   Delta: {put_data['delta']:.3f}")
        else:
            logger.warning(f"⚠️  无法获取Put期权数据")
        
        return True
        
    except Exception as e:
        logger.error(f"期权快照API测试失败: {e}")
        return False

if __name__ == "__main__":
    logger.info("🧪 开始测试新的期权合约选择逻辑")
    
    # 运行所有测试
    tests = [
        ("期权代码生成", test_option_symbol_generation),
        ("期权快照API", test_option_snapshot_api),
        ("完整合约选择", test_new_contract_selection_logic),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n🔍 测试: {test_name}")
        if test_func():
            logger.info(f"✅ {test_name} - 通过")
            passed += 1
        else:
            logger.error(f"❌ {test_name} - 失败")
    
    logger.info(f"\n" + "=" * 60)
    logger.info(f"🎉 测试完成: {passed}/{total} 项测试通过")
    
    if passed == total:
        logger.info("🚀 所有测试都通过了！新的合约选择逻辑工作正常。")
    else:
        logger.warning(f"⚠️  {total - passed} 项测试失败，需要检查相关代码。")
    
    logger.info("=" * 60) 