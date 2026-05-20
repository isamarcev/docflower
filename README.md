# DocFlow — Документообіг служби списання

Локальний десктоп-додаток для документообігу служби списання. PyQt6 + SQLite,
без серверної частини. Файли користувача зберігаються в `data/files/`,
метадані — в `data/docflow.db`.

> Стадія: **MVP (single-admin).** Документообіг працює end-to-end: імпорт,
> версіонування з гілками, відкат, теги CRUD, експорт у zip, аудит-лог, фільтри.
> Один користувач — «Адмін» (можна змінити через `DOCFLOW_USER` env).

---

## Стек

- Python 3.11+
- PyQt6 (UI)
- SQLite (stdlib `sqlite3`, без ORM)
- `pyinstaller` — для збирання .exe під Windows

## Архітектура (layered)

```
src/docflow/
├── domain/          # Сутності та доменні помилки. Без зовнішніх імпортів.
├── application/     # Інтерфейси репозиторіїв + use-cases (command/query).
├── infrastructure/  # SQLite-репозиторії + файлове сховище.
├── presentation/    # PyQt6-вікна, віджети, діалоги, QSS-стилі.
└── main/            # Config, DI-фабрика, entry-point, seed.
```

Залежності: `presentation → application ← infrastructure ← (domain)`.
Деталі — у `/Users/creator/Documents/Claude/Projects/Documentar/CLAUDE.md`.

## Запуск (локально)

```bash
cd docflow
python3 -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
make run                             # або: PYTHONPATH=src python -m docflow.main.app
```

На першому запуску БД та `data/files/` будуть створені автоматично, плюс
заллються 9 тегів і 10 демо-документів, щоб UI не був порожнім.

## Команди Makefile

| Команда | Що робить |
|---|---|
| `make venv` | Створює `.venv/` |
| `make install` | Встановлює залежності (dev) |
| `make run` | Запускає додаток |
| `make lint` | `ruff check` |
| `make fmt` | `ruff format` |
| `make typecheck` | `mypy --strict` |
| `make test` | `pytest` |
| `make build-exe` | Збирає `.exe` через PyInstaller (Windows) |
| `make clean` | Чистить кеші та збірки |

## Що вже працює (MVP)

**Документи (CRUD):**
- Імпорт із drag & drop або файл-пікера (docx · xlsx · xls · pdf)
- Картка документа: метадані (тип, шлях, sha1, розмір, версій, гілок), теги,
  опис, останні версії, останні дії
- Редагування назви/опису
- Видалення з підтвердженням і каскадом (всі версії + файли)
- Відкриття у зовнішньому редакторі (`QDesktopServices.openUrl`)

**Версіонування (Git-style):**
- `CreateVersion` — нова версія у поточній гілці (`v1.0 → v1.1`)
- `CreateBranch` — відгалуження від обраної версії (`draft-Q1`)
- `RevertToVersion` — відкат із збереженням історії
  (створюється новий коміт із вмістом старого)
- Дерево версій: гілки зліва, коміти центр, панель деталей справа

**Теги:**
- CRUD у Tag Manager (назва, колір з 7 опцій, опис)
- Прикріплення/відкріплення з картки документа
- Підбір існуючого або створення нового з пікера
- Фільтр документів за тегом із sidebar

**Пошук / сортування:**
- Live-пошук по назві файла (toolbar)
- Фільтр за тегом (клік у sidebar)
- Сортування таблиці по будь-якому стовпцю

**Експорт / аудит:**
- Експорт документа в zip: `manifest.json` + усі версії
  (namespace по гілках, щоб `v1.2` з main і draft не конфліктували)
- Експорт окремої версії в файл
- Журнал дій із фільтрами та експортом у CSV
- Аудит-записи з кольоровими chip-міти ("створено версію", "відкат", "видалено"…)

## Що буде наступним кроком (не critical для MVP)

- Розширений діалог пошуку (wildcard, дати, типи, теги include/exclude) — макет є
- Зв'язки між документами (на основі / доповнення / джерело даних)
- Сторінка налаштувань (шлях зберігання, користувач)
- Збирання `.exe` через PyInstaller (вже є make-таск)
- Юніт- та інтеграційні тести (pytest)
- Custom-painted Git-graph із лініями (зараз — плоский список комітів)

## Структура `data/`

```
data/
├── docflow.db        # SQLite-БД (не комітимо)
└── files/            # Файли документів за типом/роком/місяцем
    └── docx/2026/05/<uuid>.docx
```

## Файли, які не можна редагувати без узгодження

- `pyproject.toml`, `requirements*.txt` — версії та залежності
- `src/docflow/infrastructure/db/schema.py` — БД-схема (тільки через міграцію)

Деталі по правилах розробки — в `/Users/creator/Documents/Claude/Projects/Documentar/CLAUDE.md`.
