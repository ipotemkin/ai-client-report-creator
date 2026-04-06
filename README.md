# AI Client Report Creator

Инструменты на Python для генерации **PDF** с помощью **OpenAI-совместимого API** (в т.ч. [ProxyAPI](https://proxyapi.ru/)), **Jinja2** и **WeasyPrint**.

## Возможности

1. **Отчёт по диалогу** (`main.py report`) — по транскрипту модель извлекает поля (клиент, тема, тезисы, запрос, настроение, шаги) и собирает PDF.
2. **Карточка маркетплейса** (`main.py card`) — по названию и цене: **gpt-4o-mini** даёт текст и промпт фона, **gpt-image-1** рисует фон, затем PDF с подложкой и текстом.

Один CLI: `main.py` с подкомандами `report` и `card`.

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

### Справка по командам

```bash
python main.py --help
python main.py report --help
python main.py card --help
```

### Отчёт по диалогу (`report`)

Из файла:

```bash
python main.py report -i example_dialog.txt
```

Из stdin (после ввода текста нажмите **Ctrl+D** в терминале):

```bash
python main.py report < example_dialog.txt
# или
cat example_dialog.txt | python main.py report
```

Готовый PDF: `reports/report_YYYY-MM-DD_HH-MM.pdf`.

### Карточка маркетплейса (`card`)

```bash
python main.py card -n "Название товара" -p "1 990 ₽"
```

PDF: `reports/card_YYYY-MM-DD_HH-MM.pdf`.

## Структура проекта

```
├── main.py                 # единый CLI (подкоманды report, card)
├── requirements.txt
├── .env                    # ключи (не коммитить)
├── templates/
│   ├── report_template.html
│   └── card_template.html
├── reports/                # сюда пишутся PDF
└── src/
    ├── config.py
    ├── models.py
    ├── logging_setup.py
    ├── ai/                 # OpenAI / ProxyAPI
    │   ├── common.py       # клиент, JSON, chat → JSON
    │   ├── dialog.py       # отчёт по транскрипту
    │   └── card.py         # карточка: копирайт + картинка
    └── pdf/                # WeasyPrint + Jinja2
        ├── render.py
        ├── report.py
        └── card.py
```

## Логи

Сообщения пишутся в **stderr** через **loguru** (уровень INFO). Для отладки: `LOGURU_LEVEL=DEBUG`.

## Ограничения

- Генерация изображений для карточки идёт через тот же `base_url`, что и чат; поддержка эндпоинта `/images/generations` зависит от провайдера.
- Ключ API в логи не выводится.
