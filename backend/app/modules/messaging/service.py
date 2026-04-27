"""Service for managing messaging conversations."""
import uuid
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.messaging.models import Conversation, Message

class MessagingService:
    async def get_active_conversations(self, db: AsyncSession, channel: str | None = None):
        """Get all active conversations, optionally filtered by channel."""
        query = select(Conversation).where(Conversation.status == "active")
        if channel:
            query = query.where(Conversation.channel == channel)
        
        result = await db.execute(query)
        return result.scalars().all()

    async def toggle_control(self, db: AsyncSession, conversation_id: uuid.UUID, control: str):
        """Switch control between 'ai' and 'human'."""
        if control not in ("ai", "human"):
            raise ValueError("Control must be either 'ai' or 'human'")
        
        await db.execute(
            update(Conversation)
            .where(Conversation.id == conversation_id)
            .values(control=control)
        )
        await db.commit()
        return True

    async def send_human_message(self, db: AsyncSession, conversation_id: uuid.UUID, text: str, channel: str, chat_id: str):
        """Send a message on behalf of a human and record it in the DB."""
        from app.modules.messaging.gateway import gateway
        
        # Send via adapter
        success = await gateway.send_message(channel, chat_id, text)
        if not success:
            return False

        # Record message
        msg = Message(
            conversation_id=conversation_id,
            role="assistant", # marked as assistant because it's a reply to the user
            content=text,
            metadata_json={"sender": "human"}
        )
        db.add(msg)
        await db.commit()
        return True

messaging_service = MessagingService()
