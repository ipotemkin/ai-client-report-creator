"""CLI: отчёт по диалогу или карточка маркетплейса → PDF."""

import argparse
import asyncio
import sys
from pathlib import Path

from loguru import logger

from src.ai import (
    fetch_card_copy,
    generate_card_background,
    process_dialog_with_ai,
)
from src.cli.errors import handle_known_error
from src.config import Settings
from src.logging_setup import setup_logging
from src.models import CardCopyData, ReportData
from src.pdf import generate_marketplace_card_pdf, generate_report_pdf


def _build_parser() -> argparse.ArgumentParser:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        prog="main.py",
        description=(
            "Генерация PDF: отчёт по транскрипту диалога или карточка "
            "товара для маркетплейса (ИИ + WeasyPrint)."
        ),
    )
    sub = parser.add_subparsers(
        dest="command",
        required=True,
        metavar="КОМАНДА",
    )
    p_report: argparse.ArgumentParser = sub.add_parser(
        "report",
        help="PDF-отчёт по транскрипту разговора с клиентом",
    )
    p_report.add_argument(
        "-i",
        "--input",
        type=Path,
        default=None,
        help="Файл с транскрипцией (UTF-8). Без флага — stdin",
    )
    p_card: argparse.ArgumentParser = sub.add_parser(
        "card",
        help="PDF-карточка товара (ИИ-фон + название, цена, описание)",
    )
    p_card.add_argument(
        "-n",
        "--name",
        required=True,
        help="Название товара",
    )
    p_card.add_argument(
        "-p",
        "--price",
        required=True,
        help="Цена (как на витрине, напр. «1 990 ₽»)",
    )
    return parser


def _prompt_stdin_if_tty() -> None:
    """Без pipe stdin.read() ждёт EOF (Ctrl+D)."""
    if sys.stdin.isatty():
        hint: str = (
            "Введите транскрипт, затем Ctrl+D для завершения ввода "
            "(или: python main.py report -i файл.txt)"
        )
        print(hint, file=sys.stderr)


def _load_transcript(path: Path | None) -> str:
    if path is not None:
        logger.info("Чтение транскрипта из файла: {}", path.resolve())
        return path.read_text(encoding="utf-8")
    logger.info("Ожидание транскрипта из stdin")
    _prompt_stdin_if_tty()
    return sys.stdin.read()


async def _pipeline_report(args: argparse.Namespace) -> None:
    logger.info("Источник транскрипта: {}", args.input or "stdin")
    text: str = _load_transcript(args.input)
    if not text.strip():
        err: str = "Пустой ввод: укажите файл или текст в stdin."
        logger.warning(err)
        print(err, file=sys.stderr)
        sys.exit(1)
    logger.info("Транскрипт загружен, символов: {}", len(text))
    logger.info("Загрузка настроек (.env / окружение)")
    settings: Settings = Settings()
    logger.info(
        "API: base_url={}, model={}",
        settings.openai_base_url,
        settings.openai_model,
    )
    report: ReportData = await process_dialog_with_ai(text, settings)
    root: Path = Path(__file__).resolve().parent
    reports_dir: Path = root / "reports"
    logger.info("Каталог отчётов: {}", reports_dir.resolve())
    pdf_path: Path = await generate_report_pdf(report, reports_dir)
    rel: str = str(pdf_path.relative_to(root))
    logger.success("Отчёт успешно создан: {}", rel)


async def _pipeline_card(args: argparse.Namespace) -> None:
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


async def _run_async(args: argparse.Namespace) -> None:
    if args.command == "report":
        await _pipeline_report(args)
    else:
        await _pipeline_card(args)


def _run_with_errors(args: argparse.Namespace) -> None:
    try:
        asyncio.run(_run_async(args))
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        if handle_known_error(exc):
            return
        logger.exception("Неожиданная ошибка: {}", exc)
        sys.exit(1)


def main() -> None:
    setup_logging()
    parser: argparse.ArgumentParser = _build_parser()
    args: argparse.Namespace = parser.parse_args()
    logger.info("Команда: {}", args.command)
    try:
        _run_with_errors(args)
    except KeyboardInterrupt:
        logger.warning("Прервано пользователем (Ctrl+C)")
        sys.exit(130)


if __name__ == "__main__":
    main()
