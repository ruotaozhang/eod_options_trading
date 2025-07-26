"""
市场数据模块
负责获取和处理市场数据，包括股票价格、期权链、技术指标等
"""

import pandas as pd
import numpy as np
import re
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Tuple
from alpaca.data.historical import StockHistoricalDataClient, OptionHistoricalDataClient
from alpaca.data.requests import (
    StockBarsRequest, StockLatestQuoteRequest, StockLatestTradeRequest,
    OptionChainRequest, OptionSnapshotRequest, OptionLatestTradeRequest
)
from alpaca.data.timeframe import TimeFrame
from alpaca.data.live import StockDataStream
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetAssetsRequest
import talib
import requests
from loguru import logger

from src.config import config


class MarketDataProvider:
    """市场数据提供者"""
    
    def __init__(self, config_obj=None):
        # 使用传入的配置或默认配置
        self.config = config_obj or config
        
        self.stock_client = StockHistoricalDataClient(
            api_key=self.config.alpaca_api_key,
            secret_key=self.config.alpaca_secret_key
        )
        self.option_client = OptionHistoricalDataClient(
            api_key=self.config.alpaca_api_key,
            secret_key=self.config.alpaca_secret_key
        )
        self.trading_client = TradingClient(
            api_key=self.config.alpaca_api_key,
            secret_key=self.config.alpaca_secret_key,
            paper=True if "paper" in self.config.alpaca_base_url else False
        )
        
        # 缓存数据
        self.current_bars: Dict[str, pd.DataFrame] = {}
        self.option_chains: Dict[str, Dict] = {}
        self.option_quotes: Dict[str, Dict] = {}
        self.last_update: Dict[str, datetime] = {}
        
        # API基础URL
        self.api_base_url = "https://data.alpaca.markets"
        
    def get_current_bars(self, symbol: str, timeframe: str = "1Min", 
                        limit: int = 100) -> pd.DataFrame:
        """获取当前K线数据"""
        try:
            # 检查缓存
            cache_key = f"{symbol}_{timeframe}"
            now = datetime.now()
            
            if (cache_key in self.last_update and 
                now - self.last_update[cache_key] < timedelta(seconds=30)):
                return self.current_bars.get(cache_key, pd.DataFrame())
            
            # 获取历史数据
            request = StockBarsRequest(
                symbol_or_symbols=[symbol],
                timeframe=TimeFrame.Minute,
                start=datetime.now() - timedelta(days=1),
                end=datetime.now()
            )
            
            bars = self.stock_client.get_stock_bars(request)
            df = bars.df.reset_index()
            
            if not df.empty:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df = df.sort_values('timestamp').tail(limit)
                
                # 缓存数据
                self.current_bars[cache_key] = df
                self.last_update[cache_key] = now
                
            return df
            
        except Exception as e:
            logger.error(f"获取K线数据失败: {e}")
            return pd.DataFrame()
    
    def get_latest_quote(self, symbol: str) -> Optional[Dict]:
        """获取最新报价"""
        try:
            request = StockLatestQuoteRequest(symbol_or_symbols=[symbol])
            quotes = self.stock_client.get_stock_latest_quote(request)
            
            if symbol in quotes:
                quote = quotes[symbol]
                return {
                    'bid': quote.bid_price,
                    'ask': quote.ask_price,
                    'bid_size': quote.bid_size,
                    'ask_size': quote.ask_size,
                    'timestamp': quote.timestamp
                }
            return None
            
        except Exception as e:
            logger.error(f"获取最新报价失败: {e}")
            return None
    
    def get_option_chain(self, symbol: str, expiry_date: str = None) -> Dict:
        """获取期权链数据 - 使用Alpaca HTTP API"""
        try:
            # 检查缓存
            cache_key = f"{symbol}_options"
            now = datetime.now()
            
            if (cache_key in self.last_update and 
                now - self.last_update[cache_key] < timedelta(seconds=60)):
                return self.option_chains.get(cache_key, {})
            
            # 使用Alpaca HTTP API获取期权链
            result = self._get_option_chain_http_api(symbol)
            
            # 缓存数据
            self.option_chains[cache_key] = result
            self.last_update[cache_key] = now
            
            return result
            
        except Exception as e:
            logger.error(f"获取期权链失败: {e}")
            return {}
    
    def _get_option_chain_http_api(self, underlying_symbol: str) -> Dict:
        """使用Alpaca HTTP API获取期权链数据"""
        try:
            calls = []
            puts = []
            
            # 获取标的价格
            underlying_price = self.get_current_price(underlying_symbol)
            
            logger.info(f"开始获取{underlying_symbol}期权链数据 (使用HTTP API)")
            
            # 使用HTTP API获取期权链数据，支持分页
            start_time = datetime.now()
            all_snapshots = self._fetch_all_option_snapshots(underlying_symbol)
            end_time = datetime.now()
            
            total_time = (end_time - start_time).total_seconds()
            
            if not all_snapshots:
                logger.warning("未获取到期权快照数据")
                return {
                    'calls': [],
                    'puts': [],
                    'underlying_price': underlying_price,
                    'timestamp': datetime.now().isoformat()
                }
            
            logger.info(f"✅ HTTP API获取期权快照: {len(all_snapshots)}个快照，用时{total_time:.2f}秒")
            
            # 解析快照数据
            for symbol, snapshot_data in all_snapshots.items():
                try:
                    # 解析期权信息
                    option_info = self.parse_option_symbol(symbol)
                    
                    # 构建期权数据
                    option_data = {
                        'contractSymbol': symbol,
                        'strike': option_info['strike_price'],
                        'expiry': option_info['exp_date'].strftime('%Y-%m-%d'),
                        'days_to_exp': option_info['days_to_exp'],
                        'bid': 0,
                        'ask': 0,
                        'bidSize': 0,
                        'askSize': 0,
                        'lastPrice': 0,
                        'volume': 0,
                        'openInterest': 0,
                        'impliedVolatility': 0,
                        'delta': 0,
                        'gamma': 0,
                        'theta': 0,
                        'vega': 0,
                        'rho': 0,
                        'midPrice': 0
                    }
                    
                    # 提取报价数据
                    if 'latest_quote' in snapshot_data and snapshot_data['latest_quote']:
                        quote = snapshot_data['latest_quote']
                        option_data['bid'] = float(quote.get('bid_price', 0)) if quote.get('bid_price') else 0
                        option_data['ask'] = float(quote.get('ask_price', 0)) if quote.get('ask_price') else 0
                        option_data['bidSize'] = int(quote.get('bid_size', 0)) if quote.get('bid_size') else 0
                        option_data['askSize'] = int(quote.get('ask_size', 0)) if quote.get('ask_size') else 0
                    
                    # 提取交易数据
                    if 'latest_trade' in snapshot_data and snapshot_data['latest_trade']:
                        trade = snapshot_data['latest_trade']
                        option_data['lastPrice'] = float(trade.get('price', 0)) if trade.get('price') else 0
                        option_data['volume'] = int(trade.get('size', 0)) if trade.get('size') else 0
                    
                    # 提取Greeks数据
                    if 'greeks' in snapshot_data and snapshot_data['greeks']:
                        greeks = snapshot_data['greeks']
                        option_data['delta'] = float(greeks.get('delta', 0)) if greeks.get('delta') else 0
                        option_data['gamma'] = float(greeks.get('gamma', 0)) if greeks.get('gamma') else 0
                        option_data['theta'] = float(greeks.get('theta', 0)) if greeks.get('theta') else 0
                        option_data['vega'] = float(greeks.get('vega', 0)) if greeks.get('vega') else 0
                        option_data['rho'] = float(greeks.get('rho', 0)) if greeks.get('rho') else 0
                    
                    # 提取隐含波动率
                    if 'implied_volatility' in snapshot_data and snapshot_data['implied_volatility']:
                        option_data['impliedVolatility'] = float(snapshot_data['implied_volatility'])
                    
                    # 计算中间价
                    if option_data['bid'] > 0 and option_data['ask'] > 0:
                        option_data['midPrice'] = (option_data['bid'] + option_data['ask']) / 2
                    elif option_data['lastPrice'] > 0:
                        option_data['midPrice'] = option_data['lastPrice']
                    else:
                        option_data['midPrice'] = 0.01
                    
                    # 分类期权
                    if option_info['option_type'] == 'call':
                        calls.append(option_data)
                    else:
                        puts.append(option_data)
                        
                except Exception as e:
                    logger.warning(f"解析期权合约失败: {symbol} - {e}")
                    continue
            
            # 按行权价排序
            calls.sort(key=lambda x: x['strike'])
            puts.sort(key=lambda x: x['strike'])
            
            logger.info(f"成功解析期权链: {len(calls)}个看涨期权, {len(puts)}个看跌期权")
            
            return {
                'calls': calls,
                'puts': puts,
                'underlying_price': underlying_price,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"HTTP API获取期权链失败: {e}")
            import traceback
            traceback.print_exc()
            return {}

    def _fetch_all_option_snapshots(self, underlying_symbol: str) -> Dict:
        """获取所有页面的期权快照数据"""
        try:
            all_snapshots = {}
            page_token = None
            page_count = 0
            
            while True:
                page_count += 1
                logger.info(f"正在获取第{page_count}页期权数据...")
                
                # 构建请求URL
                url = f"https://data.alpaca.markets/v1beta1/options/snapshots/{underlying_symbol}"
                params = {
                    'feed': 'indicative',
                    'limit': 1000
                }
                
                if page_token:
                    params['page_token'] = page_token
                
                # 构建请求头
                headers = {
                    'APCA-API-KEY-ID': self.config.alpaca_api_key,
                    'APCA-API-SECRET-KEY': self.config.alpaca_secret_key,
                    'accept': 'application/json'
                }
                
                # 发送请求
                response = requests.get(url, headers=headers, params=params)
                response.raise_for_status()
                
                data = response.json()
                
                # 提取当前页的快照数据
                if 'snapshots' in data and data['snapshots']:
                    current_snapshots = data['snapshots']
                    all_snapshots.update(current_snapshots)
                    logger.info(f"第{page_count}页获取到{len(current_snapshots)}个期权快照")
                else:
                    logger.info(f"第{page_count}页无期权数据")
                
                # 检查是否有下一页
                if 'next_page_token' in data and data['next_page_token']:
                    page_token = data['next_page_token']
                    logger.info(f"检测到下一页，继续获取...")
                else:
                    logger.info(f"已获取所有页面数据，共{page_count}页")
                    break
                
                # 防止无限循环
                if page_count > 50:  # 最多50页
                    logger.warning("已达到最大页数限制，停止获取")
                    break
            
            logger.info(f"总共获取到{len(all_snapshots)}个期权快照数据")
            return all_snapshots
            
        except Exception as e:
            logger.error(f"获取期权快照数据失败: {e}")
            return {}
    
    def parse_option_symbol(self, symbol: str) -> dict:
        """
        解析21字符OSI期权代码为各个组件并计算到期天数

        Args:
            symbol (str): 期权代码, 例如 "AAPL250417C00142000"

        Returns:
            dict: {
                "underlying_symbol": str,
                "exp_date": datetime.date,
                "option_type": "call" or "put",
                "strike_price": float,
                "days_to_exp": int
            }

        Raises:
            ValueError: 如果代码不符合OSI格式
        """
        pattern = r"^([A-Z]+)(\d{6})([CP])(\d{8})$"
        m = re.match(pattern, symbol)
        if not m:
            raise ValueError(f"无效的OSI期权代码: {symbol!r}")

        underlying, yymmdd, cp_flag, strike_str = m.groups()

        # 到期日期
        exp_date = datetime.strptime(yymmdd, "%y%m%d").date()

        # 期权类型
        option_type = "call" if cp_flag == "C" else "put"

        # 行权价：最后一组 ÷ 1000
        strike_price = int(strike_str) / 1000.0

        # 到期天数
        today = date.today()
        days_to_exp = (exp_date - today).days

        return {
            "underlying_symbol": underlying,
            "exp_date": exp_date,
            "option_type": option_type,
            "strike_price": strike_price,
            "days_to_exp": days_to_exp
        }
    
    def get_option_quote(self, option_symbol: str) -> Optional[Dict]:
        """获取单个期权的最新报价"""
        try:
            # 直接使用期权快照API获取单个合约数据
            option_data = self._get_option_snapshot(option_symbol)
            
            if option_data:
                return {
                    'bid': option_data['bid'],
                    'ask': option_data['ask'],
                    'midPrice': option_data['midPrice'],
                    'lastPrice': option_data['lastPrice'],
                    'volume': option_data['volume'],
                    'delta': option_data['delta'],
                    'impliedVolatility': option_data['impliedVolatility']
                }
            
            return None
            
        except Exception as e:
            logger.error(f"获取期权报价失败: {e}")
            return None
    
    def get_current_price(self, symbol: str) -> float:
        """获取当前价格"""
        try:
            # 优先使用最新成交价
            latest_trade = self.stock_client.get_stock_latest_trade(
                StockLatestTradeRequest(symbol_or_symbols=[symbol])
            )
            if symbol in latest_trade:
                return float(latest_trade[symbol].price)
            
            # 备用方案：使用最新报价的中间价
            quote = self.get_latest_quote(symbol)
            if quote:
                return (quote['bid'] + quote['ask']) / 2
            
            # 最后备用方案：使用最新K线数据
            bars = self.get_current_bars(symbol, limit=1)
            if not bars.empty:
                return bars['close'].iloc[-1]
            
            return 0.0
            
        except Exception as e:
            logger.error(f"获取当前价格失败: {e}")
            return 0.0
    
    def find_suitable_options(self, symbol: str, option_type: str) -> List[Dict]:
        """查找合适的期权合约 - 基于价格就近选择当日到期合约"""
        try:
            # 获取当前价格
            current_price = self.get_current_price(symbol)
            if current_price <= 0:
                logger.error(f"无法获取{symbol}的当前价格")
                return []
            
            # 根据期权类型选择行权价
            if option_type.upper() == 'CALL':
                # Call期权：选择floor(当前价格)
                target_strike = int(current_price)  # floor操作
            else:
                # Put期权：选择ceil(当前价格)
                target_strike = int(current_price) + (1 if current_price > int(current_price) else 0)  # ceil操作
            
            logger.info(f"当前{symbol}价格: ${current_price:.2f}, 选择{option_type}期权行权价: ${target_strike}")
            
            # 直接生成期权合约代码
            option_symbol = self._generate_option_symbol(symbol, target_strike, option_type)
            
            # 通过API查询该合约的报价
            option_data = self._get_option_snapshot(option_symbol)
            
            if option_data:
                logger.info(f"成功获取期权{option_symbol}的报价数据")
                return [option_data]
            else:
                logger.warning(f"无法获取期权{option_symbol}的报价数据")
                return []
            
        except Exception as e:
            logger.error(f"查找合适期权失败: {e}")
            return []
    

    
    def _generate_option_symbol(self, underlying: str, strike: int, option_type: str) -> str:
        """生成期权合约代码"""
        try:
            # 获取当日日期（YYMMDD格式）
            today = datetime.now()
            date_str = today.strftime("%y%m%d")
            
            # 格式化行权价（去除小数点，补齐8位）
            # 对于整数行权价，乘以1000然后格式化为8位
            strike_str = f"{strike * 1000:08d}"
            
            # 构建期权代码：UNDERLYING + YYMMDD + C/P + 8位行权价
            option_symbol = f"{underlying}{date_str}{option_type[0].upper()}{strike_str}"
            
            logger.debug(f"生成期权代码: {option_symbol} (行权价${strike}, 类型{option_type})")
            
            return option_symbol
            
        except Exception as e:
            logger.error(f"生成期权代码失败: {e}")
            return ""
    
    def get_option_latest_trade(self, option_symbol: str) -> Optional[Dict]:
        """获取期权最新成交价 - 使用Alpaca optionlatesttrades API"""
        try:
            # 构建请求
            request = OptionLatestTradeRequest(symbol_or_symbols=[option_symbol])
            
            # 获取最新成交数据
            trades = self.option_client.get_option_latest_trade(request)
            
            if option_symbol in trades:
                trade = trades[option_symbol]
                return {
                    'price': float(trade.price),
                    'size': int(trade.size),
                    'timestamp': trade.timestamp,
                    'exchange': trade.exchange,
                    'conditions': trade.conditions
                }
            
            return None
            
        except Exception as e:
            logger.error(f"获取期权最新成交价失败: {e}")
            return None

    def get_option_latest_trade_for_tracking(self, option_symbol: str) -> Optional[float]:
        """专门用于track日志的期权最新成交价获取 - 使用HTTP API直接调用"""
        try:
            # 直接使用HTTP API调用option latest trades端点
            url = "https://data.alpaca.markets/v1beta1/options/trades/latest"
            params = {
                'symbols': option_symbol,
                'feed': 'indicative'
            }
            
            headers = {
                'APCA-API-KEY-ID': self.config.alpaca_api_key,
                'APCA-API-SECRET-KEY': self.config.alpaca_secret_key,
                'accept': 'application/json'
            }
            
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if 'trades' in data and option_symbol in data['trades']:
                trade_data = data['trades'][option_symbol]
                if isinstance(trade_data, list) and len(trade_data) > 0:
                    # 取最新的交易记录
                    latest_trade = trade_data[-1]
                    return float(latest_trade.get('price', 0)) if latest_trade.get('price') else None
                elif isinstance(trade_data, dict):
                    return float(trade_data.get('price', 0)) if trade_data.get('price') else None
            
            return None
            
        except Exception as e:
            logger.error(f"获取期权最新成交价（用于tracking）失败: {e}")
            return None
    
    def _get_option_snapshot(self, option_symbol: str) -> Optional[Dict]:
        """获取期权快照数据"""
        try:
            # 获取最新成交价
            latest_trade = self.get_option_latest_trade(option_symbol)
            
            # 获取期权快照
            request = OptionSnapshotRequest(symbol_or_symbols=[option_symbol])
            snapshots = self.option_client.get_option_snapshot(request)
            
            if option_symbol not in snapshots:
                return None
            
            snapshot = snapshots[option_symbol]
            
            # 解析期权信息获取行权价
            try:
                option_info = self.parse_option_symbol(option_symbol)
                strike_price = option_info['strike_price']
            except Exception as e:
                logger.warning(f"解析期权代码{option_symbol}失败: {e}")
                strike_price = 0
            
            # 构建期权数据
            option_data = {
                'contractSymbol': option_symbol,  # 添加contractSymbol字段
                'strike': strike_price,  # 添加strike字段
                'bid': float(snapshot.latest_quote.bid_price) if snapshot.latest_quote.bid_price else 0,
                'ask': float(snapshot.latest_quote.ask_price) if snapshot.latest_quote.ask_price else 0,
                'lastPrice': float(latest_trade['price']) if latest_trade else 0,
                'volume': int(latest_trade['size']) if latest_trade else 0,
                'midPrice': 0
            }
            
            # 计算中间价
            if option_data['bid'] > 0 and option_data['ask'] > 0:
                option_data['midPrice'] = (option_data['bid'] + option_data['ask']) / 2
            elif option_data['lastPrice'] > 0:
                option_data['midPrice'] = option_data['lastPrice']
            else:
                option_data['midPrice'] = 0.01
            
            return option_data
            
        except Exception as e:
            logger.error(f"获取期权快照失败: {e}")
            return None


