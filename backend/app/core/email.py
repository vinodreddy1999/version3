import logging
import smtplib
from email.message import EmailMessage
from typing import Protocol

from app.core.config import settings

logger = logging.getLogger("app.email")


class EmailBackend(Protocol):
    def send(self, to: str, subject: str, body: str) -> None: ...


class ConsoleEmailBackend:
    """Logs the email instead of sending it. Dev-only fallback used when no
    SMTP server is configured — never rely on this in a shared/deployed
    environment; set the SMTP_* env vars to send real email there."""

    def send(self, to: str, subject: str, body: str) -> None:
        logger.warning("No SMTP configured — logging email instead of sending.\nTo: %s\nSubject: %s\n%s", to, subject, body)


class SMTPEmailBackend:
    def __init__(self, host: str, port: int, username: str, password: str, from_email: str, use_tls: bool) -> None:
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.from_email = from_email
        self.use_tls = use_tls

    def send(self, to: str, subject: str, body: str) -> None:
        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = self.from_email
        message["To"] = to
        message.set_content(body)

        with smtplib.SMTP(self.host, self.port) as server:
            if self.use_tls:
                server.starttls()
            if self.username:
                server.login(self.username, self.password)
            server.send_message(message)


def _build_email_backend() -> EmailBackend:
    if settings.smtp_host:
        return SMTPEmailBackend(
            host=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_username,
            password=settings.smtp_password,
            from_email=settings.smtp_from_email,
            use_tls=settings.smtp_use_tls,
        )
    return ConsoleEmailBackend()


email_backend: EmailBackend = _build_email_backend()


def get_email_backend() -> EmailBackend:
    return email_backend
