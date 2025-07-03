"""
通知管理模块
负责发送各种类型的通知（简化版本，仅日志记录）
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from loguru import logger
from enum import Enum

from ..config import config


class NotificationLevel(Enum):
    """通知级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class NotificationRecord:
    """通知记录"""
    timestamp: datetime
    level: NotificationLevel
    message: str
    category: str = "general"


class NotificationManager:
    """通知管理器（简化版本）"""
    
    def __init__(self):
        self.notification_history: List[NotificationRecord] = []
        self.last_notification_time: Dict[str, datetime] = {}
        
        logger.info("通知管理器初始化完成（简化模式）")
    
    def send_message(self, message: str, priority: str = "normal", category: str = "general") -> bool:
        """发送消息（仅记录到日志）"""
        try:
            # 根据优先级确定日志级别
            level_map = {
                "low": NotificationLevel.INFO,
                "normal": NotificationLevel.INFO,
                "high": NotificationLevel.WARNING,
                "critical": NotificationLevel.ERROR
            }
            
            level = level_map.get(priority, NotificationLevel.INFO)
            
            # 记录通知
            self._record_notification(message, level, category)
            
            # 输出到日志
            if level == NotificationLevel.ERROR or level == NotificationLevel.CRITICAL:
                logger.error(f"[{category.upper()}] {message}")
            elif level == NotificationLevel.WARNING:
                logger.warning(f"[{category.upper()}] {message}")
            else:
                logger.info(f"[{category.upper()}] {message}")
            
            return True
            
        except Exception as e:
            logger.error(f"发送通知失败: {e}")
            return False
    
    def _record_notification(self, message: str, level: NotificationLevel, category: str):
        """记录通知"""
        record = NotificationRecord(
            timestamp=datetime.now(),
            level=level,
            message=message,
            category=category
        )
        
        self.notification_history.append(record)
        
        # 限制历史记录长度
        if len(self.notification_history) > 1000:
            self.notification_history = self.notification_history[-1000:]
    
    def send_startup_notification(self):
        """发送启动通知"""
        message = (
            f"🚀 EOD期权交易系统启动\n"
            f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"交易标的: {config.symbol}\n"
            f"环境: {'纸面交易' if 'paper' in config.alpaca_base_url else '实盘交易'}"
        )
        
        self.send_message(message, "normal", "startup")
    
    def send_shutdown_notification(self, reason: str = "正常关闭"):
        """发送关闭通知"""
        message = (
            f"🛑 EOD期权交易系统关闭\n"
            f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"关闭原因: {reason}"
        )
        
        self.send_message(message, "normal", "shutdown")
    
    def send_trade_notification(self, trade_info: dict):
        """发送交易通知"""
        action = trade_info.get('action', '未知')
        symbol = trade_info.get('symbol', '未知')
        price = trade_info.get('price', 0)
        quantity = trade_info.get('quantity', 0)
        
        message = (
            f"💼 交易执行\n"
            f"操作: {action}\n"
            f"标的: {symbol}\n"
            f"价格: ${price:.2f}\n"
            f"数量: {quantity}\n"
            f"时间: {datetime.now().strftime('%H:%M:%S')}"
        )
        
        self.send_message(message, "high", "trading")
    
    def send_risk_alert(self, risk_info: dict):
        """发送风险提醒"""
        risk_type = risk_info.get('type', '未知风险')
        current_value = risk_info.get('current', 0)
        limit_value = risk_info.get('limit', 0)
        
        message = (
            f"⚠️ 风险提醒\n"
            f"类型: {risk_type}\n"
            f"当前值: {current_value}\n"
            f"限制值: {limit_value}\n"
            f"时间: {datetime.now().strftime('%H:%M:%S')}"
        )
        
        self.send_message(message, "high", "risk")
    
    def send_emergency_alert(self, message: str):
        """发送紧急警报"""
        emergency_message = f"🚨 紧急警报: {message}"
        self.send_message(emergency_message, "critical", "emergency")
    
    def get_notification_summary(self) -> dict:
        """获取通知摘要"""
        now = datetime.now()
        today_notifications = [
            n for n in self.notification_history 
            if n.timestamp.date() == now.date()
        ]
        
        return {
            "total_notifications": len(self.notification_history),
            "today_notifications": len(today_notifications),
            "recent_notifications": [
                {
                    "timestamp": n.timestamp.isoformat(),
                    "level": n.level.value,
                    "message": n.message,
                    "category": n.category
                }
                for n in self.notification_history[-10:]
            ],
            "notification_methods": {
                "log": "✅ 启用",
                "slack": "❌ 已禁用",
                "email": "❌ 已禁用"
            }
        }
    
    def test_notifications(self) -> dict:
        """测试通知功能"""
        results = {}
        
        # 测试日志记录
        try:
            self.send_message("通知系统测试消息", "normal", "test")
            results["log"] = "✅ 成功"
        except Exception as e:
            results["log"] = f"❌ 失败: {e}"
        
        results["slack"] = "❌ 已禁用"
        results["email"] = "❌ 已禁用"
        
        return results


# 全局通知管理器实例
notification_manager = NotificationManager() 