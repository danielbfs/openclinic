"""Normalized message schemas for all channels."""
import uuid
from pydantic import BaseModel


class IncomingMessage(BaseModel):
    """Normalized incoming message from any channel."""
    channel: str  # "telegram", "whatsapp"
    channel_user_id: str  # user ID in the channel
    channel_chat_id: str  # chat ID in the channel
    user_name: str | None = None
    text: str


class OutgoingMessage(BaseModel):
    """Message to send back to a channel."""
    channel: str
    channel_chat_id: str
    text: str
