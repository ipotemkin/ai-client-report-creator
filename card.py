"""CLI: карточка товара (название + цена) → PDF с ИИ-фоном."""

import argparse
import asyncio
import json
import sys
from pathlib import Path

from jinja2 import TemplateNotFound
from loguru import logger
from openai import OpenAIError
from pydantic import ValidationError

from src.ai import fetch_card_copy, generate_card_background
from src.pdf import generate_marketplace_card_pdf
from src.config import Settings
from src.logging_setup import setup_logging
from src.models import CardCopyData


def _parse_args() -> argparse.Namespace:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="PDF-карточка товара для маркетплейса (ИИ-фон + текст)",
    )
    parser.add_argument(
        "-n",
        "--name",
        required=True,
        help="Название товара",
    )
    parser.add_argument(
        "-p",
        "--price",
        required=True,
        help="Цена (как на витрине, напр. «1 990 ₽»)",
    )
    return parser.parse_args()


async def _run_pipeline(args: argparse.Namespace) -> None:
    name: str = args.name.strip()
    price: str = args.price.strip()
    if not name or not price:
        logger.warning("Пустое название или цена")
        sys.exit(1)
    logger.info("Товар: «{}», цена: {}", name, price)
    logger.info("Загрузка настроек")
    settings: Settings = Settings()
    logger.info(
        "Модели: текст={}, картинка={}, API={}",
        settings.openai_model,
        settings.openai_image_model,
        settings.openai_base_url,
    )
    copy: CardCopyData = await fetch_card_copy(name, price, settings)
    logger.debug("Промпт фона (начало): {}…", copy.image_prompt[:80])
    png: bytes = await generate_card_background(copy.image_prompt, settings)
    root: Path = Path(__file__).resolve().parent
    reports: Path = root / "reports"
    pdf_path: Path = await generate_marketplace_card_pdf(
        name,
        price,
        copy.description,
        png,
        reports,
    )
    rel: str = str(pdf_path.relative_to(root))
    logger.success("Карточка сохранена: {}", rel)


async def _run(args: argparse.Namespace) -> None:
    try:
        await _run_pipeline(args)
    except asyncio.CancelledError:
        raise
    except ValidationError as exc:
        logger.error("Ошибка данных: {}", exc)
        sys.exit(1)
    except json.JSONDecodeError as exc:
        logger.error("JSON от модели текста невалиден: {}", exc)
        sys.exit(1)
    except OpenAIError:
        logger.exception("Ошибка API (текст или изображение)")
        sys.exit(1)
    except TemplateNotFound as exc:
        logger.error("Шаблон карточки не найден: {}", exc)
        sys.exit(1)
    except ValueError as exc:
        logger.error("{}", exc)
        sys.exit(1)
    except OSError as exc:
        logger.error("Ошибка ввода-вывода: {}", exc)
        sys.exit(1)
    except Exception as exc:
        logger.exception("Неожиданная ошибка: {}", exc)
        sys.exit(1)


def main() -> None:
    setup_logging()
    cli_args: argparse.Namespace = _parse_args()
    logger.info("Генерация карточки маркетплейса (PDF)")
    try:
        asyncio.run(_run(cli_args))
    except KeyboardInterrupt:
        logger.warning("Прервано пользователем (Ctrl+C)")
        sys.exit(130)


if __name__ == "__main__":
    main()
