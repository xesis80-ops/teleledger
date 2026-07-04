"""
Sweeps the `reminders` table every 5 minutes and pushes due ones via the
Telegram Bot API sendMessage endpoint. Wired up in core/apps.py on startup.
"""
import logging

import requests
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

TELEGRAM_API_URL = "https://api.telegram.org/bot{token}/sendMessage"


def send_due_reminders():
    from .models import Reminder  # local import avoids AppRegistryNotReady at boot

    due = Reminder.objects.filter(is_sent=False, remind_at__lte=timezone.now())
    if not due.exists():
        return

    url = TELEGRAM_API_URL.format(token=settings.TELEGRAM_BOT_TOKEN)
    for reminder in due:
        try:
            resp = requests.post(url, json={
                "chat_id": reminder.profile_id,
                "text": f"🔔 Reminder: {reminder.note_content}",
            }, timeout=10)
            if resp.ok:
                reminder.is_sent = True
                reminder.save(update_fields=["is_sent"])
            else:
                logger.warning("Telegram send failed for reminder %s: %s", reminder.id, resp.text)
        except requests.RequestException:
            logger.exception("Error sending reminder %s", reminder.id)


def start_scheduler():
    from apscheduler.schedulers.background import BackgroundScheduler
    from django_apscheduler.jobstores import DjangoJobStore, register_events

    scheduler = BackgroundScheduler()
    scheduler.add_jobstore(DjangoJobStore(), "default")
    scheduler.add_job(
        send_due_reminders,
        trigger="interval",
        minutes=5,
        id="send_due_reminders",
        replace_existing=True,
    )
    register_events(scheduler)
    scheduler.start()
    logger.info("APScheduler started: sweeping reminders every 5 minutes.")
