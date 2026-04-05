"""Настройка loguru: вывод в stderr, единый формат."""

import sys

from loguru import logger


def setup_logging() -> None:
    """Инициализация логгера для CLI (вызвать до остального кода)."""
    logger.remove()
    fmt: str = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<level>{message}</level>"
    )
    logger.add(sys.stderr, format=fmt, level="INFO", colorize=True)
