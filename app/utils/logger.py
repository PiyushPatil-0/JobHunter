"""
Centralized logging configuration for JobHunter AI.
"""

from pathlib import Path

from loguru import logger

ROOT_DIR = Path(__file__).resolve().parents[2]
LOG_DIR = ROOT_DIR / "logs"

LOG_DIR.mkdir(exist_ok=True)

logger.remove()

logger.add(
    sink=lambda msg: print(msg, end=""),
    level="INFO",
    colorize=True,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
           "<level>{level: <8}</level> | "
           "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
           "<level>{message}</level>",
)

logger.add(
    LOG_DIR / "jobhunter.log",
    rotation="10 MB",
    retention="30 days",
    compression="zip",
    level="DEBUG",
    encoding="utf-8",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | "
           "{name}:{function}:{line} | {message}",
)

__all__ = ["logger"]