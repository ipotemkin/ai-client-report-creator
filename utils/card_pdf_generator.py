"""PDF карточки маркетплейса: фон-картинка + текст."""

import asyncio
import shutil
import tempfile
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from loguru import logger
from weasyprint import HTML

_TEMPLATE: str = "card_template.html"


def _root() -> Path:
    return Path(__file__).resolve().parent.parent


def _card_filename(now: datetime) -> str:
    return f"card_{now.strftime('%Y-%m-%d_%H-%M')}.pdf"


def _background_filename(data: bytes) -> str:
    """Имя файла с верным расширением (WeasyPrint по типу картинки)."""
    if len(data) >= 3 and data[:3] == b"\xff\xd8\xff":
        return "card_bg.jpg"
    if len(data) >= 8 and data[:8] == b"\x89PNG\r\n\x1a\n":
        return "card_bg.png"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "card_bg.webp"
    logger.warning("Неизвестный формат изображения, сохраняем как PNG")
    return "card_bg.png"


def _render_html(
    product_name: str,
    price: str,
    description: str,
    background_image: str,
    templates_dir: Path,
) -> str:
    env: Environment = Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = env.get_template(_TEMPLATE)
    return template.render(
        product_name=product_name,
        price=price,
        description=description,
        background_image=background_image,
    )


def _base_url_for_dir(directory: Path) -> str:
    uri: str = directory.resolve().as_uri()
    if not uri.endswith("/"):
        return uri + "/"
    return uri


def _write_pdf(html_str: str, out: Path, base_url: str) -> None:
    doc: HTML = HTML(string=html_str, base_url=base_url)
    doc.write_pdf(target=str(out))


async def generate_marketplace_card_pdf(
    product_name: str,
    price: str,
    description: str,
    image_png: bytes,
    reports_dir: Path,
    at: datetime | None = None,
) -> Path:
    """
    HTML: фон через <img> (надёжнее background-image в WeasyPrint),
    файл во временном каталоге с корректным расширением.
    """
    moment: datetime = at or datetime.now()
    reports_dir.mkdir(parents=True, exist_ok=True)
    out_path: Path = reports_dir / _card_filename(moment)
    tpl_dir: Path = _root() / "templates"
    tmp_dir: Path = Path(tempfile.mkdtemp(prefix="card_pdf_"))
    bg_name: str = _background_filename(image_png)
    try:
        bg_path: Path = tmp_dir / bg_name
        bg_path.write_bytes(image_png)
        base_url: str = _base_url_for_dir(tmp_dir)
        logger.info(
            "Шаблон {}, фон: {}, base_url=диск",
            _TEMPLATE,
            bg_name,
        )
        html_str: str = _render_html(
            product_name,
            price,
            description,
            bg_name,
            tpl_dir,
        )
        await asyncio.to_thread(_write_pdf, html_str, out_path, base_url)
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
    logger.info("PDF карточки записан: {}", out_path.resolve())
    return out_path
