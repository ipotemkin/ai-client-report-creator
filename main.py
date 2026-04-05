"""CLI: транскрипт → ИИ → PDF."""

import argparse
import asyncio
import json
import sys
from pathlib import Path

from jinja2 import TemplateNotFound
from loguru import logger
from openai import OpenAIError
from pydantic import ValidationError

from utils.ai_processor import process_dialog_with_ai
from utils.config import Settings
from utils.logging_setup import setup_logging
from utils.models import ReportData
from utils.pdf_generator import generate_report_pdf


def _parse_args() -> argparse.Namespace:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="PDF-отчёт по транскрипту диалога (ИИ + HTML)",
    )
    parser.add_argument(
        "-i",
        "--input",
        type=Path,
        default=None,
        help="Файл с транскрипцией (UTF-8). Без флага — stdin",
    )
    return parser.parse_args()


def _prompt_stdin_if_tty() -> None:
    """Пояснение: без pipe stdin.read() блокируется до EOF (Ctrl+D)."""
    if sys.stdin.isatty():
        hint: str = (
            "Введите транскрипт, затем Ctrl+D для завершения ввода "
            "(или используйте: python main.py -i файл.txt)"
        )
        print(hint, file=sys.stderr)


def _load_transcript(path: Path | None) -> str:
    if path is not None:
        logger.info("Чтение транскрипта из файла: {}", path.resolve())
        return path.read_text(encoding="utf-8")
    logger.info("Ожидание транскрипта из stdin")
    _prompt_stdin_if_tty()
    return sys.stdin.read()


async def _run_pipeline() -> None:
    logger.info("Разбор аргументов командной строки")
    args: argparse.Namespace = _parse_args()
    src: str = "stdin" if args.input is None else str(args.input)
    logger.info("Источник транскрипта: {}", src)
    text: str = _load_transcript(args.input)
    if not text.strip():
        err: str = "Пустой ввод: укажите файл или текст в stdin."
        logger.warning(err)
        print(err, file=sys.stderr)
        sys.exit(1)
    n_chars: int = len(text)
    logger.info("Транскрипт загружен, символов: {}", n_chars)
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
    msg: str = f"Отчёт успешно создан: {rel}"
    logger.success(msg)


async def _run() -> None:
    try:
        await _run_pipeline()
    except asyncio.CancelledError:
        raise
    except FileNotFoundError as exc:
        logger.error("Файл транскрипта не найден: {}", exc)
        sys.exit(1)
    except IsADirectoryError as exc:
        logger.error("Указан путь к каталогу, нужен файл: {}", exc)
        sys.exit(1)
    except PermissionError as exc:
        logger.error("Нет прав на чтение или запись: {}", exc)
        sys.exit(1)
    except UnicodeDecodeError as exc:
        logger.error("Не удалось прочитать файл как UTF-8: {}", exc)
        sys.exit(1)
    except ValidationError as exc:
        logger.error("Ошибка проверки данных (конфиг или отчёт): {}", exc)
        sys.exit(1)
    except json.JSONDecodeError as exc:
        logger.error("Ответ модели не является валидным JSON: {}", exc)
        sys.exit(1)
    except OpenAIError:
        logger.exception("Ошибка API (OpenAI / ProxyAPI)")
        sys.exit(1)
    except TemplateNotFound as exc:
        logger.error("Шаблон HTML не найден: {}", exc)
        sys.exit(1)
    except ValueError as exc:
        logger.error("{}", exc)
        sys.exit(1)
    except OSError as exc:
        logger.error("Системная ошибка ввода-вывода: {}", exc)
        sys.exit(1)
    except Exception as exc:
        logger.exception("Неожиданная ошибка: {}", exc)
        sys.exit(1)


def main() -> None:
    setup_logging()
    logger.info("Запуск генератора PDF-отчётов по диалогу")
    try:
        asyncio.run(_run())
    except KeyboardInterrupt:
        logger.warning("Прервано пользователем (Ctrl+C)")
        sys.exit(130)


if __name__ == "__main__":
    main()
