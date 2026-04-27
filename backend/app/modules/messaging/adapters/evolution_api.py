"""Evolution API adapter — receive and send messages via WhatsApp."""
import logging
import httpx
from app.config import settings
from app.modules.messaging.adapters.base import AbstractMessagingAdapter
from app.modules.messaging.schemas import IncomingMessage

logger = logging.getLogger(__name__)

class EvolutionApiAdapter(AbstractMessagingAdapter):
    def __init__(self):
        self.base_url = settings.EVOLUTION_API_URL.rstrip("/")
        self.api_key = settings.EVOLUTION_API_KEY
        self.instance_name = settings.EVOLUTION_INSTANCE_NAME

    async def send_message(self, chat_id: str, text: str) -> bool:
        """Send a text message via Evolution API."""
        if not self.api_key or not self.instance_name:
            logger.warning("Evolution API not configured, skipping send")
            return False

        url = f"{self.base_url}/message/sendText/{self.instance_name}"
        headers = {
            "apikey": self.api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "number": chat_id,
            "options": {"delay": 1200, "presence": "composing"},
            "textMessage": {"text": text},
        }

        async with httpx.AsyncClient(timeout=10) as client:
            try:
                resp = await client.post(url, json=payload, headers=headers)
                if resp.status_code not in (200, 201):
                    logger.error("Evolution API send failed: %s %s", resp.status_code, resp.text)
                    return False
                return True
            except Exception as e:
                logger.exception("Error sending message via Evolution API: %s", e)
                return False

    def parse_webhook(self, payload: dict) -> IncomingMessage | None:
        """Parse Evolution API webhook payload into a normalized IncomingMessage."""
        # Evolution API sends different event types. We only care about 'messages.upsert'
        event = payload.get("event")
        if event != "messages.upsert":
            return None

        data = payload.get("data", {})
        message = data.get("message", {})
        
        # We only handle text messages for now
        text = message.get("conversation")
        if not text:
            return None

        remote_jid = data.get("remoteJid", "")
        # remove @s.whatsapp.net suffix if present
        phone = remote_jid.split("@")[0] if "@" in remote_jid else remote_jid

        push_name = data.get("pushName")

        return IncomingMessage(
            channel="whatsapp",
            channel_user_id=phone,
            channel_chat_id=phone,
            user_name=push_name,
            text=text,
        )
