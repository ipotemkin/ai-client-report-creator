"""Работа с OpenAI-совместимым API (ProxyAPI): диалоги и карточки."""

from src.ai.card import fetch_card_copy, generate_card_background
from src.ai.dialog import process_dialog_with_ai

__all__ = [
    "fetch_card_copy",
    "generate_card_background",
    "process_dialog_with_ai",
]
