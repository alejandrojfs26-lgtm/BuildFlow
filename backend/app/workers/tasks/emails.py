from app.core.email_templates import (
    password_reset_template,
    report_approved_template,
    welcome_template,
)
from app.services.email import send_email
from app.workers.celery_app import celery_app


@celery_app.task
def send_welcome_email(name: str, email: str) -> None:
    subject, body = welcome_template(name, email)
    send_email(email, subject, body)


@celery_app.task
def send_password_reset_email(name: str, email: str, token: str) -> None:
    subject, body = password_reset_template(name, token)
    send_email(email, subject, body)


@celery_app.task
def send_report_approved_email(
    worker_email: str, worker_name: str, project_name: str, date: str
) -> None:
    subject, body = report_approved_template(worker_name, project_name, date)
    send_email(worker_email, subject, body)
