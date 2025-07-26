"""
交易执行模块
负责期权交易的执行、头寸管理和风险控制
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union
from enum import Enum
from dataclasses import dataclass, field
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import (
    MarketOrderRequest, LimitOrderRequest, 
    GetOrdersRequest, StopLimitOrderRequest, StopOrderRequest
)
from alpaca.trading.enums import OrderSide, TimeInForce, OrderStatus
from loguru import logger
import pytz

from ..config import config, strategy_params
from ..data.market_data import MarketDataProvider
from ..strategy.signals import TradingSignal, SignalType
from ..utils.data_logger import strategy_data_logger


class PositionType(Enum):
    """头寸类型"""
    LONG_CALL = "LONG_CALL"
    LONG_PUT = "LONG_PUT"
    NONE = "NONE"


class OrderType(Enum):
    """订单类型"""
    MARKET = "MARKET"
    LIMIT = "LIMIT"


@dataclass
class OptionPosition:
    """期权头寸"""
    symbol: str
    option_symbol: str
    position_type: PositionType
    quantity: int
    entry_price: float
    current_price: float
    entry_time: datetime
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    parent_order_id: Optional[str] = None
    
    def update_current_price(self, price: float):
        """更新当前价格和未实现盈亏"""
        self.current_price = round(price, 2)
        if self.position_type in [PositionType.LONG_CALL, PositionType.LONG_PUT]:
            self.unrealized_pnl = (self.current_price - self.entry_price) * self.quantity * 100


@dataclass
class RiskMetrics:
    """风险指标"""
    account_value: float = 0.0
    buying_power: float = 0.0
    total_positions_value: float = 0.0
    daily_pnl: float = 0.0
    total_pnl: float = 0.0
    max_daily_risk: float = 0.0
    current_risk_used: float = 0.0
    trades_today: int = 0
    max_trades_today: int = 0


class TradingExecutor:
    """交易执行器"""
    
    def __init__(self, market_data: MarketDataProvider):
        self.market_data = market_data
        self.trading_client = TradingClient(
            api_key=config.alpaca_api_key,
            secret_key=config.alpaca_secret_key,
            paper=True if "paper" in config.alpaca_base_url else False
        )
        
        # 头寸跟踪
        self.positions: Dict[str, OptionPosition] = {}
        self.order_history: List[Dict] = []
        self.daily_trades: int = 0
        self.daily_pnl: float = 0.0
        
        # 风险控制
        self.risk_metrics = RiskMetrics()
        self.last_update_time: Optional[datetime] = None
        
        # 初始化
        self.update_account_info()
        # 同步现有持仓
        self.sync_existing_positions()
    
    def update_account_info(self) -> bool:
        """更新账户信息"""
        try:
            account = self.trading_client.get_account()
            
            self.risk_metrics.account_value = float(account.portfolio_value)
            self.risk_metrics.buying_power = float(account.buying_power)
            
            # 修复属性名错误 - 使用可用的属性或设为0
            try:
                # 尝试获取未实现盈亏，如果不存在则设为0
                self.risk_metrics.daily_pnl = float(getattr(account, 'unrealized_pnl', 0))
            except (AttributeError, ValueError):
                self.risk_metrics.daily_pnl = 0.0
            
            # 计算风险参数
            self.risk_metrics.max_daily_risk = (
                self.risk_metrics.account_value * 
                strategy_params.config.max_daily_risk_pct / 100
            )
            
            self.risk_metrics.max_trades_today = strategy_params.config.max_daily_trades
            
            logger.info(f"账户更新: 总值${self.risk_metrics.account_value:.2f}, "
                       f"买入力${self.risk_metrics.buying_power:.2f}")
            
            return True
            
        except Exception as e:
            logger.error(f"更新账户信息失败: {e}")
            return False
    
    def calculate_position_size(self, option_price: float, signal_confidence: float) -> int:
        """计算头寸大小"""
        try:
            # 基础风险控制
            max_risk_per_trade = (
                self.risk_metrics.account_value * 
                strategy_params.config.max_single_trade_risk_pct / 100
            )
            
            # 根据信号置信度调整风险
            adjusted_risk = max_risk_per_trade * signal_confidence
            
            # 计算合约数量
            contract_cost = option_price * 100  # 每个合约100股
            max_contracts = int(adjusted_risk / contract_cost)
            
            # 设置最大合约数量限制（可配置）
            max_contracts_limit = getattr(strategy_params.config, 'max_contracts_per_trade', 10)
            
            # 确保至少1张合约，但不超过风险限制和最大数量限制
            position_size = max(1, min(max_contracts, max_contracts_limit))
            
            logger.info(f"计算头寸大小: 期权价格${option_price:.2f}, "
                       f"最大风险${adjusted_risk:.2f}, 合约数量{position_size}, "
                       f"最大限制{max_contracts_limit}张")
            
            return position_size
            
        except Exception as e:
            logger.error(f"计算头寸大小失败: {e}")
            return 1
    
    def find_best_option(self, signal: TradingSignal) -> Optional[str]:
        """查找最佳期权合约 - 基于价格就近选择"""
        try:
            option_type = "CALL" if signal.signal_type == SignalType.LONG else "PUT"
            
            # 使用新的期权选择逻辑 - 基于价格就近选择
            options = self.market_data.find_suitable_options(
                config.symbol, 
                option_type
            )
            
            if not options:
                logger.warning(f"未找到合适的{option_type}期权")
                return None
            
            # 直接使用返回的期权（已经是最佳选择）
            best_option = options[0]
            option_symbol = best_option['contractSymbol']
            
            logger.info(f"选择期权: {option_symbol}, 行权价${best_option['strike']:.0f}, "
                       f"Bid=${best_option['bid']:.2f}, Ask=${best_option['ask']:.2f}, "
                       f"Delta={best_option.get('delta', 0):.3f}")
            
            return option_symbol
            
        except Exception as e:
            logger.error(f"查找最佳期权失败: {e}")
            return None
    
    def _construct_option_symbol(self, underlying: str, strike: float, option_type: str) -> str:
        """构建期权代码"""
        # 获取当日日期（YYMMDD格式）
        today = datetime.now()
        date_str = today.strftime("%y%m%d")
        
        # 格式化行权价（去除小数点，补齐8位）
        strike_str = f"{int(strike * 1000):08d}"
        
        # 构建期权代码
        option_symbol = f"{underlying}{date_str}{option_type[0]}{strike_str}"
        
        return option_symbol
    
    def execute_trade(self, signal: TradingSignal) -> bool:
        """执行交易 - 实时监控模式：主单成交后实时监控止盈止损"""
        try:
            # 防重复订单检查：检查是否在短时间内重复提交相同信号
            current_time = datetime.now()
            signal_key = f"{signal.signal_type.value}_{config.symbol}"
            
            # 检查最近5秒内是否有相同的信号被处理
            if hasattr(self, 'last_signal_time') and hasattr(self, 'last_signal_key'):
                time_diff = (current_time - self.last_signal_time).total_seconds()
                if self.last_signal_key == signal_key and time_diff < 5:
                    logger.warning(f"⚠️ 检测到{time_diff:.1f}秒内重复信号，跳过执行: {signal_key}")
                    return False
            
            # 记录当前信号信息
            self.last_signal_time = current_time
            self.last_signal_key = signal_key
            
            # 检查是否已有相同期权的持仓
            if hasattr(self, 'positions') and self.positions:
                for option_symbol, position in self.positions.items():
                    if position.position_type.value == signal.signal_type.value:
                        logger.warning(f"⚠️ 已有相同类型的期权持仓: {option_symbol}，跳过新开仓")
                        return False
            
            # 检查交易限制
            if not self._check_trading_limits():
                return False
            
            # 查找合适的期权
            option_symbol = self.find_best_option(signal)
            if not option_symbol:
                return False
            
            # 获取期权当前价格
            option_price = self._get_option_price(option_symbol)
            if option_price <= 0:
                logger.warning(f"无法获取期权{option_symbol}的价格")
                return False
            
            # 计算头寸大小
            position_size = self.calculate_position_size(option_price, signal.confidence)
            
            # 提交主订单（买入）
            main_order_request = self._create_main_order(option_symbol, position_size, option_price)
            if not main_order_request:
                return False
            
            try:
                # 提交主订单
                main_order = self.trading_client.submit_order(main_order_request)
                logger.info(f"主订单已提交: {main_order.id} {option_symbol} 买入{position_size}张 @${option_price:.2f}")
                
                # 等待主订单状态更新
                import time
                time.sleep(1)
                
                # 检查主订单状态
                main_order_status = self.trading_client.get_order_by_id(main_order.id)
                
                if main_order_status.status in [OrderStatus.FILLED, OrderStatus.PARTIALLY_FILLED]:
                    logger.info(f"主订单已成交: {main_order.id}")
                    
                    # 获取订单的实际成交价格 - 修复：使用订单对象的成交信息
                    try:
                        # 重新获取订单最新状态以确保获取到成交信息
                        updated_order = self.trading_client.get_order_by_id(main_order.id)
                        
                        # 使用订单的成交价格信息
                        if updated_order.filled_avg_price and float(updated_order.filled_avg_price) > 0:
                            actual_entry_price = float(updated_order.filled_avg_price)
                        elif updated_order.limit_price and float(updated_order.limit_price) > 0:
                            actual_entry_price = float(updated_order.limit_price)
                        else:
                            actual_entry_price = option_price  # 使用原始期权价格作为备用
                            
                        logger.info(f"订单成交价格: ${actual_entry_price:.2f}")
                        
                    except Exception as e:
                        logger.warning(f"获取成交价格失败，使用原始价格: {e}")
                        actual_entry_price = option_price
                    
                    # 计算止盈止损价格
                    take_profit_price = self._calculate_take_profit(actual_entry_price)
                    stop_loss_price = self._calculate_stop_loss(actual_entry_price)
                    
                    # 创建头寸记录 - 不立即提交止盈止损订单，而是实时监控
                    position_type = (PositionType.LONG_CALL if signal.signal_type == SignalType.LONG 
                                   else PositionType.LONG_PUT)
                    
                    position = OptionPosition(
                        symbol=config.symbol,
                        option_symbol=option_symbol,
                        position_type=position_type,
                        quantity=position_size,
                        entry_price=actual_entry_price,
                        current_price=actual_entry_price,
                        entry_time=datetime.now(),
                        stop_loss=stop_loss_price,
                        take_profit=take_profit_price,
                        parent_order_id=main_order.id
                    )
                    
                    self.positions[option_symbol] = position
                    self.daily_trades += 1
                    
                    # 记录主订单
                    self._record_order(main_order, signal, option_symbol, actual_entry_price)
                    
                    # 新增：交易明细log
                    try:
                        logger.bind(TRADE=True).info(
                            f"开仓|{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}|BUY|{option_symbol}|{position_size}|{actual_entry_price:.2f}|order_id={main_order.id}|signal={signal.signal_type.value}|reason={signal.reason}"
                        )
                    except Exception as e:
                        logger.warning(f"写入交易明细log失败: {e}")
                    
                    # 新增：通知trading_bot track该合约
                    try:
                        from src.bot.trading_bot import EODOptionsTradingBot
                        if hasattr(self, 'trading_bot_ref') and self.trading_bot_ref:
                            self.trading_bot_ref.track_option(option_symbol, actual_entry_price)
                    except Exception as e:
                        logger.warning(f"track_option通知失败: {e}")
                    
                    # 记录开仓交易分析数据
                    self._log_trade_open_data(position, signal, actual_entry_price)
                    
                    logger.info(f"🎯 实时监控交易启动: {position_type.value} {option_symbol} "
                               f"数量{position_size} 入场价${actual_entry_price:.2f} "
                               f"止盈${take_profit_price:.2f} 止损${stop_loss_price:.2f}")
                    logger.info("📊 将通过实时价格监控执行止盈止损，使用市价单确保立即成交")
                    
                    return True
                    
                else:
                    logger.warning(f"主订单未成交，状态: {main_order_status.status}")
                    # 可以选择取消订单或继续等待
                    return False
                    
            except Exception as e:
                logger.error(f"提交主订单失败: {e}")
                return False
                
        except Exception as e:
            logger.error(f"执行交易失败: {e}")
            return False
    
    def _check_trading_limits(self) -> bool:
        """检查交易限制"""
        # 检查每日交易次数
        if self.daily_trades >= self.risk_metrics.max_trades_today:
            logger.warning(f"已达到每日最大交易次数限制: {self.daily_trades}")
            return False
        
        # 检查账户风险
        if abs(self.daily_pnl) >= self.risk_metrics.max_daily_risk:
            logger.warning(f"已达到每日最大风险限制: ${abs(self.daily_pnl):.2f}")
            return False
        
        # 检查交易时间 - 修复：使用与trading_bot一致的美东时间逻辑
        et_tz = pytz.timezone('America/New_York')
        current_et_time = datetime.now(et_tz).time()
        
        start_time = datetime.strptime(config.trading_start_time, "%H:%M").time()
        end_time = datetime.strptime(config.trading_end_time, "%H:%M").time()
        
        # 检查是否为工作日
        weekday = datetime.now(et_tz).weekday()
        is_weekday = weekday < 5  # 周一到周五
        
        if not is_weekday:
            logger.warning("当前为周末，不在交易时间内")
            return False
            
        if not (start_time <= current_et_time <= end_time):
            logger.warning(f"当前不在交易时间内 - 美东时间: {current_et_time.strftime('%H:%M:%S')}, 交易时间: {config.trading_start_time}-{config.trading_end_time}")
            return False
        
        return True
    
    def _get_option_price(self, option_symbol: str) -> float:
        """获取期权价格 - 使用快照API获取最新报价"""
        try:
            # 使用快照API获取期权报价
            option_data = self.market_data._get_option_snapshot(option_symbol)
            
            if option_data:
                # 优先使用中间价
                if option_data['midPrice'] > 0:
                    return option_data['midPrice']
                # 备用方案：使用最新成交价
                elif option_data['lastPrice'] > 0:
                    return option_data['lastPrice']
                # 最后备用：使用买价
                elif option_data['bid'] > 0:
                    return option_data['bid']
                else:
                    logger.warning(f"期权{option_symbol}没有有效价格")
                    return 0.0
            else:
                logger.warning(f"无法获取期权{option_symbol}的快照数据")
                return 0.0
            
        except Exception as e:
            logger.error(f"获取期权价格失败: {e}")
            return 0.0
    
    def _create_main_order(self, option_symbol: str, quantity: int, price: float) -> Optional[LimitOrderRequest]:
        """创建主订单（买入）"""
        try:
            # 添加少量滑点保护
            limit_price = price * (1 + strategy_params.max_slippage_pct / 100)
            limit_price = round(limit_price, 2)
            
            return LimitOrderRequest(
                symbol=option_symbol,
                qty=quantity,
                side=OrderSide.BUY,
                time_in_force=TimeInForce.DAY,
                limit_price=limit_price
            )
        except Exception as e:
            logger.error(f"创建主订单失败: {e}")
            return None
    
    # 注意：以下方法在实时监控模式下不再使用，保留作为备用
    def _submit_take_profit_order(self, option_symbol: str, quantity: int, 
                                take_profit_price: float, parent_order_id: str) -> bool:
        """提交止盈订单（卖出限价单）- 已废弃，改用实时监控模式"""
        logger.warning("⚠️ _submit_take_profit_order 方法已废弃，现使用实时监控模式")
        return False
    
    def _submit_stop_loss_order(self, option_symbol: str, quantity: int, 
                              stop_loss_price: float, parent_order_id: str) -> bool:
        """提交止损订单（卖出止损单）- 已废弃，改用实时监控模式"""
        logger.warning("⚠️ _submit_stop_loss_order 方法已废弃，现使用实时监控模式")
        return False
    
    def _calculate_stop_loss(self, entry_price: float) -> float:
        """计算止损价格"""
        stop_loss = entry_price * (1 - strategy_params.config.stop_loss_pct / 100)
        return round(stop_loss, 2)
    
    def _calculate_take_profit(self, entry_price: float) -> float:
        """计算止盈价格"""
        take_profit = entry_price * (1 + strategy_params.config.take_profit_pct / 100)
        return round(take_profit, 2)
    
    def _record_order(self, order, signal: TradingSignal, option_symbol: str, price: float):
        """记录订单信息"""
        order_record = {
            'timestamp': datetime.now(),
            'order_id': order.id,
            'symbol': option_symbol,
            'side': 'BUY',
            'quantity': order.qty,
            'price': price,
            'signal_type': signal.signal_type.value,
            'signal_reason': signal.reason,
            'signal_confidence': signal.confidence
        }
        
        self.order_history.append(order_record)
    
    def update_positions(self) -> bool:
        """更新所有头寸"""
        try:
            for option_symbol, position in self.positions.items():
                # 获取当前价格
                current_price = self._get_option_price(option_symbol)
                if current_price > 0:
                    position.update_current_price(current_price)
                    
                    # 检查止损止盈
                    self._check_exit_conditions(position)
            
            # 更新风险指标
            self._update_risk_metrics()
            
            # 记录表现数据
            self._log_performance_data()
            
            return True
            
        except Exception as e:
            logger.error(f"更新头寸失败: {e}")
            return False
    
    def _check_exit_conditions(self, position: OptionPosition) -> bool:
        """检查退出条件 - 实时监控模式，立即执行市价订单"""
        try:
            should_close = False
            close_reason = ""
            order_type = "market"  # 标记为市价单
            
            # 检查止损条件
            if (position.stop_loss and 
                position.current_price <= position.stop_loss):
                should_close = True
                close_reason = f"🔻 止损触发: ${position.current_price:.2f} <= ${position.stop_loss:.2f}"
                logger.warning(f"⚠️ 止损条件触发 - {position.option_symbol}: 当前价${position.current_price:.2f} 止损价${position.stop_loss:.2f}")
            
            # 检查止盈条件  
            elif (position.take_profit and 
                  position.current_price >= position.take_profit):
                should_close = True
                close_reason = f"🎯 止盈触发: ${position.current_price:.2f} >= ${position.take_profit:.2f}"
                logger.info(f"✅ 止盈条件触发 - {position.option_symbol}: 当前价${position.current_price:.2f} 止盈价${position.take_profit:.2f}")
            
            # 检查强制平仓条件
            elif self._should_force_close():
                should_close = True
                close_reason = "🕐 临近收盘强制平仓"
                logger.info(f"🕐 强制平仓条件触发 - {position.option_symbol}: 临近收盘时间")
            
            # 立即执行市价平仓
            if should_close:
                logger.info(f"🚀 立即执行市价平仓: {close_reason}")
                return self._execute_market_exit(position, close_reason)
            
            return False
            
        except Exception as e:
            logger.error(f"检查退出条件失败: {e}")
            return False
    
    def _should_force_close(self) -> bool:
        """判断是否应该强制平仓"""
        current_time = datetime.now().time()
        force_close_time = datetime.strptime(config.force_close_time, "%H:%M").time()
        
        return current_time >= force_close_time
    
    def _execute_market_exit(self, position: OptionPosition, reason: str) -> bool:
        """执行市价平仓订单 - 确保立即成交"""
        try:
            # 获取最新价格用于记录
            latest_price = self._get_option_price(position.option_symbol)
            if latest_price > 0:
                position.update_current_price(latest_price)
            
            # 创建市价卖出订单
            order_request = MarketOrderRequest(
                symbol=position.option_symbol,
                qty=position.quantity,
                side=OrderSide.SELL,
                time_in_force=TimeInForce.DAY
            )
            
            # 立即提交市价订单
            order = self.trading_client.submit_order(order_request)
            
            # 等待订单成交
            import time
            time.sleep(1)
            
            # 获取订单的实际成交价格 - 修复：使用订单对象的成交信息
            try:
                # 重新获取订单最新状态以确保获取到成交信息
                updated_order = self.trading_client.get_order_by_id(order.id)
                
                # 使用订单的成交价格信息
                if updated_order.filled_avg_price and float(updated_order.filled_avg_price) > 0:
                    actual_close_price = float(updated_order.filled_avg_price)
                else:
                    actual_close_price = position.current_price  # 使用当前价格作为备用
                    
                logger.info(f"平仓订单成交价格: ${actual_close_price:.2f}")
                
            except Exception as e:
                logger.warning(f"获取平仓成交价格失败，使用当前价格: {e}")
                actual_close_price = position.current_price
            
            # 更新头寸的当前价格和盈亏
            position.update_current_price(actual_close_price)
            
            # 计算预期盈亏
            position.realized_pnl = position.unrealized_pnl
            self.daily_pnl += position.realized_pnl
            
            # 记录平仓订单
            close_record = {
                'timestamp': datetime.now(),
                'order_id': order.id,
                'symbol': position.option_symbol,
                'side': 'SELL',
                'quantity': position.quantity,
                'price': actual_close_price,
                'order_type': 'MARKET',
                'reason': reason,
                'pnl': position.realized_pnl
            }
            
            self.order_history.append(close_record)
            
            # 新增：交易明细log
            try:
                logger.bind(TRADE=True).info(
                    f"平仓|{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}|SELL|{position.option_symbol}|{position.quantity}|{actual_close_price:.2f}|order_id={order.id}|reason={reason}|pnl={position.realized_pnl:.2f}"
                )
            except Exception as e:
                logger.warning(f"写入交易明细log失败: {e}")
            
            # 新增：通知trading_bot更新track合约的平仓价
            try:
                from src.bot.trading_bot import EODOptionsTradingBot
                if hasattr(self, 'trading_bot_ref') and self.trading_bot_ref:
                    self.trading_bot_ref.update_option_close_price(position.option_symbol, actual_close_price)
            except Exception as e:
                logger.warning(f"update_option_close_price通知失败: {e}")
            
            # 记录平仓交易分析数据
            self._log_trade_close_data(position, actual_close_price, reason)
            
            # 根据止盈止损类型显示不同信息
            if "止盈" in reason:
                logger.info(f"✅ 止盈平仓成功: {position.option_symbol} "
                           f"市价订单{order.id} 数量{position.quantity}张 "
                           f"成交价${actual_close_price:.2f} "
                           f"预期盈亏${position.realized_pnl:.2f}")
            elif "止损" in reason:
                logger.warning(f"🔻 止损平仓成功: {position.option_symbol} "
                              f"市价订单{order.id} 数量{position.quantity}张 "
                              f"成交价${actual_close_price:.2f} "
                              f"预期盈亏${position.realized_pnl:.2f}")
            else:
                logger.info(f"🕐 强制平仓成功: {position.option_symbol} "
                           f"市价订单{order.id} 数量{position.quantity}张 "
                           f"成交价${actual_close_price:.2f} "
                           f"预期盈亏${position.realized_pnl:.2f}")
            
            # 移除头寸
            del self.positions[position.option_symbol]
            
            # 发送通知
            from ..utils.notifications import NotificationManager
            notification_msg = f"{'🎯 止盈' if '止盈' in reason else '🔻 止损' if '止损' in reason else '🕐 平仓'} {position.option_symbol}\n"
            notification_msg += f"数量: {position.quantity}张\n"
            notification_msg += f"入场价: ${position.entry_price:.2f}\n"
            notification_msg += f"平仓价: ${position.current_price:.2f}\n"
            notification_msg += f"盈亏: ${position.realized_pnl:.2f}\n"
            notification_msg += f"原因: {reason}"
            
            try:
                notification = NotificationManager()
                notification.send_message("TRADING", notification_msg)
            except:
                pass  # 通知失败不影响交易
            
            return True
            
        except Exception as e:
            logger.error(f"💥 市价平仓失败 {position.option_symbol}: {e}")
            # 如果市价单失败，尝试备用方案（使用原来的方法）
            try:
                logger.warning(f"🔄 尝试备用平仓方案: {position.option_symbol}")
                return self._close_position(position, f"{reason} (备用方案)")
            except Exception as backup_error:
                logger.error(f"💥 备用平仓方案也失败: {backup_error}")
                return False
    
    def _close_position(self, position: OptionPosition, reason: str) -> bool:
        """平仓头寸"""
        try:
            # 创建卖出订单
            order_request = MarketOrderRequest(
                symbol=position.option_symbol,
                qty=position.quantity,
                side=OrderSide.SELL,
                time_in_force=TimeInForce.DAY
            )
            
            # 提交订单
            order = self.trading_client.submit_order(order_request)
            
            # 计算实现盈亏
            position.realized_pnl = position.unrealized_pnl
            self.daily_pnl += position.realized_pnl
            
            # 记录平仓
            close_record = {
                'timestamp': datetime.now(),
                'order_id': order.id,
                'symbol': position.option_symbol,
                'side': 'SELL',
                'quantity': position.quantity,
                'price': position.current_price,
                'reason': reason,
                'pnl': position.realized_pnl
            }
            
            self.order_history.append(close_record)
            
            # 新增：交易明细log
            try:
                logger.bind(TRADE=True).info(
                    f"平仓|{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}|SELL|{position.option_symbol}|{position.quantity}|{position.current_price:.2f}|order_id={order.id}|reason={reason}|pnl={position.realized_pnl:.2f}"
                )
            except Exception as e:
                logger.warning(f"写入交易明细log失败: {e}")
            
            logger.info(f"平仓成功: {position.option_symbol} "
                       f"盈亏${position.realized_pnl:.2f} 原因: {reason}")
            
            # 移除头寸
            del self.positions[position.option_symbol]
            
            return True
            
        except Exception as e:
            logger.error(f"平仓失败: {e}")
            return False
    
    def _update_risk_metrics(self):
        """更新风险指标"""
        self.risk_metrics.trades_today = self.daily_trades
        self.risk_metrics.current_risk_used = sum(
            abs(pos.unrealized_pnl) for pos in self.positions.values()
        )
        self.risk_metrics.total_positions_value = sum(
            pos.current_price * pos.quantity * 100 
            for pos in self.positions.values()
        )
    
    def close_all_positions(self, reason: str = "手动平仓") -> bool:
        """平仓所有头寸"""
        try:
            positions_to_close = list(self.positions.values())
            
            for position in positions_to_close:
                self._close_position(position, reason)
            
            logger.info(f"已平仓所有头寸，原因: {reason}")
            return True
            
        except Exception as e:
            logger.error(f"平仓所有头寸失败: {e}")
            return False
    
    def cancel_all_open_orders(self) -> bool:
        """取消所有开放订单"""
        try:
            logger.info("正在查询所有开放订单...")
            
            # 获取所有开放订单
            from alpaca.trading.enums import QueryOrderStatus
            from alpaca.trading.requests import GetOrdersRequest
            
            request = GetOrdersRequest(
                status=QueryOrderStatus.OPEN,
                limit=500
            )
            open_orders = self.trading_client.get_orders(filter=request)
            
            if not open_orders:
                logger.info("没有发现开放订单")
                return True
            
            logger.info(f"发现 {len(open_orders)} 个开放订单，正在取消...")
            
            cancelled_count = 0
            failed_count = 0
            
            for order in open_orders:
                try:
                    # 取消订单
                    self.trading_client.cancel_order_by_id(order.id)
                    cancelled_count += 1
                    logger.info(f"已取消订单: {order.symbol} {order.side} {order.qty}张")
                    
                except Exception as e:
                    failed_count += 1
                    logger.error(f"取消订单失败 {order.id}: {e}")
            
            logger.info(f"订单取消完成: 成功{cancelled_count}个, 失败{failed_count}个")
            
            # 等待一秒后再次检查
            import time
            time.sleep(1)
            
            # 验证是否所有订单都已取消
            request = GetOrdersRequest(
                status=QueryOrderStatus.OPEN,
                limit=500
            )
            remaining_orders = self.trading_client.get_orders(filter=request)
            
            if remaining_orders:
                logger.warning(f"仍有 {len(remaining_orders)} 个订单未取消")
                return False
            else:
                logger.info("所有开放订单已成功取消")
                return True
                
        except Exception as e:
            logger.error(f"取消所有订单失败: {e}")
            return False
    
    def verify_positions_closed(self) -> bool:
        """验证所有持仓是否已关闭"""
        try:
            logger.info("正在验证持仓状态...")
            
            # 检查本地持仓跟踪
            if self.positions:
                logger.warning(f"本地持仓跟踪显示仍有 {len(self.positions)} 个持仓")
                
            # 从Alpaca API获取实际持仓
            alpaca_positions = self.trading_client.get_all_positions()
            
            # 过滤出期权持仓（期权代码长度通常>10）
            option_positions = [pos for pos in alpaca_positions if len(pos.symbol) > 10]
            
            if option_positions:
                logger.warning(f"Alpaca账户仍有 {len(option_positions)} 个期权持仓:")
                for pos in option_positions:
                    logger.warning(f"  {pos.symbol}: {pos.qty}张")
                return False
            else:
                logger.info("所有期权持仓已确认关闭")
                # 清空本地持仓跟踪
                self.positions.clear()
                return True
                
        except Exception as e:
            logger.error(f"验证持仓状态失败: {e}")
            return False
    
    def verify_orders_cancelled(self) -> bool:
        """验证所有订单是否已取消"""
        try:
            logger.info("正在验证订单状态...")
            
            # 检查开放订单
            from alpaca.trading.enums import QueryOrderStatus
            from alpaca.trading.requests import GetOrdersRequest
            
            request = GetOrdersRequest(
                status=QueryOrderStatus.OPEN,
                limit=500
            )
            open_orders = self.trading_client.get_orders(filter=request)
            
            if open_orders:
                logger.warning(f"仍有 {len(open_orders)} 个开放订单:")
                for order in open_orders:
                    logger.warning(f"  {order.symbol} {order.side} {order.qty}张 状态:{order.status}")
                return False
            else:
                logger.info("所有订单已确认取消")
                return True
                
        except Exception as e:
            logger.error(f"验证订单状态失败: {e}")
            return False
    
    def get_position_summary(self) -> Dict:
        """获取头寸摘要"""
        total_unrealized_pnl = sum(pos.unrealized_pnl for pos in self.positions.values())
        
        # 计算当日总盈亏：已实现盈亏 + 未实现盈亏
        daily_total_pnl = self.daily_pnl + total_unrealized_pnl
        
        return {
            'total_positions': len(self.positions),
            'total_unrealized_pnl': total_unrealized_pnl,
            'daily_pnl': daily_total_pnl,  # 当日总盈亏（实现+未实现）
            'daily_realized_pnl': self.daily_pnl,  # 当日已实现盈亏
            'daily_trades': self.daily_trades,
            'positions': [
                {
                    'symbol': pos.option_symbol,
                    'type': pos.position_type.value,
                    'quantity': pos.quantity,
                    'entry_price': pos.entry_price,
                    'current_price': pos.current_price,
                    'unrealized_pnl': pos.unrealized_pnl,
                    'entry_time': pos.entry_time.isoformat()
                }
                for pos in self.positions.values()
            ]
        }
    
    def get_risk_summary(self) -> Dict:
        """获取风险摘要"""
        # 计算当日总盈亏：已实现盈亏 + 未实现盈亏
        total_unrealized_pnl = sum(pos.unrealized_pnl for pos in self.positions.values())
        daily_total_pnl = self.daily_pnl + total_unrealized_pnl
        
        return {
            'account_value': self.risk_metrics.account_value,
            'buying_power': self.risk_metrics.buying_power,
            'daily_pnl': daily_total_pnl,  # 当日总盈亏（实现+未实现）
            'daily_realized_pnl': self.daily_pnl,  # 当日已实现盈亏
            'max_daily_risk': self.risk_metrics.max_daily_risk,
            'current_risk_used': self.risk_metrics.current_risk_used,
            'risk_utilization_pct': (
                self.risk_metrics.current_risk_used / 
                self.risk_metrics.max_daily_risk * 100 
                if self.risk_metrics.max_daily_risk > 0 else 0
            ),
            'trades_today': self.daily_trades,
            'max_trades_today': self.risk_metrics.max_trades_today
        }
    
    def get_account_summary(self) -> Dict:
        """获取账户摘要信息"""
        try:
            # 更新账户信息
            self.update_account_info()
            
            return {
                'account_value': self.risk_metrics.account_value,
                'buying_power': self.risk_metrics.buying_power,
                'max_daily_risk': self.risk_metrics.max_daily_risk,
                'max_daily_risk_pct': strategy_params.config.max_daily_risk_pct,
                'max_single_trade_risk_pct': strategy_params.config.max_single_trade_risk_pct,
                'max_trades_today': self.risk_metrics.max_trades_today,
                'api_source': 'Alpaca API (实时获取)',
                'paper_trading': True if "paper" in config.alpaca_base_url else False
            }
        except Exception as e:
            logger.error(f"获取账户摘要失败: {e}")
            return {
                'error': str(e),
                'account_value': 0.0,
                'api_source': '获取失败'
            }
    
    def sync_existing_positions(self) -> bool:
        """同步Alpaca账户的现有持仓"""
        try:
            logger.info("正在同步Alpaca账户现有持仓...")
            
            # 获取所有持仓
            alpaca_positions = self.trading_client.get_all_positions()
            
            synced_count = 0
            for alpaca_pos in alpaca_positions:
                symbol = alpaca_pos.symbol
                
                # 只同步期权持仓（期权代码长度通常>10）
                if len(symbol) > 10:
                    try:
                        qty = float(alpaca_pos.qty)
                        avg_entry_price = float(alpaca_pos.avg_entry_price)
                        market_value = float(alpaca_pos.market_value)
                        
                        # 获取未实现盈亏
                        unrealized_pnl = 0.0
                        for attr_name in ['unrealized_pnl', 'unrealized_pl', 'pnl', 'pl']:
                            if hasattr(alpaca_pos, attr_name):
                                unrealized_pnl = float(getattr(alpaca_pos, attr_name))
                                break
                        
                        # 计算当前期权价格 - 修复：基于市场价值和数量
                        if qty != 0:
                            current_price = abs(market_value) / (abs(qty) * 100)
                        else:
                            current_price = avg_entry_price
                        
                        # 判断持仓类型
                        if qty > 0:
                            # 根据期权代码判断是CALL还是PUT
                            if 'C' in symbol[-9:]:  # 期权代码中的C表示CALL
                                position_type = PositionType.LONG_CALL
                            else:  # P表示PUT
                                position_type = PositionType.LONG_PUT
                        else:
                            # 负数量表示卖出持仓，但我们的系统主要处理买入
                            logger.warning(f"检测到卖出持仓 {symbol}，跳过同步")
                            continue
                        
                        # 创建期权头寸对象
                        position = OptionPosition(
                            symbol=config.symbol,  # 标的符号（SPY）
                            option_symbol=symbol,
                            position_type=position_type,
                            quantity=int(abs(qty)),
                            entry_price=avg_entry_price,
                            current_price=current_price,
                            entry_time=datetime.now(),  # 无法获取确切入场时间，使用当前时间
                            stop_loss=None,  # 现有持仓没有预设止损
                            take_profit=None,  # 现有持仓没有预设止盈
                            unrealized_pnl=unrealized_pnl,  # 直接设置从Alpaca获取的盈亏
                            parent_order_id=None
                        )
                        
                        # 获取实时期权价格并更新盈亏
                        try:
                            real_time_price = self._get_option_price(symbol)
                            if real_time_price > 0:
                                position.update_current_price(real_time_price)
                                logger.info(f"已更新期权 {symbol} 实时价格: ${real_time_price:.2f}")
                            else:
                                # 如果无法获取实时价格，使用计算出的价格更新盈亏
                                position.update_current_price(current_price)
                                logger.info(f"使用计算价格更新期权 {symbol}: ${current_price:.2f}")
                        except Exception as e:
                            logger.warning(f"获取期权 {symbol} 实时价格失败: {e}，使用计算价格")
                            position.update_current_price(current_price)
                        
                        # 添加到系统持仓跟踪
                        self.positions[symbol] = position
                        synced_count += 1
                        
                        logger.info(f"已同步期权持仓: {symbol} {qty}张 入场${avg_entry_price:.2f} "
                                  f"当前${position.current_price:.2f} 盈亏${position.unrealized_pnl:.2f}")
                        
                    except Exception as e:
                        logger.error(f"同步持仓 {symbol} 失败: {e}")
            
            # 同步完成后，立即更新所有持仓价格以确保盈亏准确
            if synced_count > 0:
                logger.info("正在更新所有持仓的实时价格...")
                self.update_positions()
            
            logger.info(f"持仓同步完成: 总共同步了 {synced_count} 个期权持仓")
            return True
            
        except Exception as e:
            logger.error(f"同步现有持仓失败: {e}")
            return False
    
    def _log_performance_data(self):
        """记录表现数据"""
        try:
            # 获取账户信息
            risk_summary = self.get_risk_summary()
            position_summary = self.get_position_summary()
            
            performance_data = {
                'account_value': risk_summary.get('account_value', 0),
                'buying_power': risk_summary.get('buying_power', 0),
                'daily_pnl': risk_summary.get('daily_pnl', 0),
                'unrealized_pnl': position_summary.get('total_unrealized_pnl', 0),
                'realized_pnl': risk_summary.get('daily_realized_pnl', 0),
                'position_count': position_summary.get('total_positions', 0),
                'daily_trades': position_summary.get('daily_trades', 0),
                'risk_utilization_pct': risk_summary.get('risk_utilization_pct', 0),
                'max_daily_risk': risk_summary.get('max_daily_risk', 0)
            }
            
            strategy_data_logger.log_performance(performance_data)
            
        except Exception as e:
            logger.error(f"记录表现数据失败: {e}")
    
    def _log_trade_open_data(self, position: OptionPosition, signal: TradingSignal, entry_price: float):
        """记录开仓交易分析数据"""
        try:
            # 解析期权信息
            option_info = self.market_data.parse_option_symbol(position.option_symbol)
            
            # 获取标的价格
            underlying_price = self.market_data.get_current_price(position.symbol)
            
            trade_data = {
                'action': '开仓',
                'option_symbol': position.option_symbol,
                'option_type': 'CALL' if position.position_type == PositionType.LONG_CALL else 'PUT',
                'strike_price': option_info.get('strike_price', 0),
                'quantity': position.quantity,
                'price': entry_price,
                'signal_type': signal.signal_type.value,
                'signal_confidence': signal.confidence,
                'holding_time': 0,  # 开仓时为0
                'pnl_amount': 0,  # 开仓时为0
                'pnl_percent': 0,  # 开仓时为0
                'stop_loss': position.stop_loss,
                'take_profit': position.take_profit,
                'exit_reason': '',  # 开仓时为空
                'underlying_entry_price': underlying_price,
                'underlying_exit_price': 0  # 开仓时为0
            }
            
            strategy_data_logger.log_trade_analysis(trade_data)
            
        except Exception as e:
            logger.error(f"记录开仓交易数据失败: {e}")
    
    def _log_trade_close_data(self, position: OptionPosition, close_price: float, reason: str):
        """记录平仓交易分析数据"""
        try:
            # 解析期权信息
            option_info = self.market_data.parse_option_symbol(position.option_symbol)
            
            # 获取标的价格
            underlying_price = self.market_data.get_current_price(position.symbol)
            
            # 计算持有时间（分钟）
            holding_time = (datetime.now() - position.entry_time).total_seconds() / 60
            
            # 计算盈亏百分比
            pnl_percent = 0
            if position.entry_price > 0:
                pnl_percent = (close_price - position.entry_price) / position.entry_price * 100
            
            trade_data = {
                'action': '平仓',
                'option_symbol': position.option_symbol,
                'option_type': 'CALL' if position.position_type == PositionType.LONG_CALL else 'PUT',
                'strike_price': option_info.get('strike_price', 0),
                'quantity': position.quantity,
                'price': close_price,
                'signal_type': '',  # 平仓时不需要信号类型
                'signal_confidence': 0,  # 平仓时不需要信号置信度
                'holding_time': holding_time,
                'pnl_amount': position.realized_pnl,
                'pnl_percent': pnl_percent,
                'stop_loss': position.stop_loss,
                'take_profit': position.take_profit,
                'exit_reason': reason,
                'underlying_entry_price': 0,  # 平仓时不需要入场价
                'underlying_exit_price': underlying_price
            }
            
            strategy_data_logger.log_trade_analysis(trade_data)
            
        except Exception as e:
            logger.error(f"记录平仓交易数据失败: {e}") 