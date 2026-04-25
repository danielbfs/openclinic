"""Telegram bot adapter — receive and send messages via Telegram Bot API."""
import logging

import httpx

from app.config import settings
from app.modules.messaging.schemas import IncomingMessage

logger = logging.getLogger(__name__)

TELEGRAM_API = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}"


def parse_telegram_update(payload: dict) -> IncomingMessage | None:
    """Parse a Telegram webhook update into a normalized IncomingMessage."""
    message = payload.get("message")
    if not message:
        return None

    text = message.get("text")
    if not text:
        return None

    from_user = message.get("from", {})
    chat = message.get("chat", {})

    first = from_user.get("first_name", "")
    last = from_user.get("last_name", "")
    user_name = f"{first} {last}".strip() or None

    return IncomingMessage(
        channel="telegram",
        channel_user_id=str(from_user.get("id", "")),
        channel_chat_id=str(chat.get("id", "")),
        user_name=user_name,
        text=text,
    )


async def send_telegram_message(chat_id: str, text: str) -> bool:
    """Send a text message via Telegram Bot API."""
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN not configured, skipping send")
        return False

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            f"{TELEGRAM_API}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "Markdown",
            },
        )
        if resp.status_code != 200:
            logger.error("Telegram send failed: %s %s", resp.status_code, resp.text)
            return False
        return True


async def set_telegram_webhook(url: str) -> bool:
    """Register the webhook URL with Telegram."""
    if not settings.TELEGRAM_BOT_TOKEN:
        return False

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            f"{TELEGRAM_API}/setWebhook",
            json={"url": url, "allowed_updates": ["message"]},
        )
        logger.info("setWebhook response: %s", resp.json())
        return resp.status_code == 200
