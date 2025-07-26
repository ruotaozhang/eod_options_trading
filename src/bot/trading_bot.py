"""
主交易机器人
整合信号生成、交易执行、风险管理等所有模块
"""

import asyncio
import schedule
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from loguru import logger
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich.columns import Columns
from rich.layout import Layout
import pytz
import os

from ..config import config, strategy_params
from ..data.market_data import MarketDataProvider
from ..strategy.signals import SignalGenerator, TradingSignal, SignalType
from ..trading.executor import TradingExecutor
from ..utils.notifications import NotificationManager
from ..utils.logger_setup import setup_logger
from ..utils.data_logger import strategy_data_logger


class EODOptionsTradingBot:
    """末日期权交易机器人"""
    
    def __init__(self):
        # 初始化日志
        setup_logger()
        
        # 初始化组件
        self.market_data = MarketDataProvider()
        self.signal_generator = SignalGenerator(self.market_data)
        self.executor = TradingExecutor(self.market_data)
        self.notification_manager = NotificationManager()
        
        # 控制台显示
        self.console = Console()
        
        # 状态跟踪
        self.is_running = False
        self.is_trading_day = True
        self.last_signal_time: Optional[datetime] = None
        self.bot_start_time = datetime.now()
        self.live_display = None  # 添加Live组件引用
        
        # 性能统计
        self.session_stats = {
            'signals_generated': 0,
            'trades_executed': 0,
            'total_pnl': 0.0,
            'best_trade': 0.0,
            'worst_trade': 0.0
        }
        
        self.tracked_options = {}  # {option_symbol: {'entry_price': float, 'close_price': float or None}}
        self.tracked_log_path = None
        
    def start(self):
        """启动交易机器人"""
        logger.info("启动末日期权交易机器人")
        
        # 发送启动通知
        self.notification_manager.send_message(
            f"🚀 EOD期权交易机器人已启动\n"
            f"标的: {config.symbol}\n"
            f"账户资金: ${self.executor.risk_metrics.account_value:,.2f}\n"
            f"最大日风险: ${self.executor.risk_metrics.max_daily_risk:,.2f}\n"
            f"交易时间: {config.trading_start_time} - {config.trading_end_time}"
        )
        
        self.is_running = True
        
        # 设置定时任务
        self._setup_schedule()
        
        # 主循环
        try:
            self._run_main_loop()
        except KeyboardInterrupt:
            logger.info("收到停止信号，正在关闭机器人...")
            self.stop()
        except Exception as e:
            logger.error(f"机器人运行异常: {e}")
            self.emergency_stop()
    
    def _setup_schedule(self):
        """设置定时任务"""
        # 从配置获取监控频率设置
        position_check_seconds = getattr(config, 'position_check_seconds', 15)
        market_data_seconds = getattr(config, 'market_data_update_seconds', 30)
        signal_check_seconds = getattr(config, 'signal_check_seconds', 60)  # 默认60秒兼容原有配置
        
        # 市场数据更新
        schedule.every(market_data_seconds).seconds.do(self._update_market_data)
        
        # 信号检查 - 现在使用秒级检查
        schedule.every(signal_check_seconds).seconds.do(self._check_signals)
        
        # 头寸更新（有持仓时高频，无持仓时低频）
        schedule.every(position_check_seconds).seconds.do(self._update_positions_frequently)
        schedule.every(1).minutes.do(self._update_positions_normal)
        
        # 风险检查（每5分钟）
        schedule.every(5).minutes.do(self._risk_check)
        
        # 每小时状态报告
        schedule.every().hour.do(self._hourly_report)
        
        # 收盘前强制平仓检查
        schedule.every(1).minutes.do(self._check_force_close)
        
        # 日终报告
        schedule.every().day.at("16:30").do(self._daily_report)
        
        logger.info(f"📊 监控频率设置: 持仓检查={position_check_seconds}秒, 市场数据={market_data_seconds}秒, 信号检查={signal_check_seconds}秒")
    
    def _run_main_loop(self):
        """主运行循环"""
        try:
            # 使用transient=True让Live显示在退出时自动清除
            self.live_display = Live(
                self._generate_dashboard(), 
                refresh_per_second=1, 
                auto_refresh=False,  # 手动控制刷新
                transient=True       # 退出时清除显示
            )
            self.live_display.start()
            
            while self.is_running:
                try:
                    # 执行定时任务 (只在运行时执行)
                    if self.is_running:
                        schedule.run_pending()
                    
                    # 手动更新显示 (只在运行时执行)
                    if self.is_running:
                        self.live_display.update(self._generate_dashboard(), refresh=True)
                    
                    # 短暂休眠
                    time.sleep(0.5)  # 减少休眠时间，提高响应速度
                    
                except Exception as e:
                    logger.error(f"主循环异常: {e}")
                    time.sleep(1)  # 异常时也减少等待时间
        finally:
            # 确保Live组件被正确停止
            if self.live_display is not None:
                logger.info("🛑 主循环已停止，正在关闭实时显示...")
                try:
                    self.live_display.stop()
                    self.live_display = None
                except:
                    pass  # 忽略停止过程中的异常
    
    def force_stop_display(self):
        """强制停止Live显示"""
        if self.live_display is not None:
            try:
                self.live_display.stop()
                self.live_display = None
                # 清空控制台以避免显示残留
                print("\033[2J\033[H", end="")  # 清屏
            except:
                pass
    
    def _update_market_data(self):
        """更新市场数据"""
        try:
            if not self._is_trading_time():
                return
                
            # 更新账户信息
            self.executor.update_account_info()
            
            # 新增：track合约采样
            self._track_sample_all_options()
            
            logger.debug("市场数据更新完成")
            
        except Exception as e:
            logger.error(f"更新市场数据失败: {e}")
    
    def _check_signals(self):
        """检查交易信号"""
        try:
            if not self._is_trading_time():
                return
                
            # 生成信号
            signals = self.signal_generator.generate_signals(config.symbol)
            
            for signal in signals:
                self.session_stats['signals_generated'] += 1
                self.last_signal_time = signal.timestamp
                
                logger.info(f"检测到信号: {signal.signal_type.value} "
                           f"置信度: {signal.confidence:.2f} "
                           f"原因: {signal.reason}")
                
                # 发送信号通知
                self._send_signal_notification(signal)
                
                # 执行交易
                if self._should_execute_signal(signal):
                    success = self.executor.execute_trade(signal)
                    if success:
                        self.session_stats['trades_executed'] += 1
                        logger.info(f"信号执行成功: {signal.signal_type.value}")
                    else:
                        logger.warning(f"信号执行失败: {signal.signal_type.value}")
                        
        except Exception as e:
            logger.error(f"检查信号失败: {e}")
    
    def _update_positions_frequently(self):
        """高频头寸更新 - 仅在有持仓时执行（每15秒）"""
        try:
            if not self._is_trading_time():
                return
            
            # 仅在有持仓时执行高频更新    
            if len(self.executor.positions) > 0:
                # 更新所有头寸
                self.executor.update_positions()
                
                # 更新会话统计
                position_summary = self.executor.get_position_summary()
                self.session_stats['total_pnl'] = position_summary['daily_pnl']
                
                # 新增：track合约采样
                self._track_sample_all_options()
                
                logger.debug(f"⚡ 高频头寸更新完成 ({len(self.executor.positions)}个持仓)")
                
        except Exception as e:
            logger.error(f"高频头寸更新失败: {e}")
    
    def _update_positions_normal(self):
        """常规头寸更新 - 无持仓时执行（每1分钟）"""
        try:
            if not self._is_trading_time():
                return
            
            # 仅在无持仓时执行常规更新
            if len(self.executor.positions) == 0:
                # 更新所有头寸
                self.executor.update_positions()
                
                # 更新会话统计
                position_summary = self.executor.get_position_summary()
                self.session_stats['total_pnl'] = position_summary['daily_pnl']
                
                logger.debug("📊 常规头寸更新完成")
                
        except Exception as e:
            logger.error(f"常规头寸更新失败: {e}")
    
    def _update_positions(self):
        """兼容方法 - 通用头寸更新"""
        try:
            if not self._is_trading_time():
                return
                
            # 更新所有头寸
            self.executor.update_positions()
            
            # 更新会话统计
            position_summary = self.executor.get_position_summary()
            self.session_stats['total_pnl'] = position_summary['daily_pnl']
            
            logger.debug("头寸更新完成")
            
        except Exception as e:
            logger.error(f"更新头寸失败: {e}")
    
    def _risk_check(self):
        """风险检查"""
        try:
            risk_summary = self.executor.get_risk_summary()
            
            # 检查风险利用率
            if risk_summary['risk_utilization_pct'] > 80:
                logger.warning(f"风险利用率过高: {risk_summary['risk_utilization_pct']:.1f}%")
                
                self.notification_manager.send_message(
                    f"⚠️ 风险警告\n"
                    f"当前风险利用率: {risk_summary['risk_utilization_pct']:.1f}%\n"
                    f"当日盈亏: ${risk_summary['daily_pnl']:,.2f}\n"
                    f"请注意风险控制"
                )
            
            # 检查日内亏损
            if risk_summary['daily_pnl'] < -risk_summary['max_daily_risk'] * 0.8:
                logger.error("接近最大日亏损限制，停止新交易")
                
                self.notification_manager.send_message(
                    f"🚨 风险警报\n"
                    f"当日亏损接近限制: ${risk_summary['daily_pnl']:,.2f}\n"
                    f"停止新交易，请检查策略"
                )
                
        except Exception as e:
            logger.error(f"风险检查失败: {e}")
    
    def _check_force_close(self):
        """检查强制平仓"""
        try:
            # 使用东部时间进行判断
            et_tz = pytz.timezone('America/New_York')
            current_et_time = datetime.now(et_tz).time()
            force_close_time = datetime.strptime(config.force_close_time, "%H:%M").time()
            
            if (current_et_time >= force_close_time and 
                len(self.executor.positions) > 0):
                
                logger.info("临近收盘，执行强制平仓")
                
                # 平仓所有头寸
                self.executor.close_all_positions("临近收盘强制平仓")
                
                # 发送通知
                self.notification_manager.send_message(
                    f"🕐 强制平仓执行\n"
                    f"时间: {current_et_time}\n"
                    f"原因: 临近收盘\n"
                    f"平仓头寸数: {len(self.executor.positions)}"
                )
                
        except Exception as e:
            logger.error(f"强制平仓检查失败: {e}")
    
    def _hourly_report(self):
        """每小时报告"""
        try:
            if not self._is_trading_time():
                return
                
            position_summary = self.executor.get_position_summary()
            risk_summary = self.executor.get_risk_summary()
            
            self.notification_manager.send_message(
                f"📊 每小时报告\n"
                f"时间: {datetime.now().strftime('%H:%M')}\n"
                f"当前头寸: {position_summary['total_positions']}\n"
                f"当日交易: {position_summary['daily_trades']}\n"
                f"当日盈亏: ${position_summary['daily_pnl']:,.2f}\n"
                f"账户总值: ${risk_summary['account_value']:,.2f}"
            )
            
        except Exception as e:
            logger.error(f"每小时报告失败: {e}")
    
    def _daily_report(self):
        """日终报告"""
        try:
            position_summary = self.executor.get_position_summary()
            risk_summary = self.executor.get_risk_summary()
            signal_summary = self.signal_generator.get_signal_summary()
            
            # 计算会话统计
            session_duration = datetime.now() - self.bot_start_time
            
            report_message = (
                f"📈 日终报告 - {datetime.now().strftime('%Y-%m-%d')}\n"
                f"运行时间: {session_duration}\n"
                f"生成信号: {self.session_stats['signals_generated']}\n"
                f"执行交易: {self.session_stats['trades_executed']}\n"
                f"当日盈亏: ${position_summary['daily_pnl']:,.2f}\n"
                f"账户总值: ${risk_summary['account_value']:,.2f}\n"
                f"风险利用率: {risk_summary['risk_utilization_pct']:.1f}%\n"
                f"剩余头寸: {position_summary['total_positions']}"
            )
            
            # 保存每日汇总数据
            self._save_daily_summary(position_summary, risk_summary, signal_summary, session_duration)
            
            self.notification_manager.send_message(report_message)
            logger.info("日终报告已生成")
            
        except Exception as e:
            logger.error(f"生成日终报告失败: {e}")
    
    def _save_daily_summary(self, position_summary, risk_summary, signal_summary, session_duration):
        """保存每日汇总数据"""
        try:
            summary_data = {
                'trading_date': datetime.now().strftime('%Y-%m-%d'),
                'session_duration_minutes': session_duration.total_seconds() / 60,
                'signals_generated': self.session_stats['signals_generated'],
                'trades_executed': self.session_stats['trades_executed'],
                'total_pnl': position_summary['daily_pnl'],
                'realized_pnl': position_summary.get('daily_realized_pnl', 0),
                'unrealized_pnl': position_summary.get('total_unrealized_pnl', 0),
                'account_value': risk_summary['account_value'],
                'max_daily_risk': risk_summary['max_daily_risk'],
                'risk_utilization_pct': risk_summary['risk_utilization_pct'],
                'final_positions': position_summary['total_positions'],
                'total_signals': signal_summary.get('total_signals', 0),
                'winning_trades': 0,  # 需要计算
                'losing_trades': 0,   # 需要计算
                'win_rate': 0,        # 需要计算
                'avg_holding_time': 0, # 需要计算
                'best_trade': self.session_stats.get('best_trade', 0),
                'worst_trade': self.session_stats.get('worst_trade', 0),
                'config_snapshot': {
                    'stop_loss_pct': strategy_params.config.stop_loss_pct,
                    'take_profit_pct': strategy_params.config.take_profit_pct,
                    'max_daily_risk_pct': strategy_params.config.max_daily_risk_pct,
                    'max_single_trade_risk_pct': strategy_params.config.max_single_trade_risk_pct,
                    'orb_period_minutes': strategy_params.config.orb_period_minutes,
                    'symbol': config.symbol
                }
            }
            
            strategy_data_logger.save_daily_summary(summary_data)
            logger.info("每日汇总数据已保存")
            
        except Exception as e:
            logger.error(f"保存每日汇总数据失败: {e}")
    
    def _should_execute_signal(self, signal: TradingSignal) -> bool:
        """判断是否应该执行信号"""
        # 检查信号置信度
        if signal.confidence < 0.6:
            logger.info(f"信号置信度过低，跳过执行: {signal.confidence:.2f}")
            return False
        
        # 检查是否已有同方向头寸
        position_summary = self.executor.get_position_summary()
        for pos in position_summary['positions']:
            if ((signal.signal_type == SignalType.LONG and 'CALL' in pos['type']) or
                (signal.signal_type == SignalType.SHORT and 'PUT' in pos['type'])):
                logger.info("已有同方向头寸，跳过执行")
                return False
        
        return True
    
    def _send_signal_notification(self, signal: TradingSignal):
        """发送信号通知"""
        message = (
            f"📡 交易信号\n"
            f"类型: {signal.signal_type.value}\n"
            f"强度: {signal.strength.value}\n"
            f"置信度: {signal.confidence:.2f}\n"
            f"价格: ${signal.price:.2f}\n"
            f"原因: {signal.reason}"
        )
        
        self.notification_manager.send_message(message)
    
    def _is_trading_time(self) -> bool:
        """判断是否在交易时间内"""
        # 使用东部时间进行判断
        et_tz = pytz.timezone('America/New_York')
        current_et_time = datetime.now(et_tz).time()
        
        start_time = datetime.strptime(config.trading_start_time, "%H:%M").time()
        end_time = datetime.strptime(config.trading_end_time, "%H:%M").time()
        
        # 检查是否为工作日
        weekday = datetime.now(et_tz).weekday()
        is_weekday = weekday < 5  # 周一到周五
        
        return is_weekday and start_time <= current_et_time <= end_time
    
    def _generate_dashboard(self) -> Layout:
        """生成控制台仪表盘"""
        # 创建主布局
        layout = Layout()
        
        # 获取东部时间
        et_tz = pytz.timezone('America/New_York')
        current_et = datetime.now(et_tz)
        uptime = datetime.now() - self.bot_start_time
        
        # 如果系统正在停止，显示简化界面
        if not self.is_running:
            layout.split_column(
                Layout(self._create_system_status_panel(current_et, uptime, is_stopping=True))
            )
            return layout
        
        # 正常运行时的完整界面 - 分为上下两部分
        layout.split_column(
            Layout(name="top", ratio=1),
            Layout(name="bottom", ratio=1)
        )
        
        # 上半部分：分为左右两栏
        layout["top"].split_row(
            Layout(name="left", ratio=1),
            Layout(name="right", ratio=1)
        )
        
        # 左上：系统状态
        layout["left"].update(self._create_system_status_panel(current_et, uptime))
        
        # 右上：账户信息
        layout["right"].update(self._create_account_info_panel())
        
        # 下半部分：持仓信息（如果有持仓的话）
        layout["bottom"].update(self._create_positions_panel())
        
        return layout
    
    def _create_system_status_panel(self, current_et, uptime, is_stopping=False):
        """创建系统状态面板"""
        if is_stopping:
            status_table = Table(show_header=False, box=None)
            status_table.add_column("指标", style="cyan")
            status_table.add_column("值", style="yellow")
            
            status_table.add_row("运行状态", "🛑 正在停止")
            status_table.add_row("停止状态", "🔄 执行优雅退出流程")
            status_table.add_row("当前时间", f"🕒 {current_et.strftime('%H:%M:%S')}")
            status_table.add_row("运行时间", f"⏱️ {str(uptime).split('.')[0]}")
            
            return Panel(status_table, title="🔧 系统状态", border_style="red")
        
        # 正常运行状态
        status_table = Table(show_header=False, box=None)
        status_table.add_column("指标", style="cyan")
        status_table.add_column("值", style="magenta")
        
        # 基本状态
        status_table.add_row("运行状态", "✅ 运行中")
        status_table.add_row("交易时间", 
                           "✅ 交易时间内" if self._is_trading_time() else "⏰ 非交易时间")
        status_table.add_row("当前ET时间", f"🕒 {current_et.strftime('%H:%M:%S')}")
        status_table.add_row("运行时间", f"⏱️ {str(uptime).split('.')[0]}")
        
        # 信号信息
        status_table.add_row("生成信号", f"📡 {self.session_stats['signals_generated']}")
        status_table.add_row("最后信号", 
                           f"🕒 {self.last_signal_time.strftime('%H:%M:%S')}" if self.last_signal_time else "🕒 无")
        
        return Panel(status_table, title="🔧 系统状态", border_style="green")
    
    def _create_account_info_panel(self):
        """创建账户信息面板"""
        try:
            risk_summary = self.executor.get_risk_summary()
            position_summary = self.executor.get_position_summary()
            
            account_table = Table(show_header=False, box=None)
            account_table.add_column("指标", style="cyan")
            account_table.add_column("值", style="green")
            
            # 账户信息
            account_table.add_row("账户总值", f"💰 ${risk_summary['account_value']:,.2f}")
            account_table.add_row("当日盈亏", 
                                f"{'📈' if risk_summary['daily_pnl'] >= 0 else '📉'} ${risk_summary['daily_pnl']:,.2f}")
            account_table.add_row("风险利用率", 
                                f"{'⚠️' if risk_summary['risk_utilization_pct'] > 70 else '✅'} {risk_summary['risk_utilization_pct']:.1f}%")
            
            # 交易信息
            account_table.add_row("当前头寸", f"📊 {position_summary['total_positions']}")
            account_table.add_row("当日交易", f"🔄 {position_summary['daily_trades']}")
            account_table.add_row("执行交易", f"⚡ {self.session_stats['trades_executed']}")
            
            return Panel(account_table, title="💰 账户信息", border_style="blue")
            
        except Exception as e:
            error_table = Table(show_header=False, box=None)
            error_table.add_column("状态", style="red")
            error_table.add_row(f"❌ 获取失败: {str(e)[:40]}")
            
            return Panel(error_table, title="💰 账户信息", border_style="red")
    
    def _create_positions_panel(self):
        """创建持仓信息面板"""
        try:
            # 获取持仓信息
            positions = list(self.executor.positions.values())
            
            if not positions:
                # 没有持仓时显示简单信息
                no_position_table = Table(show_header=False, box=None)
                no_position_table.add_column("状态", style="yellow", justify="center")
                no_position_table.add_row("📭 当前无持仓")
                
                return Panel(no_position_table, title="📊 当前持仓", border_style="yellow")
            
            # 有持仓时显示详细信息
            positions_table = Table()
            positions_table.add_column("期权代码", style="cyan", no_wrap=True)
            positions_table.add_column("类型", style="magenta", justify="center")
            positions_table.add_column("数量", style="green", justify="right")
            positions_table.add_column("入场价", style="blue", justify="right") 
            positions_table.add_column("当前价", style="blue", justify="right")
            positions_table.add_column("盈亏", style="green", justify="right")
            positions_table.add_column("止损价", style="red", justify="right")
            positions_table.add_column("止盈价", style="green", justify="right")
            
            for position in positions:
                # 计算盈亏状态
                pnl_color = "green" if position.unrealized_pnl >= 0 else "red"
                pnl_symbol = "+" if position.unrealized_pnl >= 0 else ""
                
                # 简化期权代码显示
                option_display = position.option_symbol[-13:] if len(position.option_symbol) > 13 else position.option_symbol
                
                # 显示类型（CALL/PUT）
                position_type = "CALL" if "C" in position.option_symbol else "PUT"
                
                positions_table.add_row(
                    option_display,
                    position_type,
                    f"{position.quantity}",
                    f"${position.entry_price:.2f}",
                    f"${position.current_price:.2f}",
                    f"[{pnl_color}]{pnl_symbol}${position.unrealized_pnl:.2f}[/{pnl_color}]",
                    f"${position.stop_loss:.2f}" if position.stop_loss else "N/A",
                    f"${position.take_profit:.2f}" if position.take_profit else "N/A"
                )
            
            # 计算总盈亏
            total_pnl = sum(pos.unrealized_pnl for pos in positions)
            total_color = "green" if total_pnl >= 0 else "red"
            total_symbol = "+" if total_pnl >= 0 else ""
            
            # 添加总计行
            positions_table.add_row(
                "[bold]总计[/bold]",
                "",
                f"[bold]{len(positions)}[/bold]",
                "",
                "",
                f"[bold {total_color}]{total_symbol}${total_pnl:.2f}[/bold {total_color}]",
                "",
                ""
            )
            
            return Panel(positions_table, title=f"📊 当前持仓 ({len(positions)}个)", border_style="cyan")
            
        except Exception as e:
            error_table = Table(show_header=False, box=None)
            error_table.add_column("状态", style="red")
            error_table.add_row(f"❌ 获取持仓失败: {str(e)[:40]}")
            
            return Panel(error_table, title="📊 当前持仓", border_style="red")
    
    def stop(self, quick_mode: bool = False):
        """优雅停止机器人"""
        # 立即停止Live显示，避免输出混乱
        self.force_stop_display()
        
        # 使用print确保信息能够立即显示，不被Rich组件干扰
        print("\n开始优雅停止交易机器人...")
        if quick_mode:
            print("🚀 快速退出模式 - 将跳过部分验证步骤")
        print("=" * 60)
        
        logger.info("开始优雅停止交易机器人...")
        if quick_mode:
            logger.info("🚀 快速退出模式 - 将跳过部分验证步骤")
        
        self.is_running = False
        
        try:
            # 第一步：关闭所有持仓
            print("第1步: 关闭所有持仓")
            logger.info("第1步: 关闭所有持仓")
            if len(self.executor.positions) > 0:
                print(f"检测到 {len(self.executor.positions)} 个持仓，正在平仓...")
                logger.info(f"检测到 {len(self.executor.positions)} 个持仓，正在平仓...")
                success = self.executor.close_all_positions("机器人优雅停止")
                if not success:
                    print("平仓过程中出现错误，继续执行后续步骤")
                    logger.error("平仓过程中出现错误，继续执行后续步骤")
            else:
                print("没有检测到持仓")
                logger.info("没有检测到持仓")
            
            # 等待几秒让平仓订单生效
            import time
            wait_time = 1 if quick_mode else 3
            time.sleep(wait_time)
            
            # 第二步：验证所有持仓是否已关闭
            if not quick_mode:
                print("第2步: 验证所有持仓是否已关闭")
                logger.info("第2步: 验证所有持仓是否已关闭")
                max_attempts = 3
                for attempt in range(max_attempts):
                    if self.executor.verify_positions_closed():
                        print("✅ 所有持仓已确认关闭")
                        logger.info("✅ 所有持仓已确认关闭")
                        break
                    else:
                        if attempt < max_attempts - 1:
                            print(f"持仓验证失败，{3}秒后重试... (尝试 {attempt + 1}/{max_attempts})")
                            logger.warning(f"持仓验证失败，{3}秒后重试... (尝试 {attempt + 1}/{max_attempts})")
                            time.sleep(3)
                        else:
                            print("❌ 持仓关闭验证失败，请手动检查")
                            logger.error("❌ 持仓关闭验证失败，请手动检查")
            else:
                print("第2步: 快速模式 - 跳过持仓验证")
                logger.info("第2步: 快速模式 - 跳过持仓验证")
            
            # 第三步：取消所有开放订单
            print("第3步: 取消所有开放订单")
            logger.info("第3步: 取消所有开放订单")
            success = self.executor.cancel_all_open_orders()
            if not success:
                print("取消订单过程中出现错误，继续执行后续步骤")
                logger.error("取消订单过程中出现错误，继续执行后续步骤")
            
            # 等待几秒让取消订单生效
            wait_time = 1 if quick_mode else 2
            time.sleep(wait_time)
            
            # 第四步：验证所有订单是否已取消
            if not quick_mode:
                print("第4步: 验证所有订单是否已取消")
                logger.info("第4步: 验证所有订单是否已取消")
                max_attempts = 3
                for attempt in range(max_attempts):
                    if self.executor.verify_orders_cancelled():
                        print("✅ 所有订单已确认取消")
                        logger.info("✅ 所有订单已确认取消")
                        break
                    else:
                        if attempt < max_attempts - 1:
                            print(f"订单验证失败，{3}秒后重试... (尝试 {attempt + 1}/{max_attempts})")
                            logger.warning(f"订单验证失败，{3}秒后重试... (尝试 {attempt + 1}/{max_attempts})")
                            time.sleep(3)
                        else:
                            print("❌ 订单取消验证失败，请手动检查")
                            logger.error("❌ 订单取消验证失败，请手动检查")
            else:
                print("第4步: 快速模式 - 跳过订单验证")
                logger.info("第4步: 快速模式 - 跳过订单验证")
            
            # 生成最终报告
            try:
                position_summary = self.executor.get_position_summary()
                final_message = (
                    f"🛑 交易机器人已优雅停止\n"
                    f"最终盈亏: ${position_summary['daily_pnl']:,.2f}\n"
                    f"总交易次数: {position_summary['daily_trades']}\n"
                    f"运行时间: {datetime.now() - self.bot_start_time}\n"
                    f"剩余持仓: {position_summary['total_positions']} 个\n"
                    f"停止状态: 优雅停止完成"
                )
            except Exception as e:
                # 如果获取最终状态失败，使用简化报告
                logger.warning(f"获取最终状态失败: {e}")
                final_message = (
                    f"🛑 交易机器人已优雅停止\n"
                    f"运行时间: {datetime.now() - self.bot_start_time}\n"
                    f"停止状态: 优雅停止完成"
                )
            
            self.notification_manager.send_message(final_message)
            print("=" * 60)
            print("🎯 交易机器人优雅停止完成")
            logger.info("🎯 交易机器人优雅停止完成")
            
            self.tracked_options = {}  # 停止时清空track
            
        except Exception as e:
            print(f"优雅停止过程中发生异常: {e}")
            logger.error(f"优雅停止过程中发生异常: {e}")
            self.emergency_stop()
    
    def emergency_stop(self):
        """紧急停止"""
        logger.error("执行紧急停止程序")
        logger.error("=" * 60)
        
        self.is_running = False
        
        try:
            # 立即平仓所有头寸
            logger.error("紧急步骤1: 强制平仓所有头寸")
            try:
                self.executor.close_all_positions("紧急停止")
                logger.error("✅ 紧急平仓执行完成")
            except Exception as e:
                logger.error(f"❌ 紧急平仓失败: {e}")
            
            # 取消所有订单
            logger.error("紧急步骤2: 强制取消所有订单")
            try:
                self.executor.cancel_all_open_orders()
                logger.error("✅ 紧急取消订单执行完成")
            except Exception as e:
                logger.error(f"❌ 紧急取消订单失败: {e}")
            
            # 发送紧急停止通知
            try:
                position_summary = self.executor.get_position_summary()
                emergency_message = (
                    f"🚨 紧急停止执行完成\n"
                    f"停止原因: 系统异常或严重错误\n"
                    f"最终盈亏: ${position_summary['daily_pnl']:,.2f}\n"
                    f"剩余持仓: {position_summary['total_positions']} 个\n"
                    f"⚠️ 请立即手动检查账户状态"
                )
            except Exception as e:
                # 如果获取状态失败，使用简化消息
                logger.warning(f"获取紧急停止状态失败: {e}")
                emergency_message = (
                    f"🚨 紧急停止执行完成\n"
                    f"停止原因: 系统异常或严重错误\n"
                    f"运行时间: {datetime.now() - self.bot_start_time}\n"
                    f"⚠️ 请立即手动检查账户状态"
                )
            
            self.notification_manager.send_message(emergency_message)
            logger.error("=" * 60)
            logger.error("🚨 紧急停止程序执行完成，请手动检查账户状态")
            
            self.tracked_options = {}  # 停止时清空track
            
        except Exception as e:
            logger.error(f"紧急停止程序执行失败: {e}")
            # 最后的保险措施：至少发送通知
            try:
                self.notification_manager.send_message(
                    f"🚨🚨 紧急停止失败\n"
                    f"错误: {str(e)}\n"
                    f"⚠️ 请立即手动检查并关闭所有持仓和订单"
                )
            except:
                pass
        
    def get_status(self) -> Dict:
        """获取机器人状态"""
        return {
            'is_running': self.is_running,
            'is_trading_time': self._is_trading_time(),
            'uptime': str(datetime.now() - self.bot_start_time),
            'session_stats': self.session_stats,
            'positions': self.executor.get_position_summary(),
            'risk': self.executor.get_risk_summary(),
            'signals': self.signal_generator.get_signal_summary()
        }
    
    def track_option(self, option_symbol, entry_price):
        """新增track合约，若已存在则不覆盖，并写入开仓日志。"""
        if option_symbol not in self.tracked_options:
            self.tracked_options[option_symbol] = {'entry_price': entry_price, 'close_price': None}
        # 写入开仓日志
        self._ensure_tracked_log_path()
        import pytz
        from datetime import datetime
        et_tz = pytz.timezone('America/New_York')
        now_et = datetime.now(et_tz).strftime('%Y-%m-%d %H:%M:%S')
        # 使用专门的API获取最新成交价
        last_price = self.market_data.get_option_latest_trade_for_tracking(option_symbol)
        last_price_str = str(last_price) if last_price is not None else ''
        with open(self.tracked_log_path, 'a', encoding='utf-8') as f:
            f.write(f'{option_symbol},{now_et},{last_price_str},{entry_price},\n')

    def update_option_close_price(self, option_symbol, close_price):
        """更新track合约的平仓价，并写入平仓日志。"""
        if option_symbol in self.tracked_options:
            self.tracked_options[option_symbol]['close_price'] = close_price
        # 写入平仓日志
        self._ensure_tracked_log_path()
        import pytz
        from datetime import datetime
        et_tz = pytz.timezone('America/New_York')
        now_et = datetime.now(et_tz).strftime('%Y-%m-%d %H:%M:%S')
        # 使用专门的API获取最新成交价
        last_price = self.market_data.get_option_latest_trade_for_tracking(option_symbol)
        last_price_str = str(last_price) if last_price is not None else ''
        with open(self.tracked_log_path, 'a', encoding='utf-8') as f:
            f.write(f'{option_symbol},{now_et},{last_price_str},,{close_price}\n')

    def _ensure_tracked_log_path(self):
        """确保csv路径和header。"""
        import os
        from datetime import datetime
        today = datetime.now().strftime('%Y%m%d')
        log_dir = 'logs/track'
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        self.tracked_log_path = os.path.join(log_dir, f'option_track_{today}.csv')
        if not os.path.exists(self.tracked_log_path):
            with open(self.tracked_log_path, 'w', encoding='utf-8') as f:
                f.write('合约名称,时间,最新成交价,开仓价格,平仓价格\n')

    def _track_sample_all_options(self):
        """采样所有track合约的成交价，写入csv（开仓价和平仓价都为空）。"""
        self._ensure_tracked_log_path()
        import pytz
        from datetime import datetime
        et_tz = pytz.timezone('America/New_York')
        now_et = datetime.now(et_tz).strftime('%Y-%m-%d %H:%M:%S')
        for option_symbol in self.tracked_options:
            # 使用专门的API获取最新成交价
            last_price = self.market_data.get_option_latest_trade_for_tracking(option_symbol)
            last_price_str = str(last_price) if last_price is not None else ''
            # 写入csv，开仓价和平仓价都为空
            with open(self.tracked_log_path, 'a', encoding='utf-8') as f:
                f.write(f'{option_symbol},{now_et},{last_price_str},,\n') 