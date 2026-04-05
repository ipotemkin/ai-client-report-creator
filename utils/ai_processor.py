"""Асинхронная обработка транскрипта через OpenAI (ProxyAPI)."""

import json
from typing import Any

from loguru import logger
from openai import AsyncOpenAI

from utils.config import Settings
from utils.models import ReportData

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


def _build_client(settings: Settings) -> AsyncOpenAI:
    return AsyncOpenAI(
        api_key=settings.proxyapi_api_key,
        base_url=settings.openai_base_url,
    )


def _parse_report_payload(raw: str) -> ReportData:
    data: dict[str, Any] = json.loads(raw)
    return ReportData.model_validate(data)


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
    client: AsyncOpenAI = _build_client(cfg)
    response = await client.chat.completions.create(
        model=cfg.openai_model,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
    )
    choice = response.choices[0]
    content: str | None = choice.message.content
    if not content:
        msg: str = "Пустой ответ модели"
        logger.error(msg)
        raise ValueError(msg)
    logger.info("Ответ API получен, разбор JSON в ReportData")
    report: ReportData = _parse_report_payload(content)
    topic_short: str = report.topic
    if len(topic_short) > 50:
        topic_short = topic_short[:50] + "…"
    logger.info(
        "Отчёт: клиент «{}», тема: {}",
        report.client_name,
        topic_short or "—",
    )
    return report
