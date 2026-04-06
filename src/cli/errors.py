"""Обработка ошибок CLI: единые правила логирования и завершения."""

import json
import sys

from jinja2 import TemplateNotFound
from loguru import logger
from openai import OpenAIError
from pydantic import ValidationError

ErrorRule = tuple[type[Exception], str, bool]

KNOWN_ERROR_RULES: tuple[ErrorRule, ...] = (
    (FileNotFoundError, "Файл транскрипта не найден: {}", False),
    (IsADirectoryError, "Указан путь к каталогу, нужен файл: {}", False),
    (PermissionError, "Нет прав на чтение или запись: {}", False),
    (UnicodeDecodeError, "Не удалось прочитать файл как UTF-8: {}", False),
    (ValidationError, "Ошибка проверки данных: {}", False),
    (json.JSONDecodeError, "Ответ модели не является валидным JSON: {}", False),
    (TemplateNotFound, "Шаблон HTML не найден: {}", False),
    (ValueError, "{}", False),
    (OSError, "Системная ошибка ввода-вывода: {}", False),
    (OpenAIError, "Ошибка API (OpenAI / ProxyAPI)", True),
)


def log_and_exit(msg_template: str, exc: Exception, with_traceback: bool) -> None:
    """Логирует ожидаемую ошибку и завершает процесс с кодом 1."""
    if with_traceback:
        logger.exception(msg_template)
    else:
        logger.error(msg_template, exc)
    sys.exit(1)


def handle_known_error(exc: Exception) -> bool:
    """
    Обрабатывает известные ошибки (по правилам логирования).
    Возвращает True, если ошибка обработана.
    """
    for err_type, msg_template, with_traceback in KNOWN_ERROR_RULES:
        if isinstance(exc, err_type):
            log_and_exit(msg_template, exc, with_traceback)
    return False
