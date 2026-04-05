"""Общая сборка HTML → PDF (Jinja2 loader + WeasyPrint)."""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML


def project_root() -> Path:
    """Корень репозитория (src/pdf/ → вверх на два уровня)."""
    return Path(__file__).resolve().parents[2]


def jinja_env(templates_dir: Path) -> Environment:
    """Окружение Jinja2 для HTML-шаблонов в каталоге templates_dir."""
    return Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=select_autoescape(["html", "xml"]),
    )


def directory_base_url(directory: Path) -> str:
    """file:///…/ каталога; слэш в конце — для относительных url."""
    uri: str = directory.resolve().as_uri()
    if not uri.endswith("/"):
        return uri + "/"
    return uri


def write_pdf(html: str, output_path: Path, base_url: str) -> None:
    """HTML-строка и base_url для относительных путей → файл PDF."""
    doc: HTML = HTML(string=html, base_url=base_url)
    doc.write_pdf(target=str(output_path))
