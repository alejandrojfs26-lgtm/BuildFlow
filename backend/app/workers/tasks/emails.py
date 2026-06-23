"""Email tasks — transactional emails with retry and failure tracking.

Rate limits (configured in celery_app.py):
  - send_welcome_email:        10/min
  - send_password_reset_email:  5/min
  - send_report_approved_email: 20/min
"""

from app.core.email_templates import (
    password_reset_template,
    report_approved_template,
    welcome_template,
)
from app.services.email import send_email
from app.workers.celery_app import celery_app


@celery_app.task(
    bind=True,
    max_retries=5,
    default_retry_delay=60,
    max_retry_delay=3600,
    autoretry_for=(ConnectionError, TimeoutError),
    acks_late=True,
)
def send_welcome_email(self, name: str, email: str) -> None:
    subject, body = welcome_template(name, email)
    try:
        send_email(email, subject, body)
    except Exception as exc:
        raise self.retry(exc=exc)


@celery_app.task(
    bind=True,
    max_retries=5,
    default_retry_delay=60,
    max_retry_delay=3600,
    autoretry_for=(ConnectionError, TimeoutError),
    acks_late=True,
)
def send_password_reset_email(self, name: str, email: str, token: str) -> None:
    subject, body = password_reset_template(name, token)
    try:
        send_email(email, subject, body)
    except Exception as exc:
        raise self.retry(exc=exc)


@celery_app.task(
    bind=True,
    max_retries=5,
    default_retry_delay=30,
    autoretry_for=(ConnectionError, TimeoutError),
    acks_late=True,
)
def send_report_approved_email(
    self,
    worker_email: str,
    worker_name: str,
    project_name: str,
    date: str,
) -> None:
    subject, body = report_approved_template(worker_name, project_name, date)
    try:
        send_email(worker_email, subject, body)
    except Exception as exc:
        raise self.retry(exc=exc)
