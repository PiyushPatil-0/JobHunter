"""
Centralized logging configuration for JobHunter AI.
"""

from pathlib import Path
import sys

from loguru import logger

ROOT_DIR = Path(__file__).resolve().parents[2]
LOG_DIR = ROOT_DIR / "logs"

LOG_DIR.mkdir(exist_ok=True)

logger.remove()

# Windows terminals commonly default to cp1252, which cannot render
# Loguru tracebacks containing box-drawing characters. Keep console
# logging UTF-8 so an error never triggers a second logging error.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

logger.add(
    sink=sys.stdout,
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
