import logging

from app.models.email import Email


log = logging.getLogger(__name__)


def send_daily_digest(user_email: str, emails: list[Email]) -> None:
    # Stub implementation: log the digest. Wire up Email/Telegram/Slack later.
    subjects = [e.subject or "(no subject)" for e in emails[:20]]
    log.info("Daily digest to %s (%d emails): %s", user_email, len(emails), subjects)
