"""Base messaging adapter interface."""
from abc import ABC, abstractmethod


class AbstractMessagingAdapter(ABC):
    @abstractmethod
    async def send_message(self, chat_id: str, text: str) -> bool:
        ...

    @abstractmethod
    def parse_webhook(self, payload: dict) -> dict | None:
        ...
