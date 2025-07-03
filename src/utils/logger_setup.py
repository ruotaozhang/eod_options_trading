"""
日志设置模块
配置系统日志格式和输出
"""

import os
import sys
from pathlib import Path
from loguru import logger
from datetime import datetime


def setup_logger():
    """设置日志配置"""
    
    # 创建日志目录
    log_dir = Path("logs")
    trading_dir = log_dir / "trading"
    error_dir = log_dir / "error"
    trades_dir = log_dir / "trades"
    for d in [trading_dir, error_dir, trades_dir]:
        d.mkdir(parents=True, exist_ok=True)
    
    # 移除默认处理器
    logger.remove()
    
    # 控制台输出
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
               "<level>{message}</level>",
        level="INFO",
        colorize=True
    )
    
    # 文件输出 - 详细日志
    logger.add(
        trading_dir / f"eod_trading_{datetime.now().strftime('%Y%m%d')}.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        level="DEBUG",
        rotation="1 day",
        retention="30 days",
        compression="zip"
    )
    
    # 文件输出 - 错误日志
    logger.add(
        error_dir / f"error_{datetime.now().strftime('%Y%m%d')}.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        level="ERROR",
        rotation="1 day",
        retention="90 days",
        compression="zip"
    )
    
    # 交易日志
    logger.add(
        trades_dir / f"trades_{datetime.now().strftime('%Y%m%d')}.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {message}",
        level="INFO",
        filter=lambda record: "TRADE" in record["extra"],
        rotation="1 day",
        retention="365 days"
    )
    
    logger.info("日志系统初始化完成") 