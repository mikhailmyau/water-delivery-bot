"""aiohttp-сервер приёма webhook-уведомлений от платёжного провайдера.

Работает параллельно с polling-ом Telegram-апдейтов (см. app/bot.py). Один и
тот же маршрут /payments/webhook/{provider} обслуживает любой провайдер,
реализующий PaymentProvider — переключение на боевой шлюз не требует правок
здесь (ТЗ, глава 65).
"""

from __future__ import annotations

import logging

from aiogram import Bot
from aiohttp import web

from app.config import settings
from app.database.repositories.payment_repository import PaymentRepository
from app.database.session import async_session_factory
from app.payments.factory import get_payment_provider
from app.services.payment_service import PaymentService
from app.utils.money import format_price

logger = logging.getLogger("app.webhook")

_MOCK_CHECKOUT_PAGE = """<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Тестовая оплата</title>
<style>
  body {{ font-family: -apple-system, Segoe UI, Roboto, sans-serif; background: #f5f6f8;
         display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }}
  .card {{ background: #fff; border-radius: 16px; padding: 32px; max-width: 360px; width: 90%;
          box-shadow: 0 8px 24px rgba(0,0,0,.08); text-align: center; }}
  h1 {{ font-size: 20px; margin: 0 0 8px; }}
  p {{ color: #666; margin: 0 0 24px; }}
  .amount {{ font-size: 28px; font-weight: 700; margin-bottom: 24px; }}
  button {{ width: 100%; padding: 14px; border-radius: 10px; border: none; font-size: 16px;
           cursor: pointer; margin-bottom: 10px; }}
  .pay {{ background: #2AABEE; color: #fff; }}
  .cancel {{ background: #eee; color: #333; }}
  #status {{ margin-top: 16px; color: #2AABEE; font-weight: 600; }}
</style>
</head>
<body>
  <div class="card">
    <h1>💧 Оплата заказа</h1>
    <p>Тестовый платёжный провайдер (mock)</p>
    <div class="amount">{amount}</div>
    <button class="pay" onclick="send('succeeded')">Оплатить</button>
    <button class="cancel" onclick="send('canceled')">Отменить</button>
    <div id="status"></div>
  </div>
  <script>
    async function send(status) {{
      document.getElementById('status').textContent = 'Обработка...';
      const response = await fetch('{webhook_path}/mock', {{
        method: 'POST',
        headers: {{'Content-Type': 'application/json'}},
        body: JSON.stringify({{
          provider_payment_id: '{payment_id}',
          status: status,
          amount: {amount_kopecks}
        }})
      }});
      if (response.ok) {{
        document.getElementById('status').textContent = status === 'succeeded'
          ? 'Оплата прошла успешно! Вернитесь в Telegram.'
          : 'Платёж отменён. Вернитесь в Telegram.';
      }} else {{
        document.getElementById('status').textContent = 'Ошибка обработки платежа.';
      }}
    }}
  </script>
</body>
</html>"""


async def handle_mock_checkout_page(request: web.Request) -> web.Response:
    payment_id = request.match_info["payment_id"]
    async with async_session_factory() as session:
        payment = await PaymentRepository(session).get_by_provider_payment_id(payment_id)
    if payment is None:
        return web.Response(status=404, text="Платёж не найден")
    html = _MOCK_CHECKOUT_PAGE.format(
        amount=format_price(payment.amount),
        amount_kopecks=payment.amount,
        payment_id=payment_id,
        webhook_path=settings.payment_webhook_path,
    )
    return web.Response(text=html, content_type="text/html")


async def handle_payment_webhook(request: web.Request) -> web.Response:
    provider_name = request.match_info["provider"]
    provider = get_payment_provider()
    if provider.name != provider_name:
        return web.Response(status=404)

    body = await request.read()
    headers = dict(request.headers)
    remote_ip = request.remote

    try:
        status_result = provider.parse_webhook(body, headers, remote_ip)
    except Exception:
        logger.exception("Failed to parse payment webhook body")
        return web.Response(status=400)

    if status_result is None:
        return web.json_response({"status": "ignored"})

    bot: Bot = request.app["bot"]
    async with async_session_factory() as session:
        payment_service = PaymentService(session, provider, bot)
        order = await payment_service.handle_status_result(status_result)
        await session.commit()

    if order is not None:
        logger.info("Webhook processed: order=%s", order.order_number)
    return web.json_response({"status": "ok"})


def create_webhook_app(bot: Bot) -> web.Application:
    app = web.Application()
    app["bot"] = bot
    app.router.add_post(f"{settings.payment_webhook_path}/{{provider}}", handle_payment_webhook)
    app.router.add_get("/payments/mock-checkout/{payment_id}", handle_mock_checkout_page)
    return app
