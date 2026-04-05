"""Общие клиент OpenAI, JSON и вызовы chat с ответом-json."""

import json
from typing import Any, TypeVar

from loguru import logger
from openai import AsyncOpenAI
from pydantic import BaseModel

from src.config import Settings

TModel = TypeVar("TModel", bound=BaseModel)


def openai_client(settings: Settings) -> AsyncOpenAI:
    """AsyncOpenAI с ключом и base_url из настроек."""
    return AsyncOpenAI(
        api_key=settings.proxyapi_api_key,
        base_url=settings.openai_base_url,
    )


def parse_json_to_model(raw: str, model_cls: type[TModel]) -> TModel:
    """Разбор JSON-строки в Pydantic-модель."""
    data: dict[str, Any] = json.loads(raw)
    return model_cls.model_validate(data)


async def chat_completion_json_object(
    settings: Settings,
    system_prompt: str,
    user_content: str,
    *,
    empty_reply_message: str = "Пустой ответ модели",
) -> str:
    """
    Один запрос chat.completions с response_format=json_object.
    Возвращает текст ответа (JSON).
    """
    client: AsyncOpenAI = openai_client(settings)
    response = await client.chat.completions.create(
        model=settings.openai_model,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
    )
    content: str | None = response.choices[0].message.content
    if not content:
        logger.error(empty_reply_message)
        raise ValueError(empty_reply_message)
    return content
