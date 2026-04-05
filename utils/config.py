"""Загрузка настроек из окружения и .env."""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Конфигурация приложения."""

    model_config = SettingsConfigDict(
        env_file=Path(".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    proxyapi_api_key: str = Field(
        ...,
        alias="PROXYAPI_API_KEY",
        description="Ключ ProxyAPI для OpenAI",
    )
    openai_base_url: str = Field(
        default="https://api.proxyapi.ru/openai/v1",
        alias="PROXYAPI_OPENAI_BASE_URL",
        description="Базовый URL OpenAI-совместимого API",
    )
    openai_model: str = Field(
        default="gpt-4o-mini",
        alias="OPENAI_MODEL",
    )
    openai_image_model: str = Field(
        default="gpt-image-1",
        alias="OPENAI_IMAGE_MODEL",
        description="Модель генерации фона карточки",
    )
