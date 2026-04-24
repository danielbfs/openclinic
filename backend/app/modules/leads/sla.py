"""Celery task para verificação de SLA de leads."""
import asyncio
from datetime import datetime, timezone

from sqlalchemy import select, and_

from app.database import AsyncSessionLocal
from app.modules.leads.models import Lead

from celery_app import celery_app


@celery_app.task(name="app.modules.leads.sla.check_overdue_leads")
def check_overdue_leads():
    """Verifica leads com SLA vencido. Roda a cada 15 minutos via Celery Beat."""
    asyncio.run(_check_overdue())


async def _check_overdue():
    async with AsyncSessionLocal() as db:
        now = datetime.now(timezone.utc)
        result = await db.execute(
            select(Lead).where(
                and_(
                    Lead.contacted_at.is_(None),
                    Lead.sla_deadline < now,
                    Lead.status.in_(["novo", "em_contato"]),
                )
            )
        )
        overdue_leads = result.scalars().all()

        if overdue_leads:
            # TODO: Enviar notificação para secretária responsável
            # via Telegram ou outro canal quando implementado
            print(f"[SLA] {len(overdue_leads)} lead(s) com SLA vencido.")
            for lead in overdue_leads:
                print(f"  - {lead.full_name or lead.phone} (deadline: {lead.sla_deadline})")
