"""
交易信号生成模块
实现各种交易策略的信号生成逻辑
"""

import pandas as pd
import numpy as np
from datetime import datetime, time
from typing import Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
from loguru import logger

from ..data.market_data import MarketDataProvider, TechnicalIndicators
from ..config import strategy_params


class SignalType(Enum):
    """信号类型"""
    LONG = "LONG"
    SHORT = "SHORT"
    CLOSE_LONG = "CLOSE_LONG"
    CLOSE_SHORT = "CLOSE_SHORT"
    NO_SIGNAL = "NO_SIGNAL"


class SignalStrength(Enum):
    """信号强度"""
    WEAK = "WEAK"
    MEDIUM = "MEDIUM"
    STRONG = "STRONG"


@dataclass
class TradingSignal:
    """交易信号数据结构"""
    signal_type: SignalType
    strength: SignalStrength
    timestamp: datetime
    price: float
    reason: str
    confidence: float  # 0-1之间的置信度
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    additional_data: Dict = None


class SignalGenerator:
    """信号生成器"""
    
    def __init__(self, market_data: MarketDataProvider):
        self.market_data = market_data
        self.indicators = TechnicalIndicators()
        
        # 存储历史数据用于计算
        self.current_bars: Optional[pd.DataFrame] = None
        self.orb_levels: Dict[str, float] = {}
        self.vwap_data: Optional[pd.Series] = None
        
        # 信号状态跟踪
        self.last_signal: Optional[TradingSignal] = None
        self.signal_history: List[TradingSignal] = []
        
    def update_market_data(self, symbol: str) -> bool:
        """更新市场数据"""
        try:
            self.current_bars = self.market_data.get_current_bars(symbol, limit=200)
            
            if self.current_bars.empty:
                logger.warning(f"无法获取{symbol}的市场数据")
                return False
                
            # 计算技术指标
            self.vwap_data = self.indicators.calculate_vwap(self.current_bars)
            
            # 计算开盘区间水平
            self.orb_levels = self.indicators.calculate_orb_levels(
                self.current_bars, 
                strategy_params.config.orb_period_minutes
            )
            
            return True
            
        except Exception as e:
            logger.error(f"更新市场数据失败: {e}")
            return False
    
    def check_opening_range_breakout(self, symbol: str) -> Optional[TradingSignal]:
        """检查开盘区间突破信号"""
        try:
            if self.current_bars.empty or not self.orb_levels:
                return None
            
            current_time = datetime.now().time()
            
            # 扩大ORB信号检测窗口：9:45-10:15
            orb_start = time(9, 45)
            orb_end = time(10, 15)  # 扩展15分钟
            
            if not (orb_start <= current_time <= orb_end):
                return None
            
            latest_bar = self.current_bars.iloc[-1]
            current_price = latest_bar['close']
            current_volume = latest_bar['volume']
            
            # 计算RSI
            rsi_series = self.indicators.calculate_rsi(self.current_bars)
            if rsi_series.empty:
                return None
            
            current_rsi = rsi_series.iloc[-1]
            
            # 检查成交量条件
            volume_threshold = self.orb_levels['volume'] * strategy_params.orb_volume_multiplier
            
            # 多头突破信号
            if (current_price > self.orb_levels['high'] and
                current_volume > volume_threshold and
                current_rsi > strategy_params.orb_rsi_threshold_long):
                
                confidence = min(0.9, 0.6 + 
                               (current_rsi - strategy_params.orb_rsi_threshold_long) / 20 * 0.2 +
                               (current_volume / volume_threshold - 1) * 0.1)
                
                return TradingSignal(
                    signal_type=SignalType.LONG,
                    strength=SignalStrength.STRONG if confidence > 0.8 else SignalStrength.MEDIUM,
                    timestamp=datetime.now(),
                    price=current_price,
                    reason=f"ORB多头突破: 价格{current_price:.2f} > 高点{self.orb_levels['high']:.2f}, RSI={current_rsi:.1f}",
                    confidence=confidence,
                    stop_loss=self.orb_levels['low'],
                    additional_data={
                        'orb_high': self.orb_levels['high'],
                        'orb_low': self.orb_levels['low'],
                        'volume_ratio': current_volume / volume_threshold,
                        'rsi': current_rsi
                    }
                )
            
            # 空头突破信号
            elif (current_price < self.orb_levels['low'] and
                  current_volume > volume_threshold and
                  current_rsi < strategy_params.orb_rsi_threshold_short):
                
                confidence = min(0.9, 0.6 + 
                               (strategy_params.orb_rsi_threshold_short - current_rsi) / 20 * 0.2 +
                               (current_volume / volume_threshold - 1) * 0.1)
                
                return TradingSignal(
                    signal_type=SignalType.SHORT,
                    strength=SignalStrength.STRONG if confidence > 0.8 else SignalStrength.MEDIUM,
                    timestamp=datetime.now(),
                    price=current_price,
                    reason=f"ORB空头突破: 价格{current_price:.2f} < 低点{self.orb_levels['low']:.2f}, RSI={current_rsi:.1f}",
                    confidence=confidence,
                    stop_loss=self.orb_levels['high'],
                    additional_data={
                        'orb_high': self.orb_levels['high'],
                        'orb_low': self.orb_levels['low'],
                        'volume_ratio': current_volume / volume_threshold,
                        'rsi': current_rsi
                    }
                )
            
            return None
            
        except Exception as e:
            logger.error(f"ORB信号检查失败: {e}")
            return None
    
    def check_vwap_breakout(self, symbol: str) -> Optional[TradingSignal]:
        """检查VWAP突破信号"""
        try:
            if self.current_bars.empty or self.vwap_data.empty:
                return None
                
            # 获取最近几分钟的数据
            recent_bars = self.current_bars.tail(strategy_params.vwap_confirmation_minutes)
            recent_vwap = self.vwap_data.tail(strategy_params.vwap_confirmation_minutes)
            
            if len(recent_bars) < strategy_params.vwap_confirmation_minutes:
                return None
            
            current_price = recent_bars['close'].iloc[-1]
            current_vwap = recent_vwap.iloc[-1]
            
            # 计算VWAP偏离百分比
            vwap_deviation = (current_price - current_vwap) / current_vwap * 100
            
            # 计算MACD
            macd_data = self.indicators.calculate_macd(self.current_bars)
            if macd_data['histogram'].empty:
                return None
                
            current_macd_hist = macd_data['histogram'].iloc[-1]
            prev_macd_hist = macd_data['histogram'].iloc[-2] if len(macd_data['histogram']) > 1 else 0
            
            # 检查价格是否持续在VWAP上方/下方
            threshold_pct = strategy_params.vwap_breakout_threshold
            
            # 多头信号：价格持续在VWAP+0.15%上方，MACD柱状图转正
            if (vwap_deviation > threshold_pct and
                all(recent_bars['close'] > recent_vwap * (1 + threshold_pct/100)) and
                current_macd_hist > prev_macd_hist and current_macd_hist > 0):
                
                confidence = min(0.85, 0.5 + abs(vwap_deviation) / threshold_pct * 0.2 + 
                               (current_macd_hist / max(abs(current_macd_hist), 0.001)) * 0.15)
                
                return TradingSignal(
                    signal_type=SignalType.LONG,
                    strength=SignalStrength.MEDIUM,
                    timestamp=datetime.now(),
                    price=current_price,
                    reason=f"VWAP多头突破: 偏离{vwap_deviation:.2f}%, MACD转正",
                    confidence=confidence,
                    additional_data={
                        'vwap': current_vwap,
                        'vwap_deviation': vwap_deviation,
                        'macd_histogram': current_macd_hist
                    }
                )
            
            # 空头信号：价格持续在VWAP-0.15%下方，MACD柱状图转负
            elif (vwap_deviation < -threshold_pct and
                  all(recent_bars['close'] < recent_vwap * (1 - threshold_pct/100)) and
                  current_macd_hist < prev_macd_hist and current_macd_hist < 0):
                
                confidence = min(0.85, 0.5 + abs(vwap_deviation) / threshold_pct * 0.2 + 
                               abs(current_macd_hist) / max(abs(current_macd_hist), 0.001) * 0.15)
                
                return TradingSignal(
                    signal_type=SignalType.SHORT,
                    strength=SignalStrength.MEDIUM,
                    timestamp=datetime.now(),
                    price=current_price,
                    reason=f"VWAP空头突破: 偏离{vwap_deviation:.2f}%, MACD转负",
                    confidence=confidence,
                    additional_data={
                        'vwap': current_vwap,
                        'vwap_deviation': vwap_deviation,
                        'macd_histogram': current_macd_hist
                    }
                )
                
            return None
            
        except Exception as e:
            logger.error(f"VWAP信号检查失败: {e}")
            return None
    
    def check_reversal_signals(self, symbol: str) -> Optional[TradingSignal]:
        """检查反转信号（适用于尾盘）"""
        try:
            current_time = datetime.now().time()
            
            # 只在14:30-15:00之间检查反转信号
            reversal_start = time(14, 30)
            reversal_end = time(15, 0)
            
            if not (reversal_start <= current_time <= reversal_end):
                return None
                
            if self.current_bars.empty:
                return None
            
            # 计算当日涨跌幅
            day_bars = self.current_bars[self.current_bars['timestamp'].dt.date == datetime.now().date()]
            if day_bars.empty:
                return None
                
            day_open = day_bars['open'].iloc[0]
            current_price = day_bars['close'].iloc[-1]
            daily_return = (current_price - day_open) / day_open * 100
            
            # 计算5分钟RSI
            bars_5min = self.current_bars.groupby(self.current_bars['timestamp'].dt.floor('5Min')).agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }).reset_index()
            
            rsi_5min = self.indicators.calculate_rsi(bars_5min, period=14)
            if rsi_5min.empty or len(rsi_5min) < 2:
                return None
                
            current_rsi_5min = rsi_5min.iloc[-1]
            prev_rsi_5min = rsi_5min.iloc[-2]
            
            # 计算成交量趋势
            recent_volume = self.current_bars.tail(10)['volume'].mean()
            earlier_volume = self.current_bars.tail(20).head(10)['volume'].mean()
            volume_trend = recent_volume / earlier_volume if earlier_volume > 0 else 1
            
            # 多头反转信号：当日跌幅>=0.8%，RSI从30向上，缩量
            if (daily_return <= -0.8 and
                current_rsi_5min > prev_rsi_5min and
                current_rsi_5min > 30 and
                prev_rsi_5min <= 35 and
                volume_trend < 0.8):
                
                confidence = min(0.8, 0.4 + abs(daily_return) / 0.8 * 0.2 + 
                               (1 - volume_trend) * 0.2)
                
                return TradingSignal(
                    signal_type=SignalType.LONG,
                    strength=SignalStrength.WEAK,
                    timestamp=datetime.now(),
                    price=current_price,
                    reason=f"尾盘多头反转: 日跌幅{daily_return:.2f}%, RSI回升, 缩量",
                    confidence=confidence,
                    additional_data={
                        'daily_return': daily_return,
                        'rsi_5min': current_rsi_5min,
                        'volume_trend': volume_trend
                    }
                )
            
            # 空头反转信号：当日涨幅>=0.8%，RSI从70向下，缩量
            elif (daily_return >= 0.8 and
                  current_rsi_5min < prev_rsi_5min and
                  current_rsi_5min < 70 and
                  prev_rsi_5min >= 65 and
                  volume_trend < 0.8):
                
                confidence = min(0.8, 0.4 + daily_return / 0.8 * 0.2 + 
                               (1 - volume_trend) * 0.2)
                
                return TradingSignal(
                    signal_type=SignalType.SHORT,
                    strength=SignalStrength.WEAK,
                    timestamp=datetime.now(),
                    price=current_price,
                    reason=f"尾盘空头反转: 日涨幅{daily_return:.2f}%, RSI回落, 缩量",
                    confidence=confidence,
                    additional_data={
                        'daily_return': daily_return,
                        'rsi_5min': current_rsi_5min,
                        'volume_trend': volume_trend
                    }
                )
                
            return None
            
        except Exception as e:
            logger.error(f"反转信号检查失败: {e}")
            return None
    
    def check_intraday_breakout(self, symbol: str) -> Optional[TradingSignal]:
        """检查日内盘整突破信号"""
        try:
            current_time = datetime.now().time()
            
            # 在11:30-12:30之间检查日内突破
            breakout_start = time(11, 30)
            breakout_end = time(12, 30)
            
            if not (breakout_start <= current_time <= breakout_end):
                return None
                
            if self.current_bars.empty:
                return None
            
            # 获取前两小时的数据（9:30-11:30）
            morning_start = time(9, 30)
            morning_end = time(11, 30)
            
            morning_bars = self.current_bars[
                (self.current_bars['timestamp'].dt.time >= morning_start) & 
                (self.current_bars['timestamp'].dt.time <= morning_end)
            ]
            
            if morning_bars.empty:
                return None
                
            # 计算盘整区间
            range_high = morning_bars['high'].max()
            range_low = morning_bars['low'].min()
            range_volume = morning_bars['volume'].mean()
            
            # 获取当前数据
            latest_bar = self.current_bars.iloc[-1]
            current_price = latest_bar['close']
            current_volume = latest_bar['volume']
            
            # 检查是否为有效突破
            price_move_pct = 0
            volume_multiplier = current_volume / range_volume if range_volume > 0 else 1
            
            # 向上突破
            if current_price > range_high:
                price_move_pct = (current_price - range_high) / range_high * 100
                
                if price_move_pct >= 0.6 and volume_multiplier >= 1.5:
                    confidence = min(0.8, 0.4 + min(price_move_pct / 0.6, 1) * 0.2 + 
                                   min(volume_multiplier / 1.5, 1) * 0.2)
                    
                    return TradingSignal(
                        signal_type=SignalType.LONG,
                        strength=SignalStrength.MEDIUM,
                        timestamp=datetime.now(),
                        price=current_price,
                        reason=f"日内向上突破: 涨幅{price_move_pct:.2f}%, 量能放大{volume_multiplier:.1f}倍",
                        confidence=confidence,
                        stop_loss=range_low,
                        additional_data={
                            'range_high': range_high,
                            'range_low': range_low,
                            'price_move_pct': price_move_pct,
                            'volume_multiplier': volume_multiplier
                        }
                    )
            
            # 向下突破
            elif current_price < range_low:
                price_move_pct = (range_low - current_price) / range_low * 100
                
                if price_move_pct >= 0.6 and volume_multiplier >= 1.5:
                    confidence = min(0.8, 0.4 + min(price_move_pct / 0.6, 1) * 0.2 + 
                                   min(volume_multiplier / 1.5, 1) * 0.2)
                    
                    return TradingSignal(
                        signal_type=SignalType.SHORT,
                        strength=SignalStrength.MEDIUM,
                        timestamp=datetime.now(),
                        price=current_price,
                        reason=f"日内向下突破: 跌幅{price_move_pct:.2f}%, 量能放大{volume_multiplier:.1f}倍",
                        confidence=confidence,
                        stop_loss=range_high,
                        additional_data={
                            'range_high': range_high,
                            'range_low': range_low,
                            'price_move_pct': price_move_pct,
                            'volume_multiplier': volume_multiplier
                        }
                    )
                    
            return None
            
        except Exception as e:
            logger.error(f"日内突破信号检查失败: {e}")
            return None
    
    def generate_signals(self, symbol: str) -> List[TradingSignal]:
        """生成所有信号"""
        signals = []
        
        # 更新市场数据
        if not self.update_market_data(symbol):
            return signals
        
        # 检查各种信号
        signal_methods = [
            self.check_opening_range_breakout,
            self.check_vwap_breakout,
            self.check_reversal_signals,
            self.check_intraday_breakout
        ]
        
        for method in signal_methods:
            try:
                signal = method(symbol)
                if signal:
                    signals.append(signal)
                    logger.info(f"生成信号: {signal.signal_type.value} - {signal.reason}")
            except Exception as e:
                logger.error(f"信号生成方法{method.__name__}失败: {e}")
                
        # 更新信号历史
        for signal in signals:
            self.signal_history.append(signal)
            self.last_signal = signal
        
        # 限制历史记录长度
        if len(self.signal_history) > 100:
            self.signal_history = self.signal_history[-100:]
            
        return signals
    
    def get_signal_summary(self) -> Dict:
        """获取信号摘要"""
        if not self.signal_history:
            return {"total_signals": 0, "recent_signals": []}
        
        recent_signals = self.signal_history[-10:]
        
        return {
            "total_signals": len(self.signal_history),
            "recent_signals": [
                {
                    "type": s.signal_type.value,
                    "strength": s.strength.value,
                    "timestamp": s.timestamp.isoformat(),
                    "price": s.price,
                    "reason": s.reason,
                    "confidence": s.confidence
                }
                for s in recent_signals
            ],
            "last_signal": {
                "type": self.last_signal.signal_type.value,
                "timestamp": self.last_signal.timestamp.isoformat(),
                "price": self.last_signal.price,
                "confidence": self.last_signal.confidence
            } if self.last_signal else None
        } 