#!/usr/bin/env python3
"""
调试Alpaca SDK的get_option_chain方法
检查返回的数据结构
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv
import json

# 加载环境变量
load_dotenv()

# 添加src路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from alpaca.data.historical import OptionHistoricalDataClient
from alpaca.data.requests import OptionChainRequest
from config import config


def debug_option_chain():
    """调试期权链获取"""
    
    print("🔍 调试Alpaca SDK期权链获取")
    print("="*60)
    
    try:
        # 创建期权数据客户端
        option_client = OptionHistoricalDataClient(
            api_key=config.alpaca_api_key,
            secret_key=config.alpaca_secret_key
        )
        
        print(f"📡 创建期权客户端成功")
        print(f"🔑 API Key: {config.alpaca_api_key[:10]}...")
        
        # 获取期权链
        print(f"\n📊 调用get_option_chain方法...")
        start_time = datetime.now()
        
        option_chain_request = OptionChainRequest(underlying_symbol="SPY")
        print(f"📋 请求参数: underlying_symbol=SPY")
        
        option_chain_response = option_client.get_option_chain(option_chain_request)
        
        end_time = datetime.now()
        elapsed = (end_time - start_time).total_seconds()
        
        print(f"⏱️ 请求耗时: {elapsed:.2f}秒")
        print(f"📦 响应类型: {type(option_chain_response)}")
        
        # 检查响应内容
        if isinstance(option_chain_response, dict):
            print(f"📄 响应是字典，键: {list(option_chain_response.keys())}")
            
            for key, value in option_chain_response.items():
                print(f"   🔸 {key}: {type(value)} - {len(value) if hasattr(value, '__len__') else str(value)[:100]}")
                
                # 如果是列表且非空，显示前几个元素
                if isinstance(value, list) and value:
                    print(f"      样本: {value[:3]}")
                    
        else:
            print(f"📄 响应是对象")
            if hasattr(option_chain_response, '__dict__'):
                print(f"   属性: {list(option_chain_response.__dict__.keys())}")
            if hasattr(option_chain_response, 'option_symbols'):
                symbols = option_chain_response.option_symbols
                print(f"   期权符号数量: {len(symbols) if hasattr(symbols, '__len__') else 'unknown'}")
                
        # 尝试JSON序列化
        try:
            if hasattr(option_chain_response, '__dict__'):
                json_str = json.dumps(option_chain_response.__dict__, default=str, indent=2)
            else:
                json_str = json.dumps(option_chain_response, default=str, indent=2)
            
            print(f"\n📋 响应内容 (JSON):")
            # 只显示前500个字符
            if len(json_str) > 500:
                print(json_str[:500] + "...")
            else:
                print(json_str)
                
        except Exception as e:
            print(f"⚠️ JSON序列化失败: {e}")
        
    except Exception as e:
        print(f"❌ 调试失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n✅ 调试完成")


if __name__ == "__main__":
    debug_option_chain() 