"""ИИ: копирайт карточки + промпт для фона, затем gpt-image-1."""

import base64
import binascii
import json
from typing import Any

import httpx
from loguru import logger
from openai import AsyncOpenAI
from openai.types.image import Image

from utils.config import Settings
from utils.models import CardCopyData

_CARD_SYSTEM: str = (
    "Ты эксперт по маркетплейсам. По названию и цене товара верни только "
    "валидный JSON без markdown с ключами: image_prompt, description. "
    "Поле image_prompt — детальное описание визуала фона карточки для "
    "модели генерации изображений (на английском; без текста и букв на "
    "картинке; стиль: чисто, премиально, подходит под e-commerce). "
    "Поле description — краткое продающее описание товара на русском, "
    "2–4 предложения для блока текста на карточке."
)


def _client(settings: Settings) -> AsyncOpenAI:
    return AsyncOpenAI(
        api_key=settings.proxyapi_api_key,
        base_url=settings.openai_base_url,
    )


def _parse_card_json(raw: str) -> CardCopyData:
    data: dict[str, Any] = json.loads(raw)
    return CardCopyData.model_validate(data)


def _decode_b64(data_b64: str) -> bytes | None:
    raw: str = data_b64.strip()
    if not raw:
        return None
    try:
        out: bytes = base64.standard_b64decode(raw)
    except (binascii.Error, ValueError):
        try:
            pad: str = raw + "=="
            out = base64.urlsafe_b64decode(pad)
        except (binascii.Error, ValueError):
            return None
    if len(out) < 8:
        return None
    return out


async def _bytes_from_image_item(img: Image) -> bytes:
    """
    ProxyAPI чаще отдаёт b64_json; иначе — временная ссылка url.
    """
    logger.debug(
        "Ответ image: длина b64={}, есть url={}",
        len(img.b64_json or ""),
        img.url is not None,
    )
    if img.b64_json:
        decoded: bytes | None = _decode_b64(img.b64_json)
        if decoded is not None:
            logger.info("Фон из b64_json, байт: {}", len(decoded))
            return decoded
        logger.warning("Поле b64_json есть, декодирование не удалось")
    if img.url:
        logger.info("Фон по URL (скачивание)")
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.get(img.url)
            resp.raise_for_status()
        body: bytes = resp.content
        logger.info("Скачано байт: {}", len(body))
        return body
    msg: str = "В ответе images нет ни валидного b64_json, ни url"
    logger.error(msg)
    raise ValueError(msg)


async def fetch_card_copy(
    product_name: str,
    price: str,
    settings: Settings,
) -> CardCopyData:
    """gpt-4o-mini: промпт для картинки + описание для карточки."""
    logger.info("Шаг: текст для карточки и промпт фона (gpt-4o-mini)")
    client: AsyncOpenAI = _client(settings)
    user_msg: str = (
        f"Название товара: {product_name}\n" f"Цена: {price}"
    )
    response = await client.chat.completions.create(
        model=settings.openai_model,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": _CARD_SYSTEM},
            {"role": "user", "content": user_msg},
        ],
    )
    content: str | None = response.choices[0].message.content
    if not content:
        msg: str = "Пустой ответ модели (копирайт карточки)"
        logger.error(msg)
        raise ValueError(msg)
    return _parse_card_json(content)


async def generate_card_background(
    image_prompt: str,
    settings: Settings,
) -> bytes:
    """gpt-image-1: PNG (или URL) → байты для подложки PDF."""
    logger.info("Шаг: генерация фона (модель {})", settings.openai_image_model)
    client: AsyncOpenAI = _client(settings)
    resp = await client.images.generate(
        model=settings.openai_image_model,
        prompt=image_prompt,
        size="1024x1536",
        n=1,
    )
    if not resp.data:
        msg: str = "В ответе API пустой список data"
        logger.error(msg)
        raise ValueError(msg)
    first: Image = resp.data[0]
    return await _bytes_from_image_item(first)
