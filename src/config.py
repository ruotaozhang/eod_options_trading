"""
配置管理模块
管理系统的所有配置参数，包括API密钥、交易参数等
"""

import os
from datetime import time
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class TradingConfig(BaseSettings):
    """交易配置"""
    
    # Alpaca API配置
    alpaca_api_key: str = Field(..., env="ALPACA_API_KEY")
    alpaca_secret_key: str = Field(..., env="ALPACA_SECRET_KEY")
    alpaca_base_url: str = Field(
        "https://paper-api.alpaca.markets", 
        env="ALPACA_BASE_URL"
    )
    
    # 风险管理配置 - 账户资金从API自动获取，无需手动配置
    max_daily_risk_pct: float = Field(2.0, env="MAX_DAILY_RISK_PCT")
    max_single_trade_risk_pct: float = Field(1.0, env="MAX_SINGLE_TRADE_RISK_PCT")
    max_daily_trades: int = Field(5, env="MAX_DAILY_TRADES")
    max_contracts_per_trade: int = Field(10, env="MAX_CONTRACTS_PER_TRADE")  # 单笔交易最大合约数量
    
    # 策略参数
    symbol: str = Field("SPY", env="SYMBOL")
    orb_period_minutes: int = Field(15, env="ORB_PERIOD_MINUTES")
    vwap_deviation_pct: float = Field(0.2, env="VWAP_DEVIATION_PCT")
    stop_loss_pct: float = Field(10.0, env="STOP_LOSS_PCT")
    take_profit_pct: float = Field(50.0, env="TAKE_PROFIT_PCT")
    
    # 时间配置
    trading_start_time: str = Field("09:30", env="TRADING_START_TIME")
    trading_end_time: str = Field("15:50", env="TRADING_END_TIME")
    force_close_time: str = Field("15:45", env="FORCE_CLOSE_TIME")
    
    # 监控频率配置 (秒) - 极高频实时监控
    position_check_seconds: int = Field(3, env="POSITION_CHECK_SECONDS")  # 持仓检查频率 (极高频：3秒)
    market_data_update_seconds: int = Field(3, env="MARKET_DATA_UPDATE_SECONDS")  # 市场数据更新频率 (极高频：3秒)
    signal_check_seconds: int = Field(3, env="SIGNAL_CHECK_SECONDS")  # 信号检查频率 (极高频：3秒)
    
    class Config:
        env_file = ".env"
        case_sensitive = False


class StrategyParams:
    """策略参数类"""
    
    def __init__(self, config: TradingConfig):
        self.config = config
        
        # 开盘区间突破参数 - 优化后的参数
        self.orb_volume_multiplier = 1.1  # 降低成交量要求
        self.orb_rsi_threshold_long = 55   # 降低多头RSI阈值
        self.orb_rsi_threshold_short = 45  # 提高空头RSI阈值
        
        # VWAP参数 - 优化后的参数
        self.vwap_confirmation_minutes = 2    # 减少确认时间
        self.vwap_breakout_threshold = 0.12   # 降低VWAP偏离阈值
        
        # RSI参数
        self.rsi_period = 14
        self.rsi_overbought = 70
        self.rsi_oversold = 30
        
        # MACD参数
        self.macd_fast = 12
        self.macd_slow = 26
        self.macd_signal = 9
        
        # 期权选择参数 - 移除delta相关参数，改为基于价格就近选择
        self.option_dte = 0  # 严格限制：只交易当日到期的期权 (DTE=0)
        
        # 头寸管理参数
        self.position_partial_close_pct = 50  # 首次止盈时平仓比例
        self.position_scale_in_pct = 50  # 加仓比例
        
        # 风险参数
        self.max_slippage_pct = 0.1  # 最大滑点
        self.order_timeout_seconds = 30
        

# 全局配置实例
config = TradingConfig()
strategy_params = StrategyParams(config) 