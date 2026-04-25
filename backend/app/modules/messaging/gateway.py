"""Messaging gateway — routes messages to the right channel adapter."""
import logging

from app.modules.messaging.adapters.telegram import send_telegram_message

logger = logging.getLogger(__name__)


async def send_message(channel: str, chat_id: str, text: str) -> bool:
    """Send a message through the appropriate channel."""
    if channel == "telegram":
        return await send_telegram_message(chat_id, text)
    logger.warning("Unsupported channel: %s", channel)
    return False