class TechnicalIndicators:
    """技术指标计算类"""
    
    @staticmethod
    def calculate_vwap(df: pd.DataFrame) -> pd.Series:
        """计算VWAP - 修复版：只使用当日数据，避免跨日污染"""
        if df.empty or 'volume' not in df.columns:
            return pd.Series()
        
        try:
            # 使用美国东部时间确定当日数据
            import pytz
            from datetime import datetime, date
            
            # 获取美东时间的当日日期
            et_tz = pytz.timezone('US/Eastern') 
            now_et = datetime.now(et_tz)
            today_et = now_et.date()
            
            # 筛选当日数据 - 处理时区转换
            if 'timestamp' in df.columns:
                # 确保timestamp列是datetime类型
                df_copy = df.copy()
                df_copy['timestamp'] = pd.to_datetime(df_copy['timestamp'])
                
                # 将UTC时间转换为美东时间进行日期比较
                if df_copy['timestamp'].dt.tz is None:
                    # 如果没有时区信息，假设是UTC时间
                    df_copy['timestamp'] = df_copy['timestamp'].dt.tz_localize('UTC')
                
                # 转换为美东时间
                df_copy['timestamp_et'] = df_copy['timestamp'].dt.tz_convert(et_tz)
                
                # 筛选当日数据
                today_mask = df_copy['timestamp_et'].dt.date == today_et
                today_data = df_copy[today_mask].copy()
                
                if today_data.empty:
                    # 如果没有当日数据，返回空Series但保持索引结构
                    return pd.Series(index=df.index, dtype=float)
                
                logger.debug(f"VWAP计算: 总数据{len(df)}条, 当日数据{len(today_data)}条, 日期范围: {today_et}")
                
            else:
                # 后备方案：如果没有timestamp列，使用原始逻辑但记录警告
                logger.warning("VWAP计算: 数据中缺少timestamp列，使用原始计算方法")
                today_data = df.copy()
            
            # 计算当日VWAP
            typical_price = (today_data['high'] + today_data['low'] + today_data['close']) / 3
            
            # 计算累计VWAP（只针对当日数据）
            cumulative_volume = today_data['volume'].cumsum()
            cumulative_typical_volume = (typical_price * today_data['volume']).cumsum()
            
            # 避免除零错误
            vwap_values = cumulative_typical_volume / cumulative_volume.replace(0, np.nan)
            
            # 创建结果Series，为完整的DataFrame索引填充数据
            result = pd.Series(index=df.index, dtype=float)
            
            if 'timestamp' in df.columns and not today_data.empty:
                # 将计算的VWAP值映射到对应的索引位置
                result.loc[today_data.index] = vwap_values.values
                
                # 对于当日之前的数据，设置为NaN
                non_today_mask = ~(df_copy['timestamp_et'].dt.date == today_et)
                result.loc[non_today_mask] = np.nan
            else:
                # 后备方案
                result = vwap_values
            
            return result
            
        except Exception as e:
            logger.error(f"VWAP计算失败: {e}")
            # 返回空Series但保持索引结构
            return pd.Series(index=df.index, dtype=float)
    
    @staticmethod
    def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """计算RSI"""
        if df.empty or len(df) < period:
            return pd.Series()
        
        return pd.Series(talib.RSI(df['close'].values, timeperiod=period), 
                        index=df.index)
    
    @staticmethod
    def calculate_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, 
                      signal: int = 9) -> Dict[str, pd.Series]:
        """计算MACD"""
        if df.empty or len(df) < slow:
            return {'macd': pd.Series(), 'signal': pd.Series(), 'histogram': pd.Series()}
        
        macd, signal_line, histogram = talib.MACD(
            df['close'].values, 
            fastperiod=fast, 
            slowperiod=slow, 
            signalperiod=signal
        )
        
        return {
            'macd': pd.Series(macd, index=df.index),
            'signal': pd.Series(signal_line, index=df.index),
            'histogram': pd.Series(histogram, index=df.index)
        }
    
    @staticmethod
    def calculate_orb_levels(df: pd.DataFrame, period_minutes: int = 15) -> Dict[str, float]:
        """计算开盘区间突破水平 - 修复版"""
        if df.empty:
            return {'high': 0, 'low': 0, 'volume': 0}
        
        try:
            # 修复：使用正确的时间范围筛选，处理时区问题
            from datetime import datetime, time, timedelta
            import pytz
            
            # 使用美国东部时间
            et_tz = pytz.timezone('US/Eastern')
            now_et = datetime.now(et_tz)
            today_et = now_et.date()
            
            # 创建当天开盘时间（美国东部时间）
            market_open_et = et_tz.localize(datetime.combine(today_et, time(9, 30)))
            orb_end_et = market_open_et + timedelta(minutes=period_minutes)
            
            # 转换为UTC时间以匹配数据
            market_open_utc = market_open_et.utc
            orb_end_utc = orb_end_et.utc
            
            # 筛选开盘后指定分钟内的数据
            orb_period = df[
                (df['timestamp'] >= market_open_utc) & 
                (df['timestamp'] < orb_end_utc)
            ]
            
            if orb_period.empty:
                # 后备方案：使用时间筛选而不是简单的head()
                market_open_filter = df['timestamp'].dt.time >= pd.Timestamp('09:30').time()
                recent_market_data = df[market_open_filter]
                if not recent_market_data.empty:
                    # 按时间排序，取最近的period_minutes条记录
                    orb_period = recent_market_data.tail(period_minutes)
                
                if orb_period.empty:
                    return {'high': 0, 'low': 0, 'volume': 0}
            
            return {
                'high': orb_period['high'].max(),
                'low': orb_period['low'].min(),
                'volume': orb_period['volume'].mean()
            }
            
        except Exception as e:
            # 兜底方案：使用原始逻辑，但改进
            market_open_filter = df['timestamp'].dt.time >= pd.Timestamp('09:30').time()
            recent_market_data = df[market_open_filter]
            if not recent_market_data.empty:
                orb_period = recent_market_data.tail(period_minutes)  # 改用tail而不是head
                
                return {
                    'high': orb_period['high'].max(),
                    'low': orb_period['low'].min(),
                    'volume': orb_period['volume'].mean()
                }
            
            return {'high': 0, 'low': 0, 'volume': 0}


# 全局市场数据提供者实例
market_data = MarketDataProvider() 