# 💧 Water Delivery Bot

Коммерческий Telegram-магазин доставки питьевой воды: каталог с мгновенным
пересчётом стоимости, пошаговое оформление заказа, оплата через абстрактный
платёжный провайдер (mock из коробки или ЮKassa), напоминания о неоплаченных
заказах, промокоды и полностью управляемая из Telegram административная
панель — без правок кода и без перезапуска бота.

## Содержание

- [Стек](#стек)
- [Структура проекта](#структура-проекта)
- [Быстрый старт (локально)](#быстрый-старт-локально)
- [Запуск через Docker](#запуск-через-docker)
- [Переменные окружения](#переменные-окружения)
- [Команды администратора](#команды-администратора)
- [Платёжная интеграция](#платёжная-интеграция)
- [Тесты и статический анализ](#тесты-и-статический-анализ)
- [FAQ для разработчика](#faq-для-разработчика)

## Стек

- Python 3.12+, [aiogram 3](https://docs.aiogram.dev/) (polling)
- SQLAlchemy 2.x (async) + Alembic — SQLite для разработки, PostgreSQL для продакшена
- aiohttp — приём webhook от платёжного провайдера параллельно с polling-ом бота
- APScheduler — напоминания о неоплаченных заказах
- pydantic-settings — конфигурация из `.env`
- pytest / ruff / black / isort / mypy

## Структура проекта

```
app/
  bot.py              — точка входа: только запуск, без бизнес-логики
  loader.py            — сборка Bot/Dispatcher, порядок middleware
  config.py             — настройки из .env (pydantic-settings)
  webhook_server.py     — aiohttp-сервер приёма webhook от платёжного провайдера
  logging_config.py     — настройка логирования (консоль + файл)
  database/
    models/              — SQLAlchemy-модели (users, orders, payments, promo_codes, ...)
    repositories/         — единственная точка доступа к БД
  services/              — вся бизнес-логика (Price/Delivery/Promo/Order/Payment/...)
  payments/               — PaymentProvider: абстракция + Mock + ЮKassa
  handlers/                — пользовательские сценарии (start, catalog, order, ...)
    admin/                   — административная панель (/admin, /price, /delivery, ...)
  keyboards/, callbacks/     — inline-клавиатуры и типизированные CallbackData
  states/                    — FSM-состояния (заказ, промокод, админ-сценарии)
  middlewares/, filters/     — DB-сессия, антифлуд, логирование, IsAdmin
  scheduler/                 — напоминания о неоплаченных заказах
  utils/                     — форматирование, валидация, деньги, константы
alembic/                — миграции БД
tests/                  — pytest-суита
```

## Быстрый старт (локально)

Требования: Python 3.12+ (проверено также на 3.11).

```bash
git clone https://github.com/mikhailmyau/water-delivery-bot.git
cd water-delivery-bot

python3 -m venv .venv
source .venv/bin/activate           # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt  # requirements.txt — без dev-инструментов

cp .env.example .env
# откройте .env и укажите как минимум:
#   BOT_TOKEN=<токен от @BotFather>
#   ADMIN_IDS=<ваш Telegram ID>

python -m alembic upgrade head        # создаёт storage/db.sqlite3 со всеми таблицами
python -m app.bot                     # запускает polling + webhook-сервер (порт 8080)
```

По умолчанию `PAYMENT_PROVIDER=mock` — бот полностью работает без реального
платёжного шлюза: кнопка «Оплатить» открывает локальную тестовую страницу
подтверждения оплаты (`http://localhost:8080/payments/mock-checkout/...`),
которая проходит через тот же webhook-контракт, что и боевой провайдер.

Напишите боту `/start`, чтобы увидеть главное меню, и `/admin`, если ваш
Telegram ID указан в `ADMIN_IDS`, — чтобы открыть панель управления.

## Запуск через Docker

```bash
cp .env.example .env
# заполните BOT_TOKEN, ADMIN_IDS и, при необходимости, платёжные ключи

docker compose up --build -d
```

`docker-compose.yml` поднимает три контейнера: `bot`, `postgres`, `redis`.
Бот дожидается готовности БД, сам применяет миграции (`alembic upgrade head`)
при старте и слушает polling + webhook (порт из `PAYMENT_WEBHOOK_PORT`,
по умолчанию 8080, проброшен наружу).

Логи: `docker compose logs -f bot`. Остановить: `docker compose down`.

## Переменные окружения

Полный список — в [`.env.example`](.env.example). Ключевые:

| Переменная | Назначение |
|---|---|
| `BOT_TOKEN` | Токен бота от @BotFather |
| `ADMIN_IDS` | Telegram ID администраторов через запятую |
| `ADMIN_GROUP_ID` | Группа, куда приходят карточки новых заказов (необязательно) |
| `DATABASE_URL` | `sqlite+aiosqlite:///...` для разработки, `postgresql+asyncpg://...` для продакшена |
| `PAYMENT_PROVIDER` | `mock` (по умолчанию) или `yookassa` |
| `PAYMENT_API_KEY` / `PAYMENT_SECRET` | Ключи боевого провайдера |
| `PUBLIC_BASE_URL` | Публичный адрес бота — нужен для return_url и mock-чекаута |
| `REMINDER_FIRST_DELAY_MINUTES` / `REMINDER_SECOND_DELAY_MINUTES` | Интервалы напоминаний о неоплаченном заказе |
| `REDIS_URL` | Если указан — FSM-хранилище переезжает с in-memory на Redis |

Все параметры **бизнес-логики** (цена, доставка, тексты, промокоды) хранятся
в базе данных и настраиваются администратором прямо в Telegram — `.env`
содержит только инфраструктурные секреты.

## Команды администратора

Доступны только пользователям из `ADMIN_IDS`; для всех остальных полностью
не существуют (никакого ответа, никакой информации не раскрывается).

| Команда | Что делает |
|---|---|
| `/admin` | Главное меню панели управления |
| `/price` | Изменить цену за литр — применяется мгновенно |
| `/delivery` | Стоимость доставки, порог бесплатной доставки, сроки |
| `/promo` | Создание, список, включение/отключение и удаление промокодов |
| `/broadcast` | Рассылка текста/фото/видео/GIF/документа всем пользователям с превью и отчётом |
| `/stats` | Статистика за сегодня/неделю/месяц/всё время + воронка конверсии |
| `/orders` | Последние заказы, поиск по номеру, фильтр неоплаченных, экспорт в CSV, смена статуса, сообщение клиенту |
| `/logs` | Просмотр последних записей лога по уровню (ERROR/WARNING/INFO) |

Каждое административное изменение пишется в таблицу `admin_audit_log`
(кто, когда, что изменил, старое и новое значение).

## Платёжная интеграция

Бизнес-логика работает через интерфейс `PaymentProvider`
(`app/payments/base.py`) и никогда не обращается к конкретному провайдеру
напрямую:

```python
class PaymentProvider(ABC):
    async def create_payment(self, *, order_id, order_number, amount, description, return_url) -> CreatedPayment: ...
    async def get_status(self, provider_payment_id) -> PaymentStatusResult: ...
    def parse_webhook(self, body, headers, remote_ip) -> PaymentStatusResult | None: ...
```

- **`mock`** (`app/payments/mock_provider.py`) — работает полностью локально,
  без внешних ключей. Используется для разработки и демонстрации.
- **`yookassa`** (`app/payments/yookassa_provider.py`) — боевая интеграция с
  ЮKassa: создание платежа, опрос статуса, разбор webhook с проверкой IP
  отправителя, повторные попытки при недоступности API (1с → 2с → 5с → 10с).

Чтобы подключить другой платёжный сервис, добавьте новый класс,
реализующий `PaymentProvider`, и одну ветку в
`app/payments/factory.py::get_payment_provider()` — остальной проект
трогать не нужно.

Webhook-эндпоинт единый для любого провайдера:
`POST {PUBLIC_BASE_URL}{PAYMENT_WEBHOOK_PATH}/{provider}`. Обработка
идемпотентна: повторный webhook по уже подтверждённому платежу не создаёт
второй заказ и не отправляет повторное уведомление.

## Тесты и статический анализ

```bash
pytest                      # 41 тест: сервисы, репозитории, провайдер, валидация, FSM
ruff check app tests        # линтер + сортировка импортов
black --check app tests     # форматирование
mypy app                    # типы
```

## FAQ для разработчика

**Почему в заказе нет прямой FK на конкретный платёж?**
Один заказ может пройти несколько попыток оплаты (отмена → повтор), поэтому
связь `Order → Payment` сделана как one-to-many
(`order.payments`, `order.current_payment`). Обратная FK `Order.payment_id`
создавала бы циклическую зависимость внешних ключей между таблицами
`orders` и `payments`.

**Почему цены — целые числа, а не float?**
Все денежные суммы хранятся в копейках (`Integer`), чтобы избежать ошибок
округления с плавающей точкой в финансовых расчётах.

**Почему `id` — не всегда `BigInteger` в SQLite?**
SQLite даёт автоинкремент через ROWID только колонке, объявленной ровно как
`INTEGER PRIMARY KEY`; `BIGINT PRIMARY KEY` этим свойством не обладает. Тип
`BigIntPK` (`app/database/base.py`) — это `BigInteger`, кроме SQLite, где
используется обычный `Integer`. На PostgreSQL все ID остаются `BIGINT`.

**Как поменять оформление приветственного сообщения или баннер?**
`welcome_text` и `banner_file_id` хранятся в таблице `bot_settings`; чтобы
задать баннер, отправьте боту фото в личном чате (используя `/broadcast`
как отправную точку для получения `file_id`), затем обновите поле через БД
или расширьте `/admin` соответствующим пунктом меню.

**Как добавить новый пункт FAQ?**
Список вопросов и ответов сейчас формируется в `app/handlers/faq.py::_build_faq_items` —
добавьте кортеж `(id, вопрос, ответ)`.

**Что нужно настроить перед первым запуском в продакшене?**
1. `BOT_TOKEN` и `ADMIN_IDS` — обязательно.
2. `DATABASE_URL` — на PostgreSQL.
3. `PUBLIC_BASE_URL` — реальный HTTPS-адрес сервера (для return_url и webhook).
4. `PAYMENT_PROVIDER=yookassa` + `PAYMENT_API_KEY` + `PAYMENT_SECRET`.
5. Настроить реверс-прокси/сертификат для порта `PAYMENT_WEBHOOK_PORT`,
   чтобы платёжный провайдер мог достучаться до webhook.
