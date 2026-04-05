"""Pydantic-модели данных отчёта."""

from pydantic import BaseModel, Field


class ReportData(BaseModel):
    """Структурированные данные для PDF-отчёта."""

    client_name: str = Field(
        default="",
        description="Имя или компания клиента",
    )
    topic: str = Field(default="", description="Тема разговора")
    dialog_theses: str = Field(
        default="",
        description="Основные тезисы диалога (пункты, по смыслу)",
    )
    main_request: str = Field(
        default="",
        description="Основной запрос клиента",
    )
    mood: str = Field(
        default="",
        description="Настроение / тон диалога",
    )
    next_steps: str = Field(
        default="",
        description="Рекомендуемые следующие шаги",
    )


class CardCopyData(BaseModel):
    """Ответ gpt-4o-mini для карточки маркетплейса."""

    image_prompt: str = Field(
        ...,
        description="Промпт для gpt-image-1 (фон карточки)",
    )
    description: str = Field(
        ...,
        description="Текст описания на карточке",
    )
