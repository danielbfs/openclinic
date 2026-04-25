"""Follow-up Celery tasks — sends scheduled follow-up messages."""
import asyncio
import logging
import uuid

from celery_app import celery_app

logger = logging.getLogger(__name__)


def _run_async(coro):
    """Run an async function from a sync Celery task."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=300, queue="followup")
def send_followup_message(self, job_id: str):
    """Send a single follow-up message for a scheduled job."""
    _run_async(_send_followup(self, job_id))


async def _send_followup(task, job_id: str):
    from app.database import AsyncSessionLocal
    from app.modules.followup.models import FollowupJob
    from app.modules.crm.models import Patient
    from app.modules.scheduling.models import Appointment
    from app.modules.messaging.gateway import send_message
    from sqlalchemy import select
    from datetime import datetime, timezone

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(FollowupJob).where(FollowupJob.id == uuid.UUID(job_id))
        )
        job = result.scalar_one_or_none()
        if not job:
            logger.error("Follow-up job %s not found", job_id)
            return

        if job.status != "pending":
            logger.info("Job %s already processed (status=%s)", job_id, job.status)
            return

        # Load related objects
        patient = await db.get(Patient, job.patient_id)
        if not patient:
            job.status = "failed"
            job.error_message = "Patient not found"
            job.executed_at = datetime.now(timezone.utc)
            await db.commit()
            return

        appointment = await db.get(Appointment, job.appointment_id)

        # Render template
        rule = job.rule
        message = rule.message_template
        if patient.full_name:
            message = message.replace("{patient_name}", patient.full_name)
        if appointment:
            message = message.replace(
                "{appointment_date}",
                appointment.starts_at.strftime("%d/%m/%Y às %H:%M"),
            )

        # Determine channel
        channel = rule.channel or patient.channel
        chat_id = patient.channel_id

        if not chat_id:
            job.status = "failed"
            job.error_message = "Patient has no channel_id"
            job.executed_at = datetime.now(timezone.utc)
            await db.commit()
            return

        try:
            success = await send_message(channel, chat_id, message)
            if success:
                job.status = "sent"
            else:
                job.status = "failed"
                job.error_message = "Message send returned false"
        except Exception as exc:
            job.status = "failed"
            job.error_message = str(exc)[:500]
            logger.exception("Failed to send follow-up %s", job_id)
            await db.commit()
            raise task.retry(exc=exc)

        job.executed_at = datetime.now(timezone.utc)
        await db.commit()
        logger.info("Follow-up job %s completed: %s", job_id, job.status)


@celery_app.task(queue="followup")
def process_pending_followups():
    """Scan for pending follow-up jobs that are due and dispatch them."""
    _run_async(_process_pending())


async def _process_pending():
    from app.database import AsyncSessionLocal
    from app.modules.followup.models import FollowupJob
    from sqlalchemy import select, and_
    from datetime import datetime, timezone

    async with AsyncSessionLocal() as db:
        now = datetime.now(timezone.utc)
        result = await db.execute(
            select(FollowupJob).where(
                and_(
                    FollowupJob.status == "pending",
                    FollowupJob.scheduled_for <= now,
                )
            )
        )
        jobs = list(result.scalars().all())

        for job in jobs:
            send_followup_message.delay(str(job.id))

        if jobs:
            logger.info("Dispatched %d pending follow-up jobs", len(jobs))
