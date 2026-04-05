"""Анализ транскрипта диалога → структура отчёта (JSON от модели)."""

from loguru import logger

from src.ai.common import (
    chat_completion_json_object,
    parse_json_to_model,
)
from src.config import Settings
from src.models import ReportData

_SYSTEM_PROMPT: str = (
    "Ты аналитик диалогов с клиентами. По транскрипту извлеки поля "
    "для отчёта. Ответь ТОЛЬКО валидным JSON без markdown, с ключами: "
    "client_name, topic, dialog_theses, main_request, mood, next_steps. "
    "Поле dialog_theses — основные тезисы диалога: 3–7 коротких смысловых "
    "пунктов (факты, договорённости, важные детали). Каждый пункт — "
    "отдельная строка внутри значения JSON, разделяй символом переноса "
    "строки \\n. "
    "Все значения — строки на русском языке."
)


async def process_dialog_with_ai(
    text: str,
    settings: Settings | None = None,
) -> ReportData:
    """
    Передаёт транскрипцию в модель и возвращает ReportData.
    """
    cfg: Settings = settings or Settings()
    logger.info("Шаг: анализ диалога через ИИ (chat.completions)")
    logger.debug("Размер текста для модели: {} символов", len(text))
    raw_json: str = await chat_completion_json_object(
        cfg,
        _SYSTEM_PROMPT,
        text,
    )
    logger.info("Ответ API получен, разбор JSON в ReportData")
    report: ReportData = parse_json_to_model(raw_json, ReportData)
    topic_short: str = report.topic
    if len(topic_short) > 50:
        topic_short = topic_short[:50] + "…"
    logger.info(
        "Отчёт: клиент «{}», тема: {}",
        report.client_name,
        topic_short or "—",
    )
    return report
