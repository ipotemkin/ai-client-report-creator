"""Генерация PDF отчёта по диалогу (Jinja2 + WeasyPrint)."""

import asyncio
from datetime import datetime
from pathlib import Path

from loguru import logger

from src.models import ReportData
from src.pdf.render import (
    directory_base_url,
    jinja_env,
    project_root,
    write_pdf,
)

_TEMPLATE_NAME: str = "report_template.html"


def _make_output_filename(now: datetime) -> str:
    stamp: str = now.strftime("%Y-%m-%d_%H-%M")
    return f"report_{stamp}.pdf"


def _generation_date_label(now: datetime) -> str:
    return now.strftime("%d.%m.%Y %H:%M")


def _non_empty_lines(raw: str) -> list[str]:
    text: str = raw.replace("\r\n", "\n")
    lines: list[str] = text.split("\n")
    return [s.strip() for s in lines if s.strip()]


def _render_html(
    data: ReportData,
    templates_dir: Path,
    generated_at: datetime,
) -> str:
    logger.info("Шаг: подстановка данных в шаблон {}", _TEMPLATE_NAME)
    env = jinja_env(templates_dir)
    template = env.get_template(_TEMPLATE_NAME)
    gen_label: str = _generation_date_label(generated_at)
    theses: list[str] = _non_empty_lines(data.dialog_theses)
    steps: list[str] = _non_empty_lines(data.next_steps)
    return template.render(
        generation_date=gen_label,
        client_name=data.client_name,
        topic=data.topic,
        dialog_theses_items=theses,
        main_request=data.main_request,
        mood=data.mood,
        next_steps_items=steps,
    )


def _write_pdf_sync(html_string: str, output_path: Path) -> None:
    logger.info("Шаг: конвертация HTML → PDF (WeasyPrint)")
    logger.debug("Размер HTML: {} символов", len(html_string))
    base: str = directory_base_url(project_root())
    write_pdf(html_string, output_path, base)
    logger.info("Файл PDF записан: {}", output_path.resolve())


async def generate_report_pdf(
    data: ReportData,
    reports_dir: Path,
    at: datetime | None = None,
) -> Path:
    """
    Подставляет данные в шаблон, конвертирует в PDF, сохраняет в reports_dir.
    """
    moment: datetime = at or datetime.now()
    reports_dir.mkdir(parents=True, exist_ok=True)
    filename: str = _make_output_filename(moment)
    output_path: Path = reports_dir / filename
    logger.info("Целевой файл PDF: {}", output_path.name)
    templates_dir: Path = project_root() / "templates"
    html_string: str = _render_html(data, templates_dir, moment)
    await asyncio.to_thread(_write_pdf_sync, html_string, output_path)
    return output_path
