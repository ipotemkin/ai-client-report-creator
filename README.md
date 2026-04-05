# AI Client Report Creator

Инструменты на Python для генерации **PDF** с помощью **OpenAI-совместимого API** (в т.ч. [ProxyAPI](https://proxyapi.ru/)), **Jinja2** и **WeasyPrint**.

## Возможности

1. **Отчёт по диалогу с клиентом** (`main.py`) — по транскрипту разговора модель извлекает структурированные поля (клиент, тема, тезисы, запрос, настроение, шаги) и собирает PDF из HTML-шаблона.
2. **Карточка товара для маркетплейса** (`card.py`) — по названию и цене: текст для карточки и промпт фона задаёт **gpt-4o-mini**, фон рисует **gpt-image-1**, затем PDF с подложкой и текстом.

## Требования

- Python 3.11+
- Системные библиотеки для **WeasyPrint** (на macOS часто достаточно зависимостей из Homebrew: Cairo, Pango и т.д., см. [документацию WeasyPrint](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html)).

## Установка

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Создайте файл `.env` в корне проекта:

| Переменная | Обязательно | Описание |
|------------|-------------|----------|
| `PROXYAPI_API_KEY` | да | Ключ API (ProxyAPI или другой совместимый провайдер) |
| `PROXYAPI_OPENAI_BASE_URL` | нет | Базовый URL API, по умолчанию `https://api.proxyapi.ru/openai/v1` |
| `OPENAI_MODEL` | нет | Модель для текста, по умолчанию `gpt-4o-mini` |
| `OPENAI_IMAGE_MODEL` | нет | Модель для картинки карточки, по умолчанию `gpt-image-1` |

## Использование

### Отчёт по диалогу

Из файла:

```bash
python main.py -i example_dialog.txt
```

Из stdin (после ввода текста нажмите **Ctrl+D** в терминале):

```bash
python main.py < example_dialog.txt
# или
cat example_dialog.txt | python main.py
```

Готовый PDF сохраняется в каталог `reports/` с именем вида `report_YYYY-MM-DD_HH-MM.pdf`.

### Карточка маркетплейса

```bash
python card.py -n "Название товара" -p "1 990 ₽"
```

PDF: `reports/card_YYYY-MM-DD_HH-MM.pdf`.

## Структура проекта

```
├── main.py                 # CLI: отчёт по транскрипту
├── card.py                 # CLI: карточка товара
├── requirements.txt
├── .env                    # ключи (не коммитить)
├── templates/
│   ├── report_template.html
│   └── card_template.html
├── reports/                # сюда пишутся PDF
└── utils/
    ├── config.py           # настройки из .env
    ├── models.py           # Pydantic-модели
    ├── ai_processor.py     # чат с моделью для отчёта
    ├── pdf_generator.py    # отчёт → PDF
    ├── card_ai.py          # текст карточки + генерация фона
    ├── card_pdf_generator.py
    └── logging_setup.py
```

## Логи

Сообщения пишутся в **stderr** через **loguru** (уровень INFO). Для отладки: `LOGURU_LEVEL=DEBUG`.

## Ограничения

- Генерация изображений для карточки идёт через тот же `base_url`, что и чат; поддержка эндпоинта `/images/generations` зависит от провайдера.
- Ключ API в логи не выводится.
